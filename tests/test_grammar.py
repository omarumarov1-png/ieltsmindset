"""
Verifies the new Grammar skill: dashboard card (now live, not "coming
soon") -> topic list -> rule-reference study screen (form box, use-case
sections, common-error pairs) -> quiz (reusing sentence-completion /
multiple-choice renderers, same as vocabulary) -> percentage results ->
history entry.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_grammar.py
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

    step[0] = "dashboard shows a live Grammar card (not 'coming soon')"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    cards = page.query_selector_all(".skill-card")
    grammar_card = None
    for c in cards:
        if "Грамматика" in c.inner_text():
            grammar_card = c
            break
    assert grammar_card, "Grammar skill card not found on dashboard"
    assert "locked" not in (grammar_card.get_attribute("class") or ""), "Grammar card should not be locked/coming-soon anymore"
    assert "Скоро" not in grammar_card.inner_text(), "Grammar card should not say 'coming soon' anymore"

    step[0] = "open Grammar hub, confirm topics are listed"
    grammar_card.query_selector("button[data-go]").click()
    page.wait_for_timeout(400)
    topic_rows = page.query_selector_all("[data-grammar-idx]")
    print("grammar topics found:", len(topic_rows))
    assert len(topic_rows) == 4, f"expected 4 grammar topics, got {len(topic_rows)}"

    step[0] = "open the modal-verbs topic -> rule-reference study screen"
    modals_row = None
    for r in topic_rows:
        if "Modal" in r.inner_text():
            modals_row = r
            break
    assert modals_row, "modal verbs topic row not found"
    modals_row.click()
    page.wait_for_timeout(400)
    assert page.query_selector(".rule-box"), "rule box not rendered"
    assert page.query_selector(".rule-box").inner_text().count("must") >= 0  # sanity: no crash reading text
    error_pairs = page.query_selector_all(".error-pair")
    print("common-error pairs shown:", len(error_pairs))
    assert len(error_pairs) == 3, f"expected 3 common-error pairs, got {len(error_pairs)}"
    rule_sections = page.query_selector_all(".rule-section")
    assert len(rule_sections) >= 4, f"expected at least 4 use-case sections + errors section, got {len(rule_sections)}"

    step[0] = "start the quiz for this topic"
    page.click("#gQuizBtn")
    page.wait_for_timeout(400)
    assert page.query_selector(".pane-quiz-single"), "single-pane quiz shell not rendered"
    assert "hidden" in page.query_selector("#timerChip").get_attribute("class"), "grammar quiz should be untimed"
    mc_options = page.query_selector_all("#q1 .opt-choice")
    print("MC options for q1:", len(mc_options))
    assert len(mc_options) == 4

    step[0] = "answer the quiz via the JSON answer key, submit, confirm a percentage score"
    answer_map = page.evaluate("""
        async () => {
            const res = await fetch('/data/grammar/index.json');
            const data = await res.json();
            const topic = data.topics.find(t => t.id === 'grammar-modals-obligation');
            const g = topic.questionGroups[0];
            const out = {};
            g.questions.forEach(q => { out[q.number] = q.answer; });
            return out;
        }
    """)
    for qnum_str, answer_idx in answer_map.items():
        opt = page.query_selector(f'#q{qnum_str} .opt-choice[data-optidx="{answer_idx}"] input')
        assert opt, f"MC option missing for q{qnum_str} idx {answer_idx}"
        opt.check()
        page.wait_for_timeout(50)

    page.click("#submitTestBtn")
    page.wait_for_timeout(300)
    page.click("#submitConfirmBtn")
    page.wait_for_timeout(500)
    assert page.query_selector(".results-hero"), "results screen missing after grammar quiz"
    score_num = page.query_selector(".results-band .num").inner_text()
    print("grammar quiz score:", score_num)
    assert "%" in score_num, f"expected a percentage score for a grammar quiz, got {score_num!r}"
    incorrect = page.query_selector_all(".review-item.incorrect")
    assert len(incorrect) == 0, f"expected a perfect score answering from the key, got {len(incorrect)} incorrect"

    step[0] = "back to dashboard, confirm history shows the grammar attempt"
    page.click("#backHomeBtn")
    page.wait_for_timeout(300)
    history_rows = page.query_selector_all(".history-row")
    assert len(history_rows) >= 1
    latest_title = history_rows[0].query_selector(".h-title").inner_text()
    latest_score = history_rows[0].query_selector(".h-band").inner_text()
    print("latest history row:", latest_title, "|", latest_score)
    assert "Грамматика" in latest_title, f"expected a Grammar history row, got {latest_title!r}"
    assert "%" in latest_score

    step[0] = "exit a study screen (not a quiz) via the exit button -> should return to grammar hub, not a broken screen"
    page.click('[data-nav="dashboard"]')
    page.wait_for_timeout(200)
    cards = page.query_selector_all(".skill-card")
    for c in cards:
        if "Грамматика" in c.inner_text():
            c.query_selector("button[data-go]").click()
            break
    page.wait_for_timeout(400)
    page.query_selector("[data-grammar-idx]").click()
    page.wait_for_timeout(400)
    page.click("#exitBtn")
    page.wait_for_timeout(300)
    assert page.query_selector("[data-grammar-idx]"), "exiting a grammar study screen should return to the grammar hub"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
