#!/usr/bin/env python3
"""Efek talking head: 20 efek yang ditempel ke satu video orang ngomong, diatur lewat satu file JSON.

Tahap (yang sudah ada hasilnya dilewati, jadi run yang berhenti bisa dilanjutin):
  1. base   - video sumber dijadiin 1080x1920, 30 fps
  2. masks  - mask orang (rembg u2net_human_seg), cuma kalau ada efek yang butuh
  3. render - tiap frame lewat efek yang aktif di detik itu, di-pipe ke ffmpeg
  4. mux    - audio asli, loudness -14 LUFS

Pakai:
  python3 scripts/effects/effects.py config.json
  python3 scripts/effects/effects.py config.json --preview 2,6.5,12   # still doang, cepat
  python3 scripts/effects/effects.py --list                            # daftar efek
"""
import argparse, json, math, os, random, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
# Grade bawaan ("grade": true): bersihin noise HP, kontras S-curve, warna lebih hidup, tajam. Boleh diganti string filter ffmpeg sendiri.
GRADE = ("hqdn3d=2:1.5:5:4,eq=contrast=1.10:brightness=-0.02:saturation=1.18:gamma=0.97,"
         "curves=master='0/0 0.12/0.08 0.5/0.5 0.85/0.9 1/1',colorbalance=rs=-0.03:bs=0.04:rh=0.03:bh=-0.03,"
         "cas=strength=0.55,vignette=angle=PI/5")
NEED_MATTE = {"text_behind", "clones", "bg_bw", "dolly_zoom", "spotlight", "neon_outline", "echo_trail", "sticker", "bg_world"}


# ---------------------------------------------------------------- helpers
def run(cmd):
    print("$", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)

def done(p): return os.path.exists(p) and os.path.getsize(p) > 0
def clamp01(x): return max(0.0, min(1.0, x))
def ease_out(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp01(x); return 3 * x * x - 2 * x ** 3
def back_out(x, s=1.7): x = clamp01(x) - 1; return x * x * ((s + 1) * x + s) + 1
def bounce_out(x):
    x = clamp01(x)
    for a, b, c in ((1 / 2.75, 0, 0), (2 / 2.75, 1.5 / 2.75, .75), (2.5 / 2.75, 2.25 / 2.75, .9375), (9, 2.625 / 2.75, .984375)):
        if x < a: x -= b; return 7.5625 * x * x + c
def bgr(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (4, 2, 0))
def rgb(h): return bgr(h)[::-1]
def inout(tl, dur, a=0.2, b=0.2):
    """0..1 amplop: naik selama a detik, turun selama b detik terakhir."""
    return min(clamp01(tl / a) if a else 1, clamp01((dur - tl) / b) if b else 1)

_fonts = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fonts:
        try: _fonts[k] = ImageFont.truetype(path, int(size))
        except Exception:
            print("! font gak kebaca:", path, "-> pakai font bawaan", flush=True)
            _fonts[k] = ImageFont.load_default(int(size))
    return _fonts[k]

def text_rgba(txt, fnt, fill, stroke=0, stroke_fill=(0, 0, 0)):
    """Teks jadi layer BGRA (numpy), dipotong pas."""
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    b = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
    im = Image.new("RGBA", (max(1, b[2] - b[0]) + 4, max(1, b[3] - b[1]) + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - b[0], 2 - b[1]), txt, font=fnt, fill=tuple(fill) + (255,), stroke_width=stroke, stroke_fill=tuple(stroke_fill) + (255,))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA)

def card_rgba(w, h, fill, radius=28, alpha=255):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=tuple(fill) + (alpha,))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA)

def over(dst, L, x, y, alpha=1.0, scale=1.0, anchor="lt"):
    """Tempel layer BGRA ke frame BGR (di tempat), aman kalau keluar frame."""
    if alpha <= 0.003: return dst
    if abs(scale - 1) > 1e-3:
        L = cv2.resize(L, (max(1, int(L.shape[1] * scale)), max(1, int(L.shape[0] * scale))), interpolation=cv2.INTER_LINEAR)
    h, w = L.shape[:2]
    if anchor == "c": x -= w // 2; y -= h // 2
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return dst
    src = L[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (src[:, :, 3:4].astype(np.float32) / 255.0) * alpha
    dst[y0:y1, x0:x1] = (src[:, :, :3] * a + dst[y0:y1, x0:x1] * (1 - a)).astype(np.uint8)
    return dst

def mix(a, b, m):
    """a di area m (0..1 float, HxW atau angka), b di sisanya."""
    if not np.isscalar(m): m = m[:, :, None]
    return (a.astype(np.float32) * m + b.astype(np.float32) * (1 - m)).astype(np.uint8)

def shift(img, dx, dy, border=cv2.BORDER_CONSTANT):
    return cv2.warpAffine(img, np.float32([[1, 0, dx], [0, 1, dy]]), (img.shape[1], img.shape[0]), borderMode=border)

def zoom(img, s, cx=None, cy=None):
    cx = img.shape[1] / 2 if cx is None else cx; cy = img.shape[0] / 2 if cy is None else cy
    return cv2.warpAffine(img, np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]]), (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)


# ---------------------------------------------------------------- 10 efek utama
def fx_text_behind(f, m, tl, dur, e, st, C):
    """01 Teks raksasa di belakang badan: huruf masuk satu-satu, orangnya tetap di depan."""
    if "L" not in st:
        size = e.get("size", 300); col = rgb(e.get("color", C["accent"]))
        while True:                                           # kecilin sampai muat di lebar frame
            st["L"] = [text_rgba(ch, font(C["fonts"]["headline"], size), col) for ch in e["text"]]
            if sum(l.shape[1] for l in st["L"]) + e.get("gap", 6) * (len(e["text"]) - 1) <= W - 80 or size < 60: break
            size = int(size * 0.94)
        st["sub"] = None
        if e.get("sub"):
            t = text_rgba(e["sub"], font(C["fonts"]["ui"], e.get("sub_size", 54)), rgb(e.get("sub_color", C["ink"] if e.get("sub_pill", True) else "#FFFFFF")))
            if e.get("sub_pill", True):                       # kapsul biar kebaca di tembok terang maupun gelap
                c = card_rgba(t.shape[1] + 44, t.shape[0] + 26, rgb(e.get("sub_bg", "#FFFFFF")), 18); over(c[:, :, :3], t, 22, 13); t = c
            st["sub"] = t
        st["sh"] = [l.copy() for l in st["L"]]
        for l in st["sh"]: l[:, :, :3] = 0
    gap = e.get("gap", 6); tot = sum(l.shape[1] for l in st["L"]) + gap * (len(st["L"]) - 1)
    x = (W - tot) // 2 if "x" not in e else e["x"]; y = e.get("y", 520); bg = f.copy()
    out_a = clamp01((dur - tl) / 0.25)
    if st["sub"] is not None: over(bg, st["sub"], x + 6, y - st["sub"].shape[0] - 24, ease_out(tl / 0.3) * out_a)
    hmax = max(l.shape[0] for l in st["L"])
    for i, l in enumerate(st["L"]):
        p = (tl - i * e.get("stagger", 0.045)) / 0.28
        if p > 0:
            yy_ = y + hmax - l.shape[0] // 2 + (1 - ease_out(p)) * 90; sc_ = 0.6 + 0.4 * back_out(p)
            if e.get("shadow", True): over(bg, st["sh"][i], x + l.shape[1] // 2 + 8, yy_ + 12, 0.35 * clamp01(p * 2.5) * out_a, sc_, "c")
            over(bg, l, x + l.shape[1] // 2, yy_, clamp01(p * 2.5) * out_a, sc_, "c")
        x += l.shape[1] + gap
    return mix(f, bg, m)

def fx_cursor_click(f, m, tl, dur, e, st, C):
    """02 Kursor putih jalan ke satu titik, klik, keluar riak warna aksen. Bisa ada kotak seleksi + label."""
    (x0, y0), (x1, y1) = e.get("from", [W + 60, H * 0.7]), e["to"]; mv = e.get("move", min(0.6, dur * 0.5))
    p = ease_in_out(tl / mv); x, y = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p; acc = bgr(C["accent"])
    if e.get("box") and tl > mv:
        bx, by, bw, bh = e["box"]
        cv2.rectangle(f, (bx, by), (bx + bw, by + bh), acc, 3, cv2.LINE_AA)
        for hx, hy in ((bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)):
            cv2.rectangle(f, (hx - 9, hy - 9), (hx + 9, hy + 9), (255, 255, 255), -1); cv2.rectangle(f, (hx - 9, hy - 9), (hx + 9, hy + 9), acc, 2)
        if e.get("label"):
            if "lab" not in st:
                t = text_rgba(e["label"], font(C["fonts"]["mono"], 30), rgb(C["ink"])); c = card_rgba(t.shape[1] + 28, t.shape[0] + 18, rgb(C["accent"]), 8)
                over(c[:, :, :3], t, 14, 9); st["lab"] = c
            over(f, st["lab"], bx, by - st["lab"].shape[0] - 8)
    if tl > mv:                                               # riak klik
        r = (tl - mv) / 0.45
        if r < 1:
            ov = f.copy(); cv2.circle(ov, (int(x), int(y)), int(18 + 90 * ease_out(r)), acc, 8, cv2.LINE_AA); f = mix(ov, f, 1 - r)
    s = e.get("size", 1.0) * (0.86 if mv < tl < mv + 0.12 else 1.0)
    pts = np.array([[0, 0], [0, 62], [16, 48], [28, 74], [40, 68], [28, 43], [48, 43]], np.float32) * s + [x, y]
    cv2.fillPoly(f, [pts.astype(np.int32)], (255, 255, 255), cv2.LINE_AA); cv2.polylines(f, [pts.astype(np.int32)], True, (0, 0, 0), 4, cv2.LINE_AA)
    return f

def fx_type_caption(f, m, tl, dur, e, st, C):
    """03 Caption gaya command bar: huruf ngetik sendiri, kursor blok kedip."""
    txt = e["text"]; y = e.get("y", 1500); pad = 34
    if "fnt" not in st:                                       # kecilin font sampai seluruh kalimat muat di layar
        size = e.get("size", 46)
        while True:
            st["fnt"] = font(C["fonts"]["mono"], size); st["full"] = text_rgba("› " + txt + "  ", st["fnt"], (255, 255, 255))
            if st["full"].shape[1] + pad * 2 + 30 <= W - 80 or size <= 26: break
            size -= 2
    fnt = st["fnt"]
    n = int(len(txt) * clamp01(tl / e.get("type_time", max(0.4, dur * 0.6))))
    bw, bh = st["full"].shape[1] + pad * 2 + 30, st["full"].shape[0] + pad
    x = (W - bw) // 2; a = inout(tl, dur, 0.15, 0.2)
    over(f, card_rgba(bw, bh, rgb(C["ink"]), 22, 235), x, y, a)
    k = ("t", n)
    if k not in st: st[k] = text_rgba("› " + txt[:n], fnt, (255, 255, 255))
    over(f, st[k], x + pad, y + pad // 2, a)
    if int(tl * 3) % 2 == 0 or n < len(txt):
        cx = x + pad + st[k].shape[1] + 6; cv2.rectangle(f, (cx, y + pad // 2 + 2), (cx + 22, y + bh - pad // 2 - 2), bgr(C["accent"]), -1)
    return f

def fx_clones(f, m, tl, dur, e, st, C):
    """04 Kloning: salinan orangnya berjajar kiri-kanan, tiap salinan telat beberapa frame."""
    buf = st.setdefault("buf", []); buf.append((f.copy(), m.copy())); delay = e.get("delay", 4); n = e.get("count", 2)
    if len(buf) > delay * n + 1: buf.pop(0)
    out = f.copy(); sp = e.get("spacing", 250)
    for i in range(n, 0, -1):
        p = back_out((tl - (i - 1) * 0.12) / 0.35) * clamp01((dur - tl) / 0.2)
        if p <= 0: continue
        cf, cm = buf[max(0, len(buf) - 1 - i * delay)]
        for sgn in (e.get("sides", [-1, 1])):
            dx = sgn * sp * i * p; sc = e.get("dim", 0.82) ** i
            out = mix((shift(cf, dx, 0).astype(np.float32) * sc).astype(np.uint8), out, shift(cm, dx, 0))
    return mix(f, out, m)

def fx_bg_bw(f, m, tl, dur, e, st, C):
    """05 Background hitam putih, orangnya tetap berwarna."""
    g = cv2.cvtColor(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    g = cv2.convertScaleAbs(g, alpha=e.get("contrast", 1.15), beta=-12)
    a = inout(tl, dur, e.get("fade", 0.25), e.get("fade", 0.25))
    return mix(f, mix(g, f, a), m)

def fx_freeze_sketch(f, m, tl, dur, e, st, C):
    """06 Freeze, lalu garis sapuan mengubah frame beku jadi sketsa pensil."""
    if "fr" not in st:
        st["fr"] = f.copy(); g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        sk = cv2.divide(g, 255 - cv2.GaussianBlur(255 - g, (0, 0), e.get("softness", 9)), scale=256)
        sk = cv2.convertScaleAbs(sk, alpha=1.5, beta=-120); paper = np.array(bgr(e.get("paper", "#F4EFE4")), np.float32) / 255
        st["sk"] = (sk[:, :, None].astype(np.float32) * paper).astype(np.uint8)
    hold = e.get("hold", 0.35); p = ease_in_out((tl - hold) / e.get("wipe", 0.7)); y = int(H * p)
    out = st["fr"].copy(); out[:y] = st["sk"][:y]
    if 0 < p < 1: cv2.line(out, (0, y), (W, y), bgr(C["accent"]), 6)
    if tl < 0.12: out = cv2.addWeighted(out, 1, np.full_like(out, 255), 0.6 * (1 - tl / 0.12), 0)
    return out

def fx_dolly_zoom(f, m, tl, dur, e, st, C):
    """07 Dolly zoom: background membesar seolah ruangannya ketarik, orangnya tetap."""
    hole = cv2.resize((m > 0.25).astype(np.uint8) * 255, (W // 4, H // 4)); hole = cv2.dilate(hole, np.ones((9, 9), np.uint8))
    bgs = cv2.inpaint(cv2.resize(f, (W // 4, H // 4)), hole, 5, cv2.INPAINT_TELEA)       # tambal bekas orangnya dulu
    bgf = mix(cv2.resize(cv2.GaussianBlur(bgs, (0, 0), 2), (W, H)), f, cv2.GaussianBlur(cv2.resize(hole, (W, H)), (0, 0), 12).astype(np.float32) / 255)
    p = math.sin(clamp01(tl / dur) * math.pi) if e.get("return", True) else ease_in_out(tl / dur)
    ys, xs = np.nonzero(m > 0.5); cx, cy = (xs.mean(), ys.mean()) if len(xs) else (W / 2, H / 2)
    return mix(f, zoom(bgf, 1 + e.get("amount", 0.35) * p, cx, cy), m)

def fx_glitch(f, m, tl, dur, e, st, C):
    """08 Glitch: kanal warna geser + potongan horizontal loncat."""
    rnd = random.Random(int(tl * FPS) // e.get("hold_frames", 2) + e.get("seed", 7)); k = e.get("amount", 1.0) * inout(tl, dur, 0.05, 0.1)
    out = f.copy(); d = int(26 * k * rnd.uniform(0.4, 1))
    out[:, :, 2] = shift(f[:, :, 2], d, 0, cv2.BORDER_REFLECT); out[:, :, 0] = shift(f[:, :, 0], -d, 0, cv2.BORDER_REFLECT)
    for _ in range(int(7 * k)):
        y = rnd.randrange(0, H - 10); h = rnd.randrange(12, 130)
        out[y:y + h] = np.roll(out[y:y + h], int(rnd.uniform(-140, 140) * k), axis=1)
    if rnd.random() < 0.3 * k: out[::4] = (out[::4] * 0.55).astype(np.uint8)
    return out

def fx_comment_drop(f, m, tl, dur, e, st, C):
    """09 Kartu komentar jatuh dari atas dan mantul, ditumpuk."""
    if "cards" not in st:
        st["cards"] = []; fn, ft = font(C["fonts"]["ui"], 30), font(C["fonts"]["caption"], 42)
        for c in e["cards"]:
            t = text_rgba(c["text"], ft, rgb(C["ink"])); nm = text_rgba(c.get("name", "you") + " · now", fn, (90, 96, 104))
            w = max(t.shape[1], nm.shape[1]) + 170; card = card_rgba(w, 150, (255, 255, 255), 34)
            cv2.circle(card, (70, 75), 38, bgr(c.get("avatar", C["accent"])) + (255,), -1, cv2.LINE_AA)
            cv2.circle(card, (70, 64), 13, bgr(C["ink"]) + (255,), -1, cv2.LINE_AA); cv2.ellipse(card, (70, 104), (24, 18), 0, 180, 360, bgr(C["ink"]) + (255,), -1, cv2.LINE_AA)
            over(card[:, :, :3], nm, 130, 26); over(card[:, :, :3], t, 130, 72); st["cards"].append(card)
    x0, y = e.get("x", 90), e.get("y", 260); out_a = clamp01((dur - tl) / 0.25)
    for i, card in enumerate(st["cards"]):
        p = (tl - i * e.get("stagger", 0.45)) / 0.6
        if p > 0:
            sh = card.copy(); sh[:, :, :3] = 0; over(f, sh, x0 + i * 46 + 6, -200 + (y + 200) * bounce_out(p) + 12, 0.25 * out_a)
            over(f, card, x0 + i * 46, -200 + (y + 200) * bounce_out(p), out_a)
        y += card.shape[0] + 22
    return f

def fx_paper_tear(f, m, tl, dur, e, st, C):
    """10 Robek kertas: frame beku sobek jadi dua, di baliknya video jalan terus."""
    if "top" not in st:
        st["fr"] = f.copy(); rnd = random.Random(e.get("seed", 3)); y0 = H * e.get("at", 0.5); sl = e.get("slope", 0.12) * H
        pts = [(x, y0 + sl * (x / W - 0.5) + rnd.uniform(-26, 26)) for x in range(-20, W + 60, 34)]
        top = np.zeros((H, W), np.uint8); cv2.fillPoly(top, [np.array([(-20, -20)] + pts + [(W + 60, -20)], np.int32)], 255)
        edge = cv2.dilate(top, np.ones((15, 15), np.uint8)) & cv2.dilate(255 - top, np.ones((15, 15), np.uint8))
        st["top"], st["edge"] = top, edge; st["paper"] = np.full_like(f, bgr(e.get("paper", "#F4EFE4")))
    p = ease_in_out(tl / dur); d = p * H * 0.62; out = f.copy()
    fr = mix(st["paper"], st["fr"], st["edge"].astype(np.float32) / 255)
    for mask, dy, rot in ((st["top"], -d, -4 * p), (255 - st["top"], d, 3 * p)):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, 1.0); M[1, 2] += dy
        pm = cv2.warpAffine(mask | (st["edge"] if dy < 0 else 0), M, (W, H)).astype(np.float32) / 255
        out = (out * (1 - 0.35 * shift(pm, 0, 18)[:, :, None])).astype(np.uint8)      # bayangan
        out = mix(cv2.warpAffine(fr, M, (W, H)), out, pm)
    return out


# ---------------------------------------------------------------- 10 efek bonus
def fx_spotlight(f, m, tl, dur, e, st, C):
    """11 Spotlight: ruangan meredup, cahaya lonjong cuma di orangnya."""
    a = inout(tl, dur, 0.3, 0.3); ys, xs = np.nonzero(m > 0.5)
    cx, cy = (xs.mean(), ys.min() + (ys.max() - ys.min()) * 0.35) if len(xs) else (W / 2, H / 2)
    yy, xx = np.mgrid[0:H:8, 0:W:8]; g = np.exp(-(((xx - cx) / (W * 0.42)) ** 2 + ((yy - cy) / (H * 0.36)) ** 2) * 1.6)
    light = cv2.resize(g.astype(np.float32), (W, H)); lvl = e.get("dark", 0.18) + (1 - e.get("dark", 0.18)) * light
    lvl = np.maximum(lvl, m * 0.95); lvl = 1 - a * (1 - lvl)
    return (f * lvl[:, :, None]).astype(np.uint8)

def fx_neon_outline(f, m, tl, dur, e, st, C):
    """12 Garis neon menyala di sekeliling badan."""
    a = inout(tl, dur, 0.2, 0.2) * (0.8 + 0.2 * math.sin(tl * 14)); b = (m > 0.5).astype(np.uint8) * 255; t = e.get("thickness", 9)
    ring = cv2.subtract(cv2.dilate(b, np.ones((t * 2 + 1, t * 2 + 1), np.uint8)), b).astype(np.float32) / 255
    glow = cv2.GaussianBlur(ring, (0, 0), e.get("glow", 22)) * 1.8 + ring; col = np.array(bgr(e.get("color", C["accent"])), np.float32)
    bg = np.clip(f * (1 - 0.45 * a) + glow[:, :, None] * col * a, 0, 255).astype(np.uint8)
    return mix(f, bg, m)

def fx_echo_trail(f, m, tl, dur, e, st, C):
    """13 Jejak gerak: bayangan badan beberapa frame terakhir ikut di belakang."""
    buf = st.setdefault("buf", []); buf.append((f.copy(), m.copy())); n, step = e.get("count", 4), e.get("step", 3)
    if len(buf) > n * step + 1: buf.pop(0)
    out = f.copy(); tint = np.array(bgr(e.get("color", C["accent"])), np.float32)
    for i in range(n, 0, -1):
        if len(buf) > i * step:
            pf, pm = buf[-1 - i * step]; gh = (pf * 0.45 + tint * 0.55).astype(np.uint8)
            out = mix(gh, out, pm * (0.6 * (1 - i / (n + 1))))
    return mix(f, out, m)

def fx_impact_frame(f, m, tl, dur, e, st, C):
    """14 Impact frame ala anime: hitam-putih kontras tinggi, dibalik, garis kecepatan, layar getar."""
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); _, bw = cv2.threshold(cv2.GaussianBlur(g, (0, 0), 2), 0, 255, cv2.THRESH_OTSU)
    fr = int(tl * FPS)
    if fr % 4 < 2: bw = 255 - bw
    out = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR); rnd = random.Random(fr // 2)
    for _ in range(e.get("lines", 46)):
        a = rnd.uniform(0, 2 * math.pi); r0 = rnd.uniform(520, 760); c = (255, 255, 255) if rnd.random() < 0.5 else (0, 0, 0)
        p0 = (int(W / 2 + math.cos(a) * r0), int(H * 0.45 + math.sin(a) * r0 * 1.5)); p1 = (int(W / 2 + math.cos(a) * 2200), int(H * 0.45 + math.sin(a) * 2200))
        cv2.line(out, p0, p1, c, rnd.randrange(3, 16), cv2.LINE_AA)
    if e.get("tint", True): out = np.where(out > 127, np.array(bgr(C["accent"]), np.uint8), out).astype(np.uint8) if fr % 4 >= 2 else out
    return shift(zoom(out, 1.06), rnd.uniform(-18, 18), rnd.uniform(-18, 18), cv2.BORDER_REFLECT)

def fx_vhs(f, m, tl, dur, e, st, C):
    """15 VHS: warna luntur, garis scan, noise, tulisan PLAY + jam."""
    a = inout(tl, dur, 0.1, 0.1); out = f.copy()
    out[:, :, 2] = shift(f[:, :, 2], 7, 0, cv2.BORDER_REFLECT); out[:, :, 0] = shift(f[:, :, 0], -7, 0, cv2.BORDER_REFLECT)
    out = cv2.GaussianBlur(out, (0, 0), 1.3); out = cv2.convertScaleAbs(out, alpha=0.9, beta=18)
    out[::3] = (out[::3] * 0.72).astype(np.uint8)
    rnd = np.random.default_rng(int(tl * FPS)); out = np.clip(out + rnd.normal(0, 14, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1), 0, 255).astype(np.uint8)
    y = int((tl * 520) % H); out[y:y + 26] = np.roll(out[y:y + 26], 40, axis=1)
    if "t" not in st: st["t"] = text_rgba(e.get("label", "PLAY ▶"), font(C["fonts"]["mono"], 54), (255, 255, 255))
    over(out, st["t"], 70, 150)
    s = int(tl + e.get("clock_start", 0)); over(out, text_rgba(f"00:{s // 60:02d}:{s % 60:02d}", font(C["fonts"]["mono"], 46), (255, 255, 255)), 70, H - 260)
    return mix(out, f, a)

def fx_mosaic_reveal(f, m, tl, dur, e, st, C):
    """16 Mosaik: mulai kotak-kotak besar, makin halus sampai tajam."""
    p = ease_in_out(tl / dur); p = 1 - p if e.get("reverse") else p; b = int(e.get("max_block", 90) * (1 - p) ** 2)
    if b < 3: return f
    small = cv2.resize(f, (max(1, W // b), max(1, H // b)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST)

def fx_duotone(f, m, tl, dur, e, st, C):
    """17 Duotone: semua warna dipetakan ke dua warna merek (gelap ke aksen)."""
    if "lut" not in st:
        a, b = np.array(bgr(e.get("dark", C["ink"])), np.float32), np.array(bgr(e.get("light", C["accent"])), np.float32)
        t = (np.arange(256) / 255.0)[:, None] ** e.get("gamma", 0.9); st["lut"] = (a * (1 - t) + b * t).astype(np.uint8)
    g = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    return mix(st["lut"][g], f, inout(tl, dur, 0.2, 0.2) * e.get("mix", 1.0))

def fx_polaroid(f, m, tl, dur, e, st, C):
    """18 Jepret: kilat, frame beku jadi foto berbingkai putih yang miring, video di belakang jalan terus (blur)."""
    if "ph" not in st:
        bw_, bh_ = int(W * 0.62), int(W * 0.62 * 1.18); ph = np.full((bh_ + 150, bw_ + 60, 4), 255, np.uint8)
        s = max(bw_ / W, bh_ / H); r = cv2.resize(f, (int(W * s) + 1, int(H * s) + 1)); oy = int((r.shape[0] - bh_) * e.get("crop_y", 0.25)); ox = (r.shape[1] - bw_) // 2
        ph[30:30 + bh_, 30:30 + bw_, :3] = r[oy:oy + bh_, ox:ox + bw_]
        if e.get("caption"):
            t = text_rgba(e["caption"], font(C["fonts"]["caption"], 50), rgb(C["ink"])); over(ph[:, :, :3], t, (ph.shape[1] - t.shape[1]) // 2, bh_ + 56)
        st["ph"] = ph
    p = back_out(tl / 0.45); a = clamp01((dur - tl) / 0.25)
    out = cv2.convertScaleAbs(cv2.GaussianBlur(f, (0, 0), 14), alpha=1 - 0.45 * a)
    out = mix(out, f, a); ph = st["ph"]; ang = e.get("angle", -6) * p
    M = cv2.getRotationMatrix2D((ph.shape[1] / 2, ph.shape[0] / 2), ang, 1.0); big = cv2.warpAffine(np.pad(ph, ((60, 60), (60, 60), (0, 0))), np.float32([[M[0, 0], M[0, 1], M[0, 2] + 60 * (1 - M[0, 0]) - 60 * M[0, 1]], [M[1, 0], M[1, 1], M[1, 2] - 60 * M[1, 0] + 60 * (1 - M[1, 1])]]), (ph.shape[1] + 120, ph.shape[0] + 120))
    sh = big.copy(); sh[:, :, :3] = 0; cx, cy = e.get("x", W // 2), e.get("y", int(H * 0.44))
    over(out, sh, cx + 14, cy + 22, 0.35 * a, 0.7 + 0.3 * p, "c"); over(out, big, cx, cy, a, 0.7 + 0.3 * p, "c")
    if tl < 0.15: out = cv2.addWeighted(out, 1, np.full_like(out, 255), 0.85 * (1 - tl / 0.15), 0)
    return out

def fx_split3(f, m, tl, dur, e, st, C):
    """19 Layar kebelah tiga: tiga panel tegak dengan zoom beda, masuk gantian."""
    zs = e.get("zooms", [1.0, 1.7, 2.6]); out = f.copy(); pw = W // 3; gap = e.get("gap", 8); a_out = clamp01((dur - tl) / 0.2)
    ys, xs = (np.nonzero(m > 0.5) if m is not None else ((), ()))
    cx, cy = (xs.mean(), ys.min() + (ys.max() - ys.min()) * e.get("focus_y", 0.18)) if len(xs) else (W / 2, H * 0.38)
    for i, z in enumerate(zs):
        p = ease_out((tl - i * 0.12) / 0.3) * a_out
        if p <= 0: continue
        zf = zoom(f, z, cx, cy); x0 = int(cx - pw / 2); x0 = max(0, min(W - pw, x0)); pan = zf[:, x0:x0 + pw]
        dy = int((1 - p) * H * (1 if i % 2 else -1)); dst = shift(pan, 0, dy)
        vis = shift(np.full((H, pw), 255, np.uint8), 0, dy) > 0
        out[:, i * pw:i * pw + pw][vis] = dst[vis]
        if i: cv2.rectangle(out, (i * pw - gap // 2, 0), (i * pw + gap // 2, H), bgr(C["ink"]), -1)
    return out

def fx_sticker(f, m, tl, dur, e, st, C):
    """20 Stiker: orangnya dapat garis tepi putih tebal, background diganti kanvas titik-titik."""
    if "bg" not in st:
        bg = np.full((H, W, 3), bgr(e.get("canvas", C["ink"])), np.uint8)
        for y in range(40, H, 60):
            for x in range(40, W, 60): cv2.circle(bg, (x, y), 4, bgr(e.get("dots", "#2A2F3A")), -1, cv2.LINE_AA)
        st["bg"] = bg
    a = inout(tl, dur, 0.2, 0.2); b = (m > 0.5).astype(np.uint8) * 255; t = e.get("outline", 16)
    ring = cv2.GaussianBlur(cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (t * 2 + 1, t * 2 + 1))), (0, 0), 1.5).astype(np.float32) / 255
    out = mix(np.full_like(f, 255), mix(st["bg"], f, a), ring * a)
    out = mix(f, out, m)
    s = 1 + 0.05 * math.sin(clamp01(tl / 0.3) * math.pi)
    return zoom(out, s) if s > 1.001 else out

def fx_bg_world(f, m, tl, dur, e, st, C):
    """21 Ganti dunia: tembok di belakang dibuka jadi terowongan grid neon yang terus ketarik menjauh."""
    hw, hh = W // 2, H // 2; acc = np.array(bgr(e.get("color", C["accent"])), np.float32)
    ys, xs = np.nonzero(m[::4, ::4] > 0.5)
    if "c" not in st: st["c"] = (xs.mean() * 4, (ys.min() + (ys.max() - ys.min()) * 0.3) * 4) if len(xs) else (W / 2, H * 0.4)
    cx, cy = st["c"][0] / 2, st["c"][1] / 2; g = np.zeros((hh, hw), np.float32); ph = tl * e.get("speed", 0.9); N = e.get("rings", 9)
    for k in range(N):                                        # bingkai yang membesar = terowongan ketarik
        u = ((k + ph) % N) / N; sc = 0.04 + u ** 2.4 * 2.6; w2, h2 = hw * 0.62 * sc, hh * 0.62 * sc
        cv2.rectangle(g, (int(cx - w2), int(cy - h2)), (int(cx + w2), int(cy + h2)), float(0.25 + 0.75 * u), max(1, int(1 + 7 * u)), cv2.LINE_AA)
    for a in np.linspace(0, 2 * math.pi, e.get("rays", 20), endpoint=False):
        cv2.line(g, (int(cx + math.cos(a) * 30), int(cy + math.sin(a) * 30)), (int(cx + math.cos(a) * 2400), int(cy + math.sin(a) * 2400)), 0.35, 2, cv2.LINE_AA)
    rnd = random.Random(e.get("seed", 5))
    for _ in range(e.get("stars", 70)):                       # bintang melesat keluar
        a, u0, sp_ = rnd.uniform(0, 2 * math.pi), rnd.random(), rnd.uniform(0.5, 1.4); u = (u0 + tl * sp_ * 0.6) % 1; r0 = 40 + u ** 2 * 1300
        cv2.line(g, (int(cx + math.cos(a) * r0), int(cy + math.sin(a) * r0)), (int(cx + math.cos(a) * r0 * 1.12), int(cy + math.sin(a) * r0 * 1.12)), 1.0, 2, cv2.LINE_AA)
    yy, xx = np.mgrid[0:hh, 0:hw]; d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / hh
    g = g + cv2.GaussianBlur(g, (0, 0), 9) * 1.6
    world = np.clip(g[:, :, None] * acc + (np.clip(1 - d * 1.3, 0, 1) ** 2)[:, :, None] * acc * 0.22 + np.array(bgr(e.get("sky", "#060A12")), np.float32), 0, 255)
    world = cv2.resize(world.astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR)
    # transisi: lingkaran membuka dari belakang kepala
    op = ease_out(tl / e.get("open", 0.45)) * (1 if e.get("hard_out", True) else clamp01((dur - tl) / 0.3))
    Y, X = np.ogrid[0:H, 0:W]; rr = np.sqrt((X - st["c"][0]) ** 2 + (Y - st["c"][1]) ** 2); R = op * 2300
    hole = np.clip((R - rr) / 40 + 0.5, 0, 1).astype(np.float32)
    bg = mix(world, f, hole)
    if 0 < op < 1:
        ring = np.clip(1 - np.abs(rr - R) / 26, 0, 1).astype(np.float32); bg = np.clip(bg + ring[:, :, None] * 255, 0, 255).astype(np.uint8)
    mm = cv2.GaussianBlur(cv2.erode(m, np.ones((5, 5), np.uint8)), (0, 0), 1.5)          # buang pinggiran warna tembok
    if e.get("floor"): mm[int(e["floor"]):] = 1.0                    # baris di bawah ini (meja, dsb.) selalu dianggap depan
    rim = np.clip(mm - cv2.GaussianBlur(mm, (0, 0), 16), 0, 1) * 0.9 * hole                       # cahaya tepi biar nyatu
    subj = np.clip(f.astype(np.float32) * (1 - 0.18 * hole[:, :, None]) + rim[:, :, None] * acc, 0, 255).astype(np.uint8)
    out = mix(subj, bg, mm)
    if tl < 0.1: out = cv2.addWeighted(out, 1, np.full_like(out, 255), 0.5 * (1 - tl / 0.1), 0)
    return out

def fx_pill(f, m, tl, dur, e, st, C):
    """Bantu: tulisan besar di dalam kapsul (judul, CTA). Bukan bagian dari 20 efek."""
    if "L" not in st:
        t = text_rgba(e["text"], font(C["fonts"][e.get("font", "headline")], e.get("size", 96)), rgb(e.get("color", C["ink"])))
        px, py = e.get("pad", [44, 28]); c = card_rgba(t.shape[1] + px * 2, t.shape[0] + py * 2, rgb(e.get("bg", C["accent"])), e.get("radius", 30))
        over(c[:, :, :3], t, px, py); st["L"] = c
    a = inout(tl, dur, 0.12, 0.2); s = 0.7 + 0.3 * back_out(tl / 0.3)
    return over(f, st["L"], e.get("x", W // 2), e.get("y", 1380), a, s, "c")


def fx_punch(f, m, tl, dur, e, st, C):
    """Bantu: punch-in zoom cepat ke satu titik (default wajah/atas badan), balik pelan."""
    if "c" not in st:
        ys, xs = (np.nonzero(m[::4, ::4] > 0.5) if m is not None else ((), ()))
        st["c"] = e.get("at") or ((xs.mean() * 4, (ys.min() + (ys.max() - ys.min()) * 0.25) * 4) if len(xs) else (W / 2, H * 0.38))
    a = back_out(tl / e.get("in", 0.18)) if tl < e.get("in", 0.18) else 1 - ease_in_out((tl - e.get("in", 0.18)) / max(0.01, dur - e.get("in", 0.18))) * e.get("release", 1.0)
    return zoom(f, 1 + e.get("amount", 0.12) * a, *st["c"])

EFFECTS = {n[3:]: fn for n, fn in list(globals().items()) if n.startswith("fx_")}


# ---------------------------------------------------------------- label + panel daftar efek
def draw_label(f, tl, dur, e, st, C):
    """Nama efek di kiri atas selama efeknya jalan: kalau efek punya "name"."""
    if "lab_" not in st:
        L = C.get("label", {}); num = text_rgba(f"{e['n']:02d}" if e.get("n") else "+", font(C["fonts"]["mono"], L.get("num_size", 40)), rgb(C["ink"]))
        t = text_rgba(e["name"], font(C["fonts"]["headline"], L.get("size", 60)), (255, 255, 255)); hh_ = max(num.shape[0], t.shape[0]) + 36
        c = card_rgba(num.shape[1] + t.shape[1] + 110, hh_, rgb(C["ink"]), 22, 240); nb = card_rgba(num.shape[1] + 36, hh_ - 20, rgb(C["accent"]), 14)
        over(c[:, :, :3], nb, 10, 10)
        over(c[:, :, :3], num, 28, (hh_ - num.shape[0]) // 2); over(c[:, :, :3], t, num.shape[1] + 70, (hh_ - t.shape[0]) // 2); st["lab_"] = c
    L = C.get("label", {}); a = inout(tl, dur, 0.15, 0.2)
    return over(f, st["lab_"], L.get("x", 50) - (1 - ease_out(tl / 0.3)) * 80, L.get("y", 210), a)

def draw_panel(f, t, P, active, st, C):
    """Panel 'DI VIDEO INI' di sisi kanan, baris efek yang lagi jalan disorot. "windows": [[mulai, selesai], ...] kalau panelnya muncul beberapa kali."""
    wins = P.get("windows") or [[P.get("start", 0), P.get("end", 1e9)]]; win = next((w_ for w_ in wins if w_[0] <= t < w_[1]), None)
    if win is None: return f
    items = P["items"]; rh = P.get("row", 74); w = P.get("w", 400); x = P.get("x", W - w - 36); y = P.get("y", 300); fs = P.get("font_size", 38)
    h = 96 + rh * len(items) + (rh + 8 if P.get("footer") else 16)
    if "bgc" not in st:
        st["bgc"] = card_rgba(w, h, rgb(P.get("bg", C["ink"])), 30, P.get("alpha", 225)); fm, fi = font(C["fonts"]["mono"], int(fs * 0.68)), font(C["fonts"]["ui"], fs)
        st["rows"] = [(text_rgba(f"{i + 1:02d}", fm, rgb(C["accent"])), text_rgba(s, fi, (255, 255, 255)), text_rgba(s, fi, rgb(C["ink"]))) for i, s in enumerate(items)]
        st["title"] = text_rgba(P.get("title", "DI VIDEO INI"), fm, rgb(C["accent"])); st["hl"] = card_rgba(w - 20, rh - 6, (255, 255, 255), 14)
        st["foot"] = text_rgba(P["footer"], font(C["fonts"]["ui"], fs), rgb(C["accent"])) if P.get("footer") else None
    a = inout(t - win[0], win[1] - win[0], 0.3, 0.3); sx = x + (1 - ease_out((t - win[0]) / 0.4)) * (w + 60)
    over(f, st["bgc"], sx, y, a); over(f, st["title"], sx + 28, y + 34, a)
    cnt = text_rgba(f"{(active or 0):02d} / {len(items):02d}", font(C["fonts"]["mono"], int(fs * 0.68)), rgb(C["accent"])); over(f, cnt, sx + w - cnt.shape[1] - 28, y + 34, a)
    for i, (num, wh, dk) in enumerate(st["rows"]):
        ry = y + 88 + i * rh; on = active == i + 1; seen = active is not None and i + 1 <= active
        if on: over(f, st["hl"], sx + 10, ry - 3, a)
        over(f, num, sx + 28, ry + (rh - 6 - num.shape[0]) // 2, a * (1 if seen else 0.5)); over(f, dk if on else wh, sx + 28 + int(fs * 1.4), ry + (rh - 6 - wh.shape[0]) // 2, a * (1 if seen else 0.45))
    if st["foot"] is not None: over(f, st["foot"], sx + 28, y + h - rh - 2 + (rh - st["foot"].shape[0]) // 2, a)
    return f


# ---------------------------------------------------------------- tahap
def stage_base(cfg, wd):
    out = wd + "base.mp4"
    if done(out): return out
    vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    if cfg.get("grade"): vf += "," + (GRADE if cfg["grade"] is True else cfg["grade"])
    vf += ",format=yuv420p"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", cfg["input"]] + (["-t", str(cfg["duration"])] if cfg.get("duration") else [])
    run(cmd + ["-vf", vf, "-an", "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", wd + "base.tmp.mp4"])
    os.rename(wd + "base.tmp.mp4", out); return out

def matte_ranges(cfg):
    return [(e["start"] - 0.6, e["end"] + 0.1) for e in cfg["effects"] if e["type"] in NEED_MATTE or (e["type"] == "split3")]

def stage_masks(cfg, wd, base, only=None):
    """Mask orang 540x960 per frame, cuma di rentang efek yang butuh. cfg['mattes'] = folder berisi m0000.png... kalau mau pakai mask sendiri."""
    if cfg.get("mattes") and cfg["mattes"] != "auto": return cfg["mattes"].rstrip("/") + "/"
    mdir = wd + "masks/"; os.makedirs(mdir, exist_ok=True); rng = matte_ranges(cfg)
    need = lambda fi: any(a <= fi / FPS <= b for a, b in rng) and (only is None or fi in only)
    cap = cv2.VideoCapture(base); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); todo = [i for i in range(n) if need(i) and not os.path.exists(mdir + f"m{i:04d}.png")]
    if not todo: return mdir
    from rembg import new_session, remove
    sess = new_session(cfg.get("mask_model", "u2net_human_seg")); prev = None; todo = set(todo); fi = 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if fi in todo:
            small = Image.fromarray(cv2.cvtColor(cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
            mk = np.array(remove(small, session=sess, only_mask=True, post_process_mask=True)).astype(np.float32)
            if prev is not None and prev[0] == fi - 1: mk = 0.65 * mk + 0.35 * prev[1]      # halusin kedip antar frame
            prev = (fi, mk.copy()); bw = (mk > 128).astype(np.uint8); cnt, lab, stt, _ = cv2.connectedComponentsWithStats(bw)
            if cnt > 2: big = 1 + np.argmax(stt[1:, cv2.CC_STAT_AREA]); mk[(lab != big) & (lab != 0)] = 0   # buang serpihan
            cv2.imwrite(mdir + f"m{fi:04d}.png", cv2.GaussianBlur(mk, (3, 3), 0).astype(np.uint8))
            if len(os.listdir(mdir)) % 60 == 0: print("mask", len(os.listdir(mdir)), flush=True)
        fi += 1
    return mdir

def stage_render(cfg, wd, base, mdir, preview=None):
    C = {"accent": cfg.get("accent", "#C6FF00"), "ink": cfg.get("ink", "#05070B"), "fonts": cfg["fonts"], "label": cfg.get("label", {})}
    for k in ("ui", "mono", "caption"): C["fonts"].setdefault(k, C["fonts"].get("ui", C["fonts"]["headline"]))
    fx = sorted(cfg["effects"], key=lambda e: (e.get("z", 0), e["start"])); states = [dict() for _ in fx]; pst = {}
    for e in fx:
        if e["type"] not in EFFECTS: sys.exit(f"efek gak dikenal: {e['type']} (lihat --list)")
    cap = cv2.VideoCapture(base); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); out = wd + "video.mp4"
    want = None if preview is None else {int(float(t) * FPS) for t in preview}
    if want is None:
        if done(out): return out
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-crf", str(cfg.get("crf", 17)), "-preset", "medium", "-pix_fmt", "yuv420p", wd + "video.tmp.mp4"], stdin=subprocess.PIPE)
    P = cfg.get("panel")      # efek dengan z lebih besar digambar belakangan (di atas)
    for fi in range(n):
        ok, f = cap.read()
        if not ok: break
        t = fi / FPS; active = [(e, s) for e, s in zip(fx, states) if e["start"] <= t < e["end"]]
        warm = [(e, s) for e, s in zip(fx, states) if e["type"] in ("clones", "echo_trail") and e["start"] - 0.6 <= t < e["start"]]
        if want is not None and not any(abs(fi - w_) <= 24 and fi <= w_ for w_ in want): continue       # preview: cukup pemanasan 24 frame
        m = None
        if active or warm:
            mp = (mdir or "") + f"m{fi:04d}.png"
            if mdir and os.path.exists(mp): m = cv2.resize(cv2.imread(mp, 0), (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        for e, s in warm:
            if m is not None: s.setdefault("buf", []).append((f.copy(), m.copy()))
        for e, s in active:
            if e["type"] in NEED_MATTE and m is None: sys.exit(f"efek {e['type']} butuh mask tapi m{fi:04d}.png gak ada")
            f = EFFECTS[e["type"]](f, m, t - e["start"] + e.get("skip", 0), e["end"] - e["start"] + e.get("skip", 0), e, s, C)   # skip: mulai animasi dari tengah
        seen = [e["n"] for e in fx if e.get("n") and e.get("name_start", e["start"]) <= t]
        if P: f = draw_panel(f, t, P, max(seen) if seen else None, pst, C)
        for e, s in zip(fx, states):                          # nama efek selalu di atas efeknya
            a0, a1 = e.get("name_start", e["start"]), e.get("name_end", e["end"])
            if e.get("name") and a0 <= t < a1: f = draw_label(f, t - a0, a1 - a0, e, s, C)
        if want is None: ff.stdin.write(np.ascontiguousarray(f).tobytes())
        elif fi in want: cv2.imwrite(wd + f"preview_{t:06.2f}.jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if want is None and fi % 150 == 0: print("render", fi, "/", n, flush=True)
    if want is not None: return None
    ff.stdin.close()
    if ff.wait() != 0: sys.exit("ffmpeg gagal")
    os.rename(wd + "video.tmp.mp4", out); return out

def stage_mux(cfg, wd, video):
    out = cfg["output"]; os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    has_a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", cfg["input"]], capture_output=True, text=True).stdout.strip()
    if not has_a: run(["ffmpeg", "-v", "error", "-y", "-i", video, "-c", "copy", "-movflags", "+faststart", out]); return out
    run(["ffmpeg", "-v", "error", "-y", "-i", cfg["input"], "-vn", "-ac", "1", "-ar", "48000", "-af", "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=3dB", wd + "voice_pre.wav"])
    log = subprocess.run(["ffmpeg", "-i", wd + "voice_pre.wav", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    mm = json.loads(log[log.rfind("{"):log.rfind("}") + 1])          # dua pass: satu pass suka kurang keras di klip pendek
    ln = (f"loudnorm=I=-14:TP=-1.0:LRA=9:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:measured_LRA={mm['input_lra']}:"
          f"measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", wd + "voice_pre.wav", "-af", ln + ",alimiter=limit=0.79:level=disabled", "-ar", "48000", wd + "voice.wav"])
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", wd + "voice.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("config", nargs="?"); ap.add_argument("--preview", default=""); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.config:
        for n, fn in EFFECTS.items(): print(f"{n:15s} {'[mask]' if n in NEED_MATTE else '      '} {fn.__doc__}")
        return
    cfg = json.load(open(a.config)); wd = cfg.get("work_dir", "output/effects_work/"); wd = wd if wd.endswith("/") else wd + "/"; os.makedirs(wd, exist_ok=True)
    prev = [x for x in a.preview.split(",") if x]; base = stage_base(cfg, wd)
    only = None if not prev else {i for t in prev for i in range(int(float(t) * FPS) - 24, int(float(t) * FPS) + 1)}
    mdir = stage_masks(cfg, wd, base, only) if matte_ranges(cfg) else None
    v = stage_render(cfg, wd, base, mdir, prev or None)
    if prev: print("preview di", wd); return
    print("selesai:", stage_mux(cfg, wd, v))


if __name__ == "__main__":
    main()
