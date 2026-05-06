import requests, re
from bs4 import BeautifulSoup
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def extract(share_url):
    response = requests.get(share_url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
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
                    u = matches[0]
                    u = u.replace('\\\\', '\\').replace('\\/', '/')
                    idx = u.find(r'\u003c')
                    if idx != -1: u = u[:idx]
                    return u.replace(r'\u0026', '&')
    return None

url1 = 'https://www.meta.ai/@washt/post/sE8ZfW85d1A/fun-times?utm_source=meta_ai_web_copy_video_link'
url2 = 'https://www.meta.ai/@ralphmaddad518/post/Uu5EESQK5jQ?utm_source=meta_ai_web_copy_video_link'
print('1:', extract(url1))
print('2:', extract(url2))
