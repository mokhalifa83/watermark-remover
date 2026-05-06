import json, re

with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.finditer(r'self\.__next_f\.push\((.*?)\)', text)
for m in matches:
    try:
        data = json.loads(m.group(1))
        if isinstance(data, list) and len(data) == 2 and isinstance(data[1], str):
            chunk_str = data[1]
            if '73:' in chunk_str or '"73":' in chunk_str:
                print('Found in chunk!')
                idx = chunk_str.find('73:')
                if idx == -1: idx = chunk_str.find('"73":')
                print(chunk_str[max(0, idx-50) : min(len(chunk_str), idx+300)])
    except:
        pass
