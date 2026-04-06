"""
Aura AI - 安全与隐私核心模块
PII 检测/脱敏、输入清洗、路径沙箱、加密工具、审计日志
"""

import os
import re
import hashlib
import logging
import secrets
import base64
from datetime import datetime
from typing import Optional
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("AuraSecurity")

# ---------------------------------------------------------------------------
# PII 检测与脱敏
# ---------------------------------------------------------------------------

PII_PATTERNS = {
    "phone_cn": re.compile(r"1[3-9]\d{9}"),
    "id_card_cn": re.compile(r"\d{17}[\dXx]"),
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "bank_card": re.compile(r"\b\d{16,19}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "passport_cn": re.compile(r"[EeGg]\d{8}"),
}

MASK_MAP = {
    "phone_cn": lambda m: m[:3] + "****" + m[-4:],
    "id_card_cn": lambda m: m[:4] + "**********" + m[-4:],
    "email": lambda m: m.split("@")[0][:2] + "***@" + m.split("@")[1],
    "bank_card": lambda m: m[:4] + " **** **** " + m[-4:],
    "ip_address": lambda m: "***.***.***.***",
    "passport_cn": lambda m: m[:2] + "******" + m[-1:],
}


def detect_pii(text: str) -> list[dict]:
    """检测文本中的 PII（个人身份信息）"""
    findings = []
    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append({
                "type": pii_type,
                "value": match.group(),
                "start": match.start(),
                "end": match.end(),
            })
    return findings


def mask_pii(text: str) -> str:
    """对文本中的 PII 进行脱敏处理"""
    masked = text
    for pii_type, pattern in PII_PATTERNS.items():
        mask_fn = MASK_MAP.get(pii_type, lambda m: "***")
        masked = pattern.sub(lambda m: mask_fn(m.group()), masked)
    return masked


# ---------------------------------------------------------------------------
# 输入验证与清洗
# ---------------------------------------------------------------------------

MAX_QUERY_LENGTH = 4096
MAX_PATH_LENGTH = 260

DANGEROUS_PATTERNS = [
    re.compile(r"<script\b", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"\{\{.*\}\}"),              # template injection
    re.compile(r"\$\{.*\}"),                # expression injection
    re.compile(r"__(import|class|subclasses)__"),  # Python sandbox escape
]


def sanitize_query(query: str) -> str:
    """清洗用户查询输入"""
    if not query or not query.strip():
        raise ValueError("查询内容不能为空")

    query = query.strip()

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"查询内容过长（最大 {MAX_QUERY_LENGTH} 字符）")

    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(query):
            logger.warning("检测到危险输入模式: %s", pattern.pattern)
            raise ValueError("输入包含不允许的内容")

    return query


def validate_file_path(file_path: str, allowed_dirs: list[str] | None = None) -> str:
    """
    校验文件路径，防止路径遍历攻击。
    返回规范化后的绝对路径。
    """
    if not file_path:
        raise ValueError("文件路径不能为空")

    if len(file_path) > MAX_PATH_LENGTH:
        raise ValueError("文件路径过长")

    normalized = os.path.normpath(os.path.abspath(file_path))

    if allowed_dirs is None:
        project_root = os.path.dirname(os.path.abspath(__file__))
        allowed_dirs = [
            os.path.join(project_root, "data"),
            os.path.join(project_root, "logs"),
        ]

    allowed_dirs = [os.path.normpath(os.path.abspath(d)) for d in allowed_dirs]
    if not any(normalized.startswith(d) for d in allowed_dirs):
        raise PermissionError(
            f"访问被拒绝: 路径不在允许范围内（允许: {allowed_dirs}）"
        )

    return normalized


# ---------------------------------------------------------------------------
# 加密工具（Fernet 对称加密，密钥从主密码派生）
# ---------------------------------------------------------------------------

_SALT_FILE = ".aura_salt"


def _get_or_create_salt() -> bytes:
    """获取或生成加密盐值，存储在项目根目录"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    salt_path = os.path.join(project_root, _SALT_FILE)

    if os.path.exists(salt_path):
        with open(salt_path, "rb") as f:
            return f.read()

    salt = os.urandom(16)
    with open(salt_path, "wb") as f:
        f.write(salt)
    return salt


def derive_key(master_password: str) -> bytes:
    """从主密码派生 Fernet 密钥（PBKDF2）"""
    salt = _get_or_create_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return key


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    """获取 Fernet 实例（密钥从环境变量 AURA_MASTER_KEY 派生）"""
    master_key = os.environ.get("AURA_MASTER_KEY", "")
    if not master_key:
        logger.warning(
            "未设置 AURA_MASTER_KEY 环境变量，使用默认密钥（仅适用于开发环境）"
        )
        master_key = "aura-dev-default-key-change-me"
    return Fernet(derive_key(master_key))


def encrypt_text(plaintext: str) -> str:
    """加密文本，返回 base64 编码的密文"""
    return get_fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_text(ciphertext: str) -> str:
    """解密文本"""
    return get_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")


# ---------------------------------------------------------------------------
# API 安全
# ---------------------------------------------------------------------------

def generate_api_key() -> str:
    """生成安全的 API Key"""
    return f"aura_{secrets.token_urlsafe(32)}"


def verify_api_key(provided_key: str) -> bool:
    """验证 API Key（常数时间比较，防止时序攻击）"""
    expected_key = os.environ.get("AURA_API_KEY", "")
    if not expected_key:
        logger.warning("未设置 AURA_API_KEY，API 认证已禁用")
        return True
    return secrets.compare_digest(provided_key, expected_key)


# ---------------------------------------------------------------------------
# 审计日志
# ---------------------------------------------------------------------------

_audit_logger = logging.getLogger("AuraAudit")


def setup_audit_log(log_dir: str = "logs"):
    """初始化审计日志（写入独立文件）"""
    os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(
        os.path.join(log_dir, "audit.log"), encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    _audit_logger.addHandler(handler)
    _audit_logger.setLevel(logging.INFO)


def audit_log(event: str, details: str = "", client_ip: str = ""):
    """记录审计事件（自动脱敏）"""
    safe_details = mask_pii(details) if details else ""
    _audit_logger.info(
        "event=%s | ip=%s | details=%s",
        event, client_ip or "unknown", safe_details,
    )


# ---------------------------------------------------------------------------
# 安全配置汇总
# ---------------------------------------------------------------------------

class SecurityConfig:
    """集中管理安全策略"""

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    RATE_LIMIT = "30/minute"

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'self'",
    }

    FILE_SANDBOX_DIRS: list[str] = ["data", "logs"]
