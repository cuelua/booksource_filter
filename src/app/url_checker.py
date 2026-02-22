import re
import time
import httpx
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

base64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
title_pattern = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
encoding_pattern = re.compile(
    r'<meta[^>]*?(?:charset|http-equiv.*?charset)=["\']?([^"\'\s;>]+)["\']?',
    re.IGNORECASE,
)


def validate_response(response, text, config):
    if response.status_code != 200:
        return False
    # JSON 响应
    content_type = response.headers.get("Content-Type", "").lower()
    if "application/json" in content_type or "text/json" in content_type:
        try:
            data = response.json()
            return isinstance(data, (dict, list)) and bool(data)
        except (ValueError, TypeError):
            return False
    # 1. 必须包含 <html> 标签
    if "<html" not in text:
        return False
    # 4. base64 垃圾内容过滤 - 限制匹配次数以提高性能
    base64_count = 0
    for match in base64_pattern.finditer(text):
        base64_count += 1
        if base64_count > 200:
            return False
    # 2. 白名单过滤 - 转换为集合提高查找效率
    if any(key in text for key in config.url_filter.white_list):
        return True
    # 3. 黑名单过滤 - 转换为集合提高查找效率
    if any(key in text for key in config.url_filter.black_list):
        return False
    return True


# 检测单个书源 URL 是否有效
def check_source_url(source, config):
    start_time = time.perf_counter()
    try:
        with httpx.Client(
            follow_redirects=True,
            verify=config.http.verify,
            trust_env=config.http.trust_env,
            max_redirects=config.http.max_redirects,
            headers={"User-Agent": config.http.user_agent},
            timeout=httpx.Timeout(config.http.timeout, read=config.http.timeout_read),
        ) as client:
            response = client.get(source.book_source_url)
            # 计算响应时间
            delay_ms = int((time.perf_counter() - start_time) * 1000)
            source.respond_time = delay_ms

            # 读取并解码内容，限制大小以提高性能
            content = response.content[:100_000]  # 限制为100KB
            encoding = "utf-8"  # 默认编码
            html_snippet = content[:2000].decode(encoding, errors="replace")
            if meta_match := encoding_pattern.search(html_snippet):
                encoding = meta_match.group(1).strip()
            text = content.decode(encoding, errors="replace").lower()
            if title_match := title_pattern.search(text):
                source.book_source_name = title_match.group(1).strip()
            return source, validate_response(response, text, config)
    except Exception:
        return source, False


# 并发检测多个 URL
def check_urls_parallel(sources, config):
    reachable, unreachable = [], []
    with tqdm(total=len(sources)) as progress_bar:
        with ThreadPoolExecutor(config.http.max_workers) as executor:
            future_to_source = {
                executor.submit(check_source_url, source, config): source
                for source in sources
            }
            # 处理完成的任务
            for future in as_completed(future_to_source):
                source, valid = future.result()
                if valid:
                    reachable.append(source)
                else:
                    unreachable.append(source)
                progress_bar.update(1)

    # 排序 - 优先按名称排序，名称为空时按URL排序
    def sort_key(item):
        return (item.book_source_name.lower(), item.respond_time)

    reachable.sort(key=sort_key)
    unreachable.sort(key=sort_key)
    return reachable, unreachable


# 域名去重：保留最快响应的书源
def deduplicate_by_domain(sources, config):
    seen = {}
    unique, duplicates = [], []
    # 按响应时间排序（可选）
    if config.sort_by_respond_time:
        # 使用key函数避免多次访问属性
        sources = sorted(sources, key=lambda _: _.respond_time)
    # 使用字典映射来优化查找和替换
    source_index_map = {}
    for source in sources:
        domain = source.domain
        if source.domain not in seen:
            # 新域名，添加到唯一列表
            seen[domain] = source
            unique.append(source)
            source_index_map[domain] = len(unique) - 1
        else:
            # 相同域名，比较响应时间
            existing_source = seen[domain]
            existing_index = source_index_map[domain]
            if source.respond_time < existing_source.respond_time:
                # 新的书源响应更快，替换旧的
                unique[existing_index] = source
                seen[domain] = source
                duplicates.append(existing_source)
            else:
                # 旧的书源响应更快，保留旧的
                duplicates.append(source)
    return unique, duplicates
