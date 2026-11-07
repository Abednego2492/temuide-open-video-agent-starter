# Agent instructions

Read `.agents/skills/temuide-video-director/SKILL.md`, `BRIEF.md`, `docs/EDITING_CONTRACT.md` and `docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md` before editing. For voiceover, read `docs/VOICEOVER.md`.

1. Audit available media and capabilities.
2. Analyze the actual user brief and references. Do not invent reference findings.
3. Identify the strongest complete message or visual story.
4. Produce an edit plan with exact frame ranges, scene geometry, typography, color, and sound.
5. Modify the Remotion composition using real media only.
6. Check stills (`npm run stills`), then render `output/final.mp4` (use `npm run render:chunks` for long videos or unstable sandboxes). Do not equate successful compilation with finished editing.
7. Run `npm run critic`, inspect actual video/audio and append timestamped visual findings.
8. Revise specific issues and rerender, with a bounded retry count.

Never claim a feature works unless it is present, supported, and tested. Preserve original media. Do not invent publishing metrics or fake footage. Do not upload private footage to external providers without authorization.
Never print, log or commit API keys; read them from the environment or `.env`.
