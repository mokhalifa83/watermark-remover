import yt_dlp

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.meta.ai/',
}

def extract_video_url(share_url: str) -> str:
    ydl_opts = {
        'format': 'best',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'http_headers': HEADERS,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(share_url, download=False)

        if not info:
            raise Exception("yt-dlp could not extract info from this URL")

        # Direct URL on the top-level info
        if info.get('url'):
            return info['url']

        # Playlist/entries — take first one
        entries = info.get('entries') or []
        for entry in entries:
            if entry and entry.get('url'):
                return entry['url']

        # Formats list — take last (usually best quality)
        formats = info.get('formats') or []
        if formats:
            return formats[-1]['url']

        raise Exception("yt-dlp extracted info but found no video URL inside it")
