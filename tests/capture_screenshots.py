import os
from playwright.sync_api import sync_playwright

output_dir = "/home/george/Desktop/Dev2026/Jimcan/tests/visual/screenshots"
os.makedirs(output_dir, exist_ok=True)

viewports = [
    ("desktop_1440", 1440, 900),
    ("tablet_1024", 1024, 768),
    ("mobile_390", 390, 844),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, width, height in viewports:
        context = browser.new_context(viewport={"width": width, "height": height})
        page = context.new_page()
        
        # Navigate to overview with admin role
        page.goto("http://127.0.0.1:8001/overview/?role=admin", wait_until="domcontentloaded")
        page.wait_for_timeout(2000) # wait for count-up/transitions
        
        # Capture screenshot
        shot_path = os.path.join(output_dir, f"{name}.png")
        page.screenshot(path=shot_path, full_page=True)
        print(f"Captured {shot_path}")
        
        # Evaluate QA checks in page
        eval_result = page.evaluate('''() => {
            const checks = {};
            // 1. Horizontal scroll
            checks.hasHorizontalScroll = document.documentElement.scrollWidth > window.innerWidth;
            checks.scrollWidth = document.documentElement.scrollWidth;
            checks.innerWidth = window.innerWidth;

            // 2. Sidebar toggles count
            const toggles = document.querySelectorAll('#sidebar-toggle, .sidebar-toggle-btn');
            checks.toggleCount = toggles.length;

            // 3. Box-shadow checks (only .create-menu is allowed box-shadow)
            const allElements = document.querySelectorAll('*');
            const elementsWithShadow = [];
            for (const el of allElements) {
                const cs = window.getComputedStyle(el);
                if (cs.boxShadow && cs.boxShadow !== 'none' && !el.closest('.create-menu')) {
                    elementsWithShadow.push(el.tagName + '.' + el.className);
                }
            }
            checks.unauthorizedShadows = elementsWithShadow;

            // 4. Uppercase text-transform check
            const uppercaseElements = [];
            for (const el of allElements) {
                const cs = window.getComputedStyle(el);
                if (cs.textTransform === 'uppercase' && el.textContent.trim().length > 0) {
                    uppercaseElements.push(el.tagName + '.' + el.className + ': ' + el.textContent.trim().substring(0, 30));
                }
            }
            checks.uppercaseElements = uppercaseElements;

            // 5. Baselines in the three stats
            const statBlocks = document.querySelectorAll('.stat-block');
            checks.statBlocksCount = statBlocks.length;
            if (statBlocks.length === 3) {
                const offsets = Array.from(statBlocks).map(sb => {
                    const fig = sb.querySelector('.type-stat-figure');
                    return fig ? fig.getBoundingClientRect().left : null;
                });
                checks.statFigureLeftOffsets = offsets;
            }

            // 6. Committed cost label clipping
            const committedLabel = document.querySelector('.committed-label');
            if (committedLabel) {
                const rect = committedLabel.getBoundingClientRect();
                checks.committedLabelClipped = rect.left < 0 || rect.right > window.innerWidth;
                checks.committedLabelRect = { left: rect.left, right: rect.right };
            }

            return checks;
        }''')
        print(f"Results for {name}:", eval_result)
        context.close()
    browser.close()
