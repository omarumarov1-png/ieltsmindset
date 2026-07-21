"""
Checks that dashboard history rows identify *which* test/practice item was
attempted (not just skill + mode), and show the Academic/General Training
module tag for reading attempts. With 5 reading and 4 listening test sets
now live, a history list that only said "Reading - Test mode - Band 7.5"
gave no way to tell which of the 5 reading tests that was.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_history_labels.py
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

    step[0] = "complete a practice passage (single item, should show its title)"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")
    rows[0].click()
    page.wait_for_timeout(400)
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)

    history_rows = page.query_selector_all(".history-row")
    assert len(history_rows) >= 1, "expected at least one history row"
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    print("history row after practice attempt:", latest_title)
    assert "Return of the Wolves" in latest_title or len(latest_title) > len("Чтение · Режим практики"), \
        f"practice history row should include the passage title, got: {latest_title!r}"

    step[0] = "complete a full General Training reading test (testGroup 5), check module tag"
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    tg5 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "5"][0]
    tg5.click()
    page.wait_for_timeout(600)
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)

    history_rows = page.query_selector_all(".history-row")
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    print("history row after GT full test attempt:", latest_title)
    assert "5" in latest_title, f"history row should reference test group 5, got: {latest_title!r}"
    assert "GENERAL TRAINING" in latest_title.upper(), \
        f"history row for a GT attempt should show the General Training tag, got: {latest_title!r}"

    step[0] = "complete a full Academic reading test (testGroup 1), check Academic tag"
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    tg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    tg1.click()
    page.wait_for_timeout(600)
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)

    history_rows = page.query_selector_all(".history-row")
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    print("history row after Academic full test attempt:", latest_title)
    assert "ACADEMIC" in latest_title.upper() and "GENERAL" not in latest_title.upper(), \
        f"history row for an Academic attempt should show the Academic tag only, got: {latest_title!r}"

    step[0] = "listening history rows should not show a module tag (listening has no GT/Academic split)"
    page.click('[data-nav="listening"]')
    page.wait_for_timeout(300)
    ltg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    ltg1.click()
    page.wait_for_timeout(600)
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)

    history_rows = page.query_selector_all(".history-row")
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    print("history row after listening full test attempt:", latest_title)
    assert "ACADEMIC" not in latest_title.upper() and "GENERAL" not in latest_title.upper(), \
        f"listening history rows should never show a module tag, got: {latest_title!r}"
    assert "1" in latest_title, f"history row should reference test group 1, got: {latest_title!r}"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
