"""
Verifies the new Vocabulary skill: dashboard card -> set list -> flashcard
study mode (prev/next navigation, disabled at boundaries) -> quiz mode
(reusing the summary-completion renderer/grader) -> percentage results
(not a band) -> history entry.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_vocabulary.py
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

    step[0] = "dashboard shows a live Vocabulary card (not 'coming soon')"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    cards = page.query_selector_all(".skill-card")
    vocab_card = None
    for c in cards:
        if "Словарный" in c.inner_text():
            vocab_card = c
            break
    assert vocab_card, "Vocabulary skill card not found on dashboard"
    assert "locked" not in (vocab_card.get_attribute("class") or ""), "Vocabulary card should not be locked/coming-soon"
    assert "Скоро" not in vocab_card.inner_text(), "Vocabulary card should not say 'coming soon'"

    step[0] = "open Vocabulary hub, confirm sets are listed"
    vocab_card.query_selector("button[data-go]").click()
    page.wait_for_timeout(400)
    set_rows = page.query_selector_all("[data-vocab-idx]")
    print("vocabulary sets found:", len(set_rows))
    assert len(set_rows) == 3, f"expected 3 vocabulary sets, got {len(set_rows)}"

    step[0] = "open the first set -> should land in flashcard study mode"
    set_rows[0].click()
    page.wait_for_timeout(400)
    assert page.query_selector(".flashcard"), "flashcard not rendered"
    term1 = page.query_selector(".fc-term").inner_text()
    print("first flashcard term:", term1)
    prev_btn = page.query_selector("#fcPrevBtn")
    assert prev_btn.is_disabled(), "prev button should be disabled on the first card"

    step[0] = "navigate forward through flashcards"
    page.click("#fcNextBtn")
    page.wait_for_timeout(200)
    term2 = page.query_selector(".fc-term").inner_text()
    print("second flashcard term:", term2)
    assert term2 != term1, "flashcard did not advance to a new term"
    prev_btn = page.query_selector("#fcPrevBtn")
    assert not prev_btn.is_disabled(), "prev button should be enabled after moving forward"

    step[0] = "go back to the first card via prev button"
    page.click("#fcPrevBtn")
    page.wait_for_timeout(200)
    term1_again = page.query_selector(".fc-term").inner_text()
    assert term1_again == term1, "prev button did not return to the first term"

    step[0] = "start the quiz for this set"
    page.click("#fcQuizBtn")
    page.wait_for_timeout(400)
    assert page.query_selector(".pane-quiz-single"), "single-pane quiz shell not rendered"
    assert page.query_selector("#timerChip") and "hidden" in page.query_selector("#timerChip").get_attribute("class"), \
        "vocabulary quiz should be untimed"

    step[0] = "answer the quiz via the JSON answer key, submit, confirm a percentage score"
    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/vocabulary/index.json');
            const data = await res.json();
            const set = data.sets[0];
            const g = set.questionGroups[0];
            const out = {};
            g.questions.forEach(q => { out[q.number] = q.answer[0]; });
            return out;
        }
    """)
    for qnum_str, answer in answer_map.items():
        inp = page.query_selector(f'input[data-qnum="{qnum_str}"]')
        assert inp, f"quiz input missing for q{qnum_str}"
        inp.fill(answer)
    page.wait_for_timeout(150)

    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    assert page.query_selector(".results-hero"), "results screen missing after vocabulary quiz"
    score_num = page.query_selector(".results-band .num").inner_text()
    print("vocabulary quiz score:", score_num)
    assert "%" in score_num, f"expected a percentage score for a vocabulary quiz, got {score_num!r}"
    incorrect = page.query_selector_all(".review-item.incorrect")
    print("incorrect (expect 0, answered from the key):", len(incorrect))
    assert len(incorrect) == 0, "expected a perfect score answering straight from the JSON key"

    step[0] = "back to dashboard, confirm history shows the vocabulary attempt"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    history_rows = page.query_selector_all(".history-row")
    assert len(history_rows) >= 1
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    latest_score = history_rows[0].query_selector(".h-band").inner_text()
    print("latest history row:", latest_title, "|", latest_score)
    assert "Словарный" in latest_title, f"expected a Vocabulary history row, got {latest_title!r}"
    assert "%" in latest_score, f"expected a percentage in vocabulary history, got {latest_score!r}"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
