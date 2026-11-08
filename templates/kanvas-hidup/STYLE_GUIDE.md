# Style guide: Kanvas Hidup

Aturan ini yang bikin hasilnya kerasa "digambar tangan di kertas", bukan template motion graphic. Kasih file ini ke Claude dan minta dia ikutin, bukan improvisasi.

## 1. Konsep

- **Metafora:** kertas krem lecek = kanvas hidup. Benang tinta = perjalanan. Kusut di tengah, nyambung di akhir.
- **Satu dunia, satu kamera.** Semua stasiun ada di satu lembar kertas raksasa. Kamera yang jalan, bukan ganti slide.
- **Nada:** jujur dan lucu. Tahun + peran ditulis rapi, realitanya ditulis merah kayak coretan curhat.

## 2. Kanvas (kertas)

| Properti | Nilai |
|---|---|
| Ukuran dunia | ±2160 × (1400 × jumlah stasiun + 2000) px |
| Warna dasar | krem `#EDE3D1` → `#E2D5BE` (gradasi pelan) |
| Tekstur | noise lecek (fractal noise 3–4 oktaf) + 6–10 garis lipatan diagonal tipis, multiply 8–14% |
| Vignette | sudut lebih gelap ±12%, hangat (bukan abu-abu) |
| Grain | statis tipis, jangan animasi grain (bikin pusing di HP) |

Generate kertasnya secara prosedural sekali jadi PNG, jangan pakai foto stok.

## 3. Benang tinta

- Satu path SVG yang nyambung dari hook sampai CTA. Tiap stasiun punya **bentuk** dari benang yang sama (toga, mobil, toko, laptop, roket, dll), lalu benang lanjut berupa loop bergelombang ke stasiun berikutnya.
- Stroke `#1A1714`, 5–7 px, `stroke-linecap: round`.
- Kesan tinta: SVG `feTurbulence` + `feDisplacementMap` scale 2–3, blur 0,4, `mix-blend-mode: multiply`.
- Animasi gambar: `strokeDasharray` + offset, progress diikat ke posisi karakter. Benang gak pernah "muncul", selalu **digambar**.
- Jarak antar stasiun ≥ 1050 px supaya stasiun tetangga gak bocor ke frame.

## 4. Tipografi

| Elemen | Font | Ukuran (1080 px lebar) | Warna |
|---|---|---|---|
| Tahun | Permanent Marker | 110–130 px | `#1A1714` + garis bawah coretan |
| Peran | Caveat Bold | 46–54 px | `#1A1714` |
| Realita (curhat) | Permanent Marker | 40–46 px, kapital | merah `#C62D1F` |
| Stempel bukti | Inter 800 / Anton | 34–40 px, kotak outline 4 px, miring −6° | merah `#C62D1F`, opacity 0,85 |
| Hook & reveal | Permanent Marker | 70–90 px | hitam + satu kata merah |

Semua font dari `@fontsource` (npm) atau Google Fonts GitHub. Realita diketik per karakter (25–35 karakter/detik) dengan suara ketik. Stempel masuk dengan slam (scale 1,6 → 1,0 dalam 6 frame + SFX).

## 5. Karakter mini

- Satu komponen SVG `<Mini expr="..." />`. Kepala bulat agak besar (proporsi chibi 1:1,4), rambut + kacamata/ciri khas lo dari foto referensi, badan simpel.
- **Muka statis, ekspresi yang ganti.** Jangan bikin karakter baru per stasiun.
- Ekspresi yang disediakan: `surprised`, `waving`, `relaxed`, `tired`, `referee`, `proud`, `sleepy`, `fired-up`, `up-late`, `cheering`, `thumbs-up`, `walking`. Tambah sendiri kalau cerita lo butuh.
- Masuk: pop dengan squash & stretch (scale y 0,7 → 1,1 → 1,0). Keluar: "dikelupas" kayak stiker.
- Jalan: bob vertikal 6–8 px, langkah 2,5 Hz, SFX langkah.

## 6. Kamera

| Momen | Gerak |
|---|---|
| Hook (0–3 dtk) | zoom ke coretan kusut yang berubah jadi muka |
| Jalan antar stasiun | follow karakter, zoom 0,82, ease in-out |
| Tiap stasiun | ease ke titik tahan, zoom 1,0, sedikit drift (±10 px) biar gak mati |
| Reveal | tarik mundur sampai seluruh benang kelihatan, tahan 2–3 dtk |
| CTA | push-in ke muka karakter |

Gak ada cut keras. Semua transisi = kamera jalan di dunia yang sama.

## 7. Timing (VO yang nyetir)

```ts
let t = HOOK_END;
ST.forEach((st, i) => {
  st.t0 = t;
  st.voAt = i === 0 ? t + 12 : t + 22;          // mulai ngomong pas karakter masih jalan masuk
  st.t1 = Math.max(st.voAt + VO[st.key] + 14, t + 140);
  t = st.t1;
});
```

- Hook ≤ 3 dtk. Intro ≤ 6 dtk. Tiap stasiun 8–16 dtk. Reveal 5–8 dtk. CTA 4–6 dtk.
- Teks satu stasiun cuma tampil di stasiunnya, lalu muncul lagi bareng-bareng pas reveal.

## 8. Suara

| SFX | Kapan |
|---|---|
| langkah | karakter jalan |
| pensil | benang lagi digambar |
| pop | karakter muncul |
| ketik | realita diketik |
| slam | stempel |
| whoosh + ding | reveal |

SFX bisa disintesis sendiri (noise + envelope) biar bebas lisensi. Musik: tambahin dari library Instagram/TikTok pas upload, volume rendah. Master −14 LUFS, true peak −1 dB.

## 9. Teks di layar: wajib & dilarang

- ✅ Tahun, peran, satu realita, satu angka.
- ✅ CTA yang jelas di akhir.
- ❌ Nomor HP, email, alamat, gaji.
- ❌ Paragraf panjang. Maks 2 baris realita per stasiun.
- ❌ Logo perusahaan (pakai teks aja).

## 10. Format output

1080 × 1920, 30 fps, H.264 CRF 16–18, AAC 192 kbps, durasi 60–150 dtk. Safe zone Reels: hindari teks penting di 230 px teratas dan 380 px terbawah.
