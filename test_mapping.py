import re

with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'\\?"id\\?":\\?"Uu5EESQK5jQ\\?".*?\\?"url\\?":\\?"\$([^"\$]+)\\?"', text)
if match:
    ref_id = match.group(1)
    print('Ref ID is:', ref_id)
    
    # Next.js format is usually 73:"url" or 73:["$","video","url"...]
    # Let's search for the actual definition of ref_id.
    # It might be in the same line or script block.
    # We will find the script block where this ref_id is mapped to a URL.
    
    blocks = re.findall(r'<script[^>]*>(.*?)</script>', text, re.DOTALL)
    for b in blocks:
        if f'"{ref_id}":' in b or f'{ref_id}:' in b:
            # Print surrounding chars
            idx = b.find(f'"{ref_id}":')
            if idx == -1: idx = b.find(f'{ref_id}:')
            print("Found definition in block:", b[max(0, idx-100) : idx+200])
