import re
import tldextract
from functools import lru_cache
from urllib.parse import urlparse

# 初始化域名提取器（不依赖外部后缀列表）
tldextractor = tldextract.TLDExtract(suffix_list_urls=())


@lru_cache(maxsize=None)
def extract_domain_cached(url):
    # 缓存域名提取结果，避免重复计算
    return tldextractor(url)


# 清理书源名称：去掉特殊符号，只保留字母、数字、中文
def clean_name(text):
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# 分类逻辑：根据书源类型、分组、名称和注释匹配标签
def classify_source_group(source, category_patterns, config):
    matched = []

    # 收集所有需要匹配的文本：分组、名称（可选）、注释（可选）
    texts = [source.book_source_group or ""]

    # 如果启用名称分类，添加名称到匹配文本
    if config.name_for_classify:
        texts.append(source.book_source_name or "")

    # 如果启用注释分类，添加注释到匹配文本
    if config.comment_for_classify:
        texts.append(source.book_source_comment or "")

    # 合并所有文本进行匹配
    combined = " ".join(texts)

    #  匹配分类（保持顺序 + 去重）
    seen = set()
    matched = []
    for group, pattern in category_patterns.items():
        if pattern.search(combined) and group not in seen:
            seen.add(group)
            matched.append(group)

    if config.save_by_category and matched:
        source.primary_category = matched[0]

    type_label = config.classify.reverse_type_map.get(source.book_source_type)
    if config.use_novel_default_label or source.book_source_type != 0:
        matched.insert(0, type_label)

    source.book_source_group = ",".join(matched)
    return source


# URL 规范化：提取协议和域名
def normalize_source_url(source, url_pattern, ip_pattern):
    raw_url = source.book_source_url.strip()
    match = url_pattern.search(raw_url)
    if match and not ip_pattern.search(raw_url):
        protocol, host = match.groups()
        normalized = f"{protocol}{host}" if protocol else f"https://{host}"
        source.book_source_url = normalized
        # 提取域名（优先用 tldextract，否则用 urlparse）
        ext = extract_domain_cached(normalized)
        source.domain = ext.domain or (urlparse(normalized).hostname or "")
    return source


# 分类并排序书源：返回分组、有域名的有效书源、无效书源
def classify_and_sort_sources(sources, config):
    # 构建分类正则模式
    category_patterns = {
        group: re.compile("|".join(map(re.escape, keywords)), re.I)
        for group, keywords in config.classify.categories.items()
    }
    # 初始化分组字典
    grouped = {
        tid: {"id": tid, "name": name, "items": []}
        for tid, name in config.classify.reverse_type_map.items()
    }
    url_pattern = re.compile(r"(https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
    ip_pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
    valid_sources, invalid_sources = [], []
    for source in sources:
        source.book_source_name = clean_name(source.book_source_name)
        source = classify_source_group(source, category_patterns, config)
        source = normalize_source_url(source, url_pattern, ip_pattern)
        # 有域名 → 有效，否则无效
        if source.domain:
            valid_sources.append(source)
        else:
            invalid_sources.append(source)
    return grouped, valid_sources, invalid_sources
