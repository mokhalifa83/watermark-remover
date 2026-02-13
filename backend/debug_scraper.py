from scraper import extract_video_url
import yt_dlp
import json

url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"

print(f"Testing extraction for: {url}")

try:
    # Test the function directly
    # video_url = extract_video_url(url)
    # print(f"Result URL: {video_url}")

    # Inspect raw output to see structure
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print("Keys:", info.keys())
        if 'entries' in info:
            print("Found entries!")
            entries = list(info['entries'])
            if entries:
                first_entry = entries[0]
                print("First entry keys:", first_entry.keys())
                print("First entry URL:", first_entry.get('url'))
        else:
            print("No entries found.")
            print("URL:", info.get('url'))
            
except Exception as e:
    print(f"Error: {e}")
