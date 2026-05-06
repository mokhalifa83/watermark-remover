import requests, re
from scraper import HEADERS

url = 'https://www.meta.ai/@washt'
r = requests.get(url, headers=HEADERS)
links = re.findall(r'https://[^/"\'\s?]+\.xx\.fbcdn\.net/[^"\'\s?]+', r.text)
for l in links[:20]:
    print(l)
