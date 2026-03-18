import requests
import re

HEADERS = {
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

    # Meta AI embeds direct fbcdn.net .mp4 URLs in the page HTML inside JSON blobs.
    # We grab them out directly, making sure to grab all the URL parameters.
    # We stop at quotes, whitespace, or angle brackets.
    raw_urls = re.findall(r'https://video-[^\s"\'<>]+', text)

    if not raw_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+fbcdn\.net[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)

    if raw_urls:
        # Take the first one, it's usually the highest quality preload source
        url_str = raw_urls[0]

        # Cleanup: the URL is often inside a JSON string, so it has escaped characters
        # If the regex grabbed a trailing backslash before a quote, remove it
        if url_str.endswith('\\'):
            url_str = url_str[:-1]

        # Stop if we hit an escaped XML tag like \u003c/BaseURL\u003e
        idx = url_str.find(r'\u003c')
        if idx != -1:
            url_str = url_str[:idx]

        # Fix JSON escapes
        url_str = url_str.replace(r'\u0026', '&')
        url_str = url_str.replace(r'\/', '/')
        url_str = url_str.replace('&amp;', '&')

        return url_str

    raise Exception(
        "Could not find a video in this Meta AI link. "
        "Make sure it is a direct video post URL (not an image or text post)."
    )
