from scraper import extract_video_url, HEADERS, unescape_url, is_progressive, check_url_size
import requests
import re
import concurrent.futures

url = 'https://www.meta.ai/@ralphmaddad518/post/Uu5EESQK5jQ?utm_source=meta_ai_web_copy_video_link'
response = requests.get(url, headers=HEADERS, timeout=15)
text = response.text

raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
cleaned_urls = list(set([unescape_url(u) for u in raw_urls]))
prog_urls = [u for u in cleaned_urls if is_progressive(u)]

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_url_size, u): u for u in prog_urls}
    for future in concurrent.futures.as_completed(futures):
        u, size = future.result()
        results.append((size, u))

results.sort(reverse=True)
for size, u in results:
    print(f'{size / (1024*1024):.2f} MB - {u[:80]}...')
