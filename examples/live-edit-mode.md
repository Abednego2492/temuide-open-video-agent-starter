# Recipe: "Live edit mode" talking-head style

The video looks like it is being edited live by the AI in front of the viewer. Built for an AI-education creator; works for any talking head about tools or workflows.

## Look

- Colours: near-black `#05070B` + lime `#C6FF00`; red `#FF3B30` only for errors.
- Fonts: Anton (headlines), Inter 900 (captions), JetBrains Mono (HUD/UI).
- HUD: lime frame corners, a `LIVE EDIT · claude` label with timecode, a clip timeline with a playhead near the bottom that stops and turns red on a freeze.

## Motion grammar

- A white cursor moves to each layer and clicks (lime ripple + click SFX) exactly on the word that triggers it.
- Captions are a command bar `›`: words appear as they are spoken, the active word in lime, a blinking block cursor.
- New headlines appear with a selection box, handles and a `text.layer` label. Sections are toggle switches (`reason_n n/3`).
- A face-lock bracket on the face at the hook, each new section, and freezes.
- "Error" beat: freeze + desaturate, a caption drops onto the head, rough red box + toast `caption overlap: subject`, the cursor drags it to the command bar, toast `moved to safe zone`. Label it as an illustration if it is a re-enactment.
- CTA actions are UI: save/share buttons switch to "saved/shared", a comment box types and sends, the FOLLOW button is clicked and becomes `FOLLOWING ✓`, ending on `render complete ✓`.
- The presenter slides down ~380 px onto a dot-grid canvas whenever a layer opens above.

## Needs

Word-level timing (for cursor clicks and captions), face boxes (YuNet), and a person matte for any text that passes behind the head. See `docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md`.
