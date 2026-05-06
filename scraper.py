import requests
import re
import base64
import urllib.parse
import json
import concurrent.futures

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}


def unescape_url(url_str: str) -> str:
    if url_str.endswith('\\'):
        url_str = url_str[:-1]
    idx = url_str.find(r'\u003c')
    if idx != -1:
        url_str = url_str[:idx]
    url_str = url_str.replace(r'\u0026', '&')
    url_str = url_str.replace(r'\/', '/')
    url_str = url_str.replace('&amp;', '&')
    return url_str


def is_progressive(url_str: str) -> bool:
    """
    Checks if the URL is a progressive stream (contains both audio and video)
    by decoding the 'efg' parameter from the Facebook CDN URL.
    """
    match = re.search(r'efg=([^&]+)', url_str)
    if not match:
        return False
    efg = urllib.parse.unquote(match.group(1))
    try:
        pad = len(efg) % 4
        if pad:
            efg += '=' * (4 - pad)
        dec = base64.b64decode(efg).decode('utf-8', errors='ignore')
        return 'progressive' in dec.lower()
    except Exception:
        return False


def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL.
    """
    ua_list = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    session = requests.Session()
    text = ""
    for ua in ua_list:
        try:
            current_headers = HEADERS.copy()
            current_headers['User-Agent'] = ua
            response = session.get(share_url, headers=current_headers, timeout=15)
            response.raise_for_status()
            text = response.text
            
            if "Verify you are human" in text or "Check if there is a typo" in text or "Checking your browser" in text:
                text = "" 
                continue
            break
        except Exception:
            continue

    if not text:
        raise Exception(
            "Meta AI blocked the request or the page is unavailable. "
            "This often happens after multiple requests. Please wait a few minutes or try a different video link."
        )

    post_id_match = re.search(r'/post/([^/?]+)', share_url)
    post_id = post_id_match.group(1) if post_id_match else None

    parsed_chunks = []
    chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                parsed_chunks.append(data[1])
        except Exception:
            pass

    ref_id = None
    if post_id:
        for chunk_str in parsed_chunks:
            if post_id in chunk_str:
                idx = chunk_str.find(post_id)
                sub = chunk_str[max(0, idx - 100):idx + 2000]
                url_match = re.search(r'\\?"url\\?":\\?"\$([^"$\\]+)\\?"', sub)
                if url_match:
                    ref_id = url_match.group(1)
                    break

    if ref_id:
        search_sources = parsed_chunks + [text]
        for source in search_sources:
            for pattern in [f'{ref_id}:T', f'{ref_id}:"', f'{ref_id}:\\"']:
                idx = source.find(pattern)
                if idx != -1:
                    sub = source[idx:idx + 3000]
                    mp4_match = re.search(r'(https?://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*)', sub)
                    if mp4_match:
                        u = mp4_match.group(1)
                        u = u.replace(r'\u0026', '&').replace('\\\\', '\\').replace('\\/', '/')
                        u = re.sub(r'[a-z0-9]+:T[a-z0-9]+,.*$', '', u)
                        u = u.rstrip('\\')
                        return u

    fallback_urls = []
    search_sources = parsed_chunks + [text]
    patterns = [
        r'(https?://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*)',
        r'(https?://video[^\s"\'<>\\]+\.fbcdn\.net/[^\s"\'<>\\]+)',
        r'(https?://[^\s"\'<>\\]+efg=[^\s"\'<>\\]+)'
    ]
    
    for source in search_sources:
        for pattern in patterns:
            matches = re.findall(pattern, source)
            for m in matches:
                u = m.replace(r'\u0026', '&').replace('\\\\', '\\').replace('\\/', '/')
                fallback_urls.append(u)

    if not fallback_urls:
        if not post_id:
            raise Exception(
                "Could not find a video in this Meta AI link. "
                "Make sure it is a direct video post URL (not a profile page)."
            )
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not an image or text post)."
        )

    seen = set()
    cleaned_urls = []
    for u in fallback_urls:
        if u not in seen:
            seen.add(u)
            cleaned_urls.append(u)

    prog_urls = [u for u in cleaned_urls if is_progressive(u)]
    if not prog_urls:
        prog_urls = cleaned_urls

    if not prog_urls:
        raise Exception(
            "Found Meta AI content, but could not locate a downloadable video stream."
        )

    def _check_size(url):
        try:
            import random
            ua = random.choice(ua_list)
            h = requests.head(url, timeout=5, headers={'User-Agent': ua, 'Referer': 'https://www.meta.ai/'})
            return url, int(h.headers.get('Content-Length', 0))
        except Exception:
            return url, 0

    best_url = prog_urls[0]
    best_size = 0
    if len(prog_urls) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(prog_urls), 10)) as executor:
            results = list(executor.map(_check_size, prog_urls))
            for url, size in results:
                if size > best_size:
                    best_size = size
                    best_url = url

    return best_url
