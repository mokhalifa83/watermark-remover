import requests
import re
import base64
import urllib.parse
import json
import concurrent.futures

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


def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL.

    Strategy: Meta AI uses Next.js server-side rendering. The post's video URL
    is stored as a reference (e.g. "$73") in the post data, and the actual URL
    is defined in a separate data chunk. We trace post_id -> ref_id -> video URL
    to guarantee we get the exact video for the requested post, not a random
    recommended clip.

    Falls back to picking the largest progressive video if reference tracing fails.
    """
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    text = response.text

    # 1. Extract Post ID from the share URL
    post_id_match = re.search(r'/post/([^/?]+)', share_url)
    if not post_id_match:
        raise Exception("Could not extract post ID from URL.")
    post_id = post_id_match.group(1)

    # 2. Parse ALL Next.js data chunks
    parsed_chunks = []
    chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                parsed_chunks.append(data[1])
        except Exception:
            pass

    # 3. Find the reference ID for this post's video URL
    ref_id = None
    for chunk_str in parsed_chunks:
        # Check for post_id in various formats
        if post_id in chunk_str:
            idx = chunk_str.find(post_id)
            # Search a window around the post_id for the video URL reference
            sub = chunk_str[max(0, idx - 100):idx + 2000]
            # Match "url":"$73" or \"url\":\"$73\"
            url_match = re.search(r'\\?"url\\?":\\?"\$([^"$\\]+)\\?"', sub)
            if url_match:
                ref_id = url_match.group(1)
                break

    # 4. Resolve the reference ID to the actual video URL
    if ref_id:
        # Search both parsed chunks and raw text for the resolved URL
        # We look for patterns like 73:T or 73:" or 73:\"
        search_sources = parsed_chunks + [text]
        for source in search_sources:
            for pattern in [f'{ref_id}:T', f'{ref_id}:"', f'{ref_id}:\\"']:
                idx = source.find(pattern)
                if idx != -1:
                    sub = source[idx:idx + 3000]
                    mp4_match = re.search(r'(https?://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*)', sub)
                    if mp4_match:
                        u = mp4_match.group(1)
                        # Clean the URL (unescape characters)
                        u = u.replace(r'\u0026', '&').replace('\\\\', '\\').replace('\\/', '/')
                        # Strip any trailing Next.js chunk separator junk
                        u = re.sub(r'[a-z0-9]+:T[a-z0-9]+,.*$', '', u)
                        u = u.rstrip('\\')
                        return u

    # 5. Fallback: scan all URLs in parsed chunks and pick
    #    the largest progressive one.
    fallback_urls = []
    for chunk_str in parsed_chunks:
        matches = re.findall(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', chunk_str)
        fallback_urls.extend(matches)

    # Also scan raw HTML as a last resort
    if not fallback_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
        fallback_urls = [unescape_url(u) for u in raw_urls]

    if not fallback_urls:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not an image or text post)."
        )

    # Order-preserving deduplication
    seen = set()
    cleaned_urls = []
    for u in fallback_urls:
        if u not in seen:
            seen.add(u)
            cleaned_urls.append(u)

    prog_urls = [u for u in cleaned_urls if is_progressive(u)]
    if not prog_urls:
        prog_urls = cleaned_urls

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
