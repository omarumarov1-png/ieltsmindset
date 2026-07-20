"""
Confirms the General Training reading band table is actually selected for
General Training test groups (testGroup 5, "reading-passage-013/014/015"),
not just that the Academic/General Training split doesn't crash.

At raw score 30/40: the Academic table gives band 8.0, but the General
Training table gives band 6.0. Answering only the first 30 questions
correctly and leaving the rest blank pins the raw score at exactly 30, so
the two tables diverge and we can prove which one was actually used.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_band_table_divergence.py
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

    step[0] = "start GT reading test group 5, answer only the first 30 correctly"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(300)
    tg_rows = page.query_selector_all("[data-testgroup]")
    tg5 = [r for r in tg_rows if r.get_attribute("data-testgroup") == "5"][0]
    tg5.click()
    page.wait_for_timeout(600)

    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/reading/index.json');
            const data = await res.json();
            const items = data.passages.filter(p => p.testGroup === '5');
            const out = {};
            items.forEach(p => {
                p.questionGroups.forEach(g => {
                    g.questions.forEach(q => {
                        out[q.number] = { type: g.type, q, headingOptions: g.headingOptions };
                    });
                });
            });
            return out;
        }
    """)

    for qnum_str, info in answer_map.items():
        qnum = int(qnum_str)
        if qnum > 30:
            continue  # leave these unanswered -> raw score exactly 30
        t = info["type"]
        q = info["q"]
        cell = page.query_selector(f'.palette-cell[data-qnum="{qnum}"]')
        if cell:
            cell.click()
            page.wait_for_timeout(100)
        if t in ("true-false-not-given", "yes-no-not-given"):
            page.query_selector(f'#q{qnum} .tfng-btn[data-value="{q["answer"]}"]').click()
        elif t == "matching-headings":
            page.query_selector(f'select[data-qnum="{qnum}"]').select_option(value=str(q["answer"]))
        elif t in ("matching-information", "matching-features"):
            page.query_selector(f'select[data-qnum="{qnum}"]').select_option(label=str(q["answer"]))
        elif t == "multiple-choice":
            page.query_selector(f'#q{qnum} .opt-choice[data-optidx="{q["answer"]}"] input').check()
        else:
            ans = q["answer"]
            val = ans[0] if isinstance(ans, list) else ans
            page.query_selector(f'input[data-qnum="{qnum}"]').fill(str(val))
        page.wait_for_timeout(50)

    step[0] = "submit with exactly 30/40 correct"
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    band_text = page.query_selector(".results-band .num").inner_text()
    print("band shown:", band_text)
    band = float(band_text.strip())
    print(f"General Training table expects 6.0 at raw 30; Academic table would give 8.0. Got: {band}")
    assert band == 6.0, f"expected General Training band 6.0 at raw score 30, got {band} (looks like the Academic table was used instead)"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
