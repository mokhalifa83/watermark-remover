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


from bs4 import BeautifulSoup

def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL.
    By parsing the script tags in DOM order, we guarantee the first match
    is the main post video, avoiding recommended 5s videos.
    """
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all('script')
    
    for script in scripts:
        if script.string:
            patterns = [
                r'"(https?://[^"]+\.mp4[^"]*)"',
                r"'(https?://[^']+\.mp4[^']*)'",
                r'"videoUrl":\s*"([^"]+)"',
                r'"video_url":\s*"([^"]+)"',
                r'"url":\s*"(https?://[^"]+\.mp4[^"]*)"'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string)
                if matches:
                    u = matches[0]
                    u = u.replace('\\\\', '\\').replace('\\/', '/')
                    idx = u.find(r'\u003c')
                    if idx != -1: 
                        u = u[:idx]
                    return u.replace(r'\u0026', '&')

    # Fallback to general regex if script tags don't have it
    raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', response.text)
    if not raw_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+fbcdn\.net[^\s"\'<>]+\.mp4[^\s"\'<>]*', response.text)
        
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
    if prog_urls:
        return prog_urls[0]
        
    return cleaned_urls[0]
