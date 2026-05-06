import urllib.parse, base64, json, re

with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

raw_urls = re.findall(r'https://[^\s"\'<>]+\.mp4[^\s"\'<>]*', text)
for u in set(raw_urls):
    u = u.replace('\\\\', '\\').replace('\\/', '/')
    idx = u.find(r'\u003c')
    if idx != -1: u = u[:idx]
    u = u.replace(r'\u0026', '&')
    
    match = re.search(r'efg=([^&]+)', u)
    if match:
        efg = urllib.parse.unquote(match.group(1))
        pad = len(efg) % 4
        if pad: efg += '=' * (4 - pad)
        try:
            dec = base64.b64decode(efg).decode('utf-8', errors='ignore')
            if 'progressive' in dec.lower():
                print(dec)
        except: pass
