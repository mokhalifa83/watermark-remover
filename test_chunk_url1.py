import requests, re, json
from scraper import HEADERS
response = requests.get('https://www.meta.ai/@washt/post/sE8ZfW85d1A/fun-times?utm_source=meta_ai_web_copy_video_link', headers=HEADERS, timeout=15)
text = response.text
chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
for chunk in chunks:
    try:
        data = json.loads(chunk)
        if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
            chunk_str = data[1]
            if '11:' in chunk_str or '"11":' in chunk_str:
                idx = chunk_str.find('11:')
                if idx == -1: idx = chunk_str.find('"11":')
                print(chunk_str[max(0, idx-100) : min(len(chunk_str), idx+200)])
    except:
        pass
