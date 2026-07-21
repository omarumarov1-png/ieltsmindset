"""
Full correctness audit: for every existing reading test group and every
listening test group, auto-answer every question directly from the JSON
answer key (via a page.evaluate fetch of the raw data file, not by reading
DOM state), submit, and assert a perfect run -> band 9.0 with 0 incorrect
review items. This catches answer-key/grading mismatches that spot-checks
in individual scripts wouldn't necessarily cover, since it exhaustively
answers every question of every test group instead of a handful of
representative ones. Scales automatically to however many test groups
exist -- no counts to keep updated as content is added.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/audit_answer_keys.py
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8935"
errors = []
step = ["boot"]
failures = []

def on_console(msg):
    if msg.type == "error":
        errors.append(f"[console @ {step[0]}] {msg.text}")

def on_pageerror(exc):
    errors.append(f"[pageerror @ {step[0]}] {exc}")


def build_answer_map(page, skill, testgroup_id):
    js = """
        async (args) => {
            const [skill, tg] = args;
            const url = skill === 'reading' ? '/data/reading/index.json' : '/data/listening/index.json';
            const res = await fetch(url);
            const data = await res.json();
            const items = (skill === 'reading' ? data.passages : data.tests)
                .filter(it => it.kind !== 'quick' && (it.testGroup || '1') === tg);
            const out = {};
            items.forEach(it => {
                it.questionGroups.forEach(g => {
                    g.questions.forEach(q => {
                        out[q.number] = { type: g.type, q, headingOptions: g.headingOptions };
                    });
                });
            });
            return out;
        }
    """
    return page.evaluate(js, [skill, testgroup_id])


def answer_all(page, answer_map):
    for qnum_str, info in answer_map.items():
        qnum = int(qnum_str)
        t = info["type"]
        q = info["q"]
        cell = page.query_selector(f'.palette-cell[data-qnum="{qnum}"]')
        if cell:
            cell.click()
            page.wait_for_timeout(60)
        if t in ("true-false-not-given", "yes-no-not-given"):
            btn = page.query_selector(f'#q{qnum} .tfng-btn[data-value="{q["answer"]}"]')
            assert btn, f"tfng/ynng button missing for q{qnum}"
            btn.click()
        elif t == "matching-headings":
            sel = page.query_selector(f'select[data-qnum="{qnum}"]')
            assert sel, f"heading select missing q{qnum}"
            sel.select_option(value=str(q["answer"]))
        elif t in ("matching-information", "matching-features"):
            sel = page.query_selector(f'select[data-qnum="{qnum}"]')
            assert sel, f"match select missing q{qnum}"
            sel.select_option(label=str(q["answer"]))
        elif t == "multiple-choice":
            ans = q["answer"]
            idxs = ans if isinstance(ans, list) else [ans]
            for i in idxs:
                opt = page.query_selector(f'#q{qnum} .opt-choice[data-optidx="{i}"] input')
                assert opt, f"MC option missing q{qnum} idx {i}"
                opt.check()
        else:
            ans = q["answer"]
            val = ans[0] if isinstance(ans, list) else ans
            inp = page.query_selector(f'input[data-qnum="{qnum}"]')
            assert inp, f"completion input missing q{qnum}"
            inp.fill(str(val))
        page.wait_for_timeout(40)


def audit_skill(page, skill):
    nav_sel = f'[data-nav="{skill}"]'
    page.click(nav_sel)
    page.wait_for_timeout(300)
    tg_rows = page.query_selector_all("[data-testgroup]")
    tg_ids = [r.get_attribute("data-testgroup") for r in tg_rows]
    print(f"{skill}: found test groups {tg_ids}")

    for tg_id in tg_ids:
        step[0] = f"{skill} testGroup {tg_id}: start"
        page.click('[data-nav="' + skill + '"]')
        page.wait_for_timeout(300)
        row = [r for r in page.query_selector_all("[data-testgroup]") if r.get_attribute("data-testgroup") == tg_id][0]
        row.click()
        page.wait_for_timeout(600)

        answer_map = build_answer_map(page, skill, tg_id)
        n_questions = len(answer_map)
        step[0] = f"{skill} testGroup {tg_id}: answering {n_questions} questions"
        answer_all(page, answer_map)

        step[0] = f"{skill} testGroup {tg_id}: submit"
        page.click("#submitTestBtn")
        page.wait_for_timeout(300)
        page.click("#submitConfirmBtn")
        page.wait_for_timeout(500)

        band_el = page.query_selector(".results-band .num")
        band = float(band_el.inner_text().strip()) if band_el else None
        incorrect = page.query_selector_all(".review-item.incorrect")
        review_items = page.query_selector_all(".review-item")
        print(f"  {skill} tg{tg_id}: {n_questions} answered, {len(review_items)} reviewed, "
              f"{len(incorrect)} incorrect, band={band}")

        if len(incorrect) != 0:
            wrong_nums = []
            for item in incorrect:
                qnum_el = item.query_selector(".r-q .qnum")
                wrong_nums.append(qnum_el.inner_text() if qnum_el else "?")
            failures.append(f"{skill} testGroup {tg_id}: {len(incorrect)} incorrect on a full-mark run "
                             f"(questions: {wrong_nums})")
        if band is not None and band != 9.0:
            failures.append(f"{skill} testGroup {tg_id}: expected band 9.0 for a perfect run, got {band}")
        if n_questions != 40:
            failures.append(f"{skill} testGroup {tg_id}: expected 40 questions, found {n_questions}")

        page.click("#backHomeBtn")
        page.wait_for_timeout(300)


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", on_console)
    page.on("pageerror", on_pageerror)

    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)

    audit_skill(page, "reading")
    audit_skill(page, "listening")

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)

print(f"\n{len(failures)} answer-key/grading failures")
for f in failures:
    print(" -", f)

sys.exit(1 if (errors or failures) else 0)
