# Voiceover with ElevenLabs Eleven v4

`scripts/vo_generate.py` turns a JSON list of lines into one audio file per line with your own voice clone, then transcribes every take and keeps the one that best matches the script.

## Setup

```bash
cp .env.example .env            # never commit .env
# fill ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID
pip install sherpa-onnx numpy   # optional, enables take scoring
```

Use a **restricted, short-lived API key** with text-to-speech permission only, and revoke it after the job. The script reads it from the environment and never writes it to disk or logs.

Speech scoring uses `sherpa-onnx-whisper-small` (download from the k2-fsa GitHub releases into `models/` or set `WHISPER_DIR`). Without it, the script keeps the first successful take.

## Run

```bash
python3 scripts/vo_generate.py examples/vo-lines.example.json public/vo --takes 4 --lang id
python3 scripts/vo_generate.py examples/vo-lines.example.json public/vo --only hook cta   # redo some lines
```

The model defaults to `eleven_v4` (`ELEVENLABS_MODEL` overrides it). Use v4 for narration; `eleven_v4_turbo` is meant for real-time agents.

## Make it sound human, not "AI VO"

Eleven v4 reads **audio tags** in square brackets as performance direction, not as words:

- Emotion / delivery: `[playful]`, `[warm, friendly]`, `[sarcastic]`, `[excited]`, `[softly, reflective]`, `[building energy]`
- Reactions and breath: `[laughs]`, `[chuckles]`, `[sighs]`, `[exhales]`, `[gasps]`
- Pace: `[short pause]`, `[long pause]`, `...` for a short beat

Write the line the way you would *say* it to a friend, then direct it like a talent:

```text
[storytelling, amused] Hari pertama kerja... salah masuk ruang meeting, langsung disuruh presentasi! [chuckles]
[sarcastic] Ya udah... presentasi aja. [laughs]
```

Other settings that helped: `stability` 0.25–0.5 (lower = more expressive; the script cycles through several), `style` 0.45, `similarity_boost` 0.85, `language_code: "id"` for Indonesian.

## Pronunciation fixes

- Spell numbers the way you say them ("tiga puluh enam jam", not "36 jam").
- English acronyms inside an Indonesian line get read letter by letter. Write them phonetically for the target language: `AI` → `Ei-Ai`, `GM` → `G-M`.
- Fix one line at a time with `--only <key>` and keep the rest of the takes.

## QA

The script prints the transcript and a 0–1 match score per take, and penalises takes where a tag was read out loud. A low score is not always a bad take: digits vs spelled numbers and English words in Indonesian mode lower the score. Listen to the flagged lines, or re-check them with an English transcription.

After generating, level every line the same way before placing it in the timeline, for example:

```bash
ffmpeg -i public/vo/line.mp3 -af "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 public/vo_n/line.wav
```

Then let the voice drive the timeline: each scene holds until its line has finished (see `examples/doodle-career-journey.md`).

## Plan notes

`output_format=mp3_44100_192` needs a higher plan tier; `mp3_44100_128` works on all plans. A key without `voices_read` permission can still synthesise with a known voice ID.
