import requests
import re
import base64
import urllib.parse

HEADERS = {
    'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
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


def check_url_size(u: str) -> tuple[str, int]:
    try:
        h = requests.head(u, timeout=5, headers=HEADERS)
        return u, int(h.headers.get('Content-Length', 0))
    except Exception:
        return u, 0

def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL.
    We prioritize 'progressive' streams and then fetch the largest file size
    to ensure we get the main video and not a random 5s recommended video.
    """
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    text = response.text

    # Meta AI embeds direct fbcdn.net .mp4 URLs in the page HTML inside JSON blobs.
    raw_urls = re.findall(r'https://video-[^\s"\'<>]+', text)
    if not raw_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+fbcdn\.net[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)

    if not raw_urls:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not an image or text post)."
        )

    # Clean all found URLs
    cleaned_urls = list(set([unescape_url(u) for u in raw_urls]))
    
    # 1. Filter out only progressive URLs
    prog_urls = [u for u in cleaned_urls if is_progressive(u)]
    if not prog_urls:
        prog_urls = cleaned_urls

    # 2. To avoid random 5-second suggested videos, we need to find the main video.
    # The main video is usually the largest one. We use ThreadPoolExecutor to check sizes concurrently.
    import concurrent.futures

    best_url = None
    max_size = -1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url_size, u): u for u in prog_urls}
        for future in concurrent.futures.as_completed(futures):
            u, size = future.result()
            if size > max_size:
                max_size = size
                best_url = u

    if best_url:
        return best_url

    # Fallback: just return the first one found
    return prog_urls[0]
