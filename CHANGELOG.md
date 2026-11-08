# Changelog

## 0.3.0 — 2026-11-09

Kanvas Hidup template, usable by anyone without the author's story.

### Added
- `templates/kanvas-hidup/`: workflow README, STYLE_GUIDE, PROMPTS, REMIX guide, `story.template.json` and `vo-lines.template.json` with placeholders (Indonesian).
- `scripts/remix/remix.py` + `remix.example.json`: talking-head cutout over a sped-up background video. Stages: warm faded grade, background time-lapse, rembg masks (u2net_human_seg, optional isnet-general-use veto against dark background leaks, biggest-blob cleanup, temporal smoothing), compose with review-mode HUD, headlines (auto-fit), static captions, CTA pill, two-pass loudnorm to −14 LUFS. Resumable, `--preview` stills.
- npm script `remix`.

### Changed
- Example VO lines and the voiceover doc no longer contain the author's personal story; they use placeholders and a neutral example.
- `.gitignore` ignores `fonts/` and `models/`.

## 0.2.0 — 2026-11-07

Claude video editor workflow, tested on two real videos edited end to end from the Claude mobile app.

### Added
- `docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md`: sandbox setup (network access, reachable sources), verified toolchain (sherpa-onnx Whisper, YuNet, rembg, Remotion + local Chromium), edit order, and the gotchas we hit.
- `docs/VOICEOVER.md` + `scripts/vo_generate.py`: ElevenLabs **Eleven v4** voiceover with a voice clone, audio tags for emotion/breath/pauses, best-of-N takes scored by transcription, pronunciation fixes for English acronyms in Indonesian lines.
- `scripts/render_chunks.sh`: resumable chunked render (muted video parts + one audio pass), lossless join, −14 LUFS mastering and mux.
- `scripts/stills.mjs`: render a few frames to check layout before a full render.
- `examples/doodle-career-journey.md`: "Kanvas hidup" recipe (ink thread on crumpled paper, walking mini character, VO-driven timeline).
- `examples/live-edit-mode.md`: "Live edit mode" talking-head style.
- `examples/vo-lines.example.json`: sample VO script with audio tags.
- npm scripts `vo`, `render:chunks`, `stills`.

### Changed
- `.env.example` documents the ElevenLabs variables.
- Agent skill and AGENTS.md now point to the workflow, voiceover and quality steps.

## 0.1.0

Initial agent-assisted Remotion starter: starter composition, asset mapping, preview/render scripts, technical critic, agent instructions.
