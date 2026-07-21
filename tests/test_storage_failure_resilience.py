"""
Regression check for a real robustness gap found by code inspection:
loadProgress() had a try/catch for corrupted localStorage JSON, but
saveProgress() had none. localStorage.setItem can genuinely throw --
private browsing mode in Safari, quota exceeded, storage blocked by an
extension or browser policy -- and that call happens synchronously inside
recordResult(), which runs right when a user finishes a full timed test,
immediately before the results screen renders. An uncaught exception there
would have broken the results screen entirely, silently losing the results
of a just-completed exam with no error message.

This test overrides localStorage.setItem to always throw, then completes a
full test and confirms the results screen still renders successfully (and
without an uncaught JS error) despite persistence failing.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_storage_failure_resilience.py
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

    # Simulate a browser environment where localStorage writes fail (private
    # browsing / quota exceeded / blocked), while reads still work normally
    # (getItem is untouched, matching how these failures actually behave).
    page.add_init_script("""
        Storage.prototype.setItem = function() {
            throw new DOMException('Simulated storage failure', 'QuotaExceededError');
        };
    """)

    step[0] = "complete a full reading test with localStorage.setItem always throwing"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    tg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    tg1.click()
    page.wait_for_timeout(500)

    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)

    step[0] = "confirm the results screen still rendered despite the storage failure"
    results_hero = page.query_selector(".results-hero")
    print("results hero rendered:", results_hero is not None)
    assert results_hero, "results screen failed to render when localStorage.setItem threw"
    review_items = page.query_selector_all(".review-item")
    print("review items rendered:", len(review_items))
    assert len(review_items) == 40, f"expected 40 review items, got {len(review_items)}"

    step[0] = "confirm returning to the dashboard also doesn't crash"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    assert page.query_selector(".skill-grid"), "dashboard failed to render after a storage failure"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
