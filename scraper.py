import yt_dlp
import requests
from bs4 import BeautifulSoup
import re
import json

def extract_video_url(share_url):
    """
    Extracts the direct video URL from a Meta AI share link using multiple methods.
    """
    
    # Method 1: Try yt-dlp with enhanced options
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.meta.ai/',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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

            # Helper to add candidate
            def add_candidate(entry):
                url = entry.get('url')
                if url:
                    # Try to get size from metadata first
                    size = entry.get('filesize') or entry.get('filesize_approx')
                    if size is None:
                        # Fallback to HEAD request
                        try:
                            head = requests.head(url, allow_redirects=True, timeout=5)
                            if head.status_code == 200:
                                size = int(head.headers.get('Content-Length', 0))
                        except:
                            pass
                    
                    if size is not None:
                        candidates.append({'url': url, 'size': size})

            # 1. Check for 'entries' (Playlist)
            if 'entries' in info_dict:
                entries = list(info_dict['entries'])
                # Check first 10 entries to be safe
                for entry in entries[:10]:
                    add_candidate(entry)
            
            # 2. Check for single video in top-level
            else:
                add_candidate(info_dict)

            # 3. If no URL yet, check formats
            if not candidates and 'formats' in info_dict:
                 formats = info_dict.get('formats', [])
                 # Filter mostly likely useful formats
                 video_formats = [f for f in formats if f.get('url') and (f.get('vcodec') != 'none' or f.get('ext') == 'mp4')]
                 if video_formats:
                     # Just take the best one from formats if we are here
                     add_candidate(video_formats[-1])

            # Select the largest video
            if candidates:
                # Sort by size descending
                candidates.sort(key=lambda x: x['size'], reverse=True)
                best_video = candidates[0]
                print(f"Selected video with size: {best_video['size'] / (1024*1024):.2f} MB")
                return best_video['url']
                
    except Exception as e:
        print(f"yt-dlp error: {e}")
        pass  # Fall through to next method
    
    # Method 2: Direct HTML scraping with BeautifulSoup
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.meta.ai/'
        }
        
        session = requests.Session()
        response = session.get(share_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check OpenGraph video tags
            og_video = soup.find("meta", property="og:video")
            if og_video and og_video.get('content'):
                return og_video['content']
                
            og_video_secure = soup.find("meta", property="og:video:secure_url")
            if og_video_secure and og_video_secure.get('content'):
                return og_video_secure['content']
            
            # Check for video tags
            video_tag = soup.find("video")
            if video_tag:
                src = video_tag.get("src")
                if src:
                    return src
                sources = video_tag.find_all("source")
                for source in sources:
                    src = source.get('src')
                    if src:
                        return src
            
            # Look for video URLs in script tags
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string:
                    # Look for common video URL patterns
                    patterns = [
                        r'"(https?://[^"]+\.mp4[^"]*)"',
                        r"'(https?://[^']+\.mp4[^']*)'",
                        r'"videoUrl":\s*"([^"]+)"',
                        r'"video_url":\s*"([^"]+)"',
                        r'"url":\s*"(https?://[^"]+\.mp4[^"]*)"'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string)
                        if matches:
                            return matches[0]
        
    except Exception as e:
        pass  # Fall through to next method
    
    # Method 3: Try to extract from JSON-LD or structured data
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.meta.ai/'
        }
        response = requests.get(share_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Look for video content URL
                if isinstance(data, dict):
                    if 'contentUrl' in data:
                        return data['contentUrl']
                    if 'video' in data and isinstance(data['video'], dict):
                        if 'contentUrl' in data['video']:
                            return data['video']['contentUrl']
            except json.JSONDecodeError:
                continue
        
    except Exception as e:
        pass
    
    # If all methods fail
    raise Exception("Failed to extract video URL using all available methods. Meta AI may have changed their video structure or the URL may be invalid.")
