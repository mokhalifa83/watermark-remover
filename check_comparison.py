import requests
from bs4 import BeautifulSoup
import re
import json
import yt_dlp
import sys

def check_all_methods(url):
    print(f"Testing URL: {url}\n")
    
    # --- Method 1: yt-dlp ---
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
                print(f"Found playlist with {len(info['entries'])} entries.")
                print(f"Entry 0 Title: {info['entries'][0].get('title')}")
                print(f"Entry 0 URL: {info['entries'][0].get('url')}")
            else:
                print(f"Title: {info.get('title')}")
                print(f"URL: {info.get('url')}")
    except Exception as e:
        print(f"Error: {e}")

    # --- Method 2: BS4 ---
    print("\n--- Method 2: BS4 ---")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.meta.ai/'
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        og_video = soup.find("meta", property="og:video")
        if og_video:
            print(f"og:video: {og_video.get('content')}")
            
        og_video_secure = soup.find("meta", property="og:video:secure_url")
        if og_video_secure:
            print(f"og:video:secure_url: {og_video_secure.get('content')}")
            
        # Regex on scripts
        scripts = soup.find_all("script")
        found_regex = False
        for script in scripts:
            if script.string:
                patterns = [
                    r'"(https?://[^"]+\.mp4[^"]*)"',
                    r'"video_url":\s*"([^"]+)"'
                ]
                for p in patterns:
                    matches = re.findall(p, script.string)
                    for m in matches:
                        print(f"Regex Match: {m[:100]}...")
                        found_regex = True
    except Exception as e:
        print(f"Error: {e}")

    # --- Method 3: JSON-LD ---
    print("\n--- Method 3: JSON-LD ---")
    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            data = json.loads(script.string)
            print(f"JSON-LD Data: {str(data)[:200]}...")
            if 'contentUrl' in str(data):
                print("Found contentUrl in JSON-LD")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    check_all_methods(test_url)
