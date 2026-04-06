"""
归一化模块 — 技能同义词 & 学校别称 & 学历映射
"""

# === 技能同义词表 ===
# key = 标准名(小写), values = 所有别称(小写)
_SKILL_SYNONYM_RAW: dict[str, list[str]] = {
    # 编程语言
    "python": ["py", "python3", "python2"],
    "javascript": ["js", "es6", "es2015", "ecmascript"],
    "typescript": ["ts"],
    "c++": ["cpp", "c plus plus", "cplusplus"],
    "c#": ["csharp", "c sharp"],
    "c": [],
    "java": [],
    "golang": ["go"],
    "rust": [],
    "sql": ["mysql", "postgresql", "postgres", "pg", "sqlite", "mssql", "oracle"],
    "r": [],
    "swift": [],
    "kotlin": ["kt"],
    "scala": [],
    "ruby": ["rb"],
    "php": [],
    "shell": ["bash", "sh", "zsh", "powershell"],
    "lua": [],

    # 前端
    "react": ["react.js", "reactjs", "react js"],
    "vue": ["vue.js", "vuejs", "vue2", "vue3"],
    "angular": ["angular.js", "angularjs"],
    "next.js": ["nextjs", "next"],
    "nuxt.js": ["nuxtjs", "nuxt"],
    "webpack": [],
    "vite": [],
    "tailwind": ["tailwindcss", "tailwind css"],
    "html": ["html5"],
    "css": ["css3", "scss", "sass", "less"],
    "electron": [],

    # 后端
    "spring": ["spring boot", "springboot", "spring framework", "spring cloud", "springcloud"],
    "django": [],
    "flask": [],
    "fastapi": ["fast api"],
    "express": ["express.js", "expressjs"],
    "node.js": ["nodejs", "node"],
    "gin": [],
    "nest.js": ["nestjs"],
    "graphql": ["gql"],

    # AI/ML
    "pytorch": ["torch"],
    "tensorflow": ["tf", "tensorflow2"],
    "keras": [],
    "scikit-learn": ["sklearn", "scikit learn"],
    "pandas": ["pd"],
    "numpy": ["np"],
    "opencv": ["cv2"],
    "langchain": ["lang chain"],
    "rag": ["retrieval augmented generation", "检索增强生成"],
    "agent": ["ai agent", "llm agent", "agent开发"],
    "mcp": ["model context protocol"],
    "prompt engineering": ["prompt", "提示词工程"],
    "transformer": ["transformers"],
    "huggingface": ["hf", "hugging face"],
    "onnx": [],
    "tensorrt": ["trt", "tensorrt-llm", "trt-llm"],
    "vllm": [],
    "sglang": [],
    "ollama": [],
    "大模型": ["llm", "large language model", "大语言模型"],
    "深度学习": ["deep learning", "dl"],
    "机器学习": ["machine learning", "ml"],
    "自然语言处理": ["nlp", "natural language processing"],
    "计算机视觉": ["cv", "computer vision"],
    "模型量化": ["int8", "fp16", "int4", "量化", "quantization", "ptq", "qat"],
    "模型微调": ["fine-tune", "finetuning", "fine tuning", "lora", "qlora", "sft"],

    # 测试
    "pytest": ["py.test"],
    "junit": [],
    "selenium": [],
    "playwright": ["playwright ui", "playwright自动化", "playwright ui自动化"],
    "cypress": [],
    "appium": [],
    "jmeter": [],
    "k6": ["grafana k6"],
    "postman": [],
    "接口测试": ["api测试", "api testing", "api test"],
    "自动化测试": ["automation testing", "test automation", "自动化"],
    "性能测试": ["performance testing", "压测", "压力测试", "并发测试", "负载测试",
                "k6并发/性能测试", "k6并发", "k6性能"],
    "ui测试": ["ui自动化", "ui自动化测试", "e2e测试", "端到端测试"],
    "单元测试": ["unit test", "unit testing"],
    "测试开发": ["sdet", "test dev", "软件测试开发", "测试开发工程师"],

    # DevOps / 工具
    "docker": ["container", "容器"],
    "kubernetes": ["k8s"],
    "git": ["github", "gitlab", "gitee"],
    "ci/cd": ["cicd", "持续集成", "持续部署", "github actions", "jenkins",
              "gitlab ci", "ci/cd(github actions)"],
    "linux": ["ubuntu", "centos", "debian", "redhat"],
    "nginx": [],
    "redis": [],
    "mongodb": ["mongo"],
    "elasticsearch": ["es", "elastic"],
    "kafka": [],
    "rabbitmq": [],
    "grpc": [],
    "restful": ["rest api", "rest"],
    "jira": [],
    "confluence": [],

    # 云平台
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "阿里云": ["aliyun"],
    "腾讯云": ["tencent cloud"],
}

# 构建反向索引: alias -> canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in _SKILL_SYNONYM_RAW.items():
    _key = _canonical.lower().strip()
    _ALIAS_TO_CANONICAL[_key] = _key
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_a.lower().strip()] = _key


def normalize_skill(raw: str) -> str:
    """将技能名归一化为标准名，匹配不到则返回原名小写"""
    key = raw.lower().strip()
    return _ALIAS_TO_CANONICAL.get(key, key)


def normalize_skills(raw_list: list[str]) -> set[str]:
    """批量归一化技能列表，返回去重集合"""
    result = set()
    for s in raw_list:
        result.add(normalize_skill(s))
    return result


# === 学校别称表 ===
_SCHOOL_ALIASES: dict[str, list[str]] = {
    "北京大学": ["北大", "pku", "peking university"],
    "清华大学": ["清华", "thu", "tsinghua"],
    "浙江大学": ["浙大", "zju", "zhejiang university"],
    "复旦大学": ["复旦", "fudan"],
    "上海交通大学": ["上交", "交大", "sjtu", "shanghai jiao tong"],
    "中国科学技术大学": ["中科大", "ustc", "科大"],
    "南京大学": ["南大", "nju", "nanjing university"],
    "哈尔滨工业大学": ["哈工大", "hit"],
    "西安交通大学": ["西交", "xjtu"],
    "华中科技大学": ["华科", "hust"],
    "中山大学": ["中大", "sysu"],
    "武汉大学": ["武大", "whu"],
    "同济大学": ["同济", "tongji"],
    "华东师范大学": ["华师大", "华东师大", "ecnu"],
    "南京工业大学": ["南工大", "njtech"],
    "北京航空航天大学": ["北航", "buaa"],
    "北京理工大学": ["北理", "北理工", "bit"],
    "电子科技大学": ["电子科大", "成电", "uestc"],
    "东南大学": ["东大", "seu"],
    "天津大学": ["天大", "tju"],
    "大连理工大学": ["大工", "dlut"],
    "中南大学": ["中南", "csu"],
    "四川大学": ["川大", "scu"],
    "山东大学": ["山大", "sdu"],
    "厦门大学": ["厦大", "xmu"],
    "吉林大学": ["吉大", "jlu"],
    "华南理工大学": ["华工", "scut"],
    "西北工业大学": ["西工大", "nwpu"],
    "中国人民大学": ["人大", "ruc"],
    "北京师范大学": ["北师大", "bnu"],
    "兰州大学": ["兰大", "lzu"],
    "重庆大学": ["重大", "cqu"],
    "湖南大学": ["湖大", "hnu"],
    "南开大学": ["南开", "nankai"],
}

_SCHOOL_ALIAS_MAP: dict[str, str] = {}
for _name, _aliases in _SCHOOL_ALIASES.items():
    _SCHOOL_ALIAS_MAP[_name.lower()] = _name
    for _a in _aliases:
        _SCHOOL_ALIAS_MAP[_a.lower()] = _name


def normalize_school(raw: str) -> str:
    """学校名归一化"""
    key = raw.lower().strip()
    return _SCHOOL_ALIAS_MAP.get(key, raw.strip())


# === 学历等级映射 ===
_DEGREE_LEVEL = {
    "博士": 4, "phd": 4, "doctor": 4, "博士研究生": 4,
    "硕士": 3, "master": 3, "研究生": 3, "硕士研究生": 3,
    "本科": 2, "bachelor": 2, "学士": 2,
    "大专": 1, "专科": 1, "associate": 1,
    "高中": 0, "中专": 0,
}


def degree_level(raw: str) -> int:
    """学历文本 -> 等级数值 (0-4)，匹配不到返回 -1"""
    key = raw.lower().strip()
    for k, v in _DEGREE_LEVEL.items():
        if k in key:
            return v
    return -1


# === 工作经验年限解析 ===
import re


def parse_experience_years(text: str) -> tuple[int, int]:
    """
    从 JD 文本中提取经验年限要求，返回 (min_years, max_years)。
    无法识别时返回 (0, 99)。
    """
    text = text.replace("（", "(").replace("）", ")")

    patterns = [
        r"(\d+)\s*[-~到至]\s*(\d+)\s*年",
        r"(\d+)\s*年以上",
        r"至少\s*(\d+)\s*年",
        r"(\d+)\+?\s*years?",
        r"(\d+)\s*年及以上",
        r"(\d+)\s*年工作经验",
        r"(\d+)\s*年以上.*经验",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                return int(groups[0]), int(groups[1])
            return int(groups[0]), 99

    if any(kw in text for kw in ["不限", "应届", "实习", "无经验要求", "0年"]):
        return 0, 99

    return 0, 99
