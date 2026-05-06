import re
import json

with open('meta_debug.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all self.__next_f.push calls
chunks = re.findall(r'self\.__next_f\.push\((.*?)\)', text)
parsed_chunks = []
for chunk in chunks:
    try:
        data = json.loads(chunk)
        if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
            parsed_chunks.append(data[1])
    except:
        pass

# Search for the post ID and the video URL in the chunks
post_id = 'sE8ZfW85d1A'
for i, chunk in enumerate(parsed_chunks):
    if post_id in chunk:
        print(f"--- Chunk {i} contains post_id ---")
        # Print a bit of context around the post_id
        idx = chunk.find(post_id)
        print(chunk[max(0, idx-100):idx+500])

# Find all mp4 URLs and their reference IDs
for i, chunk in enumerate(parsed_chunks):
    matches = re.finditer(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', chunk)
    for m in matches:
        print(f"--- Found mp4 in Chunk {i} ---")
        url = m.group(1)
        # Look for ref_id near the URL
        start = max(0, m.start() - 50)
        context = chunk[start:m.start()]
        print(f"Context: {context}")
        print(f"URL: {url[:100]}...")
