"""
Question-type rendering checks not covered by test_core_flows.py: multiple-
choice option selection styling, YNNG button labels/values, and the option
count on a matching-information dropdown (placeholder + A-F).

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_question_types.py
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

    step[0] = "load and go to reading hub"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")

    step[0] = "open passage 2 (multiple-choice + summary-completion)"
    rows[1].click()
    page.wait_for_timeout(400)

    step[0] = "answer MC q14 (reading, radio)"
    opt = page.query_selector('#q14 .opt-choice[data-optidx="2"] input')
    assert opt, "q14 option C missing"
    opt.check()
    page.wait_for_timeout(150)
    sel_class = page.query_selector('#q14 .opt-choice[data-optidx="2"]').get_attribute("class")
    assert "selected" in sel_class, f"q14 option not marked selected: {sel_class}"

    step[0] = "answer summary-completion blanks q23-27"
    for n in [23, 24, 25, 26, 27]:
        inp = page.query_selector(f'input[data-qnum="{n}"]')
        assert inp, f"summary completion input q{n} missing"
        inp.fill("test")
    page.wait_for_timeout(200)
    answered = page.query_selector_all(".palette-cell.answered")
    print("passage 2 answered count (1 MC + 5 summary):", len(answered))
    assert len(answered) == 6, f"expected 6, got {len(answered)}"

    step[0] = "exit to hub"
    page.click("#exitBtn")
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")

    step[0] = "open passage 3 (yes-no-not-given + table-completion + matching-information)"
    rows[2].click()
    page.wait_for_timeout(400)

    step[0] = "answer YNNG q28"
    ynng_btns = page.query_selector_all('#q28 .tfng-btn')
    assert len(ynng_btns) == 3, f"expected 3 YNNG buttons, got {len(ynng_btns)}"
    print("YNNG button labels:", [b.inner_text().replace(chr(10), ' | ') for b in ynng_btns])
    ynng_btns[1].click()  # NO
    page.wait_for_timeout(150)
    cls = page.query_selector('#q28 .tfng-btn[data-value="NO"]').get_attribute("class")
    assert "selected" in cls

    step[0] = "answer table-completion q33-36"
    for n in [33, 34, 35, 36]:
        inp = page.query_selector(f'input[data-qnum="{n}"]')
        assert inp, f"table completion input q{n} missing"
        inp.fill("x")
    page.wait_for_timeout(150)

    step[0] = "answer matching-information q37"
    sel = page.query_selector('select[data-qnum="37"]')
    assert sel
    opts = sel.query_selector_all("option")
    print("matching-information q37 option count:", len(opts))
    assert len(opts) == 7  # placeholder + A-F

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
