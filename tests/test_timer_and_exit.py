"""
Timer countdown and exit-confirm-then-leave flow for a full (timed) test.
test_core_flows.py already covers exit-confirm-then-cancel; this covers the
complementary "confirm leave" path and checks the timer is actually ticking
down and hides again once you leave the test shell.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_timer_and_exit.py
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
    page = browser.new_page()
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    step[0] = "start full reading test"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(200)
    tg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    tg1.click()
    page.wait_for_timeout(500)

    step[0] = "confirm timer is counting down"
    t1 = page.inner_text("#timerText")
    page.wait_for_timeout(2100)
    t2 = page.inner_text("#timerText")
    print("timer readings:", t1, "->", t2)
    assert t1 != t2, "timer does not appear to be counting down"

    step[0] = "leave via exit-confirm-leave button"
    page.click("#exitBtn")
    page.wait_for_timeout(200)
    page.click("#exitConfirmLeave")
    page.wait_for_timeout(300)
    assert page.query_selector(".skill-grid"), "should be back on dashboard after confirmed exit"
    timer_chip = page.query_selector("#timerChip")
    assert "hidden" in timer_chip.get_attribute("class"), "timer chip should hide after leaving test"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
