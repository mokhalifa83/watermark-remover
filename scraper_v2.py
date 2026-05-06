import yt_dlp
import re
import json
import requests
from bs4 import BeautifulSoup

# Minimum size for a video to be considered "substantial" (not a thumbnail/placeholder)
MIN_SUBSTANTIAL_SIZE = 1024 * 1024 # 1MB

def extract_video_url(share_url):
    """
    Extracts direct video URL from Meta AI share link using yt-dlp as primary,
    with fallback to BeautifulSoup scraping.
    """
    
    # Method 1: yt-dlp
    try:
        print(f"[Method 1] Trying yt-dlp extraction for: {share_url}")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.meta.ai/',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(share_url, download=False)
            if not info_dict:
                raise Exception("yt-dlp returned empty info_dict")

            candidates = []
            def add_candidate(entry):
                url = entry.get('url')
                if url:
                    size = entry.get('filesize') or entry.get('filesize_approx')
                    if size is None:
                        try:
                            head = requests.head(url, allow_redirects=True, timeout=5)
                            if head.status_code == 200:
                                size = int(head.headers.get('Content-Length', 0))
                        except Exception:
                            pass
                    if size is not None:
                        candidates.append({'url': url, 'size': size})

            if 'entries' in info_dict:
                entries = list(info_dict['entries'])
                if entries:
                    primary_entry = entries[0]
                    add_candidate(primary_entry)
                    formats = primary_entry.get('formats', [])
                    for f in formats:
                        if f.get('url'):
                            add_candidate(f)
                else:
                    add_candidate(info_dict)
            else:
                add_candidate(info_dict)

            if not candidates and 'formats' in info_dict:
                 formats = info_dict.get('formats', [])
                 for f in formats:
                     if f.get('url'):
                         add_candidate(f)

            if candidates:
                unique_candidates = {c['url']: c for c in candidates}.values()
                sorted_candidates = sorted(unique_candidates, key=lambda x: x['size'], reverse=True)
                best_video = sorted_candidates[0]
                if best_video['size'] >= MIN_SUBSTANTIAL_SIZE:
                    print(f"[Method 1] Success! Selected video: {best_video['url'][:60]}...")
                    return best_video['url']
                
    except Exception as e:
        print(f"[Method 1] yt-dlp failed: {str(e)}")
    
    # Method 2: BeautifulSoup Fallback
    try:
        print(f"[Method 2] Trying direct HTML scraping...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.meta.ai/'
        }
        response = requests.get(share_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for video tags
        video_tag = soup.find("video")
        if video_tag and video_tag.get("src"):
            return video_tag.get("src")
            
        # Check script tags for mp4 URLs
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:
                matches = re.findall(r'"(https?://[^"]+\.mp4[^"]*)"', script.string)
                if matches:
                    return matches[0].replace('\\/', '/')
        
    except Exception as e:
        print(f"[Method 2] HTML scraping failed: {str(e)}")
    
    raise Exception("Failed to extract video URL using yt-dlp or fallback methods.")
