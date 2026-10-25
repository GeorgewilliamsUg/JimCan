#!/usr/bin/env python3
"""
Jimcan Operations Dashboard - Visual Regression Screenshot Capture
Captures high-fidelity baseline screenshots at 390px (mobile) and 1440px (desktop).
Conforms to Project Plan v0.2 Section 6 (Review Criteria) and TRD Section 13.
"""

import os
import sys
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_URL = os.environ.get("TARGET_URL", "http://127.0.0.1:8000/styleguide/")

def capture():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright is not installed in the active environment.")
        print("    Install via: pip install playwright && playwright install chromium")
        sys.exit(0)

    print(f"[*] Capturing visual regression baselines from: {TARGET_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # 1. Mobile Phone Viewport (390 x 844 px)
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
        )
        mobile_page = mobile_context.new_page()
        try:
            mobile_page.goto(TARGET_URL, wait_until="networkidle")
            mobile_path = SCREENSHOTS_DIR / "styleguide_mobile_390px.png"
            mobile_page.screenshot(path=str(mobile_path), full_page=True)
            print(f"[+] Saved mobile baseline: {mobile_path}")
        except Exception as e:
            print(f"[-] Could not capture mobile view: {e}")

        # 2. Desktop Viewport (1440 x 900 px)
        desktop_context = browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        desktop_page = desktop_context.new_page()
        try:
            desktop_page.goto(TARGET_URL, wait_until="networkidle")
            desktop_path = SCREENSHOTS_DIR / "styleguide_desktop_1440px.png"
            desktop_page.screenshot(path=str(desktop_path), full_page=True)
            print(f"[+] Saved desktop baseline: {desktop_path}")
        except Exception as e:
            print(f"[-] Could not capture desktop view: {e}")

        browser.close()
    print("[*] Visual regression capture finished.")

if __name__ == "__main__":
    capture()
