"""
Regression/coverage check for multi-answer multiple-choice questions
("choose TWO letters" -- a real IELTS question type). The schema and
grading code (Array.isArray(q.answer) branches in renderMCQuestion and
gradeQuestion) supported this from the start, but no content ever used it
until testGroup 6's q14 (reading-passage-017, Silk Road passage), so this
path had literally never been exercised by any test or real content.

Verifies: renders as checkboxes (not radio buttons) with the right count,
selecting exactly the two correct options grades as correct, and selecting
only one of the two correct options (a partial match) grades as incorrect
-- not just that the "all correct" case happens to pass.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_multi_select_mc.py
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

    step[0] = "open the Silk Road passage (reading-passage-017, testGroup 6) directly"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")
    target = None
    for r in rows:
        if "Silk Road" in r.inner_text():
            target = r
            break
    assert target, "could not find the Silk Road practice row"
    target.click()
    page.wait_for_timeout(400)

    step[0] = "q14 should render as checkboxes, not radio buttons (multi-answer MC)"
    inputs = page.query_selector_all("#q14 .opt-choice input")
    assert len(inputs) == 5, f"expected 5 options for q14, got {len(inputs)}"
    types = set(inp.get_attribute("type") for inp in inputs)
    print("q14 input types:", types)
    assert types == {"checkbox"}, f"expected checkboxes for a multi-answer MC question, got {types}"

    step[0] = "select only ONE of the two correct options (B), submit, expect incorrect"
    page.query_selector('#q14 .opt-choice[data-optidx="1"] input').check()
    # fill everything else in the passage with something plausible-but-wrong
    # so submission doesn't get blocked by an unrelated validation step
    page.wait_for_timeout(150)
    page.click("#exitBtn")
    page.wait_for_timeout(300)

    step[0] = "re-open and select BOTH correct options (B and C), verify palette shows answered"
    rows = page.query_selector_all("#contentList .content-row")
    for r in rows:
        if "Silk Road" in r.inner_text():
            r.click()
            break
    page.wait_for_timeout(400)
    page.query_selector('#q14 .opt-choice[data-optidx="1"] input').check()
    page.query_selector('#q14 .opt-choice[data-optidx="2"] input').check()
    page.wait_for_timeout(150)
    cell14 = page.query_selector('.palette-cell[data-qnum="14"]')
    assert "answered" in (cell14.get_attribute("class") or ""), "q14 should show as answered with 2 selections"

    step[0] = "answer everything else via the JSON answer key, submit, confirm q14 grades CORRECT"
    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/reading/index.json');
            const data = await res.json();
            // Practice mode only loads the single Silk Road passage into the
            // DOM (Q14-27), not the whole test group -- scope to just that.
            const p = data.passages.find(p => p.id === 'reading-passage-017');
            const out = {};
            p.questionGroups.forEach(g => {
                g.questions.forEach(q => {
                    out[q.number] = { type: g.type, q, headingOptions: g.headingOptions };
                });
            });
            return out;
        }
    """)
    for qnum_str, info in answer_map.items():
        qnum = int(qnum_str)
        if qnum == 14:
            continue  # already answered correctly above
        t = info["type"]
        q = info["q"]
        cell = page.query_selector(f'.palette-cell[data-qnum="{qnum}"]')
        if cell:
            cell.click()
            page.wait_for_timeout(60)
        if t in ("true-false-not-given", "yes-no-not-given"):
            page.query_selector(f'#q{qnum} .tfng-btn[data-value="{q["answer"]}"]').click()
        elif t == "matching-headings":
            page.query_selector(f'select[data-qnum="{qnum}"]').select_option(value=str(q["answer"]))
        elif t in ("matching-information", "matching-features"):
            page.query_selector(f'select[data-qnum="{qnum}"]').select_option(label=str(q["answer"]))
        elif t == "multiple-choice":
            ans = q["answer"]
            idxs = ans if isinstance(ans, list) else [ans]
            for i in idxs:
                page.query_selector(f'#q{qnum} .opt-choice[data-optidx="{i}"] input').check()
        else:
            ans = q["answer"]
            val = ans[0] if isinstance(ans, list) else ans
            page.query_selector(f'input[data-qnum="{qnum}"]').fill(str(val))
        page.wait_for_timeout(40)

    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    incorrect = page.query_selector_all(".review-item.incorrect")
    print("incorrect review items (expect 0, q14 fully correct):", len(incorrect))
    assert len(incorrect) == 0, f"expected a perfect run with q14 fully correct, got {len(incorrect)} incorrect"

    step[0] = "done -- now verify a PARTIAL selection (only 1 of 2) grades as incorrect"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")
    for r in rows:
        if "Silk Road" in r.inner_text():
            r.click()
            break
    page.wait_for_timeout(400)
    page.query_selector('#q14 .opt-choice[data-optidx="1"] input').check()  # only B, missing C
    page.wait_for_timeout(150)
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    q14_review = None
    for item in page.query_selector_all(".review-item"):
        if item.query_selector(".r-q .qnum") and item.query_selector(".r-q .qnum").inner_text() == "14":
            q14_review = item
            break
    assert q14_review, "could not find q14 in the review list"
    is_incorrect = "incorrect" in (q14_review.get_attribute("class") or "")
    print("q14 marked incorrect with only a partial (1 of 2) selection:", is_incorrect)
    assert is_incorrect, "a partial selection (1 of 2 correct options) should NOT grade as correct"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
