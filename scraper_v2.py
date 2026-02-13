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
        print(f"[Method 1] Trying yt-dlp extraction for: {share_url}")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
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
                        except Exception as e:
                            print(f"[Method 1] Error checking size for {url[:30]}...: {e}")
                    
                    if size is not None:
                        print(f"[Method 1] Candidate found: {url[:30]}... ({size / (1024*1024):.2f} MB)")
                        candidates.append({'url': url, 'size': size})

            # 1. Process entries - ONLY trust the first one to avoid random suggestions
            if 'entries' in info_dict:
                entries = list(info_dict['entries'])
                print(f"[Method 1] Found playlist with {len(entries)} entries")
                if entries:
                    # The first entry is the actual post video
                    primary_entry = entries[0]
                    add_candidate(primary_entry)
                    
                    # If the primary entry has its own formats, add them too
                    formats = primary_entry.get('formats', [])
                    for f in formats:
                        if f.get('url'):
                            add_candidate(f)
                else:
                    add_candidate(info_dict)
            else:
                add_candidate(info_dict)

            # 2. Check formats in top-level if still no candidates
            if not candidates and 'formats' in info_dict:
                 formats = info_dict.get('formats', [])
                 for f in formats:
                     if f.get('url'):
                         add_candidate(f)

            # Select the largest video from our validated candidates (all matching the primary content)
            if candidates:
                # Remove duplicates and sort by size
                unique_candidates = {c['url']: c for c in candidates}.values()
                sorted_candidates = sorted(unique_candidates, key=lambda x: x['size'], reverse=True)
                best_video = sorted_candidates[0]
                print(f"[Method 1] Success! Selected primary video: {best_video['url'][:100]}... ({best_video['size'] / (1024*1024):.2f} MB)")
                return best_video['url']
            else:
                print("[Method 1] Failed - no video URL found in yt-dlp extraction")
                
    except Exception as e:
        print(f"[Method 1] yt-dlp failed: {str(e)}")
    
    # Method 2: Direct HTML scraping with BeautifulSoup
    try:
        print(f"[Method 2] Trying direct HTML scraping...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.meta.ai/'
        }
        
        session = requests.Session()
        response = session.get(share_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check OpenGraph video tags
        og_video = soup.find("meta", property="og:video")
        if og_video and og_video.get('content'):
            video_url = og_video['content']
            print(f"[Method 2] Found og:video: {video_url[:100]}...")
            return video_url
            
        og_video_secure = soup.find("meta", property="og:video:secure_url")
        if og_video_secure and og_video_secure.get('content'):
            video_url = og_video_secure['content']
            print(f"[Method 2] Found og:video:secure_url: {video_url[:100]}...")
            return video_url
        
        # Check for video tags
        video_tag = soup.find("video")
        if video_tag:
            src = video_tag.get("src")
            if src:
                print(f"[Method 2] Found video tag src: {src[:100]}...")
                return src
            sources = video_tag.find_all("source")
            for source in sources:
                src = source.get('src')
                if src:
                    print(f"[Method 2] Found video source: {src[:100]}...")
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
                        video_url = matches[0]
                        print(f"[Method 2] Found video URL in script: {video_url[:100]}...")
                        return video_url
        
        print("[Method 2] Failed - no video URL found in HTML")
        
    except Exception as e:
        print(f"[Method 2] HTML scraping failed: {str(e)}")
    
    # Method 3: Try to extract from JSON-LD or structured data
    try:
        print(f"[Method 3] Trying JSON-LD extraction...")
        response = requests.get(share_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Look for video content URL
                if isinstance(data, dict):
                    if 'contentUrl' in data:
                        print(f"[Method 3] Found contentUrl: {data['contentUrl'][:100]}...")
                        return data['contentUrl']
                    if 'video' in data and isinstance(data['video'], dict):
                        if 'contentUrl' in data['video']:
                            print(f"[Method 3] Found video.contentUrl: {data['video']['contentUrl'][:100]}...")
                            return data['video']['contentUrl']
            except json.JSONDecodeError:
                continue
        
        print("[Method 3] Failed - no video URL found in JSON-LD")
        
    except Exception as e:
        print(f"[Method 3] JSON-LD extraction failed: {str(e)}")
    
    # If all methods fail
    raise Exception("Failed to extract video URL using all available methods. Meta AI may have changed their video structure or the URL may be invalid.")
