from scraper_v2 import extract_video_url
import sys

# Test URL from the screenshot
test_url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"

print("=" * 80)
print(f"Testing Meta AI Video Extraction")
print(f"URL: {test_url}")
print("=" * 80)

try:
    video_url = extract_video_url(test_url)
    print("\n" + "=" * 80)
    print("SUCCESS!")
    print(f"Extracted Video URL: {video_url}")
    print("=" * 80)
except Exception as e:
    print("\n" + "=" * 80)
    print("FAILED!")
    print(f"Error: {str(e)}")
    print("=" * 80)
    sys.exit(1)
