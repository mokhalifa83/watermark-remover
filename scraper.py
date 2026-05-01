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


import json


def _clean_video_url(u: str) -> str:
    """Clean up a raw video URL extracted from Meta's page source."""
    u = u.replace(r'\u0026', '&').replace('\\/', '/').replace('\\\\', '\\')
    idx = u.find(r'\u003c')
    if idx != -1:
        u = u[:idx]
    # Strip trailing backslashes or Next.js chunk separators
    u = re.sub(r'[a-z0-9]+:T[a-z0-9]+,.*$', '', u)
    u = u.rstrip('\\')
    return u


def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL.

    Strategy: Meta AI uses Next.js server-side rendering. The post's video URL
    is stored as a reference (e.g. "$73") in the post data, and the actual URL
    is defined in a separate data chunk. We trace post_id → ref_id → video URL
    to guarantee we get the exact video for the requested post, not a random
    recommended clip.
    """
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    text = response.text

    # 1. Extract Post ID from the share URL
    post_id_match = re.search(r'/post/([^/?]+)', share_url)
    if not post_id_match:
        raise Exception("Could not extract post ID from URL.")
    post_id = post_id_match.group(1)

    # 2. Parse Next.js data chunks to find the reference ID for this post's video
    chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
    ref_id = None
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                chunk_str = data[1]
                if post_id in chunk_str:
                    idx = chunk_str.find(post_id)
                    sub = chunk_str[max(0, idx - 10):idx + 1500]
                    url_match = re.search(r'\\?"url\\?":\\?"\$([^"$\\]+)\\?"', sub)
                    if url_match:
                        ref_id = url_match.group(1)
                        break
        except Exception:
            pass

    # 3. Resolve the reference ID to the actual video URL
    if ref_id:
        # The ref_id definition looks like `72:T400,https://...mp4?...`
        idx = text.find(f'{ref_id}:T')
        if idx == -1:
            idx = text.find(f'{ref_id}:"')
        if idx == -1:
            idx = text.find(f'{ref_id}:\\"')

        if idx != -1:
            sub = text[idx:idx + 2000]
            mp4_match = re.search(r'(https?://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*)', sub)
            if mp4_match:
                return _clean_video_url(mp4_match.group(1))

    # 4. Fallback: scan all URLs and pick the best one by file size
    raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
    if not raw_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+fbcdn\.net[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)

    if not raw_urls:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not an image or text post)."
        )

    # Order-preserving deduplication
    seen = set()
    cleaned_urls = []
    for u in raw_urls:
        cu = unescape_url(u)
        if cu not in seen:
            seen.add(cu)
            cleaned_urls.append(cu)

    prog_urls = [u for u in cleaned_urls if is_progressive(u)]
    if not prog_urls:
        prog_urls = cleaned_urls

    # Pick the largest file to avoid 5-second thumbnails
    import concurrent.futures

    def _check_size(url):
        try:
            h = requests.head(url, timeout=5, headers=HEADERS)
            return url, int(h.headers.get('Content-Length', 0))
        except Exception:
            return url, 0

    best_url, best_size = prog_urls[0], 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for url, size in executor.map(lambda u: _check_size(u), prog_urls):
            if size > best_size:
                best_size = size
                best_url = url

    return best_url
