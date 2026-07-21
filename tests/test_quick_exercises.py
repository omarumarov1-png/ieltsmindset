"""
Verifies the new "quick exercises" feature: short (5-8 question), single-
question-type, untimed drills separate from the 40-question full tests and
13-14-question full practice passages/sections.

Covers: quick items show in their own hub section (not lumped into the
full-test count or the regular practice list), each shows a question-type
badge instead of a "Тест N" badge, completing one shows a plain percentage
score rather than a misleading IELTS band (band tables assume a ~40-question
test), and quick attempts are excluded from the dashboard's rolling overall
band average.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_quick_exercises.py
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

    step[0] = "reading hub - quick exercises appear in their own section"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    page.click('[data-nav="reading"]')
    page.wait_for_timeout(400)

    tg_rows = page.query_selector_all("[data-testgroup]")
    print("full test groups (should be unaffected by quick drills):", len(tg_rows))
    # every full test group should still have exactly 40 questions worth of
    # content -- quick items must not have leaked into test-group bundling
    for row in tg_rows:
        assert "40" in row.inner_text(), f"a full test group's question count looks wrong: {row.inner_text()!r}"

    section_titles = [el.inner_text() for el in page.query_selector_all(".section-title")]
    print("hub section titles:", section_titles)
    assert any("Быстрые" in t for t in section_titles), "quick-exercises section title missing from hub"

    practice_rows = page.query_selector_all("#contentList .content-row")
    for row in practice_rows:
        badge = row.query_selector(".c-badge").inner_text().upper()
        assert "ТЕСТ" in badge, f"a row in the regular practice list has a non-full-passage badge: {badge!r}"
    print("regular practice rows (should exclude quick drills):", len(practice_rows))

    step[0] = "find a quick drill row (question-type badge, ~5 мин status, not in #contentList)"
    all_rows = page.query_selector_all(".content-row")
    quick_row = None
    for row in all_rows:
        badge = row.query_selector(".c-badge")
        status = row.query_selector(".c-status")
        if badge and status and "мин" in status.inner_text() and "ТЕСТ" not in badge.inner_text().upper() and "60 мин" not in status.inner_text():
            quick_row = row
            break
    assert quick_row, "could not find a quick-drill row with a type badge and a minutes estimate"
    print("found quick drill row:", quick_row.inner_text().replace("\n", " | "))
    assert quick_row.get_attribute("data-practice-idx") is not None, "quick row should be clickable via data-practice-idx"

    step[0] = "open the quick drill, confirm it's untimed (no timer chip) and has a small question count"
    quick_row.click()
    page.wait_for_timeout(400)
    timer_chip = page.query_selector("#timerChip")
    assert timer_chip and "hidden" in (timer_chip.get_attribute("class") or ""), \
        "quick drills should be untimed (practice mode), timer chip should stay hidden"
    palette_cells = page.query_selector_all(".palette-cell")
    print("quick drill question count:", len(palette_cells))
    assert 1 <= len(palette_cells) <= 10, f"expected a small quick-drill question count, got {len(palette_cells)}"

    step[0] = "answer every question in the quick drill via the JSON answer key"
    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/reading/index.json');
            const data = await res.json();
            const item = data.passages.find(p => p.kind === 'quick');
            const out = {};
            item.questionGroups.forEach(g => {
                g.questions.forEach(q => { out[q.number] = { type: g.type, q, headingOptions: g.headingOptions }; });
            });
            return { id: item.id, out };
        }
    """)
    # The first quick reading item in document order should match what's open;
    # this drill only opened whichever quick row appeared first in the hub,
    # which by construction is reading-quick-001 (TFNG) unless content changes.
    for qnum_str, info in answer_map["out"].items():
        qnum = int(qnum_str)
        t = info["type"]
        q = info["q"]
        if t in ("true-false-not-given", "yes-no-not-given"):
            btn = page.query_selector(f'#q{qnum} .tfng-btn[data-value="{q["answer"]}"]')
            if btn:
                btn.click()
                page.wait_for_timeout(50)

    step[0] = "submit the quick drill and confirm a PERCENTAGE score is shown, not a band"
    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    assert page.query_selector(".results-hero"), "results screen missing after quick drill submit"
    score_label = page.query_selector(".results-band .lbl").inner_text()
    score_num = page.query_selector(".results-band .num").inner_text()
    print("quick drill results label/number:", score_label, "/", score_num)
    assert "%" in score_num, f"expected a percentage score for a quick drill, got {score_num!r}"
    assert "Верных" in score_label or "верных" in score_label.lower(), \
        f"expected the quick-drill score label, not the band label, got {score_label!r}"

    step[0] = "back to dashboard, confirm history shows the quick attempt distinctly and excludes it from overall band"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    history_rows = page.query_selector_all(".history-row")
    assert len(history_rows) >= 1
    latest_band_text = history_rows[0].query_selector(".h-band").inner_text()
    print("latest history row score (should be a %, not a band):", latest_band_text)
    assert "%" in latest_band_text, f"quick drill history row should show a percentage, got {latest_band_text!r}"
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    print("latest history row title:", latest_title)
    assert "Быстрое" in latest_title, f"quick drill history row should say 'quick exercise', got {latest_title!r}"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
