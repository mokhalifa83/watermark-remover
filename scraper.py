import requests
import re
from bs4 import BeautifulSoup

HEADERS = {
    # Facebook's own crawler UA — meta.ai serves full SSR HTML to this
    'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def extract_video_url(share_url: str) -> str:
    """
    Fetches the Meta AI post page and extracts the direct .mp4 CDN URL
    that Meta embeds in the page HTML as preload/video assets.
    """
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    text = response.text

    # Meta AI embeds direct fbcdn.net .mp4 URLs in the page HTML
    # They appear in preload tags, JSON data, and inline script blocks
    # We find all of them and return the first unique valid one
    raw_urls = re.findall(r'https://video-[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*', text)

    if raw_urls:
        # Unescape HTML entities (&amp; -> &) and Unicode escapes
        clean = raw_urls[0].replace('&amp;', '&')
        return clean

    # Fallback: any fbcdn video URL
    fallback = re.findall(r'https://[^\s"\'<>\\]+fbcdn\.net[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*', text)
    if fallback:
        return fallback[0].replace('&amp;', '&')

    raise Exception(
        "Could not find a video in this Meta AI link. "
        "Make sure it is a direct video post URL (not an image or text post)."
    )
