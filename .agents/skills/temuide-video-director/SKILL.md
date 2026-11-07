---
name: temuide-video-director
description: Use to plan, compose, render and critique videos from real media and visual references in a Remotion project.
---
# TEMUIDE Video Director

This skill guides the coding agent, not a standalone auto-editing model.

## Start
Read `AGENTS.md`, `BRIEF.md`, `src/project.json` and inventory `public/assets` / `public/references`. Run `npm run doctor`.

## Analyze before editing
1. Get FFprobe data for all video/audio files.
2. Watch, sample and describe actual source and reference scenes. Never invent observed material.
3. If there is speech, transcribe and align word boundaries with an available, verified tool; mark uncertain timestamps.
4. Select only complete, meaningful phrases.
5. Propose the strongest hook and context-matched B-roll.
6. Derive typography, colors, density, camera and transition grammar from the reference and content. Never force a preset.
7. Create an EDL and scene design contract. Record exact start/end frames and every major element's x/y/width/height/zIndex, text metrics and animation timing.

## Voiceover (optional)
If the brief asks for a voiceover, follow `docs/VOICEOVER.md`: model `eleven_v4`, audio tags for emotion, breath and pauses, numbers spelled out, English acronyms written phonetically. Transcribe every take back and keep the best. Generate the VO before timing scenes and let line lengths drive the timeline.

## Render
- Use Remotion frame time: `useCurrentFrame`, `spring`, `interpolate`.
- Never animate with uncontrolled browser timers.
- Preserve source media, original speech, product identity and factual claims.
- Keep one dominant focus per beat.
- Use only properly licensed music, sound effects and artwork.
- Run `npm run typecheck`, check `npm run stills` on hook / each scene / ending, then `npm run render` (or `npm run render:chunks`) and `npm run critic`.
- Master audio to about −14 LUFS integrated, true peak ≤ −1 dBTP. Measure A/V sync from fully decoded audio, not `-ss` seeks.

## Independent critic
Inspect the real MP4 at mobile viewing scale, plus transition boundaries and representative frames. Evaluate semantic continuity, visual hierarchy, text readability, B-roll relevance, mask quality, motion pacing, audio collisions, actual loudness and technical playback.
Log timestamped defects, revise and rerender with a finite retry budget.
Do not report professional quality from passing compile/FFprobe alone.

## Delivery
Return editable Remotion project, `output/final.mp4`, `output/critic-report.json`, and list of unresolved limitations. Never promise automatic advanced editing without verifying the needed toolchain.
