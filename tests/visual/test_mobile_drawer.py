from pathlib import Path
from playwright.sync_api import sync_playwright

def test_drawer():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto("http://127.0.0.1:8000/setup/?role=admin", wait_until="networkidle")
        
        # Click hamburger menu
        page.click('button[aria-label="Open sidebar"]')
        page.wait_for_timeout(400) # wait for CSS transition
        
        screenshot_path = Path("tests/visual/screenshots/mobile_drawer_open.png")
        page.screenshot(path=str(screenshot_path))
        print(f"[+] Saved drawer open screenshot: {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    test_drawer()
