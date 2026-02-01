import time
import httpx
from tqdm import tqdm
from selectolax.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed


# 尝试多种编码解码网页内容，避免乱码
def try_decode(raw):
    for enc in ("utf-8", "gbk", "gb2312", "big5", "shift_jis", "latin1"):
        try:
            return raw.decode(enc, errors="ignore")
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


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
            text = try_decode(response.content[:100_000])  # 只解码前 100KB
            delay_ms = int((time.perf_counter() - start_time) * 1000)
            source.respond_time = delay_ms

            # ---- 复杂逻辑：判断 URL 是否有效 ----
            # 1. JSON 响应：必须有内容且状态码 200
            if "application/json" in response.headers.get("Content-Type", "").lower():
                try:
                    data = response.json()
                    return source, bool(data and response.status_code == 200)
                except Exception:
                    return source, False

            lower = text.lower()
            # 2. 必须包含 HTML 标签
            if "<html" not in lower:
                return source, False
            # 3. HTML 长度不足 → 判定无效
            if len(text) < config.url_filter.min_html_length:
                return source, False
            # 4. 包含屏蔽词 → 判定无效
            if any(k in lower for k in config.url_filter.keywords):
                return source, False

            # 5. 使用 selectolax 解析 DOM
            tree = HTMLParser(text)
            if not tree.root:
                return source, False
            nodes = tree.root.css("*")
            if len(nodes) < 5:  # 节点过少 → 判定无效
                return source, False

            # 6. 提取 body 内文本
            texts = [
                n.text(strip=True) for n in tree.css("body *") if n.text(strip=True)
            ]
            if len(texts) > 5000:  # 文本过多 → 直接判定有效
                return source, True

            visible_text = " ".join(texts)
            if len(visible_text) < config.url_filter.min_visible_text_length:
                return source, False

            # 7. 最终判定：必须状态码 200
            return source, response.status_code == 200
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
