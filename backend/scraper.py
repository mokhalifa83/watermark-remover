import re
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

def extract_video_url(share_url: str) -> str:
    """
    Extracts the direct video URL from a Meta AI share link using a stealthy headless browser.
    """
    
    # 1. Validation: Ensure it's not a profile page
    if '/post/' not in share_url and '@' in share_url and 'post' not in share_url.lower():
         raise Exception(
            "Could not find a video in this Meta AI link. "
            "Make sure it is a direct video post URL (not a profile page)."
        )

    video_url = None

    with sync_playwright() as p:
        # Launch browser with stealth
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        stealth_sync(page)

        def handle_request(request):
            nonlocal video_url
            url = request.url
            if (".mp4" in url or "fbcdn.net" in url) and ("_nc_cat" in url or "efg=" in url or "bytestart=" in url):
                if not video_url or "progressive" in url:
                    video_url = url

        page.on("request", handle_request)

        try:
            print(f"[Playwright] Stealth navigating to: {share_url}")
            page.goto(share_url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            try:
                page.mouse.click(960, 540)
                time.sleep(2)
                page.mouse.wheel(0, 500)
                time.sleep(2)
            except:
                pass
            
            start_time = time.time()
            while not video_url and time.time() - start_time < 20:
                time.sleep(1)

        except Exception as e:
            print(f"[Playwright] Error: {e}")
        finally:
            browser.close()

    if not video_url:
        raise Exception(
            "Could not find a video in this Meta AI link. "
            "Meta AI may be blocking the request or the video link has expired."
        )

    return video_url
