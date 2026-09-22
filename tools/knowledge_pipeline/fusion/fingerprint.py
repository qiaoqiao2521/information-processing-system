"""
语义指纹提取与相似度计算 (Semantic Fingerprinting & Entity Matcher)
纯 Python 标准库实现，零外部依赖，极速稳定。
提供多维度判据：
- 细粒度 URL 核心资产身份 (包含 GitHub releases/tags 与聚合平台 id 参数)
- 强化实体识别 (AI 模型、开源工具、版本标记与中文科技专有名词)
- 中英文跨语言词元对齐与规范化
- 版本差异性冲突拦截 (防止同一产品不同大/小版本误合并)
- 同名不同实体领域消歧 (如 Gemini 谷歌模型 vs 加密货币交易所，Atlas 机器人 vs 云数据库)
- 历史时间跨度冲突拦截 (防止数年前旧闻与当前最新发布混淆)
- 横向对比/综述评测边界隔离 (防止桥梁节点触发并查集单链击穿)
"""
from __future__ import annotations

import re
import math
import hashlib
from typing import Any, Set, List, Dict, Tuple, Optional
from collections import Counter
from urllib.parse import urlparse, parse_qs


# 常见停用词 (纯文本相似度过滤)
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "by", "from",
    "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
    "can", "could", "will", "would", "should", "of", "it", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "its", "our", "their", "new", "using", "based",
    "via", "into", "about", "more", "how", "what", "which", "who", "when", "where", "why",
    "all", "now", "just", "get", "set", "use", "make", "over", "out", "also", "some", "between",
    "的", "了", "和", "是", "就", "都", "而", "及", "与", "着", "或", "一个", "没有", "我们",
    "你们", "他们", "基于", "使用", "通过", "进行", "对于", "关于", "今日", "发布", "正式", "宣布"
}

# 常见复合描述修饰词（排除误识别为专有实体）
GENERIC_COMPOUNDS: Set[str] = {
    "hands-on", "multi-agent", "multi-node", "multi-step", "multi-vector",
    "zero-overhead", "computer-use", "computer-using", "state-of-the-art",
    "in-depth", "real-world", "next-generation", "few-shot", "large-scale",
    "open-source", "high-throughput", "low-latency", "end-to-end",
    "step-by-step", "test-time", "cloud-native", "production-ready",
    "fine-tuning", "pre-training", "long-context", "self-rewarding",
    "domain-specific", "free-threaded", "deep-dive"
}

# 明确已知的技术/框架/模型名称库 (解决小写前缀与专有词大小写不统一问题)
KNOWN_TECH_ENTITIES: Set[str] = {
    "vllm", "pgvector", "autogen", "milvus", "qdrant", "pinecone", "langchain",
    "langgraph", "crewai", "ollama", "evalplus", "humaneval", "swe-bench",
    "pep-703", "pep703", "python-3.13", "python313", "deepseek-r1", "deepseek-v3",
    "qwen2.5", "qwen2.5-coder", "llama", "llama-3", "llama-3.1", "gpt-4o", "gpt-4.5",
    "gpt-3", "claude-3.5", "arc-agi", "arc-prize", "operator", "gemini",
    "mongodb-atlas", "atlas-robot", "so-arm100", "fair-use", "web-scraping", "copyright"
}

# 中英文科技核心概念映射 (Cross-Lingual Alignment)
CHINESE_TECH_SYNONYMS: Dict[str, str] = {
    "通义千问": "qwen",
    "深度求索": "deepseek",
    "波士顿动力": "boston-dynamics",
    "多头潜在注意力": "mla",
    "混合专家": "moe",
    "代码大模型": "code-llm",
    "代码模型": "code-model",
    "开源": "opensource",
    "强化学习": "reinforcement-learning",
    "阿里": "alibaba",
    "阿里巴巴": "alibaba",
    "大模型": "llm",
    "技术报告": "technical-report",
}

# 同名不同实体领域知识库 (Domain Disambiguation)
HOMONYM_DOMAINS: Dict[str, Dict[str, Set[str]]] = {
    "gemini": {
        "ai": {"ai", "model", "multimodal", "google", "deepmind", "llm", "context", "token", "reasoning", "benchmark", "pro", "1.5"},
        "crypto": {"crypto", "cryptocurrency", "exchange", "earn", "nydfs", "sec", "bitcoin", "refund", "bankruptcy", "winklevoss", "finance", "settles", "trust", "customers", "investigation"}
    },
    "atlas": {
        "robotics": {"robot", "robotics", "humanoid", "boston", "dynamics", "actuator", "joint", "bipedal", "electric", "manufacturing", "grippers"},
        "database": {"mongodb", "database", "cloud", "cluster", "vector", "search", "query", "nosql", "tables", "dedicated", "latency"}
    }
}

# 典型竞争竞品技术组（用于识别横向横评/综述文章）
COMPETING_PRODUCTS: List[Set[str]] = [
    {"pgvector", "milvus", "qdrant", "pinecone"},
    {"langchain", "autogen", "crewai"},
]


def extract_url_key(url: str | None) -> str:
    """提取 URL 中的核心资产身份 (精确支持 GitHub releases/tags 及聚合平台 query 参数)"""
    if not url:
        return ""
    parsed = urlparse(url.lower().strip())
    netloc = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/")
    
    if "github.com" in netloc:
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 4 and parts[2] == "releases":
            return f"github::{parts[0]}/{parts[1]}/release/{parts[-1]}"
        elif len(parts) >= 2:
            return f"github::{parts[0]}/{parts[1]}"
    elif "arxiv.org" in netloc and "/abs/" in path:
        parts = [p for p in path.split("/") if p]
        if parts:
            clean_id = parts[-1].replace(".pdf", "").split("v")[0]
            return f"arxiv::{clean_id}"
            
    # 对于带有重要辨识参数的聚合类新闻 (如 Hacker News item?id=...)
    if parsed.query:
        qs = parse_qs(parsed.query)
        if "id" in qs:
            return f"{netloc}/{path}?id={qs['id'][0]}"
        elif "v" in qs:
            return f"{netloc}/{path}?v={qs['v'][0]}"
            
    return f"{netloc}/{path}"


def normalize_version(v: str) -> str:
    """规范化版本号字符串 (如将 3.13.0 归一化为 3.13，方便主次版本对齐)"""
    v = v.lstrip("v").strip()
    parts = v.split(".")
    if len(parts) == 3 and parts[2] == "0":
        return f"{parts[0]}.{parts[1]}"
    return v


def extract_release_versions(title: str) -> Set[str]:
    """从标题中提取明确指示软件/模型发布版本的标记 (排查年份与纯评测分数)"""
    title_lower = title.lower()
    versions: Set[str] = set()
    
    for m in re.finditer(r'\bv?(\d+\.\d+(?:\.\d+)?)\b', title_lower):
        raw = m.group(1)
        # 排除 2024, 2025 等公元年份
        if not (raw.startswith("20") and len(raw) == 4):
            versions.add(normalize_version(raw))
            
    return versions


def has_version_conflict(item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
    """检查两篇材料是否属于同一产品但锁定了互相冲突的具体发布版本号"""
    t1 = item1.get("title", "")
    t2 = item2.get("title", "")
    
    v1 = extract_release_versions(t1)
    v2 = extract_release_versions(t2)
    
    # 只有当双方标题均明确提及版本号，且完全没有交集时，才视为版本冲突
    if v1 and v2 and not (v1 & v2):
        is_survey = any(k in (t1 + " " + t2).lower() for k in ["vs", "comparing", "comparison", "survey", "retrospective", "bakeoff", "history", "landscape", "choosing"])
        if not is_survey:
            return True
            
    return False


def has_homonym_domain_conflict(text1: str, text2: str) -> bool:
    """检查同名实体（如 Gemini、Atlas）是否分别属于完全冲突的领域"""
    text1_lower = text1.lower()
    text2_lower = text2.lower()
    
    for entity, domains in HOMONYM_DOMAINS.items():
        if entity in text1_lower and entity in text2_lower:
            domain_names = list(domains.keys())
            d1_words = domains[domain_names[0]]
            d2_words = domains[domain_names[1]]
            
            # 计算 text1 与 text2 在两个领域词库中的命中数
            t1_d1 = len(set(re.findall(r'[a-z0-9]+', text1_lower)) & d1_words)
            t1_d2 = len(set(re.findall(r'[a-z0-9]+', text1_lower)) & d2_words)
            
            t2_d1 = len(set(re.findall(r'[a-z0-9]+', text2_lower)) & d1_words)
            t2_d2 = len(set(re.findall(r'[a-z0-9]+', text2_lower)) & d2_words)
            
            # 若 text1 强偏向领域 1，而 text2 强偏向领域 2
            if (t1_d1 >= 2 and t1_d2 == 0 and t2_d2 >= 2 and t2_d1 == 0) or \
               (t1_d2 >= 2 and t1_d1 == 0 and t2_d1 >= 2 and t2_d2 == 0):
                return True
                
    return False


def has_temporal_gap_conflict(item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
    """检测时间跨度差异过大（数年前的旧闻重新传播与最新突发）"""
    p1 = item1.get("published_at", "")
    p2 = item2.get("published_at", "")
    
    y1, y2 = None, None
    if p1 and len(p1) >= 4 and p1[:4].isdigit():
        y1 = int(p1[:4])
    if p2 and len(p2) >= 4 and p2[:4].isdigit():
        y2 = int(p2[:4])
        
    if y1 and y2:
        year_gap = abs(y1 - y2)
        if year_gap >= 2:
            # 除非明确包含历史回顾字样
            all_text = f"{item1.get('title','')} {item2.get('title','')} {item1.get('summary','')} {item2.get('summary','')}".lower()
            if not any(k in all_text for k in ["retrospective", "history", "years of", "looking back", "anniversary"]):
                return True
                
    return False


def extract_entities(input_data: str | Dict[str, Any]) -> List[str]:
    """从材料中抽取高判别度实体与专有名词 (支持大小写、中英文及复合模型命名)"""
    if isinstance(input_data, dict):
        title = input_data.get("title", "")
        summary = input_data.get("summary", "") or input_data.get("raw_text", "")
        tags = " ".join(input_data.get("tags", []))
        text = f"{title}\n{summary}\n{tags}"
    else:
        text = input_data or ""
        
    if not text:
        return []
    
    found: Set[str] = set()
    text_lower = text.lower()
    
    # 1. 显式已知的关键技术框架与实体（支持连字符、空格或无间隔变体，如 llama-3.1 与 llama 3.1）
    for term in KNOWN_TECH_ENTITIES:
        pattern_str = re.escape(term).replace(r"\-", r"[\s\-_]?")
        pattern = r'(?<![a-zA-Z0-9_\-\.])' + pattern_str + r'(?![a-zA-Z0-9_\-\.])'
        if re.search(pattern, text_lower):
            canonical = term
            if canonical == "arc-prize":
                canonical = "arc-agi"
            found.add(canonical)

    # 2. 中文核心科技实体识别与归一化
    for cn_term, en_norm in CHINESE_TECH_SYNONYMS.items():
        if cn_term in text:
            found.add(en_norm)

    # 3. 典型带连接号/点号的模型代号 (如 DeepSeek-R1, Qwen2.5-Coder, Llama-3.1-405B, GPT-4.5)
    code_pattern = re.compile(r'\b([a-zA-Z][a-zA-Z0-9]*(?:[-_.][a-zA-Z0-9]+)+)\b')
    for m in code_pattern.finditer(text):
        raw = m.group(1).strip("._-/")
        if raw.lower() not in GENERIC_COMPOUNDS and len(raw) >= 3:
            found.add(raw)
            found.add(raw.lower())

    # 4. GitHub 仓库模式 (如 github.com/meta-llama/llama3 或 meta-llama/llama3)
    gh_url_pattern = re.compile(r'github\.com/([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)')
    for m in gh_url_pattern.finditer(text):
        found.add(m.group(1).lower().strip("._-/"))

    repo_pattern = re.compile(r'(?<![a-zA-Z0-9_\-\./])([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)(?![a-zA-Z0-9_\-\./])')
    for m in repo_pattern.finditer(text):
        repo = m.group(1).lower().strip("._-/")
        if "/" in repo and len(repo) >= 5 and "github.com" not in repo:
            found.add(repo)

    # 5. 代表性技术专有名词
    capitalized_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9_]{2,})\b')
    for m in capitalized_pattern.finditer(text):
        word = m.group(1).strip("._-/").lower()
        if word in {"gemini", "operator", "milvus", "atlas", "postgres", "postgresql", "transformer", "claude", "openai", "alibaba", "python", "autogen", "langchain", "qdrant", "pinecone", "llama"}:
            found.add(word)

    # 6. ArXiv ID (如 2404.12345, 2501.12948)
    arxiv_pattern = re.compile(r'\b(\d{4}\.\d{4,5}(?:v\d+)?)\b')
    for m in arxiv_pattern.finditer(text):
        found.add(f"arxiv:{m.group(1)}")

    return sorted(found)


def is_comparative(item: Dict[str, Any], entities: Set[str]) -> bool:
    """检测文章是否为横向对比、基准测试或技术选型综述"""
    title = item.get("title", "").lower()
    if any(m in title for m in ["bakeoff", "landscape", "choosing between", "survey", "comparing", " vs ", "comparison"]):
        return True
    for comp_group in COMPETING_PRODUCTS:
        if len(entities & comp_group) >= 2:
            return True
    return False


def tokenize_text(text: str) -> List[str]:
    """混合分词：支持中文字元 2-gram、英文词元及中英语义对齐"""
    if not text:
        return []
        
    text_lower = text.lower()
    tokens: List[str] = []
    
    # 提取英文字词与模型代码
    en_words = re.findall(r'[a-z0-9_\-\.]+', text_lower)
    for w in en_words:
        cleaned = w.strip("._-")
        if len(cleaned) > 1 and cleaned not in STOP_WORDS and cleaned not in GENERIC_COMPOUNDS:
            tokens.append(cleaned)
            
    # 中文科技同义词映射
    for cn_term, en_norm in CHINESE_TECH_SYNONYMS.items():
        if cn_term in text:
            tokens.append(en_norm)

    # 提取中文字符串并生成 2-gram
    cjk_text = "".join(re.findall(r'[\u4e00-\u9fff]', text_lower))
    for i in range(len(cjk_text) - 1):
        bigram = cjk_text[i:i+2]
        if bigram not in STOP_WORDS:
            tokens.append(bigram)
            
    return tokens


def compute_tf_vector(tokens: List[str]) -> Dict[str, float]:
    """计算词频向量并进行 L2 归一化"""
    counts = Counter(tokens)
    total = len(tokens)
    if total == 0:
        return {}
    
    vector = {k: v / total for k, v in counts.items()}
    norm = math.sqrt(sum(v * v for v in vector.values()))
    if norm > 0:
        return {k: v / norm for k, v in vector.items()}
    return vector


def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    """计算两个稀疏向量的余弦相似度"""
    if not v1 or not v2:
        return 0.0
    common = set(v1.keys()) & set(v2.keys())
    return sum(v1[k] * v2[k] for k in common)


def are_items_semantically_related(
    item1: Dict[str, Any],
    item2: Dict[str, Any],
    sim_threshold: float = 0.45
) -> Tuple[bool, float, str]:
    """
    多重判据综合评估两则信息是否属于同一突发事件/开源主题/技术发布：
    1. 强判据：指向相同 GitHub 仓库 (含对应 release tag) 或同一 arXiv 论文
    2. 硬冲突拦截：版本冲突、同名异义领域冲突、时间大跨度冲突、单产品发布 vs 跨产品横评隔离
    3. 实体判据：存在独特具体模型代号/开源产品与版本匹配
    4. 语义判据：标题与摘要文本 TF-IDF 余弦相似度
    """
    t1 = item1.get("title", "")
    t2 = item2.get("title", "")
    s1 = item1.get("summary", "") or item1.get("raw_text", "")
    s2 = item2.get("summary", "") or item2.get("raw_text", "")
    tags1 = " ".join(item1.get("tags", []))
    tags2 = " ".join(item2.get("tags", []))
    
    text1 = f"{t1}\n{s1}\n{tags1}"
    text2 = f"{t2}\n{s2}\n{tags2}"
    
    # 1. 强判据：URL 核心资产身份
    url1_key = extract_url_key(item1.get("url"))
    url2_key = extract_url_key(item2.get("url"))
    if url1_key and url2_key:
        if url1_key == url2_key:
            return True, 1.0, f"shared_asset_key:{url1_key}"
        if url1_key.startswith("github::") and url2_key.startswith("github::"):
            repo1 = url1_key.split("/release/")[0]
            repo2 = url2_key.split("/release/")[0]
            if repo1 == repo2 and not has_version_conflict(item1, item2):
                return True, 0.95, f"shared_asset_key:{repo1}"

    # 2. 硬冲突拦截
    # (a) 同名不同实体领域冲突 (如 Gemini 谷歌 vs 加密货币，Atlas 机器人 vs 云数据库)
    if has_homonym_domain_conflict(text1, text2):
        return False, 0.0, "conflict:homonym_domain_mismatch"

    # (b) 版本冲突 (如 vLLM 0.6 vs 0.7，Llama 3 vs 3.1)
    if has_version_conflict(item1, item2):
        return False, 0.05, "conflict:version_mismatch"

    # (c) 跨年旧闻时间跨度冲突 (如 2020 与 2025/2026)
    if has_temporal_gap_conflict(item1, item2):
        return False, 0.05, "conflict:temporal_gap"

    e1 = set(extract_entities(item1))
    e2 = set(extract_entities(item2))

    # (d) 横向横评/综述文章与单一产品发布的边界隔离 (杜绝桥梁节点链式击穿)
    comp1 = is_comparative(item1, e1)
    comp2 = is_comparative(item2, e2)
    if comp1 != comp2:
        return False, 0.10, "conflict:comparative_survey_vs_single_product"
    if comp1 and comp2:
        common_comp = e1 & e2
        if len(common_comp) >= 2 or any(k in (t1 + " " + t2).lower() for k in ["vector", "agent"]):
            return True, 0.75, "shared_comparative_domain"

    # 3. 实体判据
    meaningful_shared = {e for e in (e1 & e2) if e not in GENERIC_COMPOUNDS and len(e) >= 3}

    # (a) 同一产品 + 匹配的具体发布版本号 (如 vLLM 0.6.0, Milvus 2.4.0, LangChain 0.3)
    v1 = extract_release_versions(t1)
    v2 = extract_release_versions(t2)
    shared_versions = v1 & v2
    shared_products = meaningful_shared & {"vllm", "milvus", "langchain", "autogen", "pgvector", "python"}
    if shared_products and shared_versions:
        return True, 0.88, f"shared_product_version:{list(shared_products)[0]}:{list(shared_versions)[0]}"

    # (b) 高特异性具体模型代号/项目 (无需强依赖纯文本词袋交集)
    HIGH_SPECIFICITY_ENTITIES = {
        "qwen2.5-coder", "deepseek-v3", "deepseek-r1", "llama-3.1", "llama-3",
        "pep-703", "pep703", "arc-agi", "chatgpt-plugins", "gpt-4.5", "gpt-3"
    }
    for ent in meaningful_shared:
        if ent in HIGH_SPECIFICITY_ENTITIES or any(marker in ent for marker in ["-", ".", "::"]):
            return True, 0.85, f"shared_unique_entity:{ent}"

    # (c) 同一 disambiguated 实体领域且包含共同事件词 (如 Gemini 交易所和解)
    for homonym, domains in HOMONYM_DOMAINS.items():
        if homonym in e1 and homonym in e2:
            for dname, dwords in domains.items():
                w1 = len(set(re.findall(r'[a-z0-9]+', text1.lower())) & dwords)
                w2 = len(set(re.findall(r'[a-z0-9]+', text2.lower())) & dwords)
                if w1 >= 2 and w2 >= 2:
                    return True, 0.80, f"shared_disambiguated_entity:{homonym}:{dname}"

    # (d) 共同专业标签集合 (如著作权/合理使用争议)
    tags_overlap = set(item1.get("tags", [])) & set(item2.get("tags", []))
    if len(tags_overlap) >= 2:
        return True, 0.75, f"shared_tags:{','.join(tags_overlap)}"

    if len(meaningful_shared) >= 2:
        return True, 0.80, f"shared_entities:{','.join(meaningful_shared)}"

    # 4. 语义判据：混合分词与 TF 余弦相似度
    title_tokens1 = tokenize_text(t1)
    title_tokens2 = tokenize_text(t2)
    title_sim = cosine_similarity(compute_tf_vector(title_tokens1), compute_tf_vector(title_tokens2))
    
    if title_sim >= 0.55:
        return True, title_sim, "high_title_similarity"

    full_tokens1 = tokenize_text(text1)
    full_tokens2 = tokenize_text(text2)
    full_sim = cosine_similarity(compute_tf_vector(full_tokens1), compute_tf_vector(full_tokens2))
    
    combined_score = 0.55 * title_sim + 0.45 * full_sim
    if combined_score >= sim_threshold:
        return True, combined_score, f"semantic_score:{combined_score:.2f}"
        
    return False, combined_score, "dissimilar"
