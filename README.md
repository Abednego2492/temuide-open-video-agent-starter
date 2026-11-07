# TEMUIDE Open Video Agent Starter 🎬

![version](https://img.shields.io/badge/version-0.2.0-C6FF00) ![remotion](https://img.shields.io/badge/remotion-4.0.539-111) ![voice](https://img.shields.io/badge/voiceover-ElevenLabs%20v4-111)

Turn a coding agent into a reference-driven video editing assistant in your own repository.

**What works:** a Remotion starter composition, asset mapping, local preview and render scripts, a technical critic, and agent instructions. **What is not automatic yet:** semantic trimming, reference-style inference, matting, 3D motion, and professional creative review. The agent must implement and test those workflows for your footage. A successful MP4 render is not proof of editorial quality.

## What's new in 0.2.0: Claude video editor workflow

The workflow used to edit real videos end to end with Claude, operated from a phone:

- **[Claude video editor workflow](docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md):** set up the sandbox, the verified toolchain (Whisper transcription, face detection, person cutout, Remotion), the edit order, and the mistakes to avoid.
- **[Voiceover with Eleven v4](docs/VOICEOVER.md):** your own voice clone, audio tags for emotion, breath and pauses, best-of-N takes checked by transcription. `npm run vo -- examples/vo-lines.example.json public/vo`
- **Resumable chunked render:** `COMP=DynamicEdit TOTAL=180 npm run render:chunks` renders in parts, joins them, masters audio to −14 LUFS and muxes.
- **Layout check before rendering:** `COMP=DynamicEdit npm run stills -- 0 90 150`
- **Style recipes:** [doodle career journey](examples/doodle-career-journey.md) and [live edit mode](examples/live-edit-mode.md).

Full list in the [changelog](CHANGELOG.md).

## Quick start

Requires Node.js 20+, npm, Git. FFmpeg and FFprobe are recommended.

```bash
git clone https://github.com/Abednego2492/temuide-open-video-agent-starter.git
cd temuide-open-video-agent-starter
npm install
npm run doctor
npm test
npm run dev
```

1. Put real clips and images in `public/assets/`.
2. Put reference videos/images in `public/references/`.
3. Edit `BRIEF.md` in your own words.
4. Tell AGY / Codex / Claude Code to **read AGENTS.md** and follow its skill.
5. Run `npm run assets` to map local media to the starter scenes (this is NOT an intelligent edit).
6. Have the agent implement the real edit, then run `npm run render` and `npm run critic`.
7. Watch `output/final.mp4` and ask for timestamped corrections. The critic produces a **technical** report and leaves creative approval pending.

Read [installation](docs/INSTALL.md), [Claude video editor workflow](docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md), [voiceover](docs/VOICEOVER.md), [editing contract](docs/EDITING_CONTRACT.md), [quality gates](docs/QUALITY_GATES.md), and [agent prompts](docs/AGENT_PROMPTS.md).

## Commands

| Command | Purpose |
|---|---|
| `npm run doctor` | Verify dependencies and timeline |
| `npm test` | Run code-level tests |
| `npm run assets` | Map media to starter scenes |
| `npm run dev` | Remotion Studio preview |
| `npm run render` | Render `output/final.mp4` |
| `npm run render:chunks` | Resumable chunked render + audio master (`COMP`, `TOTAL` env) |
| `npm run stills -- <frames>` | Render a few frames to `output/stills/` |
| `npm run vo -- <lines.json> <outdir>` | ElevenLabs Eleven v4 voiceover with take scoring |
| `npm run critic` | Probe video and write `output/critic-report.json` |
| `npm run typecheck` | TypeScript validation |

## Install optional editor capabilities

The full creative stack is **not bundled**. Agent may add verified integrations from the official ecosystems for `three`, `@react-three/fiber`, `@remotion/three`, `gsap`, motion blur, captions, WhisperX, PySceneDetect, or matting. See [INSTALL](docs/INSTALL.md). Don't install heavyweight GPU dependencies unless the job needs them.

## Folder map

- `.agents/skills/temuide-video-director/SKILL.md`: project-local agent guidance.
- `BRIEF.md`: edit request.
- `public/assets/`: user assets, not committed.
- `public/references/`: editing references, not committed.
- `src/project.json`: editable scene timeline.
- `src/video.tsx`: starter composition.
- `output/`: renders, stills and reports, not committed.
- `scripts/`: doctor, assets, critic, stills, chunked render, voiceover.
- `examples/`: briefs, style recipes and a sample VO script.
- `.env`: your local API keys (copy from `.env.example`), never committed.

## License and costs

The code authored in this repository is MIT licensed. Remotion and other dependencies retain **their own licenses**. Review [Remotion licensing](https://www.remotion.dev/docs/license/pricing) for commercial video automation. Local AI agents, API inference, GPU, cloud rendering, footage, and music may have additional costs.

## ⭐ Useful?

If this starter helped your agent render its first video, a GitHub Star is a nice way to support future work. Totally optional.

[⭐ Star this repository](https://github.com/Abednego2492/temuide-open-video-agent-starter)

## TEMUIDE GEN AI

Want a managed workflow for content creation and supported social publishing without maintaining a codebase? [Explore TEMUIDE GEN AI](https://app.temuidegenai.com/start). Platform availability depends on connected accounts and integrations.
