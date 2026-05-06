import re
from playwright.sync_api import sync_playwright
import time

def extract_video_url(share_url: str) -> str:
    """
    Extracts the direct video URL from a Meta AI share link using a headless browser (Playwright).
    This intercepts network requests to find the direct CDN link.
    """
    
    # 1. Validation: Ensure it's not a profile page
    if '/post/' not in share_url:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not a profile page)."
        )

    video_url = None

    with sync_playwright() as p:
        # Launch browser with a realistic User-Agent
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Listen for network requests
        def handle_request(request):
            nonlocal video_url
            url = request.url
            if (".mp4" in url or "fbcdn.net" in url) and ("efg=" in url or "bytestart=" in url):
                if not video_url or "progressive" in url:
                    video_url = url

        page.on("request", handle_request)

        try:
            print(f"[Playwright] Navigating to: {share_url}")
            page.goto(share_url, wait_until="networkidle", timeout=60000)
            
            start_time = time.time()
            while not video_url and time.time() - start_time < 15:
                time.sleep(0.5)

        except Exception as e:
            print(f"[Playwright] Error during extraction: {e}")
        finally:
            browser.close()

    if not video_url:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "The link might have expired, or Meta AI is blocking headless browsers."
        )

    return video_url
