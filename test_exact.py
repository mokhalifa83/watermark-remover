import requests, re, json
from scraper import HEADERS

def extract_exact(share_url):
    response = requests.get(share_url, headers=HEADERS, timeout=15)
    text = response.text
    
    # 1. Extract Post ID
    match = re.search(r'/post/([^/?]+)', share_url)
    if not match:
        print('Could not find post ID in URL')
        return None
    post_id = match.group(1)
    
    # 2. Find the reference ID
    # Pattern looks like: "id":"POST_ID" ... "url":"$REF_ID"
    # Note: there might be escaped quotes like \"id\":\"POST_ID\"
    # We can unescape the whole text first? No, it's safer to use a loose regex.
    # We can look for `id` and `url` within a short distance (e.g. 1000 chars)
    # Actually, we can unescape Next.js JSON strings.
    # Let's just find all self.__next_f.push(...) chunks and parse them.
    
    ref_id = None
    chunks = re.findall(r'self\.__next_f\.push\((.*?)\)</script>', text)
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                chunk_str = data[1]
                # Look for the post ID in the chunk string
                if post_id in chunk_str:
                    # Look for "id":"POST_ID" or similar
                    # Then find the "url" property right after
                    idx = chunk_str.find(post_id)
                    sub = chunk_str[max(0, idx-50) : min(len(chunk_str), idx+1500)]
                    
                    # Regex to find "url":"$REF_ID"
                    # It might be "url":"$73" or \"url\":\"$73\"
                    url_match = re.search(r'\\?"url\\?":\\?"\$([^"\$\\]+)\\?"', sub)
                    if url_match:
                        ref_id = url_match.group(1)
                        break
        except Exception as e:
            pass

    if not ref_id:
        print(f'Could not find reference ID for {post_id}')
        return None
        
    print(f'Found ref_id: {ref_id} for {post_id}')
    
    # 3. Find the URL for this ref_id in all chunks
    video_url = None
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
                chunk_str = data[1]
                # Look for ref_id definition
                # It usually looks like `73:Txxx,https...` or `73:"https...`
                # So we can search for `{ref_id}:` or `"{ref_id}":`
                if f'{ref_id}:' in chunk_str or f'"{ref_id}":' in chunk_str:
                    # Extract the mp4 URL near it
                    idx = chunk_str.find(f'{ref_id}:')
                    if idx == -1: idx = chunk_str.find(f'"{ref_id}":')
                    sub = chunk_str[idx : min(len(chunk_str), idx+2000)]
                    
                    # find the first https://...mp4 in sub
                    mp4_match = re.search(r'(https?://[^"\\]+\.mp4[^"\\]*)', sub)
                    if mp4_match:
                        video_url = mp4_match.group(1)
                        video_url = video_url.replace(r'\u0026', '&')
                        if video_url.endswith('\\'): video_url = video_url[:-1]
                        break
        except Exception as e:
            pass

    return video_url

print('1:', extract_exact('https://www.meta.ai/@washt/post/sE8ZfW85d1A/fun-times?utm_source=meta_ai_web_copy_video_link'))
print('2:', extract_exact('https://www.meta.ai/@ralphmaddad518/post/Uu5EESQK5jQ?utm_source=meta_ai_web_copy_video_link'))
