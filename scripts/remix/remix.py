#!/usr/bin/env python3
"""Kanvas Hidup remix: talking-head cutout over a sped-up (time-lapse) story video.

Stages (each one is skipped when its output already exists, so a stopped run resumes):
  1. grade   - warm + faded grade of the talking-head clip, 30 fps
  2. bg      - background video sped up to fill the talking-head duration
  3. masks   - person masks with rembg (u2net_human_seg), optional ISNet veto pass
  4. compose - background + cutout + HUD + headlines + captions, piped to ffmpeg
  5. mux     - talking-head audio, loudness -14 LUFS

Usage:
  python3 scripts/remix/remix.py scripts/remix/remix.example.json
  python3 scripts/remix/remix.py my.json --preview 2,6,12   # stills only, no full render
"""
import json, math, os, subprocess, sys, argparse
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30


def run(cmd):
    print("$", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


def probe_duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def done(p): return os.path.exists(p) and os.path.getsize(p) > 0


# ---------------------------------------------------------------- stages 1-2
GRADE = ("colortemperature=temperature={temp}:mix=0.7:pl=0.6,eq=contrast=0.97:saturation=1.02,"
         "colorbalance=rm=0.04:bm=-0.03:rh=0.05:bh=-0.07,"
         "curves=master='0/{black} 0.25/0.29 0.5/0.53 0.75/0.76 1/{white}',"
         "vignette=angle=PI/4.8,noise=alls=5:allf=t+u,format=yuv420p")


def stage_grade(cfg, wd):
    out = wd + "cam_graded.mp4"
    if done(out): return out
    g = cfg.get("grade", {})
    vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}," + GRADE.format(
        temp=g.get("temperature", 4600), black=g.get("fade_black", 0.09), white=g.get("fade_white", 0.93))
    tmp = wd + "cam_graded.tmp.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", cfg["talking_head"], "-t", str(cfg["duration"]), "-vf", vf,
         "-an", "-c:v", "libx264", "-crf", "15", "-preset", "veryfast", tmp])
    os.rename(tmp, out); return out


def stage_bg(cfg, wd):
    """intro_seconds of the background play at intro_speed (the hook), the rest is squeezed into what is left."""
    out = wd + "bg_fast.mp4"
    if done(out): return out
    src = cfg["background"]; total = probe_duration(src); dur = cfg["duration"]
    b = cfg.get("background_timing", {})
    intro_src = b.get("intro_seconds", 6.6); intro_speed = b.get("intro_speed", 2.0)
    intro_out = intro_src / intro_speed
    rest_speed = (total - intro_src) / max(0.1, dur - intro_out)
    cfg["_bg_map"] = [intro_src, intro_speed, intro_out, rest_speed, total]
    warm = "colortemperature=temperature=5200:mix=0.5,curves=master='0/0.06 0.5/0.52 1/0.95',vignette=angle=PI/5.2"
    norm = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "0", "-t", str(intro_src), "-i", src, "-vf",
         f"setpts=PTS/{intro_speed},fps={FPS},{norm},format=yuv420p", "-an", "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", wd + "bg1.mp4"])
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(intro_src), "-i", src, "-vf",
         f"setpts=PTS/{rest_speed:.4f},fps={FPS},{norm},format=yuv420p", "-an", "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", wd + "bg2.mp4"])
    with open(wd + "bg_list.txt", "w") as f: f.write("file bg1.mp4\nfile bg2.mp4\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", wd + "bg_list.txt", "-c", "copy", wd + "bg_join.mp4"])
    tmp = wd + "bg_fast.tmp.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", wd + "bg_join.mp4", "-t", str(dur), "-vf", warm + ",format=yuv420p",
         "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", tmp])
    os.rename(tmp, out); return out


def bg_source_time(cfg, t):
    intro_src, intro_speed, intro_out, rest_speed, total = cfg["_bg_map"]
    if t < intro_out: return t * intro_speed
    return min(total, intro_src + (t - intro_out) * rest_speed)


# ---------------------------------------------------------------- stage 3
def stage_masks(cfg, wd, cam):
    mdir = wd + "masks/"; os.makedirs(mdir, exist_ok=True)
    n = int(round(cfg["duration"] * FPS))
    if os.path.exists(mdir + f"m{n - 1:04d}.png"): return mdir
    from rembg import new_session, remove
    sess = new_session("u2net_human_seg")
    veto = new_session("isnet-general-use") if cfg.get("mask", {}).get("isnet_veto", False) else None
    cap = cv2.VideoCapture(cam); prev = None; f = 0; v_prev = None
    k9 = np.ones((9, 9), np.uint8)
    while True:
        ok, fr = cap.read()
        if not ok: break
        p = mdir + f"m{f:04d}.png"
        small = cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA)
        if os.path.exists(p): prev = cv2.imread(p, 0).astype(np.float32); f += 1; continue
        rgb = Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        m = np.array(remove(rgb, session=sess, only_mask=True, post_process_mask=True)).astype(np.float32)
        if prev is not None: m = 0.65 * m + 0.35 * prev     # temporal smoothing against flicker
        prev = m.copy()
        if veto is not None:
            # u2net sometimes drags dark background next to the head; ISNet (every 3rd frame) vetoes it
            if f % 3 == 0 or v_prev is None:
                v_prev = cv2.dilate(np.array(remove(rgb, session=veto, only_mask=True)), k9)
            lum = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            m[~((v_prev > 40) | (lum > 95))] = 0
        bw = (m > 128).astype(np.uint8)
        cnt, lab, st, _ = cv2.connectedComponentsWithStats(bw)
        if cnt > 1:                                          # keep the biggest blob only
            big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m[(lab != big) & (lab != 0)] = 0
        cv2.imwrite(p, cv2.GaussianBlur(m, (3, 3), 0).astype(np.uint8))
        f += 1
        if f % 60 == 0: print("mask", f, "/", n, flush=True)
    return mdir


# ---------------------------------------------------------------- drawing helpers
def clamp01(x): return max(0.0, min(1.0, x))
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp01(x); return 3 * x * x - 2 * x ** 3
def back_out(x, s=1.7): x = clamp01(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def text_layer(lines, fnt, fills, align="left", stroke=0, pad=36, gap=1.2):
    tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    bs = [tmp.textbbox((0, 0), l, font=fnt, stroke_width=stroke) for l in lines]
    lh = int(fnt.size * gap); wmax = max(b[2] - b[0] for b in bs)
    im = Image.new("RGBA", (wmax + pad * 2, lh * len(lines) + pad * 2), (0, 0, 0, 0))
    def xo(b): return (wmax - (b[2] - b[0])) if align == "right" else ((wmax - (b[2] - b[0])) // 2 if align == "center" else 0)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); y = pad
    for l, b in zip(lines, bs):
        sd.text((pad + xo(b) - b[0] + 3, y - b[1] + 5), l, font=fnt, fill=(0, 0, 0, 220), stroke_width=stroke + 3, stroke_fill=(0, 0, 0, 220)); y += lh
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(im); y = pad
    for l, b, c in zip(lines, bs, fills):
        d.text((pad + xo(b) - b[0], y - b[1]), l, font=fnt, fill=c + (255,), stroke_width=stroke, stroke_fill=(20, 16, 10, 255)); y += lh
    return im


def chip(txt, fnt, bg, fg, padx=24, pady=14):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1))); b = tmp.textbbox((0, 0), txt, font=fnt)
    w, h = b[2] - b[0] + padx * 2, b[3] - b[1] + pady * 2
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((20, 26, 20 + w, 26 + h), h // 2, fill=(0, 0, 0, 110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg)
    d.text((20 + padx - b[0], 20 + pady - b[1]), txt, font=fnt, fill=fg + (255,))
    return im


def paste(img, L, x, y, alpha=1.0, scale=1.0, anchor="lt"):
    if alpha <= 0: return
    if scale != 1.0: L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.LANCZOS)
    if alpha < 1.0:
        L = L.copy(); L.putalpha(L.getchannel("A").point(lambda v: int(v * alpha)))
    if anchor in ("ct", "cc"): x -= L.width // 2
    if anchor == "rt": x -= L.width
    if anchor == "cc": y -= L.height // 2
    img.alpha_composite(L, (int(x), int(y)))


# ---------------------------------------------------------------- stage 4
def stage_compose(cfg, wd, cam, bg, mdir, preview=None):
    out_tmp = wd + "video.tmp.mp4"; out = wd + "video.mp4"
    if preview is None and done(out): return out
    S = cfg["style"]; fonts = S["fonts"]
    accent = rgb(S.get("accent", "#C6FF00")); white = (255, 255, 255); ink = rgb(S.get("ink", "#05070B"))
    head_f = lambda size: load_font(fonts["headline"], size, fonts.get("headline_weight"))
    cap_f = load_font(fonts["caption"], S.get("caption_size", 44), fonts.get("caption_weight"))
    ui_f = load_font(fonts["ui"], 28); ui_s = load_font(fonts["ui"], 22)

    heads = []
    for h in cfg.get("headlines", []):
        lines = h["lines"]; size = h.get("size", 140)
        layers = []
        for i, l in enumerate(lines):
            col = [accent if (i == len(lines) - 1 and len(lines) > 1) or h.get("accent") else white]
            sz = size
            L = text_layer([l], head_f(sz), col)
            while L.width - 72 > W - 120 and sz > 40:      # auto-fit: keep every line inside the frame
                sz = int(sz * 0.92); L = text_layer([l], head_f(sz), col)
            layers.append(L)
        heads.append(dict(h, layers=layers))
    caps = [dict(c, L=text_layer(c["lines"], cap_f, [white] * len(c["lines"]), align="right", stroke=3, pad=30)) for c in cfg.get("captions", [])]
    cta = cfg.get("cta"); cta_L = chip(cta["text"], load_font(fonts["ui"], 46), accent + (255,), ink) if cta else None

    P = cfg.get("presenter", {}); ps = P.get("scale", 0.70); px, py = P.get("x", -20), P.get("y", 636)
    t_in = P.get("enter_at", 3.3); PW, PH = int(W * ps), int(H * ps)
    hud_cfg = cfg.get("hud", {}); hud_on = hud_cfg.get("enabled", True)
    hud = chip("●  " + hud_cfg.get("label", "REVIEW MODE"), ui_f, (5, 7, 11, 215), accent)
    hud_file = chip(hud_cfg.get("file_label", "kanvas_hidup.mp4"), ui_f, (5, 7, 11, 215), (170, 176, 186))
    bg_total = cfg["_bg_map"][4]
    shade = np.clip((np.arange(H) - 1500) / 420, 0, 1)[:, None] * 150
    shade = Image.fromarray(np.dstack([np.full((H, W), c, np.uint8) for c in ink] + [np.repeat(shade, W, 1).astype(np.uint8)]), "RGBA")

    N = int(round(cfg["duration"] * FPS))
    prev_frames = set(int(float(x) * FPS) for x in preview) if preview else set()
    pipe = None if preview else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                                  "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", out_tmp], stdin=subprocess.PIPE)
    kv, hv = cv2.VideoCapture(bg), cv2.VideoCapture(cam)
    flags = [(h["start"], h["end"]) for h in heads if h.get("dim_background", True)]
    for f in range(N):
        ok1, kb = kv.read(); ok2, hb = hv.read()
        if not (ok1 and ok2): break
        if preview and f > max(prev_frames): break
        if preview and f not in prev_frames: continue
        t = f / FPS
        # hook camera: push-in on the background, snap back with overshoot when the presenter enters
        s = 1.0 + 0.10 * ease_in_out(t / t_in) if t < t_in else (1.10 - 0.10 * back_out((t - t_in) / 0.65, 2.2) if t < t_in + 0.65 else 1.0)
        if abs(s - 1) > 0.002:
            M = np.float32([[s, 0, 540 * (1 - s) + 5 * math.sin(t * 0.9)], [0, s, 700 * (1 - s)]])
            kb = cv2.warpAffine(kb, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        dim = 0.0
        for a, b in flags:
            if a <= t < b: dim = 0.55 * min(ease_out((t - a) / 0.2), 1 - ease_in_out((t - (b - 0.25)) / 0.25) if t > b - 0.25 else 1)
        if dim: kb = (kb.astype(np.float32) * (1 - dim)).astype(np.uint8)
        img = Image.fromarray(cv2.cvtColor(kb, cv2.COLOR_BGR2RGB)).convert("RGBA")

        if t >= t_in:
            p = back_out((t - t_in) / 0.55, 1.3); a = ease_out((t - t_in) / 0.3)
            sh = shade.copy(); sh.putalpha(sh.getchannel("A").point(lambda v: int(v * a))); img.alpha_composite(sh)
            m = cv2.GaussianBlur(cv2.resize(cv2.imread(mdir + f"m{f:04d}.png", 0), (PW, PH)), (5, 5), 0)
            cut = Image.fromarray(cv2.cvtColor(cv2.resize(hb, (PW, PH), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)).convert("RGBA")
            cut.putalpha(Image.fromarray(m)); img.alpha_composite(cut, (px, int(py + (1 - p) * 420)))
            if hud_on:
                hx = 40 - (1 - p) * 300; bt = bg_source_time(cfg, t)
                paste(img, hud, hx, 72); paste(img, hud_file, hx + hud.width - 24, 72)
                tc = lambda v: f"{int(v) // 60:02d}:{int(v) % 60:02d}"
                paste(img, chip(f"{tc(bt)} / {tc(bg_total)}", ui_f, (5, 7, 11, 215), (170, 176, 186)), 1040, 72, anchor="rt")
                d = ImageDraw.Draw(img); x0, x1, y = 60, 1020, 168; xp = x0 + (x1 - x0) * bt / bg_total
                d.rounded_rectangle((x0, y - 3, x1, y + 3), 3, fill=(5, 7, 11, 160)); d.rounded_rectangle((x0, y - 3, xp, y + 3), 3, fill=accent + (255,))
                d.ellipse((xp - 9, y - 9, xp + 9, y + 9), fill=accent + (255,))
                spd = cfg["_bg_map"][1] if t < cfg["_bg_map"][2] else cfg["_bg_map"][3]
                d.text((60, 186), f"speed {spd:.1f}x   ·   {hud_cfg.get('cam_label', 'cam 01')}", font=ui_s, fill=(5, 7, 11, 200))

        for h in heads:
            if not (h["start"] <= t < h["end"]): continue
            a_out = 1 - ease_in_out((t - (h["end"] - 0.25)) / 0.25) if t > h["end"] - 0.25 else 1
            for i, L in enumerate(h["layers"]):
                st = h["start"] + i * h.get("stagger", 0.6)
                if t < st: continue
                sc = 1.3 - 0.3 * back_out((t - st) / 0.3, 1.6)
                y0 = h.get("y", 420) + sum(int(h["layers"][j].height * 0.78) for j in range(i))
                paste(img, L, h.get("x", 540), y0, min(ease_out((t - st) / 0.22), a_out), sc,
                      anchor="ct" if h.get("x", 540) == 540 else "lt")

        if cta and t >= cta["start"]:
            a = ease_out((t - cta["start"]) / 0.25); sc = 1.15 - 0.15 * back_out((t - cta["start"]) / 0.35, 1.6)
            paste(img, cta_L, cta.get("x", 1030), cta.get("y", 530), a, sc, anchor="rt")
        for i, c in enumerate(caps):
            nxt = caps[i + 1]["start"] if i + 1 < len(caps) else 1e9
            if c["start"] <= t < min(c["end"] + 0.2, nxt):
                a = min(ease_out((t - c["start"]) / 0.15), 1 - ease_in_out((t - c["end"]) / 0.2) if t > c["end"] else 1)
                paste(img, c["L"], c.get("x", 1030), c.get("y", 630), a, anchor="rt")

        if preview: img.convert("RGB").save(wd + f"preview_{f:04d}.jpg", quality=90)
        else: pipe.stdin.write(img.convert("RGB").tobytes())
        if f % 150 == 0: print("frame", f, "/", N, flush=True)
    if pipe:
        pipe.stdin.close(); pipe.wait()
        if pipe.returncode != 0: sys.exit("compose failed")
        os.rename(out_tmp, out)
    return out


# ---------------------------------------------------------------- stage 5
def stage_mux(cfg, wd, video):
    out = cfg["output"]; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    pre = "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=3dB"
    run(["ffmpeg", "-v", "error", "-y", "-i", cfg["talking_head"], "-t", str(cfg["duration"]), "-vn", "-ac", "1", "-ar", "48000",
         "-af", pre, wd + "voice_pre.wav"])
    # two-pass loudnorm: single pass undershoots on short clips
    log = subprocess.run(["ffmpeg", "-i", wd + "voice_pre.wav", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(log[log.rfind("{"):log.rfind("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.0:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", wd + "voice_pre.wav", "-af", ln + ",alimiter=limit=0.79:level=disabled", "-ar", "48000", wd + "voice.wav"])
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wd + "voice.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("--preview", default="")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    wd = cfg.get("work_dir", "output/remix_work/"); wd = wd if wd.endswith("/") else wd + "/"; os.makedirs(wd, exist_ok=True)
    cfg.setdefault("duration", round(probe_duration(cfg["talking_head"]) - 0.1, 2))
    cam = stage_grade(cfg, wd); bg = stage_bg(cfg, wd)
    if "_bg_map" not in cfg:   # bg reused from an earlier run: rebuild the time map
        b = cfg.get("background_timing", {}); src_total = probe_duration(cfg["background"])
        i_s, i_sp = b.get("intro_seconds", 6.6), b.get("intro_speed", 2.0); i_o = i_s / i_sp
        cfg["_bg_map"] = [i_s, i_sp, i_o, (src_total - i_s) / max(0.1, cfg["duration"] - i_o), src_total]
    mdir = stage_masks(cfg, wd, cam)
    prev = [x for x in a.preview.split(",") if x]
    v = stage_compose(cfg, wd, cam, bg, mdir, preview=prev or None)
    if prev: print("previews in", wd); return
    print("done:", stage_mux(cfg, wd, v))


if __name__ == "__main__":
    main()
