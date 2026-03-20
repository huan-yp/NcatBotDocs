"""
检查真实部署的文档站点中的失效链接。

用法:
    python docs/tools/check_links.py [--external] [BASE_URL]

    --external  同时检查外部链接（默认只检查站内）

默认 BASE_URL 为 http://localhost:8080

工作流程:
    1. 从首页开始，获取 HTML 内容
    2. 用正则提取所有 <a href="..."> 链接
    3. 对站内链接进行并发爬取，已访问的不重复
    4. 记录并报告所有失效链接（非 2xx 响应）
"""
import io
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

# Windows GBK stdout 会导致 emoji 输出崩溃，强制 UTF-8
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests

# ── 配置 ──────────────────────────────────────────────
DEFAULT_BASE = "http://localhost:8080"
TIMEOUT = 5
WORKERS = 20  # 本地服务器并发线程数
LINK_PATTERN = re.compile(r'<a\s[^>]*?href=["\']([^"\']*)["\']', re.IGNORECASE)
# ──────────────────────────────────────────────────────


def is_internal(url: str, base_host: str) -> bool:
    """判断 url 是否属于站内。"""
    parsed = urlparse(url)
    return parsed.hostname in (None, "", base_host, "localhost", "127.0.0.1")


def normalize(url: str) -> str:
    """去掉 fragment，统一末尾 /。"""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def extract_links(html: str, page_url: str) -> list[str]:
    """从 HTML 中提取所有 href，转为绝对 URL。"""
    links = []
    for href in LINK_PATTERN.findall(html):
        href = href.strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urljoin(page_url, href)
        links.append(absolute)
    return links


def fetch_page(session, url: str) -> tuple[int, str, str]:
    """获取页面，返回 (status_code, content_type, html_body)。异常返回 (-1, error_msg, "")。"""
    try:
        resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        ct = resp.headers.get("Content-Type", "")
        return resp.status_code, ct, resp.text if "text/html" in ct else ""
    except requests.RequestException as exc:
        return -1, str(exc), ""


def head_check(session, url: str) -> tuple[int, str]:
    """HEAD 检查外部链接，返回 (status_code, error_msg)。"""
    try:
        resp = session.head(url, timeout=TIMEOUT, allow_redirects=True)
        return resp.status_code, ""
    except requests.RequestException as exc:
        return -1, str(exc)


def check_site(base_url: str, check_external: bool = False) -> list[dict]:
    """并发爬取站点，返回失效链接列表。"""
    base_host = urlparse(base_url).hostname
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=WORKERS, pool_maxsize=WORKERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers["User-Agent"] = "NcatBot-LinkChecker/1.0"

    lock = threading.Lock()
    visited: set[str] = set()
    checked_ext: set[str] = set()
    broken: list[dict] = []
    pending_internal: list[tuple[str, str]] = []  # 待爬的站内 (url, referrer)
    pending_external: list[tuple[str, str]] = []  # 待检的外部 (url, referrer)

    start = normalize(base_url)
    visited.add(start)
    pending_internal.append((start, "(start)"))

    page_count = 0

    # 分轮并发：每轮并发抓取当前 pending，收集新链接，下一轮继续
    while pending_internal:
        batch = pending_internal[:]
        pending_internal.clear()
        new_links: list[tuple[str, str, str]] = []  # (link, referrer, type)

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            future_map = {
                pool.submit(fetch_page, session, url): (url, referrer)
                for url, referrer in batch
            }
            for future in as_completed(future_map):
                url, referrer = future_map[future]
                status, ct, html = future.result()

                if status == -1:
                    broken.append({"url": url, "referrer": referrer, "status": ct})
                    continue
                if status >= 400:
                    broken.append({"url": url, "referrer": referrer, "status": status})
                    continue
                if not html:
                    continue

                page_count += 1
                print(f"  [OK {status}] {url}")

                for link in extract_links(html, url):
                    link_norm = normalize(link)
                    if is_internal(link, base_host):
                        with lock:
                            if link_norm not in visited:
                                visited.add(link_norm)
                                pending_internal.append((link, url))
                    else:
                        if check_external:
                            with lock:
                                if link_norm not in checked_ext:
                                    checked_ext.add(link_norm)
                                    pending_external.append((link, url))

    # 并发检查外部链接
    if pending_external:
        print(f"\n检查 {len(pending_external)} 个外部链接...")
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            future_map = {
                pool.submit(head_check, session, url): (url, referrer)
                for url, referrer in pending_external
            }
            for future in as_completed(future_map):
                url, referrer = future_map[future]
                status, err = future.result()
                if status == -1:
                    broken.append({"url": url, "referrer": referrer, "status": err})
                    print(f"  [ERROR] {url}  (from {referrer}): {err}")
                elif status >= 400:
                    broken.append({"url": url, "referrer": referrer, "status": status})
                    print(f"  [BROKEN {status}] {url}  (from {referrer})")

    print(f"\n爬取完成: 访问了 {page_count} 个站内页面, 检查了 {len(checked_ext)} 个外部链接")
    return broken


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_external = "--external" in sys.argv
    base_url = args[0] if args else DEFAULT_BASE
    print(f"=== 文档链接检查 ===")
    print(f"目标: {base_url}")
    print(f"外部链接: {'检查' if check_external else '跳过'}\n")

    broken = check_site(base_url, check_external=check_external)

    if not broken:
        print("\n[PASS] 所有链接均正常!")
        sys.exit(0)

    print(f"\n[FAIL] 发现 {len(broken)} 个失效链接:\n")
    for item in broken:
        print(f"  URL:      {item['url']}")
        print(f"  状态:     {item['status']}")
        print(f"  来源页面: {item['referrer']}")
        print()

    sys.exit(1)


if __name__ == "__main__":
    main()
