import yt_dlp
import requests
from bs4 import BeautifulSoup
import re
import json

# Minimum file size to trust a video URL (avoid logos/placeholders)
MIN_SUBSTANTIAL_SIZE = 1 * 1024 * 1024  # 1MB

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.meta.ai/',
}


def extract_video_url(share_url: str) -> str:
    """
    Extracts the direct CDN video URL from a Meta AI share link.
    Tries multiple methods in order of reliability.
    Returns the URL string on success, raises Exception on failure.
    """

    # === METHOD 1: yt-dlp (most reliable — kept up-to-date against Meta changes) ===
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'extract_flat': False,
            'http_headers': HEADERS,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(share_url, download=False)

            if not info:
                raise Exception("yt-dlp returned no info")

            candidates = []

            def add_candidate(entry):
                url = entry.get('url')
                if not url:
                    return
                size = entry.get('filesize') or entry.get('filesize_approx')
                if size is None:
                    try:
                        head = requests.head(url, allow_redirects=True, timeout=5, headers=HEADERS)
                        if head.status_code == 200:
                            size = int(head.headers.get('Content-Length', 0))
                    except Exception:
                        size = 0
                candidates.append({'url': url, 'size': size or 0})

            # Only trust first entry to avoid random suggestions
            if 'entries' in info:
                entries = list(info['entries'])
                if entries:
                    primary = entries[0]
                    add_candidate(primary)
                    for fmt in primary.get('formats', []):
                        if fmt.get('url'):
                            add_candidate(fmt)
                else:
                    add_candidate(info)
            else:
                add_candidate(info)
                for fmt in info.get('formats', []):
                    if fmt.get('url'):
                        add_candidate(fmt)

            if candidates:
                unique = {c['url']: c for c in candidates}.values()
                best = sorted(unique, key=lambda x: x['size'], reverse=True)[0]

                if best['size'] < MIN_SUBSTANTIAL_SIZE:
                    raise Exception(f"Video too small ({best['size']} bytes) — likely a placeholder")

                print(f"[yt-dlp] Found video: {best['size'] / 1024 / 1024:.2f} MB")
                return best['url']

            raise Exception("yt-dlp found no usable video candidates")

    except Exception as e:
        print(f"[yt-dlp] Failed: {e}")

    # === METHOD 2: HTML scraping — OpenGraph, video tags, JSON-LD, inline scripts ===
    try:
        url = _scrape_video_url(share_url)
        if url:
            print(f"[Scrape] Found video URL via HTML scraping")
            return url
    except Exception as e:
        print(f"[Scrape] Failed: {e}")

    raise Exception(
        "Failed to extract video URL using all available methods. "
        "Try updating yt-dlp: pip install -U yt-dlp"
    )


def _scrape_video_url(share_url: str) -> str | None:
    """Fallback scraper using BeautifulSoup on the Meta AI page HTML."""
    session = requests.Session()
    response = session.get(share_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. OpenGraph video tags
    for prop in ('og:video:secure_url', 'og:video'):
        tag = soup.find('meta', property=prop)
        if tag and tag.get('content'):
            return tag['content']

    # 2. HTML <video> tag
    video_tag = soup.find('video')
    if video_tag:
        src = video_tag.get('src')
        if src:
            return src
        for source in video_tag.find_all('source'):
            if source.get('src'):
                return source['src']

    # 3. JSON-LD structured data
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            if isinstance(data, dict):
                if 'contentUrl' in data:
                    return data['contentUrl']
                if isinstance(data.get('video'), dict):
                    url = data['video'].get('contentUrl')
                    if url:
                        return url
        except (json.JSONDecodeError, TypeError):
            continue

    # 4. Regex patterns inside inline <script> tags
    patterns = [
        r'"(https?://[^"]+\.mp4[^"]*)"',
        r"'(https?://[^']+\.mp4[^']*)'",
        r'"videoUrl":\s*"([^"]+)"',
        r'"video_url":\s*"([^"]+)"',
        r'"contentUrl":\s*"([^"]+)"',
    ]
    for script in soup.find_all('script'):
        text = script.string or ''
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Decode unicode escapes (e.g. \u0026 → &)
                return matches[0].encode().decode('unicode_escape')

    return None
