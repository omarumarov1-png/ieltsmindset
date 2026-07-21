"""
Regression check for a real bug found via visual QA: the mobile stylesheet
used to set `.topnav { display: none; }` below 860px, hiding the Reading/
Listening nav links entirely with no replacement -- users could only switch
skills by first returning to the dashboard. Fixed by wrapping the topbar to
two rows on narrow viewports instead. This test fails loudly if that
regresses back to a hidden, unusable nav.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_mobile_nav.py
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8935"
errors = []
step = ["boot"]

def on_console(msg):
    if msg.type == "error":
        errors.append(f"[console @ {step[0]}] {msg.text}")

def on_pageerror(exc):
    errors.append(f"[pageerror @ {step[0]}] {exc}")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    step[0] = "load dashboard at mobile width"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)

    step[0] = "topnav must be visible and clickable, not hidden"
    reading_link = page.query_selector('[data-nav="reading"]')
    assert reading_link, "reading nav link missing from DOM"
    assert reading_link.is_visible(), "reading nav link exists but is not visible on mobile"

    step[0] = "click into reading hub via topnav"
    reading_link.click()
    page.wait_for_timeout(400)
    assert page.query_selector(".content-list"), "did not navigate to reading hub"

    step[0] = "switch to listening via topnav from inside a hub screen (no dashboard round-trip)"
    listening_link = page.query_selector('[data-nav="listening"]')
    assert listening_link.is_visible(), "listening nav link not visible on mobile"
    listening_link.click()
    page.wait_for_timeout(400)
    rows = page.query_selector_all("#contentList .content-row")
    assert len(rows) > 0, "did not land on listening hub content after nav switch"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
