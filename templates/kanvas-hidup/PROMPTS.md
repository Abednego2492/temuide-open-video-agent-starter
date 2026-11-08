# Prompt siap pakai

Copy-paste ke Claude per tahap. Ganti bagian `{{...}}`. Jangan lompat tahap: tiap tahap ngecek tahap sebelumnya.

---

## Prompt 1 — Script table

```
Baca templates/kanvas-hidup/README.md dan STYLE_GUIDE.md.
Ini cerita gue (public/assets/story.json) dan naskah VO (public/assets/vo-lines.json).

Bikin script table: stasiun, tahun, peran, realita (maks 2 baris), stempel (1 angka),
ekspresi karakter, bentuk benang, baris VO, estimasi durasi.

Aturan:
- Jangan nambah kejadian yang gak ada di cerita gue.
- Kalau ada realita yang kepanjangan atau datar, kasih 2 alternatif pakai kata-kata gue sendiri.
- Tandai kalau ada info pribadi (HP, email, gaji, nama orang) yang harus diapus.
Jangan bikin video dulu.
```

## Prompt 2 — Bangun video

```
Script table udah gue approve. Sekarang bangun komposisi Remotion "KanvasHidup" 1080x1920 30fps.
Ikutin STYLE_GUIDE.md persis: kertas prosedural, satu benang tinta SVG yang digambar,
karakter mini <Mini expr> dari foto referensi gue (public/assets/face.jpg),
kamera follow karakter, timeline dari durasi VO (public/vo/*.wav).

Urutan kerja:
1. Generate kertas dulu, kirim still-nya.
2. Bikin karakter dengan 3 ekspresi, kirim still-nya.
3. Baru susun semua stasiun.
Jangan render penuh sebelum gue liat still.
```

## Prompt 3 — Cek still

```
Render still di: hook, tiap stasiun di tengah tahan, reveal, CTA.
Lihat sendiri tiap still dan laporin:
- teks nabrak properti atau karakter
- karakter / teks kepotong tepi frame atau masuk area UI Reels (230 px atas, 380 px bawah)
- reveal kekecilan dibaca di HP
- teks pribadi yang kelewat
Benerin semua, kirim contact sheet sebelum dan sesudah. Baru render penuh.
```

## Prompt 4 — Revisi

```
Catatan gue:
- {{0:42}} {{tulisan merah ketutup karakter}}
- {{1:10}} {{jalan ke stasiun 5 kelamaan}}
Benerin cuma bagian itu, render ulang bagian yang berubah aja (render:chunks),
terus kirim still di timestamp yang sama sebelum dan sesudah.
```

## Prompt 5 — Caption posting

```
Bikinin caption Instagram dan Threads buat video ini.
IG: perkenalan singkat, 2–3 kalimat cerita, satu kalimat "kusut tapi nyambung" versi gue,
ajakan komen, 3–5 hashtag. Threads: lebih pendek, tanpa hashtag, maks 500 karakter.
Jangan pakai em dash, jangan pakai frasa kayak "di era AI" atau "game changer",
jangan pakai emoji berderet. Tulis kayak gue ngomong.
```

---

## Brief singkat (kalau mau sekali tembak)

```
Ubah cerita karir gue (story.json) jadi video Kanvas Hidup sesuai templates/kanvas-hidup.
Kertas krem lecek = kanvas hidup, benang tinta hitam nyambung antar fase,
tulisan tangan, realita merah, karakter kartun mini muka gue dengan ekspresi beda tiap fase
yang jalan di benang. Hook gimmick di awal, reveal "kusut tapi nyambung", CTA follow + komen.
VO pakai clone suara gue (Eleven v4), nada santai kayak ngobrol.
Gak ada nomor HP / email / data pribadi di layar.
```
