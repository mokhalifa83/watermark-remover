import re
with open('meta_page2.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.finditer(r'"73":"(https://[^"]+)"', text)
for m in matches:
    print(m.group(1))

matches2 = re.finditer(r'73:\["([^"]+)"', text)
for m in matches2:
    print(m.group(1))
