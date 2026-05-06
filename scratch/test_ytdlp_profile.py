import yt_dlp
ydl_opts = {'quiet': True, 'extract_flat': True}
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info('https://www.meta.ai/@washt', download=False)
        if 'entries' in info:
            print(f"Found {len(info['entries'])} entries")
            for entry in info['entries'][:3]:
                print(f"Entry: {entry.get('url') or entry.get('id')}")
        else:
            print("No entries found")
except Exception as e:
    print(f"Error: {e}")
