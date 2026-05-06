import requests, json, re
from scraper import HEADERS

url = 'https://www.meta.ai/@washt'
r = requests.get(url, headers=HEADERS)
text = r.text

chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
for i, chunk in enumerate(chunks):
    try:
        data = json.loads(chunk)
        if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
            chunk_str = data[1]
            if 'fbcdn' in chunk_str:
                print(f"Chunk {i} has fbcdn links")
                # Find all URLs in this chunk
                urls = re.findall(r'https?://[^\s"\'<>\\]+', chunk_str)
                for u in urls:
                    if 'fbcdn.net' in u:
                        print(f"  {u}")
    except:
        pass
