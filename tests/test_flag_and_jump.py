"""
Regression check for two related bugs found by code inspection:

1. The "flag this question" button always flagged whichever question was
   *first in the DOM*, regardless of which question the user had actually
   scrolled to and was looking at. In a long passage this silently flagged
   the wrong question every time the user wasn't at the very top of the
   list. Fixed by picking the question actually visible in the viewport.

2. Jumping to a question via the palette added a `flagged-flash` CSS class
   that had no matching stylesheet rule anywhere and was never removed --
   a highlight effect that silently did nothing. Renamed to `jump-flash`
   and gave it an actual (self-cleaning) animation, reused for both the
   palette-jump highlight and the flag action's own feedback.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_flag_and_jump.py
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

    def flagged_qnums():
        return set(page.evaluate(
            "() => Array.from(document.querySelectorAll('.palette-cell.flagged')).map(el => el.dataset.qnum)"
        ))

    assert page.query_selector("#flagCurrentBtn"), "flag button missing"

    step[0] = "at the top of the passage, flag the current question -> should be q1"
    page.click("#flagCurrentBtn")
    page.wait_for_timeout(200)
    flagged_at_top = flagged_qnums()
    print("flagged while scrolled to top:", flagged_at_top)
    assert flagged_at_top == {"1"}, f"expected only q1 flagged at the top of the passage, got {flagged_at_top}"
    page.click("#flagCurrentBtn")  # unflag it again
    page.wait_for_timeout(200)
    assert flagged_qnums() == set(), "expected q1 to be unflagged after toggling again"

    step[0] = "scroll to the last question of the passage, flag the current question"
    q13 = page.query_selector("#q13")
    assert q13, "q13 missing"
    q13.evaluate("el => el.scrollIntoView({block: 'end'})")
    page.wait_for_timeout(200)
    page.click("#flagCurrentBtn")
    page.wait_for_timeout(200)
    flagged_at_bottom = flagged_qnums()
    print("flagged while scrolled to the last question:", flagged_at_bottom)
    assert flagged_at_bottom, "expected some question to be flagged after scrolling down"
    assert flagged_at_bottom != {"1"}, \
        "flag button should track scroll position, but it flagged q1 again after scrolling to the bottom"
    assert flagged_at_bottom != flagged_at_top, \
        "flagging after scrolling down should target a different question than flagging at the top"

    step[0] = "click flag again on the same scroll position -> should unflag it"
    page.click("#flagCurrentBtn")
    page.wait_for_timeout(200)
    assert flagged_qnums() == set(), "expected the flag to be removed after toggling again"

    step[0] = "jump to q30 via palette, confirm the jump-flash class is applied then removed"
    cell30 = page.query_selector('.palette-cell[data-qnum="30"]')
    assert cell30, "q30 palette cell missing"
    cell30.click()
    page.wait_for_timeout(150)
    q30 = page.query_selector("#q30")
    assert q30, "q30 not rendered after jump"
    has_flash_immediately = "jump-flash" in (q30.get_attribute("class") or "")
    print("jump-flash present right after jump:", has_flash_immediately)
    assert has_flash_immediately, "expected jump-flash class to be applied immediately after a palette jump"

    page.wait_for_timeout(1100)
    has_flash_later = "jump-flash" in (page.query_selector("#q30").get_attribute("class") or "")
    print("jump-flash present ~1.1s later:", has_flash_later)
    assert not has_flash_later, "expected jump-flash class to have been removed after the animation finished"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
