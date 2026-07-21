"""
Regression check for mixed-question-type quick drills: a single short text
with two different question-group types (e.g. TFNG + short-answer, or
sentence-completion + multiple-choice) rather than one type per drill.
Confirms the "Неск. типов" (multiple types) badge shows instead of a
single-type label, and that both groups render and grade correctly on one
combined submission.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_mixed_type_quick_drills.py
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

    step[0] = "find the 'Ordering a Taxi' mixed-type quick drill in the listening hub"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="listening"]')
    page.wait_for_timeout(400)
    rows = page.query_selector_all(".content-row")
    target = None
    for r in rows:
        if "Ordering a Taxi" in r.inner_text():
            target = r
            break
    assert target, "could not find the 'Ordering a Taxi' quick drill"
    badge = target.query_selector(".c-badge").inner_text().upper()
    print("badge for a 2-type quick drill:", badge)
    assert "ТИП" in badge, f"expected the multi-type badge, got {badge!r}"

    step[0] = "open it, confirm both question types render (sentence-completion inputs + MC options)"
    target.click()
    page.wait_for_timeout(400)
    blank_input = page.query_selector('input[data-qnum="1"]')
    assert blank_input, "sentence-completion input for q1 missing"
    mc_options = page.query_selector_all('#q4 .opt-choice')
    print("MC options rendered for q4:", len(mc_options))
    assert len(mc_options) == 4, f"expected 4 MC options for q4, got {len(mc_options)}"

    step[0] = "answer both groups correctly via the JSON answer key, submit, expect a perfect score"
    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/listening/index.json');
            const data = await res.json();
            const item = data.tests.find(t => t.id === 'listening-quick-005');
            const out = {};
            item.questionGroups.forEach(g => {
                g.questions.forEach(q => { out[q.number] = { type: g.type, q }; });
            });
            return out;
        }
    """)
    for qnum_str, info in answer_map.items():
        qnum = int(qnum_str)
        t = info["type"]
        q = info["q"]
        if t == "sentence-completion":
            ans = q["answer"]
            val = ans[0] if isinstance(ans, list) else ans
            page.query_selector(f'input[data-qnum="{qnum}"]').fill(str(val))
        elif t == "multiple-choice":
            page.query_selector(f'#q{qnum} .opt-choice[data-optidx="{q["answer"]}"] input').check()
        page.wait_for_timeout(50)

    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    incorrect = page.query_selector_all(".review-item.incorrect")
    review_items = page.query_selector_all(".review-item")
    print(f"reviewed: {len(review_items)}, incorrect: {len(incorrect)}")
    assert len(review_items) == 5, f"expected 5 questions across both groups, got {len(review_items)}"
    assert len(incorrect) == 0, "expected a perfect score answering both group types from the key"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
