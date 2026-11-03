# TEMUIDE Open Video Agent Starter 🎬

Turn a coding agent into a reference-driven video editing assistant in your own repository.

**What works:** a Remotion starter composition, asset mapping, local preview and render scripts, a technical critic, and agent instructions. **What is not automatic yet:** semantic trimming, reference-style inference, matting, 3D motion, and professional creative review. The agent must implement and test those workflows for your footage. A successful MP4 render is not proof of editorial quality.

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

Read [installation](docs/INSTALL.md), [editing contract](docs/EDITING_CONTRACT.md), [quality gates](docs/QUALITY_GATES.md), and [agent prompts](docs/AGENT_PROMPTS.md).

## Commands

| Command | Purpose |
|---|---|
| `npm run doctor` | Verify dependencies and timeline |
| `npm test` | Run code-level tests |
| `npm run assets` | Map media to starter scenes |
| `npm run dev` | Remotion Studio preview |
| `npm run render` | Render `output/final.mp4` |
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
- `output/`: renders and reports, not committed.

## License and costs

The code authored in this repository is MIT licensed. Remotion and other dependencies retain **their own licenses**. Review [Remotion licensing](https://www.remotion.dev/docs/license/pricing) for commercial video automation. Local AI agents, API inference, GPU, cloud rendering, footage, and music may have additional costs.

## ⭐ Useful?

If this starter helped your agent render its first video, a GitHub Star is a nice way to support future work. Totally optional.

[⭐ Star this repository](https://github.com/Abednego2492/temuide-open-video-agent-starter)

## TEMUIDE GEN AI

Want a managed workflow for content creation and supported social publishing without maintaining a codebase? [Explore TEMUIDE GEN AI](https://app.temuidegenai.com/start). Platform availability depends on connected accounts and integrations.
