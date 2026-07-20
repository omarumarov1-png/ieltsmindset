# IELTSmindset Playwright tests

Manual-verification scripts (no test runner/CI wired up yet, matching the
sibling apps' convention). Each script is self-contained and checks console
errors + page errors in addition to its own assertions.

## Running

```bash
pip install playwright && playwright install chromium   # one-time setup
cd ieltsmindset
python3 -m http.server 8935 &
python3 tests/test_core_flows.py
python3 tests/test_question_types.py
python3 tests/test_timer_and_exit.py
python3 tests/audit_answer_keys.py
python3 tests/test_band_table_divergence.py
```

## What each script covers

- **test_core_flows.py** — dashboard → practice mode → full test mode →
  submit → results → history, for both Reading and Listening. TFNG,
  matching-headings, short-answer, matching-information, table-completion,
  the exit-confirm-during-test guard (cancel path), timer chip visibility,
  listening audio player TTS-fallback play button.
- **test_question_types.py** — multiple-choice selection styling, YNNG
  button labels, matching-information dropdown option count.
- **test_timer_and_exit.py** — timer actually counts down; exit-confirm
  "leave" path (complement to the cancel path in test_core_flows.py).
- **audit_answer_keys.py** — exhaustive correctness audit: auto-answers
  *every* question in *every* existing test group straight from the JSON
  answer keys and asserts a perfect run scores band 9.0 with 0 incorrect
  reviews. Scales automatically to however many test groups exist — run
  this after adding new content, before committing it.
- **test_band_table_divergence.py** — proves the General Training reading
  band table (not the Academic one) is actually used for General Training
  test groups, by landing on a raw score where the two tables' outputs
  differ (30/40 → GT band 6.0 vs Academic band 8.0).

Some assertions target specific, stable, long-standing content (e.g.
`reading-passage-001`'s exact question count) rather than deriving
everything dynamically — that's intentional for content that isn't
expected to change; item/test-group *counts* are derived dynamically so
adding new test groups doesn't require updating hardcoded numbers here.
