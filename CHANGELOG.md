# Changelog

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
