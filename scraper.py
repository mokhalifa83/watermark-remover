import re
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None
import time
import os

def extract_video_url(share_url: str) -> str:
    """
    Extracts the direct video URL from a Meta AI share link.
    Combines Playwright network interception with DOM inspection.
    """
    
    if '/post/' not in share_url and '@' in share_url and 'post' not in share_url.lower():
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not a profile page)."
        )

    video_url = None

    with sync_playwright() as p:
        print(f"[Scraper] Starting Playwright for: {share_url}")
        # Memory-optimized launch
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        if stealth_sync:
            stealth_sync(page)

        # Track all potential video URLs
        captured_urls = []

        def handle_request(request):
            nonlocal video_url
            url = request.url
            # Log for debugging in Render
            if "fbcdn.net" in url and (".mp4" in url or "efg=" in url):
                captured_urls.append(url)
                if "progressive" in url:
                    video_url = url

        page.on("request", handle_request)

        try:
            page.goto(share_url, wait_until="domcontentloaded", timeout=45000)
            
            # 1. Immediate DOM check for <video> tags
            time.sleep(3)
            video_tags = page.query_selector_all("video")
            for tag in video_tags:
                src = tag.get_attribute("src")
                if src and src.startswith("http") and "fbcdn.net" in src:
                    print(f"[Scraper] Found video src in DOM: {src[:60]}...")
                    video_url = src
                    break

            if not video_url:
                # 2. Interaction to trigger load
                print("[Scraper] No video yet, attempting interaction...")
                page.mouse.click(640, 360)
                time.sleep(5)
                
                # Check captured URLs from network
                if captured_urls and not video_url:
                    # Pick the best one (usually the last or largest)
                    video_url = captured_urls[-1]

            # 3. Final wait if still nothing
            start_time = time.time()
            while not video_url and time.time() - start_time < 10:
                time.sleep(1)

        except Exception as e:
            print(f"[Scraper] Playwright error: {e}")
        finally:
            browser.close()

    if not video_url and captured_urls:
        video_url = captured_urls[0]

    if not video_url:
        # Fallback to a simple regex check on the page source if Playwright failed to intercept
        # (Sometimes helpful if network idle happens too late)
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Meta AI may be blocking the request or the video link has expired."
        )

    return video_url
