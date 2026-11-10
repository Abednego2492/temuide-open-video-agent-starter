# Template: 20 efek talking head ⚡

Lo rekam satu video ngomong pakai HP. Claude nempelin efeknya: teks di belakang badan, kloning, sketsa pensil, layar robek, dan 16 efek lain. Gak ada app edit, gak ada template. Semua efek ada di satu skrip Python (`scripts/effects/effects.py`) dan diatur lewat satu file JSON, jadi lo (atau Claude) tinggal ganti teks dan detiknya.

Format videonya: tiap efek muncul pas namanya lo sebut, dan di kanan ada panel "DI VIDEO INI 03 / 10" yang nyorot efek yang lagi jalan.

> **Status tes (10 Nov 2026):** ke-20 efek, panel, render penuh dan audio sudah dites di klip sintetis 22 detik. Sebelas di antaranya (01–10 dan `bg_world`), label nama efek, panel dan mask otomatis rembg juga sudah dipakai di satu video asli 84 detik (HP, 1080×1920, render ±4,5 menit di 2 CPU, mask ±1 frame/detik). Efek bonus 11–20 **belum dites di footage orang asli**. Cek still dulu sebelum render penuh.

## Yang lo butuhin

- Video lo ngomong, portrait, 30–60 detik, satu take.
- Python 3.10+, ffmpeg, dan `pip install opencv-python pillow numpy rembg onnxruntime`.
- Model mask `u2net_human_seg.onnx` di `~/.u2net/` (GitHub release `danielgatis/rembg` tag `v0.0.0`, ±175 MB. Kalau hasil download cuma beberapa byte, ulangi).
- Font di folder `fonts/` (gak ke-commit): Anton, Inter SemiBold/Bold, JetBrains Mono Bold. Font lain boleh, ganti path di config.

## Cara rekam biar efeknya jadi

- HP agak mundur: sisain ruang di atas kepala (buat teks di belakang) dan ruang kosong di kanan (buat panel).
- Baju jangan sewarna tembok, tangan jangan nutup muka. Dua-duanya bikin mask bocor.
- Jeda setengah detik tiap habis nyebut satu efek. Itu jatah efeknya main.
- Gerakan kecil yang ngebantu: geser badan dikit pas "kloning", diam 1 detik pas "freeze", gerak cepat pas "jejak gerak".

## Alur kerja

```bash
cp scripts/effects/effects.example.json public/assets/efek.json
# isi path video, teks, dan detik mulai/selesai tiap efek
npm run effects -- --list                                   # daftar efek + mana yang butuh mask
npm run effects -- public/assets/efek.json --preview 5.6,12.8,18   # still dulu, cepat
npm run effects -- public/assets/efek.json                  # render penuh -> output/efek.mp4
```

1. **Transkrip dulu.** Minta Claude transkrip videonya dan catat detik tiap nama efek disebut (lihat `docs/CLAUDE_VIDEO_EDITOR_WORKFLOW.md`). `start` efek = detik kata itu mulai.
2. **Isi config.** Satu efek = satu baris di `effects`. `n` = nomor baris panel yang disorot.
3. **Cek still.** `--preview` cuma bikin mask dan frame di detik yang lo minta. Liat: teks kepotong gak, panel nutup muka gak, mask bocor gak.
4. **Render penuh.** Tiap tahap disimpan di `work_dir`. Ganti teks → hapus `video.mp4` aja, mask gak dibikin ulang.
5. **Tonton hasilnya** dari awal sampai akhir sebelum posting. Render sukses bukan berarti editnya udah enak.

## 10 efek utama

| # | `type` | Yang keliatan | Mask | Pengaturan penting |
|---|---|---|---|---|
| 01 | `text_behind` | Teks raksasa di belakang badan, huruf masuk satu-satu | ya | `text`, `sub`, `size` (otomatis dikecilin kalau gak muat), `y` |
| 02 | `cursor_click` | Kursor putih jalan, klik, riak warna aksen, kotak seleksi + label | – | `to`, `from`, `box` [x,y,w,h], `label` |
| 03 | `type_caption` | Command bar `›`, huruf ngetik, kursor blok kedip | – | `text`, `y`, `type_time` |
| 04 | `clones` | Salinan lo berjajar kiri-kanan, telat beberapa frame | ya | `count`, `spacing`, `delay`, `sides` |
| 05 | `bg_bw` | Background hitam putih, lo tetap berwarna | ya | `contrast`, `fade` |
| 06 | `freeze_sketch` | Frame beku, garis sapuan ngubah jadi sketsa pensil | – | `hold`, `wipe`, `paper` |
| 07 | `dolly_zoom` | Ruangan di belakang kayak ketarik, lo tetap | ya | `amount`, `return` |
| 08 | `glitch` | Kanal warna geser, potongan gambar loncat | – | `amount`, `seed` |
| 09 | `comment_drop` | Kartu komentar jatuh dan mantul | – | `cards` [{name, text}], `x`, `y` |
| 10 | `paper_tear` | Frame beku sobek jadi dua, video lanjut di baliknya | – | `at`, `slope`, `seed` |

## 10 efek bonus

| # | `type` | Yang keliatan | Mask | Pengaturan penting |
|---|---|---|---|---|
| 11 | `spotlight` | Ruangan meredup, cahaya cuma di lo | ya | `dark` |
| 12 | `neon_outline` | Garis neon nyala di sekeliling badan | ya | `thickness`, `glow`, `color` |
| 13 | `echo_trail` | Bayangan gerakan lo ketinggalan di belakang | ya | `count`, `step`, `color` |
| 14 | `impact_frame` | Frame hitam-putih kontras ala anime + garis kecepatan (0,3–0,5 dtk aja) | – | `lines`, `tint` |
| 15 | `vhs` | Rekaman VHS: garis scan, noise, tulisan PLAY + jam | – | `label`, `clock_start` |
| 16 | `mosaic_reveal` | Kotak-kotak besar yang makin tajam | – | `max_block`, `reverse` |
| 17 | `duotone` | Semua warna jadi dua warna merek lo | – | `dark`, `light`, `mix` |
| 18 | `polaroid` | Kilat, frame beku jadi foto berbingkai yang miring | – | `caption`, `angle`, `x`, `y` |
| 19 | `split3` | Layar kebelah tiga panel dengan zoom beda | opsional | `zooms`, `focus_y` |
| 20 | `sticker` | Lo jadi stiker bergaris tepi putih di kanvas titik-titik | ya | `outline`, `canvas`, `dots` |

Tambahan di luar 20 efek:

- `bg_world` (butuh mask): tembok di belakang lo dibuka jadi terowongan grid neon yang terus ketarik. Cocok kalau background lo polos dan `dolly_zoom` jadi gak keliatan. `floor` = baris piksel yang di bawahnya selalu dianggap depan (meja).
- `pill`: tulisan besar dalam kapsul buat judul atau CTA.
- **Nama efek di layar:** kasih `"name": "KLONING"` di efek mana pun, namanya muncul di kiri atas selama efek jalan. `name_start` / `name_end` kalau mau muncul lebih awal (pas lo mulai nyebut namanya). Posisi diatur di `"label": {"x", "y", "size"}`.
- **Panel muncul beberapa kali:** `"windows": [[7, 9.3], [12.6, 51]]`. Ukuran teks: `font_size`, `row`.

Semua efek punya `start` dan `end` (detik). Warna aksen dan gelap diatur sekali di `accent` dan `ink`.

## Prompt siap pakai

**Prompt 1: timing**
```
Ini video gue ngomong (terlampir). Transkrip, lalu bikin tabel: tiap nama efek yang gue sebut,
detik mulai dan selesai katanya. Jangan ngarang kata yang gak kedengeran; tandain yang lo ragu.
```

**Prompt 2: pasang efek**
```
Baca templates/efek-talking-head/README.md dan scripts/effects/effects.py di repo ini.
Bikin public/assets/efek.json dari tabel timing tadi: tiap efek mulai pas namanya gue sebut
dan selesai sebelum efek berikutnya. Warna merek gue: {{aksen}} dan {{gelap}}.
Jalanin --preview di tengah tiap efek, liat still-nya satu-satu, dan benerin yang salah
(teks kepotong, panel nutup muka, mask bocor) sebelum render penuh.
```

**Prompt 3: efek baru**
```
Tambahin efek baru di scripts/effects/effects.py: {{jelasin efeknya kayak ngobrol}}.
Ikutin pola fungsi fx_ yang ada (frame, mask, detik lokal, durasi, pengaturan, state, warna).
Tes di video gue pakai --preview, tunjukin still-nya ke gue.
```

## Yang sering salah

- **Mask bocor** (tembok ikut jadi "orang"): ganti `"mask_model"` ke `isnet-general-use`, atau rekam ulang dengan background yang kontras sama baju.
- **Sketsa kosong:** `freeze_sketch` butuh tekstur. Footage yang overexposed hasilnya putih polos.
- **Dolly zoom belang:** bekas badan ditambal otomatis. Kalau lo banyak gerak di segmen itu, kecilin `amount`.
- **`bg_bw` gak keliatan:** kalau tembok lo udah netral (putih, krem, abu), set `contrast` ke 0.6 biar background jadi abu gelap.
- **Efek numpuk:** dua efek boleh jalan bareng, urutannya ikut `start`. Efek beku (`freeze_sketch`, `paper_tear`, `polaroid`) nimpa efek sebelumnya.
- **Audio:** suara asli tetap jalan waktu gambar beku. Itu sengaja.
