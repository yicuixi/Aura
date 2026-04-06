"""
Aura AI FastAPI 服务
提供 RESTful API 接口访问 Aura ReAct Agent
集成安全中间件：API Key 认证、速率限制、输入校验、审计日志
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

from security import (
    SecurityConfig,
    verify_api_key,
    sanitize_query,
    validate_file_path,
    mask_pii,
    audit_log,
    setup_audit_log,
)

logger = logging.getLogger("AuraAPI")

# ---------------------------------------------------------------------------
# 速率限制（基于内存的简易令牌桶）
# ---------------------------------------------------------------------------
from collections import defaultdict
import time

class RateLimiter:
    """令牌桶速率限制器"""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > window_start
        ]
        if len(self._requests[client_id]) >= self.max_requests:
            return False
        self._requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


# ---------------------------------------------------------------------------
# Lifespan（启动/关闭）
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_audit_log()
    audit_log("server_start", "Aura API 服务启动")
    yield
    audit_log("server_stop", "Aura API 服务关闭")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Aura AI API",
    description="本地AI助手API服务（隐私优先）",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.environ.get("AURA_ENV") != "production" else None,
    redoc_url=None,
)

# CORS —— 收紧来源
allowed_origins = os.environ.get("AURA_CORS_ORIGINS", "").split(",")
allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
if not allowed_origins:
    allowed_origins = SecurityConfig.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


# ---------------------------------------------------------------------------
# 安全头中间件
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# API Key 认证依赖
# ---------------------------------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
):
    """校验 API Key；未设置 AURA_API_KEY 时放行（开发模式）"""
    if not os.environ.get("AURA_API_KEY"):
        return True

    if not api_key:
        audit_log("auth_fail", "缺少 API Key", client_ip=request.client.host)
        raise HTTPException(status_code=401, detail="缺少 API Key")

    if not verify_api_key(api_key):
        audit_log("auth_fail", "无效 API Key", client_ip=request.client.host)
        raise HTTPException(status_code=403, detail="无效的 API Key")

    return True


# ---------------------------------------------------------------------------
# 速率限制依赖
# ---------------------------------------------------------------------------
async def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        audit_log("rate_limited", f"IP {client_ip} 触发速率限制")
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


# ---------------------------------------------------------------------------
# Agent 延迟加载
# ---------------------------------------------------------------------------
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from aura_react import AuraReActAgent
        _agent = AuraReActAgent()
    return _agent


# ---------------------------------------------------------------------------
# 请求/响应模型（带校验）
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    use_tools: bool = True


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    error: Optional[str] = None


class KnowledgeRequest(BaseModel):
    file_path: str = Field(..., min_length=1, max_length=260)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Aura AI API", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(require_api_key), Depends(check_rate_limit)],
)
async def chat(request: ChatRequest, raw_request: Request):
    """与 Aura 对话"""
    try:
        clean_query = sanitize_query(request.query)
        audit_log(
            "chat_request",
            mask_pii(clean_query[:120]),
            client_ip=raw_request.client.host,
        )
        agent = get_agent()
        response = agent.process_query(clean_query)
        return ChatResponse(response=response, success=True)
    except ValueError as e:
        return ChatResponse(response="", success=False, error=str(e))
    except Exception as e:
        logger.error("chat 处理异常: %s", e)
        return ChatResponse(response="", success=False, error="内部错误")


@app.post(
    "/knowledge/add",
    dependencies=[Depends(require_api_key), Depends(check_rate_limit)],
)
async def add_knowledge(request: KnowledgeRequest, raw_request: Request):
    """添加知识到 RAG（路径限制在 data/ 目录）"""
    try:
        safe_path = validate_file_path(request.file_path)
        audit_log(
            "knowledge_add", safe_path,
            client_ip=raw_request.client.host,
        )
        agent = get_agent()
        agent.rag_system.add_documents(safe_path)
        return {"success": True, "message": f"已添加: {safe_path}"}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("knowledge/add 异常: %s", e)
        raise HTTPException(status_code=500, detail="内部错误")


@app.get(
    "/knowledge/search",
    dependencies=[Depends(require_api_key), Depends(check_rate_limit)],
)
async def search_knowledge(
    query: str,
    top_k: int = Field(default=3, ge=1, le=20),
    hybrid: bool = True,
    raw_request: Request = None,
):
    """搜索知识库（支持多路召回）"""
    try:
        clean_query = sanitize_query(query)
        agent = get_agent()
        if hybrid:
            results = agent.rag_system.hybrid_search(
                clean_query, k=top_k, use_rerank=True
            )
        else:
            results = agent.rag_system.search(clean_query, k=top_k)

        result_list = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in results
        ]
        return {
            "success": True,
            "results": result_list,
            "mode": "hybrid" if hybrid else "vector",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("knowledge/search 异常: %s", e)
        raise HTTPException(status_code=500, detail="内部错误")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
