import requests, re
from scraper import HEADERS, unescape_url, is_progressive

url1 = 'https://www.meta.ai/@washt/post/sE8ZfW85d1A/fun-times?utm_source=meta_ai_web_copy_video_link'
url2 = 'https://www.meta.ai/@ralphmaddad518/post/Uu5EESQK5jQ?utm_source=meta_ai_web_copy_video_link'

def check(url):
    response = requests.get(url, headers=HEADERS, timeout=15)
    text = response.text
    raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
    if not raw_urls:
        raw_urls = re.findall(r'https://[^\s"\'<>]+fbcdn\.net[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
    
    seen = set()
    cleaned_urls = []
    for u in raw_urls:
        cu = unescape_url(u)
        if cu not in seen:
            seen.add(cu)
            cleaned_urls.append(cu)
            
    prog_urls = [u for u in cleaned_urls if is_progressive(u)]
    print('First progressive URL:', prog_urls[0][:100] if prog_urls else 'None')
    
    if prog_urls:
        try:
            h = requests.head(prog_urls[0], timeout=5, headers=HEADERS)
            size = int(h.headers.get('Content-Length', 0))
            print(f'Size: {size / (1024*1024):.2f} MB')
        except:
            pass

print('Checking URL 1...')
check(url1)
print('Checking URL 2...')
check(url2)
