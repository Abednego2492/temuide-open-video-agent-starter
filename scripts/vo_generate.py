#!/usr/bin/env python3
"""Generate voiceover lines with ElevenLabs (default model: eleven_v4) and keep the best take per line.

Usage:
  python3 scripts/vo_generate.py LINES.json OUT_DIR [--takes 4] [--lang id] [--only key1 key2]

LINES.json is a list of {"key": "...", "text": "..."} objects. Text may contain Eleven v4 audio tags like [laughs].
Credentials come from the environment (or a local .env): ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, optional ELEVENLABS_MODEL.
If sherpa-onnx and a Whisper model are available, each take is transcribed and scored against the script.
The API key is never printed or written to disk.
"""
import argparse, difflib, json, os, re, subprocess, sys, time, urllib.error, urllib.request

TAGWORDS = {"laughs", "chuckles", "sighs", "exhales", "sarcastic", "playful", "excited", "curious", "tired", "pause",
            "softly", "proud", "warm", "friendly", "upbeat", "nostalgic", "storytelling", "determined", "exasperated", "reflective"}
STABILITIES = [0.35, 0.5, 0.25, 0.42, 0.3]


def load_env(path=".env"):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def tts(text, stability, key, voice, model, lang):
    body = {"text": text, "model_id": model,
            "voice_settings": {"stability": stability, "similarity_boost": 0.85, "style": 0.45, "use_speaker_boost": True}}
    if lang:
        body["language_code"] = lang
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


class Scorer:
    def __init__(self, lang):
        self.rec = None
        wdir = os.environ.get("WHISPER_DIR", "models/sherpa-onnx-whisper-small")
        try:
            import numpy  # noqa: F401
            import sherpa_onnx
            enc = next((f for f in os.listdir(wdir) if f.endswith("encoder.int8.onnx")), None)
            dec = next((f for f in os.listdir(wdir) if f.endswith("decoder.int8.onnx")), None)
            tok = next((f for f in os.listdir(wdir) if f.endswith("tokens.txt")), None)
            self.rec = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=os.path.join(wdir, enc), decoder=os.path.join(wdir, dec), tokens=os.path.join(wdir, tok),
                language=lang or "en", task="transcribe", num_threads=2)
        except Exception as e:  # scoring is optional
            print(f"(no transcription scoring: {type(e).__name__})", flush=True)

    def transcribe(self, path):
        import numpy as np
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", "apad=pad_dur=0.6", "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True).stdout
        s = self.rec.create_stream()
        s.accept_waveform(16000, np.frombuffer(pcm, np.float32))
        self.rec.decode_stream(s)
        return s.result.text.strip()


def words(t):
    return re.sub(r"[^a-z0-9 ]", " ", t.lower()).split()


def score(script, heard):
    spoken = re.sub(r"\[[^\]]*\]", " ", script)
    sc = difflib.SequenceMatcher(None, words(spoken), words(heard)).ratio()
    leaked = [w for w in words(heard) if w in TAGWORDS and w not in words(spoken)]
    return sc - 0.25 * len(leaked)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out")
    ap.add_argument("--takes", type=int, default=4)
    ap.add_argument("--lang", default="id")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--good", type=float, default=0.9, help="stop early once a take scores this high")
    a = ap.parse_args()

    load_env()
    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    model = os.environ.get("ELEVENLABS_MODEL", "eleven_v4")
    if not key or not voice:
        sys.exit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID (environment or .env).")
    lines = json.load(open(a.lines, encoding="utf8"))
    if a.only:
        lines = [l for l in lines if l["key"] in a.only]
    os.makedirs(a.out, exist_ok=True)
    scorer = Scorer(a.lang)
    print(f"model={model} lines={len(lines)} takes<={a.takes}", flush=True)

    for line in lines:
        k, text, best = line["key"], line["text"], None
        for n in range(a.takes):
            stab = STABILITIES[n % len(STABILITIES)]
            try:
                audio = tts(text, stab, key, voice, model, a.lang)
            except urllib.error.HTTPError as e:
                print(f"{k} take{n} HTTP {e.code}: {e.read()[:200]!r}", flush=True)
                time.sleep(2)
                continue
            tmp = os.path.join(a.out, f".{k}.take{n}.mp3")
            open(tmp, "wb").write(audio)
            if not scorer.rec:
                best = (1.0, tmp)
                break
            heard = scorer.transcribe(tmp)
            sc = score(text, heard)
            print(f"{k} take{n} stability={stab} score={sc:.2f} | {heard}", flush=True)
            if best is None or sc > best[0]:
                best = (sc, tmp)
            if sc >= a.good:
                break
        if best:
            os.replace(best[1], os.path.join(a.out, f"{k}.mp3"))
            print(f"KEEP {k} score={best[0]:.2f}", flush=True)
        for f in os.listdir(a.out):
            if f.startswith(f".{k}.take"):
                os.remove(os.path.join(a.out, f))


if __name__ == "__main__":
    main()
