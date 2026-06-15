#!/usr/bin/env python3
"""Robust TTS for demo narration — per-beat retries + idempotent (skips clips already made).

Same output contract as the skill's tts.py (clip_NNN.mp3 + manifest.json) so the assembler
works unchanged. Reads OPENAI_API_KEY from env. Usage:
  python scripts/gen_tts.py demo/script.md demo/audio [voice] [model]
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

API = "https://api.openai.com/v1/audio/speech"
KEY = os.environ.get("OPENAI_API_KEY", "")


def beats_from(path):
    raw = open(path).read()
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    out = []
    for blk in re.split(r"\n\s*\n", raw):
        lines = [ln for ln in blk.splitlines() if not ln.lstrip().startswith("#")]
        text = re.sub(r"\s+", " ", " ".join(l.strip() for l in lines)).strip()
        if text:
            out.append({"id": len(out) + 1, "text": text})
    return out


def synth(text, voice, model, attempts=5):
    body = json.dumps({"model": model, "voice": voice, "input": text,
                       "response_format": "mp3"}).encode()
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"   retry {i+1}/{attempts} after error: {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"TTS failed after {attempts} attempts: {last}")


def dur(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "quiet", "-of", "json", "-show_format", path],
                             capture_output=True, text=True, check=True)
        return round(float(json.loads(out.stdout)["format"]["duration"]), 2)
    except Exception:
        return 4.0


def main():
    script, outdir = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "sage"
    model = sys.argv[4] if len(sys.argv) > 4 else "gpt-4o-mini-tts"
    os.makedirs(outdir, exist_ok=True)
    beats = beats_from(script)
    manifest = []
    for b in beats:
        fn = os.path.join(outdir, f"clip_{b['id']:03d}.mp3")
        if os.path.exists(fn) and os.path.getsize(fn) > 1000:
            print(f"beat {b['id']:>2}: exists, skip")
        else:
            print(f"beat {b['id']:>2}: synth ({len(b['text'].split())} words)")
            data = synth(b["text"], voice, model)
            open(fn, "wb").write(data)
        manifest.append({"id": b["id"], "file": os.path.basename(fn),
                         "seconds": dur(fn), "text": b["text"]})
    json.dump(manifest, open(os.path.join(outdir, "manifest.json"), "w"), indent=2)
    total = sum(m["seconds"] for m in manifest)
    print(f"DONE {len(manifest)} beats, {round(total,1)}s ({round(total/60,2)}min)")


if __name__ == "__main__":
    main()
