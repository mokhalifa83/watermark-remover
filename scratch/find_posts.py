import requests, re
from scraper import HEADERS

url = 'https://www.meta.ai/@washt'
r = requests.get(url, headers=HEADERS)
posts = re.findall(r'/post/([^/"\'\s?]+)', r.text)
print(f"Found posts: {list(set(posts))}")
