"""
Core UX flow smoke test: dashboard -> practice mode -> full test mode -> submit
-> results -> history, for both Reading and Listening. Exercises TFNG,
matching-headings, short-answer, matching-information, table-completion,
the exit-confirm-in-test-mode guard, the timer chip, and the listening
audio player's TTS-fallback play button.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_core_flows.py

Practice/full-test item counts are derived from however many test groups
currently exist rather than hardcoded, so this doesn't go stale as content
is added — see tests/audit_answer_keys.py for an exhaustive per-testGroup
correctness check.
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

    step[0] = "load dashboard"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(600)
    print("dashboard title:", page.title())
    assert page.query_selector(".skill-grid"), "skill grid missing"

    step[0] = "open reading hub"
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    assert page.query_selector(".content-list"), "reading content list missing"
    tg_rows = page.query_selector_all("[data-testgroup]")
    rows = page.query_selector_all("#contentList .content-row")
    print(f"reading test groups: {len(tg_rows)}, passages listed: {len(rows)}")
    assert len(tg_rows) >= 1, "expected at least one reading test group"
    assert len(rows) == len(tg_rows) * 3, f"expected {len(tg_rows)*3} practice passages, got {len(rows)}"

    step[0] = "start reading practice passage 1 (reading-passage-001, stable content)"
    rows[0].click()
    page.wait_for_timeout(400)
    assert page.query_selector(".pane-passage"), "passage pane missing"
    assert page.query_selector(".pane-questions"), "questions pane missing"
    palette_cells = page.query_selector_all(".palette-cell")
    print("palette cells (passage 1 practice):", len(palette_cells))
    assert len(palette_cells) == 13, f"expected 13, got {len(palette_cells)}"

    step[0] = "answer TFNG question 1"
    tfng_btns = page.query_selector_all('#q1 .tfng-btn')
    assert len(tfng_btns) == 3
    tfng_btns[0].click()  # TRUE
    page.wait_for_timeout(150)

    step[0] = "answer matching-heading select q6"
    sel = page.query_selector('select[data-qnum="6"]')
    assert sel, "matching-headings select for q6 missing"
    sel.select_option(index=1)
    page.wait_for_timeout(150)

    step[0] = "answer short-answer q10"
    inp = page.query_selector('input[data-qnum="10"]')
    assert inp, "short-answer input q10 missing"
    inp.fill("fourteen")
    page.wait_for_timeout(150)

    step[0] = "check palette answered states"
    answered = page.query_selector_all(".palette-cell.answered")
    print("answered cells after 3 answers:", len(answered))
    assert len(answered) == 3, f"expected 3 answered, got {len(answered)}"

    step[0] = "exit practice via exit button"
    page.click("#exitBtn")
    page.wait_for_timeout(300)
    assert page.query_selector(".content-list"), "did not return to hub"

    step[0] = "start full reading test (test group 1)"
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(200)
    tg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    tg1.click()
    page.wait_for_timeout(500)
    timer_chip = page.query_selector("#timerChip")
    assert timer_chip and "hidden" not in timer_chip.get_attribute("class"), "timer chip should be visible in test mode"
    all_cells = page.query_selector_all(".palette-cell")
    print("palette cells (full reading test):", len(all_cells))
    assert len(all_cells) == 40, f"expected 40, got {len(all_cells)}"

    step[0] = "click exit during test -> confirm modal should appear, not leave immediately"
    page.click("#exitBtn")
    page.wait_for_timeout(200)
    backdrop = page.query_selector("#exitConfirmBackdrop")
    assert backdrop and "hidden" not in backdrop.get_attribute("class"), "exit confirm modal did not show in test mode"
    assert page.query_selector(".test-shell"), "should still be in test shell while modal is up"

    step[0] = "cancel exit -> stay in test"
    page.click("#exitConfirmCancel")
    page.wait_for_timeout(200)
    assert page.query_selector(".test-shell"), "should still be in test after cancel"

    step[0] = "jump to passage 3 via palette (q37)"
    cell37 = page.query_selector('.palette-cell[data-qnum="37"]')
    assert cell37, "q37 palette cell missing"
    cell37.click()
    page.wait_for_timeout(400)
    assert page.query_selector('#q37'), "q37 not rendered after jump"

    step[0] = "answer a matching-information select on passage 3"
    sel37 = page.query_selector('select[data-qnum="37"]')
    assert sel37, "matching-information select q37 missing"
    sel37.select_option(label="C")
    page.wait_for_timeout(150)

    step[0] = "answer table-completion blank q33"
    tblinp = page.query_selector('input[data-qnum="33"]')
    assert tblinp, "table completion input q33 missing"
    tblinp.fill("evapotranspiration")
    page.wait_for_timeout(150)

    step[0] = "submit test (confirm modal)"
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    assert page.query_selector("#submitConfirmBackdrop"), "confirm modal missing"
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)

    step[0] = "check results screen"
    assert page.query_selector(".results-hero"), "results hero missing"
    band_text = page.query_selector(".results-band .num").inner_text()
    print("band score shown:", band_text)
    review_items = page.query_selector_all(".review-item")
    print("review items:", len(review_items))
    assert len(review_items) == 40

    step[0] = "back to dashboard, check history recorded"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    history_rows = page.query_selector_all(".history-row")
    print("history rows on dashboard:", len(history_rows))
    assert len(history_rows) >= 1

    # ---------------- Listening ----------------
    step[0] = "open listening hub"
    page.click('[data-nav="listening"]')
    page.wait_for_timeout(300)
    ltg_rows = page.query_selector_all("[data-testgroup]")
    lrows = page.query_selector_all("#contentList .content-row")
    print(f"listening test groups: {len(ltg_rows)}, sections listed: {len(lrows)}")
    assert len(ltg_rows) >= 1
    assert len(lrows) == len(ltg_rows) * 4, f"expected {len(ltg_rows)*4}, got {len(lrows)}"

    step[0] = "start listening practice section 1"
    lrows[0].click()
    page.wait_for_timeout(400)
    assert page.query_selector(".audio-player"), "audio player missing"
    lpalette = page.query_selector_all(".palette-cell")
    print("palette cells (listening section 1 practice):", len(lpalette))
    assert len(lpalette) == 10

    step[0] = "answer sentence-completion listening q1"
    linp = page.query_selector('input[data-qnum="1"]')
    assert linp, "listening q1 input missing"
    linp.fill("Daniel")
    page.wait_for_timeout(150)
    lanswered = page.query_selector_all(".palette-cell.answered")
    assert len(lanswered) == 1

    step[0] = "click play button (TTS fallback path, should not throw)"
    play_btn = page.query_selector("#apPlayBtn")
    assert play_btn
    play_btn.click()
    page.wait_for_timeout(800)
    play_btn.click()  # pause/cancel immediately to avoid long real TTS wait in headless chromium
    page.wait_for_timeout(300)

    step[0] = "exit listening practice"
    page.click("#exitBtn")
    page.wait_for_timeout(300)
    assert page.query_selector(".content-list")

    step[0] = "start full listening test, verify 40 questions across 4 sections"
    ltg1 = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == "1"][0]
    ltg1.click()
    page.wait_for_timeout(500)
    lfullpalette = page.query_selector_all(".palette-cell")
    print("palette cells (full listening test):", len(lfullpalette))
    assert len(lfullpalette) == 40, f"expected 40, got {len(lfullpalette)}"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
