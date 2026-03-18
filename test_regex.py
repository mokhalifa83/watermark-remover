import requests, re
url = 'https://www.meta.ai/@kasey.duney/post/oN6J5K1br8a/remix-of-pizzaslime?utm_source=meta_ai_web_copy_video_link'
r = requests.get(url, headers={'User-Agent': 'facebookexternalhit/1.1'}, timeout=15)
text = r.text

raw_urls = re.findall(r'https://video-[^\s"\'<>]+', text)
for i, u in enumerate(raw_urls[:3]):
    print(f"Raw {i}: {u}")
    try:
        # Some URLs are inside JSON strings, so they have \u0026 instead of &
        # and \/ instead of /
        clean = u.encode().decode('unicode_escape')
    except Exception:
        clean = u
    clean = clean.replace('&amp;', '&')
    print(f"Clean {i}: {clean}")
