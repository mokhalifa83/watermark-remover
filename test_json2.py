import json, re

with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

def unescape_url(u):
    if u.endswith('\\'): u = u[:-1]
    u = u.replace('\\\\', '\\').replace('\\/', '/')
    idx = u.find(r'\u003c')
    if idx != -1: u = u[:idx]
    return u.replace(r'\u0026', '&')

matches = re.finditer(r'<script type="application/json".*?>(.*?)</script>', text)

for m in matches:
    try:
        data = json.loads(m.group(1))
        data_str = json.dumps(data)
        if 'Uu5EESQK5jQ' in data_str:
            print("Found Post ID in JSON block! Length:", len(data_str))
            
            # Find URLs
            urls = set(re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', data_str))
            if urls:
                print(f"Found {len(urls)} MP4 URLs in this block:")
                for u in urls:
                    print("  ->", unescape_url(u)[:100])
            else:
                print("No MP4 URLs found in this JSON block.")
    except Exception as e:
        pass
