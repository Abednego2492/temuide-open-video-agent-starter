# Remix: lo ngomong di depan time-lapse Kanvas Hidup

Video Kanvas Hidup lo (2 menit) dipakai lagi jadi background yang dipercepat sampai tamat, terus lo yang lagi ngomong (direkam pakai HP) di-cutout dan ditaruh gede di depannya, lengkap dengan HUD "review mode". Cocok buat video ajakan / CTA: penonton liat hasil karya lo sambil denger lo ngomong.

```
0–3 dtk   Kanvas full layar, push-in pelan, headline hook (2 baris)
3,3 dtk   lo masuk (cutout slide-up), HUD review mode + scrubber muncul
...       kanvas jalan 5x lebih cepat sampai CTA-nya, caption putih statis di kanan
punch     kanvas diredupin, headline nyodok di tengah
akhir     pill "komen: KEYWORD" + caption penutup
```

## Yang lo butuhin

- Video Kanvas Hidup lo (hasil template ini) → `public/assets/`.
- Video lo ngomong, portrait, 15–40 detik. **3 detik pertama jangan ngomong dulu** (senyum / jalan / gestur), itu jatah hook.
- Python 3.10+, ffmpeg, dan:
  ```bash
  pip install opencv-python pillow numpy rembg onnxruntime
  ```
- Model mask (sekali download, ±175 MB per model, taruh di `~/.u2net/`):
  - `u2net_human_seg.onnx` dan (opsional) `isnet-general-use.onnx` dari GitHub release `danielgatis/rembg` tag `v0.0.0`.
  - Kalau download dapet 504 / file cuma beberapa byte, ulangi. Cek ukurannya > 10 MB.
- Font: Playfair Display (+ Italic) dari `google/fonts` (folder `ofl/playfairdisplay`) dan Inter SemiBold. Taruh di `fonts/` (folder ini di-`.gitignore`, jadi gak ke-commit).

## Cara pakai

```bash
cp scripts/remix/remix.example.json public/assets/remix.json
# edit path, teks headline, caption, waktu (detik)
python3 scripts/remix/remix.py public/assets/remix.json --preview 2,9,12,21   # cek still dulu
python3 scripts/remix/remix.py public/assets/remix.json                       # render penuh
```

Hasil: `output/remix.mp4`. Skrip bisa dilanjutin kalau berhenti di tengah: tiap stage (grade, background, mask, compose) disimpan di `work_dir` dan dilewatin kalau udah ada. Hapus file stage-nya kalau mau ulang bagian itu (mis. hapus `video.mp4` setelah ganti teks; mask gak perlu dibikin ulang).

## Ngisi config

| Kunci | Isi |
|---|---|
| `background_timing.intro_seconds` / `intro_speed` | bagian awal kanvas buat hook (default 6,6 dtk @ 2x). Sisanya otomatis dipercepat supaya pas habis di akhir video lo |
| `grade.temperature` | makin kecil makin hangat (4600 = golden hour). `fade_black` 0,06–0,12 = seberapa "matte" |
| `mask.isnet_veto` | `true` kalau background lo ada benda gelap nempel kepala (pintu, rambut temen). Lebih bersih tapi ±3x lebih lama |
| `presenter` | skala & posisi cutout. 0,70 di kiri bawah = gede tapi kanvas masih kebaca |
| `headlines[]` | `lines`, `start`, `end`, `size`. Baris terakhir otomatis warna aksen. Kepanjangan → otomatis dikecilin biar muat |
| `captions[]` | 1–2 baris, huruf kecil, rata kanan. Muncul/hilang fade, gak gerak |
| `cta` | teks pill + waktu muncul |

Tips timing: dengerin video lo, catat detik tiap kalimat mulai. Headline taruh tepat di kata yang paling nendang ("gak ada **alasan**", "komen **TOOLS**").

## Waktu render (2 CPU)

| Stage | 25 dtk video |
|---|---|
| grade + background | ±1 menit |
| mask u2net saja | ±13 menit |
| mask + ISNet veto | ±30 menit |
| compose | ±4 menit |

## Biar masking-nya mulus

- Rekam dengan background yang **kontras sama rambut**: dinding terang, langit, jalan. Pintu/pager hitam di belakang kepala bikin mask nyeret.
- Jangan terlalu backlight; tangan yang kena bayangan bisa jadi semi-transparan.
- Model masih bisa nganggap daun/kanopi yang nempel rambut sebagai bagian lo. Kalau keganggu, geser sedikit posisi berdiri pas rekam.

## Gaya yang dipakai

- Grade: hangat (color temperature 4600K), fade (black diangkat, putih di-roll off), vignette, grain halus. Kanvas ikut dihangatin biar nyatu.
- Font: Playfair Display Black buat headline (gaya majalah), Playfair Italic buat caption, Inter buat HUD.
- Aksen: satu warna aja (default lime `#C6FF00`), dipakai di HUD, scrubber, baris kedua headline, pill CTA.
- Caption putih polos + outline gelap tipis (biar kebaca di atas kertas krem), **statis**, cuma fade.
