import yt_dlp
import sys

def inspect_playlist(url):
    print(f"Testing URL: {url}\n")
    print("--- Method 1: yt-dlp ---")
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
                    print(f"\nEntry {i}:")
                    print(f"  ID: {entry.get('id')}")
                    print(f"  Title: {entry.get('title')}")
                    print(f"  Duration: {entry.get('duration')}")
                    print(f"  URL: {entry.get('url')}")
            else:
                print("Not a playlist.")
                print(f"ID: {info.get('id')}")
                print(f"Title: {info.get('title')}")
                print(f"Duration: {info.get('duration')}")
                print(f"URL: {info.get('url')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    inspect_playlist(test_url)
