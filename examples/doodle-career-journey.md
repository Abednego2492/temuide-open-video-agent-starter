# Recipe: "Kanvas hidup" doodle career journey

Fully animated vertical video (no camera footage needed) that tells a career story from a CV. One black ink thread travels across a giant sheet of crumpled cream paper; the camera follows a small walking character from station to station.

## Brief to give the agent

> Turn my CV into a career-journey video. Crumpled cream paper is the canvas of life, a black ink thread blends into the paper, handwriting looks written on the paper. Each job gets one funny workplace-reality line in my own words. A mini 2D cartoon of my face reacts with a different expression per stage, and walks along the thread between stages like travelling city to city. Open with a gimmick hook, end with a follow + comment CTA. Voiceover in my cloned voice, natural influencer tone.

Do **not** put phone numbers, email addresses or other private CV details on screen.

## Script first

Before building anything, write the script table: station, year, role, the reality line (funny, true, in the creator's voice), on-screen stamp (one proof number), character expression, VO line. Get the creator's own stories; invented anecdotes fall flat.

## Building blocks

- **World:** one tall paper image (e.g. 2160 × 9900) generated procedurally (crumple noise + fold lines), placed in world space.
- **Stations:** array of `{key, cx, cy, shape, year, role, real[], stamp, expr, side}`, alternating left/right, ≥ 1050 px apart so neighbours don't bleed into frame.
- **Thread:** each shape is a single resampled line (SVG path). Connectors between stations are wavy loops. Draw with `strokeDasharray` progress tied to the walker; ink look = SVG turbulence displacement + slight blur + `mix-blend-mode: multiply`.
- **Text:** year in a marker font, role in a handwriting font, reality lines typed per character in red marker, a rubber-stamp label that slams in. Show a station's text only during its own scene and again in the final reveal.
- **Mini character:** one SVG component with an `expr` prop (surprised, waving, relaxed, tired, referee, proud, sleepy, fired-up, up-late, cheering, thumbs-up, walking). Static face, only the expression and props change. Pop in with squash/stretch, peel away at scene end.
- **Camera:** hook zooms on a scribble that morphs into the face → follow the walker at ~0.82 zoom while travelling → ease into each station hold → final reveal pulls back to the whole thread ("messy, but every line connects") → push into the face for the CTA.
- **SFX:** footsteps while walking, pencil on draw, pop on character, typing, stamp slam, whoosh + ding on reveal.

## Let the voice drive the timeline

Generate the VO first (see `docs/VOICEOVER.md`), store frame lengths in `vo.json`, then compute station timing from it:

```ts
let t = HOOK_END;
ST.forEach((st, i) => {
  st.t0 = t;
  st.voAt = i === 0 ? t + 12 : t + 22;            // start talking while still walking in
  st.t1 = Math.max(st.voAt + VO[st.key] + 14, t + 140);
  t = st.t1;
});
```

Every scene then holds exactly as long as the line needs, and changing one line only shifts the scenes after it.

## Check before the full render

Contact sheet of: hook, each station mid-hold, reveal, CTA. Look for text overlapping props, characters cut off at the frame edge, and the reveal being too small to read on a phone.
