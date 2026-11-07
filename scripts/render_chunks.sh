#!/usr/bin/env bash
# Render a Remotion composition in resumable chunks, then join, master and mux.
# Usage: COMP=DynamicEdit TOTAL=3609 [CHUNK=1350] [ENTRY=src/index.ts] [OUT=output/final.mp4] bash scripts/render_chunks.sh
# Optional: BROWSER=/path/to/chrome (adds --browser-executable), CONCURRENCY=2, LUFS=-14
set -euo pipefail
COMP=${COMP:?set COMP to the composition id}
TOTAL=${TOTAL:?set TOTAL to the composition duration in frames}
CHUNK=${CHUNK:-1350}
ENTRY=${ENTRY:-src/index.ts}
OUT=${OUT:-output/final.mp4}
CONCURRENCY=${CONCURRENCY:-2}
LUFS=${LUFS:--14}
PARTS=output/parts
mkdir -p "$PARTS"
EXTRA=()
if [ -n "${BROWSER:-}" ]; then EXTRA+=(--browser-executable="$BROWSER"); fi

: > "$PARTS/list.txt"
i=0
for ((start = 0; start < TOTAL; start += CHUNK)); do
  end=$((start + CHUNK - 1)); ((end >= TOTAL)) && end=$((TOTAL - 1))
  part="$PARTS/p$i.mp4"
  if [ -s "$part" ]; then
    echo "skip $part (exists)"
  else
    echo "render frames $start-$end -> $part"
    npx remotion render "$ENTRY" "$COMP" "$part" --frames="$start-$end" --muted --codec=h264 --crf=17 \
      --pixel-format=yuv420p --concurrency="$CONCURRENCY" "${EXTRA[@]}"
  fi
  echo "file 'p$i.mp4'" >> "$PARTS/list.txt"
  i=$((i + 1))
done

if [ ! -s "$PARTS/audio.wav" ]; then
  echo "render audio"
  npx remotion render "$ENTRY" "$COMP" "$PARTS/audio.wav" --codec=wav --concurrency="$CONCURRENCY" "${EXTRA[@]}"
fi

ffmpeg -v error -y -f concat -safe 0 -i "$PARTS/list.txt" -c copy "$PARTS/video.mp4"
ffmpeg -v error -y -i "$PARTS/audio.wav" -af "alimiter=limit=0.89:level=false,loudnorm=I=$LUFS:TP=-1.2:LRA=11" -ar 48000 "$PARTS/audio_m.wav"
ffmpeg -v error -y -i "$PARTS/video.mp4" -i "$PARTS/audio_m.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart "$OUT"

frames=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$OUT" | tr -d ',')
echo "frames: $frames / $TOTAL"
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tail -2
echo "done -> $OUT"
