import requests
from bs4 import BeautifulSoup
import re
import json

def test_scrape(url):
    print(f"Testing URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Check OpenGraph tags
        og_video = soup.find("meta", property="og:video")
        if og_video:
            print(f"Found og:video: {og_video['content']}")
            return og_video['content']
            
        og_video_secure = soup.find("meta", property="og:video:secure_url")
        if og_video_secure:
            print(f"Found og:video:secure_url: {og_video_secure['content']}")
            return og_video_secure['content']
            
        # 2. Check standard video tags
        video_tag = soup.find("video")
        if video_tag:
            src = video_tag.get("src")
            if src:
                print(f"Found video tag src: {src}")
                return src
            sources = video_tag.find_all("source")
            for source in sources:
                print(f"Found video source: {source.get('src')}")
                return source.get('src')

        # 3. Look for JSON-LD or script data
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:
                if "video_url" in script.string:
                    print("Found 'video_url' in script, attempting regex extraction...")
                    # Naive regex for mp4 urls
                    matches = re.findall(r'"(https?://[^"]+\.mp4[^"]*)"', script.string)
                    if matches:
                        print(f"Regex match: {matches[0]}")
                        return matches[0]

        print("No video found in initial pass.")
        # print("Page content snippet:")
        # print(response.text[:1000])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # URL from user's screenshot
    test_scrape("https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/")
