import re, json
with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Allow optional backslashes before quotes
pattern = r'\\?"id\\?":\\?"Uu5EESQK5jQ\\?".*?\\?"url\\?":\\?"\$([^"\$]+)\\?"'
match = re.search(pattern, text)
if match:
    ref_id = match.group(1)
    print('Found Reference ID:', ref_id)
    
    url_pattern = r'\\?"' + ref_id + r'\\?":\\?"(https://[^"]+\.mp4[^"\\]*)\\?"'
    url_match = re.search(url_pattern, text)
    if url_match:
        print('Found Video URL via Quotes:', url_match.group(1))
    else:
        url_pattern = ref_id + r':\\?"(https://[^"]+\.mp4[^"\\]*)\\?"'
        url_match = re.search(url_pattern, text)
        if url_match:
            print('Found Video URL without Quotes:', url_match.group(1))
        else:
            print('URL not found for reference ID')
            
            idx = text.find(f'\\"{ref_id}\\":')
            if idx != -1:
                print(text[idx-50:idx+150])
else:
    print('Pattern not found')
