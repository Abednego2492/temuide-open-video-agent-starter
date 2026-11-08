# Template: Kanvas Hidup 🧵

Video journal perjalanan hidup / karir lo, digambar Claude di atas kertas lecek. Satu benang tinta hitam nyambung dari satu fase ke fase berikutnya, karakter kartun mini muka lo jalan di benang itu, dan di akhir kamera mundur nunjukin semuanya: kusut, tapi nyambung.

Gak butuh footage kamera. Bahannya cuma cerita lo, satu foto muka (buat referensi karakter), dan (opsional) voice clone lo.

> Template ini **gak berisi cerita siapa pun**. Semua isi cerita ada di `story.template.json` dan `vo-lines.template.json` sebagai placeholder `{{...}}`. Isi pakai cerita lo sendiri.

## Isi folder

| File | Fungsinya |
|---|---|
| `README.md` | Alur kerja dari nol sampai posting (file ini) |
| `STYLE_GUIDE.md` | Aturan visual lengkap: kertas, benang, font, warna, karakter, kamera, SFX, timing |
| `PROMPTS.md` | Prompt siap copy-paste ke Claude untuk tiap tahap |
| `story.template.json` | Struktur cerita (stasiun) yang lo isi |
| `vo-lines.template.json` | Naskah voice over dengan audio tag Eleven v4 |
| `REMIX.md` | Versi kedua: video lo ngomong (di-cutout) di atas time-lapse kanvas, pakai `scripts/remix/` |

## Yang lo siapin

- Claude (app atau Claude Code) dengan akses bikin file + internet ke npm/PyPI/GitHub.
- Cerita lo: 4–7 fase hidup/karir. Tiap fase: tahun, peran, **satu kejadian lucu yang beneran kejadian**, satu angka bukti.
- 1 foto muka yang jelas (depan, terang) buat referensi karakter kartun. Foto ini cuma dipakai di sesi lo sendiri, jangan di-commit.
- Opsional: API key ElevenLabs + voice ID clone suara lo (lihat `docs/VOICEOVER.md`).

## Alur kerja

### 0. Privasi dulu
- **Jangan upload CV mentah** ke repo, ke issue, atau ke tempat publik. Kalau mau ngasih CV ke Claude, kasih di chat pribadi lo aja, dan suruh dia ambil seperlunya.
- Gak ada nomor HP, email, alamat, gaji, atau nama atasan di layar.
- Nama perusahaan lama opsional. Banyak kreator lebih aman pakai kategori ("retail", "startup", "dealer mobil").
- `public/assets/` dan `public/references/` udah di-`.gitignore`. Taruh foto dan VO di situ.

### 1. Tulis cerita (15–30 menit, ini bagian paling penting)
Salin `story.template.json` ke `public/assets/story.json`, isi tiap stasiun. Aturan:
- **Satu fase = satu kejadian spesifik.** "Kerja keras banget" itu datar. "Jam 2 pagi masih demo aplikasi ke klien" itu kebayang.
- **Realita pakai bahasa lo sendiri**, kayak cerita ke temen. Anekdot karangan AI langsung kerasa palsu.
- **Satu angka bukti per fase** buat stempel (cabang, klien, kota, tahun, follower).
- Ekspresi karakter beda tiap fase (lihat daftar di STYLE_GUIDE).

### 2. Tulis naskah VO
Salin `vo-lines.template.json`, ganti placeholder. Satu baris per stasiun + hook + intro + reveal + CTA. Total 90–150 detik. Baca keras-keras: kalau lo gak bakal ngomong gitu ke temen, tulis ulang.

### 3. Generate VO (opsional tapi bikin beda jauh)
```bash
npm run vo -- public/assets/vo-lines.json public/vo --takes 4 --lang id
```
Model `eleven_v4`. Angka dieja ("tiga puluh", bukan "30"), singkatan Inggris ditulis fonetik (`AI` → `Ei-Ai`). Detail di `docs/VOICEOVER.md`. Tanpa VO, timing tiap stasiun pakai durasi baca teks (±2,5 kata/detik + 1,5 detik).

### 4. Suruh Claude bikin script table
Pakai **Prompt 1** di `PROMPTS.md`. Hasilnya tabel: stasiun, tahun, peran, realita, stempel, ekspresi, baris VO, durasi. Cek, koreksi, baru lanjut.

### 5. Suruh Claude bangun video
Pakai **Prompt 2**. Claude baca `STYLE_GUIDE.md`, bikin komposisi Remotion (kertas prosedural, benang SVG, karakter SVG, kamera), timeline digerakin durasi VO.

### 6. Cek still sebelum render penuh
```bash
COMP=KanvasHidup npm run stills -- 0 120 600 1500 3000
```
Prompt 3 nyuruh Claude ngecek: teks nabrak properti, karakter kepotong tepi, reveal kekecilan di HP. Benerin dulu, baru render.

### 7. Render
```bash
COMP=KanvasHidup TOTAL=<jumlah_frame> npm run render:chunks
```
Render per bagian biar aman kalau sandbox restart. Audio di-master ke −14 LUFS.

### 8. Review & revisi
Tonton di HP. Kasih catatan pakai timestamp ("0:42 tulisan merah ketutup karakter"). Prompt 4 buat revisi terarah tanpa render ulang semua.

### 9. Posting
- Cover: frame hook atau reveal.
- Caption: perkenalan singkat + "kusut tapi nyambung" + ajakan komen.
- Mau dipakai lagi? Lihat `REMIX.md`: lo ngomong di depan time-lapse kanvas ini.

## Estimasi waktu

| Tahap | Waktu |
|---|---|
| Nulis cerita + naskah | 30–60 menit |
| VO (4 take per baris) | 5–10 menit |
| Claude bangun komposisi | 20–40 menit |
| Still check + revisi | 10–20 menit |
| Render 2 menit (2 CPU) | 15–25 menit |

## Kesalahan yang paling sering

- Cerita kebanyakan fase → tiap fase cuma lewat. 5 fase yang kuat > 9 fase yang tipis.
- Semua teks muncul barengan → penonton gak tau mana yang dibaca. Satu elemen masuk per beat.
- Reveal akhir terlalu kecil di HP → zoom out cukup sampai benang kebaca, jangan sampai teksnya jadi semut.
- VO dibikin setelah animasi → timing jadi maksa. **VO dulu, animasi ngikut.**
