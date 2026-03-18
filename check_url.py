import requests
from scraper import extract_video_url
import sys

def check_url(url):
    print(f"Testing URL: {url}")
    try:
        video_url = extract_video_url(url)
        print(f"\nExtracted URL: {video_url}")
        
        # Check headers
        try:
            head = requests.head(video_url, allow_redirects=True, timeout=5)
            print(f"Status Code: {head.status_code}")
            print(f"Content-Type: {head.headers.get('Content-Type')}")
            print(f"Content-Length: {head.headers.get('Content-Length')}")
            
            size_mb = int(head.headers.get('Content-Length', 0)) / (1024 * 1024)
            print(f"Size: {size_mb:.2f} MB")
            
            if size_mb < 1.0:
                 print("WARNING: Video is very small (< 1MB). Likely a placeholder.")
            else:
                 print("Video seems substantial.")
                 
        except Exception as e:
            print(f"Could not fetch headers: {e}")

    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    test_url = "https://www.meta.ai/@tonz1959/post/OY6KfFbJ9iU/"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    check_url(test_url)
