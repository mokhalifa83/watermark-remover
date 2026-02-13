import yt_dlp
import requests
import sys

def check_sizes(url):
    print(f"Testing URL: {url}\n")
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.meta.ai/',
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                entries = list(info['entries'])
                print(f"Found playlist with {len(entries)} entries.")
                for i, entry in enumerate(entries):
                    vid_url = entry.get('url')
                    if vid_url:
                        try:
                            # Use range header to just get headers without downloading
                            head = requests.head(vid_url, allow_redirects=True, timeout=5)
                            size = int(head.headers.get('Content-Length', 0))
                            size_mb = size / (1024 * 1024)
                            print(f"Entry {i}: {size_mb:.2f} MB (Duration: {entry.get('duration')}s)")
                        except Exception as e:
                            print(f"Entry {i}: Error fetching size ({e})")
            else:
                print("Not a playlist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    check_sizes(test_url)
