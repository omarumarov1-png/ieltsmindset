#!/usr/bin/env python3
"""Offline ElevenLabs audio generator for IELTSmindset Listening content.

This is a pre-generation step, not a runtime API call: it reads a listening
test's `transcript` (per-speaker lines) from data/listening/index.json,
generates each speaker turn as a separate TTS request with that speaker's
assigned voice, stitches the resulting clips into one .mp3 with short gaps
between turns, writes it to audio/, and updates the test's `audioFile`
field to point at the new file. No API key is ever exposed to the app
itself — this script runs once, offline, and the app just plays the
resulting static file.

Setup:
    pip install requests pydub
    brew install ffmpeg          # pydub needs ffmpeg on PATH for mp3 export
    export ELEVENLABS_API_KEY=sk_...

Usage:
    # First, see what voices are actually available on the account and
    # pick IDs for VOICE_MAP below (the placeholder names are illustrative
    # only — ElevenLabs' exact voice library/IDs should be confirmed live).
    python3 scripts/generate_audio.py --list-voices

    # Then generate audio for one test (by id) or all tests missing audio.
    python3 scripts/generate_audio.py --test-id listening-test-001-section-1
    python3 scripts/generate_audio.py --all
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTENING_INDEX = ROOT / "data" / "listening" / "index.json"
AUDIO_DIR = ROOT / "audio"
API_BASE = "https://api.elevenlabs.io/v1"
GAP_MS = 500  # silence between speaker turns, tune to taste

# ---------------------------------------------------------------------------
# Voice map: transcript `voiceId` label -> ElevenLabs voice_id.
# PLACEHOLDERS — run --list-voices with a real API key first and replace
# these with actual IDs from the account's available voice library. Aim for
# a mix of British/American/Australian, male/female, reused consistently
# per role across every test so the "cast" feels stable over time.
# ---------------------------------------------------------------------------
VOICE_MAP = {
    "female-british": "REPLACE_ME_female_british_voice_id",
    "male-british": "REPLACE_ME_male_british_voice_id",
    "female-american": "REPLACE_ME_female_american_voice_id",
    "male-american": "REPLACE_ME_male_american_voice_id",
    "female-australian": "REPLACE_ME_female_australian_voice_id",
    "male-australian": "REPLACE_ME_male_australian_voice_id",
}

MODEL_ID = "eleven_turbo_v2_5"  # fast + natural; swap to eleven_multilingual_v2 if needed


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY in your environment first.")
    return key


def list_voices():
    import requests
    r = requests.get(f"{API_BASE}/voices", headers={"xi-api-key": api_key()})
    r.raise_for_status()
    voices = r.json().get("voices", [])
    print(f"{len(voices)} voices available:\n")
    for v in voices:
        labels = v.get("labels", {})
        print(f"  {v['voice_id']}  {v['name']!r:20}  accent={labels.get('accent','?'):10} gender={labels.get('gender','?'):8} age={labels.get('age','?')}")


def tts_bytes(text, voice_id):
    import requests
    url = f"{API_BASE}/text-to-speech/{voice_id}"
    r = requests.post(
        url,
        headers={"xi-api-key": api_key(), "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs TTS failed ({r.status_code}): {r.text[:300]}")
    return r.content


def generate_test_audio(test):
    from pydub import AudioSegment
    import io

    transcript = test.get("transcript") or []
    if not transcript:
        print(f"  skip {test['id']}: no transcript")
        return None

    combined = AudioSegment.silent(duration=0)
    gap = AudioSegment.silent(duration=GAP_MS)

    for i, line in enumerate(transcript):
        voice_role = line.get("voiceId", "male-british")
        voice_id = VOICE_MAP.get(voice_role)
        if not voice_id or voice_id.startswith("REPLACE_ME"):
            raise RuntimeError(
                f"VOICE_MAP['{voice_role}'] is still a placeholder — run --list-voices "
                f"and fill in a real voice_id before generating audio."
            )
        print(f"  [{i+1}/{len(transcript)}] {line['speaker']} ({voice_role}): {line['text'][:60]}...")
        clip_bytes = tts_bytes(line["text"], voice_id)
        clip = AudioSegment.from_file(io.BytesIO(clip_bytes), format="mp3")
        combined += clip + gap
        time.sleep(0.2)  # be gentle on rate limits

    AUDIO_DIR.mkdir(exist_ok=True)
    out_path = AUDIO_DIR / f"{test['id']}.mp3"
    combined.export(out_path, format="mp3")
    print(f"  wrote {out_path} ({len(combined)/1000:.1f}s)")
    return f"audio/{out_path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--test-id", help="generate audio for a single test id")
    ap.add_argument("--all", action="store_true", help="generate audio for every test missing audioFile")
    args = ap.parse_args()

    if args.list_voices:
        list_voices()
        return

    data = json.loads(LISTENING_INDEX.read_text(encoding="utf-8"))
    tests = data["tests"]

    targets = []
    if args.test_id:
        targets = [t for t in tests if t["id"] == args.test_id]
        if not targets:
            sys.exit(f"No test with id {args.test_id}")
    elif args.all:
        targets = [t for t in tests if not t.get("audioFile")]
    else:
        ap.print_help()
        return

    for test in targets:
        print(f"Generating: {test['id']} — {test['title']}")
        rel_path = generate_test_audio(test)
        if rel_path:
            test["audioFile"] = rel_path

    LISTENING_INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nUpdated {LISTENING_INDEX}")


if __name__ == "__main__":
    main()
