import requests, re, json
from scraper import HEADERS

def get_video_exact(share_url):
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    text = response.text
    
    match = re.search(r'/post/([^/?]+)', share_url)
    if not match: return None
    post_id = match.group(1)
    
    ref_id = None
    chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                chunk_str = data[1]
                if f'"id":"{post_id}"' in chunk_str or f'\\"id\\":\\"{post_id}\\"' in chunk_str:
                    idx = chunk_str.find(post_id)
                    sub = chunk_str[max(0, idx-10):idx+1500]
                    url_match = re.search(r'\\?"url\\?":\\?"\$([^"\$\\]+)\\?"', sub)
                    if url_match:
                        ref_id = url_match.group(1)
                        print(f'Found ref_id: {ref_id}')
                        break
        except Exception:
            pass
            
    if not ref_id: return None
    
    # 3. Find the URL for this ref_id
    idx = text.find(f'{ref_id}:T')
    if idx == -1: idx = text.find(f'{ref_id}:"')
    if idx == -1: idx = text.find(f'{ref_id}:\\"')
    
    if idx != -1:
        sub = text[idx : idx + 2000]
        # Unescape common JSON escapes
        sub = sub.replace(r'\u0026', '&').replace(r'\/', '/').replace(r'\"', '"')
        
        mp4_match = re.search(r'(https?://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*)', sub)
        if mp4_match:
            return mp4_match.group(1)
        
    return None

print('1:', get_video_exact('https://www.meta.ai/@washt/post/sE8ZfW85d1A/fun-times?utm_source=meta_ai_web_copy_video_link'))
print('2:', get_video_exact('https://www.meta.ai/@ralphmaddad518/post/Uu5EESQK5jQ?utm_source=meta_ai_web_copy_video_link'))
