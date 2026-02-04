import re
import time
import httpx
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


# 尝试多种编码解码网页内容，避免乱码
def try_decode(raw):
    for enc in ("utf-8", "gbk", "gb2312", "big5", "shift_jis", "latin1"):
        try:
            return raw.decode(enc, errors="ignore")
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


base64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")


def validate_response(response, config):
    if response.status_code != 200:
        return False

    # JSON 响应
    if "application/json" in response.headers.get("Content-Type", "").lower():
        try:
            data = response.json()
        except Exception:
            return False
        return isinstance(data, dict) and bool(data)

    # HTML 响应
    raw = response.content[:100_000]
    text = try_decode(raw).lower()

    # 1. 必须包含 <html>
    if "<html" not in text:
        return False

    # 3. 白名单过滤
    if any(k in text for k in config.url_filter.white_list):
        return True

    # 4. 黑名单过滤
    if any(k in text for k in config.url_filter.black_list):
        return False

    # 5. base64 垃圾内容过滤
    matches = base64_pattern.findall(text)
    if len(matches) > 200:
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
            delay_ms = int((time.perf_counter() - start_time) * 1000)
            source.respond_time = delay_ms
            return source, validate_response(response, config)
    except Exception:
        return source, False


# 并发检测多个 URL
def check_urls_parallel(sources, config):
    reachable, unreachable = [], []
    with tqdm(total=len(sources)) as progress_bar:
        with ThreadPoolExecutor(config.http.max_workers) as executor:
            futures = {
                executor.submit(check_source_url, source, config): source
                for source in sources
            }
            for future in as_completed(futures):
                source, valid = future.result()
                progress_bar.update(1)
                if valid:
                    reachable.append(source)
                else:
                    unreachable.append(source)
    return reachable, unreachable


# 域名去重：保留最快响应的书源
def deduplicate_by_domain(sources):
    sorted_sources = sorted(sources, key=lambda _: _.respond_time or float("inf"))
    seen = {}
    unique, duplicates = [], []
    for source in sorted_sources:
        if source.domain not in seen:
            seen[source.domain] = source
            unique.append(source)
        else:
            duplicates.append(source)
    return unique, duplicates
