# Install and first edit

## 1. Prerequisites
Node.js 20+, npm, Git, and a compatible coding agent (AGY, Codex, Claude Code or similar). Install FFmpeg and FFprobe for technical video inspection. Check license requirements before commercial automation.

## 2. Clone and install
```bash
git clone https://github.com/Abednego2492/temuide-open-video-agent-starter.git
cd temuide-open-video-agent-starter
npm install
npm run doctor
npm test
```

## 3. Enable agent skills
Open the cloned project in the coding agent. Instruct it: "Read AGENTS.md and .agents/skills/temuide-video-director/SKILL.md". Optionally install official Remotion agent skills using `npx remotion skills add` after checking the installed CLI's supported command.

## 4. Provide media
Put videos and images in `public/assets/`, style references in `public/references/`. Edit `BRIEF.md`. Do not commit private footage. Run `npm run assets` to map clips into sample scenes.

## 5. Preview, edit, render
```bash
npm run dev
npm run render
npm run critic
```
Ask your agent to change `src/video.tsx` and `src/project.json` based on the actual media and references. The default composition is only a pipeline smoke test; existing video layers are muted. To preserve dialogue the agent must implement and test correct audio routing.

## 6. Optional tools
Only install features a scene really needs. Optional: `three`, `@react-three/fiber`, `@react-three/drei`, `gsap`, `@remotion/three`, `@remotion/transitions`, `@remotion/captions`; Python `scenedetect`, `whisperx`, `opencv-python`, `librosa`. Use `npx remotion add <package>` for Remotion packages to keep versions aligned. GPU matting and heavy models should be separate optional workers.

## Troubleshooting
- No MP4: `npm run doctor`, verify Chromium/dependencies, check render stderr.
- Media missing: verify exact filenames and `public/assets/`.
- Type errors: `npm run typecheck`.
- Silent video: baseline clips are muted by design. Ask agent to implement voice audio.
- Black alpha: verify actual alpha decoding in rendered frames.
- Flat/slideshow result: agent hasn't completed reference and semantic editing; fix plan and layout, not just more effects.
