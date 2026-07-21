"""
Regression check for a real bug found by code inspection: the sound-toggle
button in the topbar flipped its icon and persisted a preference to
localStorage, but nothing ever read the `soundOn` variable -- audio played
at full volume regardless of the toggle's state. Fixed by having setupAudio
respect it for real <audio> elements (.muted) and the TTS fallback respect
it per-utterance (.volume).

Since no real audio files exist yet (audioFile is null on every listening
item until the ElevenLabs generation step runs), this test intercepts
`speechSynthesis.speak` to confirm the utterance volume actually reflects
the toggle state, rather than trusting that the code merely doesn't crash.

Run with a static server serving the app root:
    python3 -m http.server 8935   (from the ieltsmindset/ directory)
    python3 tests/test_sound_toggle.py
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

    # Intercept speechSynthesis.speak before any app code runs, recording the
    # .volume of every utterance passed to it, and prevent it from actually
    # trying to speak (headless Chromium has no voices anyway).
    page.add_init_script("""
        window.__speakVolumes = [];
        if (window.speechSynthesis) {
            window.speechSynthesis.speak = (utter) => {
                window.__speakVolumes.push(utter.volume);
                setTimeout(() => { if (utter.onend) utter.onend(); }, 10);
            };
            window.speechSynthesis.cancel = () => {};
        }
    """)

    step[0] = "load dashboard, confirm sound starts on"
    page.goto(BASE + "/index.html")
    page.wait_for_timeout(500)
    sound_btn = page.query_selector("#soundToggle")
    assert sound_btn.inner_text() == "🔊", "sound should default to on"

    step[0] = "start listening practice with sound ON, play, check utterance volume"
    page.click('[data-nav="listening"]')
    page.wait_for_timeout(300)
    rows = page.query_selector_all("#contentList .content-row")
    rows[0].click()
    page.wait_for_timeout(400)
    page.click("#apPlayBtn")
    page.wait_for_timeout(300)
    volumes_on = page.evaluate("window.__speakVolumes")
    print("utterance volumes with sound ON:", volumes_on)
    assert len(volumes_on) > 0, "expected at least one utterance to have been queued"
    assert all(v == 1 for v in volumes_on), f"expected volume 1 with sound on, got {volumes_on}"

    step[0] = "toggle sound OFF, replay, check utterance volume is now 0"
    page.evaluate("window.__speakVolumes = []")
    page.click("#exitBtn")
    page.wait_for_timeout(300)
    page.click("#soundToggle")
    page.wait_for_timeout(100)
    assert page.query_selector("#soundToggle").inner_text() == "🔇", "icon should switch to muted"

    rows = page.query_selector_all("#contentList .content-row")
    rows[0].click()
    page.wait_for_timeout(400)
    page.click("#apPlayBtn")
    page.wait_for_timeout(300)
    volumes_off = page.evaluate("window.__speakVolumes")
    print("utterance volumes with sound OFF:", volumes_off)
    assert len(volumes_off) > 0, "expected at least one utterance to have been queued"
    assert all(v == 0 for v in volumes_off), f"expected volume 0 with sound off, got {volumes_off}"

    step[0] = "toggle back on for cleanliness, confirm state persists via localStorage key"
    page.click("#soundToggle")
    page.wait_for_timeout(100)
    stored = page.evaluate("localStorage.getItem('ieltsmindset-sound')")
    print("localStorage sound pref after toggling back on:", stored)
    assert stored == "1", f"expected localStorage to record sound back on, got {stored!r}"

    step[0] = "done"
    browser.close()

print(f"\n{len(errors)} JS errors captured")
for e in errors[:50]:
    print(" ", e)
sys.exit(1 if errors else 0)
