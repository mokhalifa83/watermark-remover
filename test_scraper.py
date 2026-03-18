from scraper import extract_video_url
import sys

url = 'https://www.meta.ai/@kasey.duney/post/oN6J5K1br8a/remix-of-pizzaslime?utm_source=meta_ai_web_copy_video_link'

try:
    print("Testing extraction...")
    video = extract_video_url(url)
    print("Extracted video URL:")
    print(video)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
