import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.meta.ai/',
}


def extract_video_url(share_url: str) -> str:
    """
    Extracts the direct video URL from a Meta AI share link.
    Meta AI serves og:video tags in its page HTML — we grab that directly.
    yt-dlp does NOT support meta.ai URLs so it is not used here.
    """
    session = requests.Session()
    response = session.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # og:video:secure_url is preferred (HTTPS), fall back to og:video
    for prop in ('og:video:secure_url', 'og:video:url', 'og:video'):
        tag = soup.find('meta', property=prop)
        if tag and tag.get('content'):
            return tag['content']

    raise Exception(
        "Could not find a video in this Meta AI link. "
        "Make sure the link is a direct video post URL."
    )
