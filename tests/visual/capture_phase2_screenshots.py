#!/usr/bin/env python3
"""
Jimcan Operations Dashboard - Phase 2 Visual Regression Capture
Captures desktop (1440px) and mobile (390px) screenshots of:
1. S-00 Sign In (/login/)
2. S-01 Password Reset (/password_reset/)
3. S-95 Admin Setup Checklist (/setup/?role=admin)
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    {"name": "login", "url": "http://127.0.0.1:8000/login/"},
    {"name": "password_reset", "url": "http://127.0.0.1:8000/password_reset/"},
    {"name": "setup_checklist", "url": "http://127.0.0.1:8000/setup/?role=admin"},
]

def capture_all():
    print("[*] Launching Playwright Chromium headless driver...")
    with sync_playwright() as p:
        browser = p.chromium.launch()

        for target in TARGETS:
            name = target["name"]
            url = target["url"]
            print(f"[*] Navigating to {name}: {url}")

            # 1. Desktop Viewport (1440 x 900 px)
            desktop_context = browser.new_context(viewport={"width": 1440, "height": 900})
            desktop_page = desktop_context.new_page()
            desktop_page.goto(url, wait_until="networkidle")
            desktop_file = SCREENSHOTS_DIR / f"{name}_desktop_1440px.png"
            desktop_page.screenshot(path=str(desktop_file), full_page=True)
            print(f"  [+] Saved: {desktop_file}")
            desktop_context.close()

            # 2. Mobile Viewport (390 x 844 px)
            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
            )
            mobile_page = mobile_context.new_page()
            mobile_page.goto(url, wait_until="networkidle")
            mobile_file = SCREENSHOTS_DIR / f"{name}_mobile_390px.png"
            mobile_page.screenshot(path=str(mobile_file), full_page=True)
            print(f"  [+] Saved: {mobile_file}")
            mobile_context.close()

        browser.close()
    print("[*] All Phase 2 visual screenshots captured successfully!")

if __name__ == "__main__":
    capture_all()
