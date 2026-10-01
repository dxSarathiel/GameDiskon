"""
Sistem tampilan bersama untuk semua halaman gamediskon.my.id.

Tema: "rak promo minimarket" — label harga kuning di tepi rak, angka potongan merah,
harga coret, dan stempel GRATIS. Semua halaman memakai satu file gaya: docs/gaya.css.
Mengubah tampilan cukup di file ini; halaman lain ikut berubah otomatis.
"""

import base64
import hashlib
import json
import os
from html import escape

# Username bot alarm harga (tanpa @). Kosongkan untuk menyembunyikan semua ajakan alarm.
USERNAME_BOT_ALARM = "DiskonGame_bot"

LINK_TELEGRAM = ""   # diisi radar_diskon.py saat berjalan, supaya tombol Telegram muncul di semua halaman

# Huruf Archivo (lisensi OFL) di-host sendiri: file .woff2 ada di folder aset/ dan disalin ke docs/fonts/.
# Dulu diambil dari Google Fonts, tapi CSS eksternal itu menahan tampilan halaman (render-blocking)
# dan hurufnya datang terlambat sehingga judul besar "melompat" (CLS).
FOLDER_REPO = os.path.dirname(os.path.abspath(__file__))
FOLDER_ASET = os.path.join(FOLDER_REPO, "aset")   # kalau file ada di akar repo (unggah lewat web), itu juga dicari
FILE_ASET = {                      # nama di aset/ -> alamat di situs
    "archivo-latin.woff2": "fonts/archivo-latin.woff2",
    "archivo-latin-ext.woff2": "fonts/archivo-latin-ext.woff2",
    "permanent-marker-latin.woff2": "fonts/permanent-marker-latin.woff2",   # huruf spidol (Apache 2.0)
    "og-gamediskon.png": "og-gamediskon.png",
}
FONT_PRELOAD = "/fonts/archivo-latin.woff2"

# Gambar pratinjau bawaan (Facebook, WhatsApp, Telegram, X) untuk halaman yang tidak punya gambar sendiri
OG_BAWAAN = "https://gamediskon.my.id/og-gamediskon.png"

CSS = r"""
/* ---------- Huruf (di-host sendiri) ---------- */
@font-face {
  font-family: "Archivo"; font-style: normal; font-weight: 400 900; font-stretch: 62% 125%; font-display: swap;
  src: url(/fonts/archivo-latin-ext.woff2) format("woff2");
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
}
@font-face {
  font-family: "Archivo"; font-style: normal; font-weight: 400 900; font-stretch: 62% 125%; font-display: swap;
  src: url(/fonts/archivo-latin.woff2) format("woff2");
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
/* Huruf spidol untuk stiker & coretan tangan. Hanya hiasan: kalau belum termuat, dipakai Archivo (optional = tanpa lompatan). */
@font-face {
  font-family: "Spidol"; font-style: normal; font-weight: 400; font-display: optional;
  src: url(/fonts/permanent-marker-latin.woff2) format("woff2");
  unicode-range: U+0000-00FF, U+2013-2014, U+2018-201E, U+2022, U+2026, U+20AC, U+2212;
}

/* =========================================================
   GameDiskon — tema "Etalase Malam" (v3)
   Toko promo yang buka malam: latar arang hangat, label harga kuning
   di tepi rak, stiker potongan merah, kupon game gratis, papan LED
   berjalan, dan struk kasir untuk riwayat harga.
   Semua nama class lama tetap dipakai.
   ========================================================= */

/* ---------- Token ---------- */
:root {
  color-scheme: dark;
  --malam: #15120e;        /* latar halaman */
  --malam-2: #1f1a14;      /* kartu */
  --malam-3: #2a231b;      /* kartu saat disorot, input */
  --hitam: #0c0a08;        /* papan LED, kaki */
  --garis: #3a3127;
  --garis-terang: #55483a;
  --tinta: #f6efe1;        /* teks utama   16,3:1 di --malam */
  --redup: #b9ab93;        /* teks kedua    8,3:1 di --malam, 7,6:1 di --malam-2 */
  --kertas: #f6efe1;       /* kupon, struk */
  --tinta-gelap: #1a140d;  /* teks di atas kuning/kertas */
  --redup-gelap: #5e5243;  /* teks kedua di atas kertas  6,6:1 */
  --kuning: #ffc928;       /* label harga */
  --kuning-tua: #5a4300;   /* teks kedua di atas kuning  6,1:1 */
  --merah: #d92d1b;        /* stiker potongan (teks putih 4,8:1) */
  --merah-terang: #ff6b4a; /* teks merah di latar gelap  6,6:1 */
  --hijau: #6fdc8c;        /* harga termurah, kabar baik */
  --led: #ffb22e;
  --tautan: #ffd45c;
  --sempit: 68%;           /* lebar huruf papan promo */
  --lebar-isi: 76rem;
  --sudut: 6px;
  --cepat: 160ms cubic-bezier(.2, .7, .3, 1);
}

*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body {
  margin: 0; background: var(--malam); color: var(--tinta);
  font-family: "Archivo", system-ui, sans-serif; font-size: 1rem; line-height: 1.6;
  font-size-adjust: from-font;          /* huruf cadangan tetap seukuran selama Archivo dimuat */
  -webkit-font-smoothing: antialiased;
}
img { max-width: 100%; height: auto; }
a { color: var(--tautan); text-underline-offset: 3px; text-decoration-thickness: 1px; transition: color var(--cepat); }
a:hover { color: var(--tinta); text-decoration-thickness: 2px; }
:focus-visible { outline: 3px solid var(--kuning); outline-offset: 3px; border-radius: 2px; }
::selection { background: var(--kuning); color: var(--tinta-gelap); }
.wadah { max-width: var(--lebar-isi); margin: 0 auto; padding: 0 1.25rem; }
.lompat { position: absolute; left: -999px; }
.lompat:focus { left: 1rem; top: 1rem; z-index: 50; background: var(--kuning); color: var(--tinta-gelap); padding: .5rem 1rem; font-weight: 800; }

/* ---------- Kepala ---------- */
.pita {
  position: relative; isolation: isolate; overflow: hidden;
  background: var(--malam); border-bottom: 1px solid var(--garis);
}
/* titik-titik cetak (halftone) di pojok, seperti brosur promo */
.pita::before {
  content: ""; position: absolute; z-index: -1; pointer-events: none;
  top: -4rem; right: -6rem; width: 38rem; height: 30rem;
  background: radial-gradient(circle, rgba(217, 45, 27, .5) 1.6px, transparent 2.2px) 0 0 / 14px 14px;
  -webkit-mask-image: radial-gradient(closest-side, #000, transparent);
          mask-image: radial-gradient(closest-side, #000, transparent);
}
.pita a { color: var(--tinta); }
.nav { display: flex; align-items: center; gap: 1.5rem; padding: 1rem 0; flex-wrap: wrap; }

/* Logo: "GAME" + stiker merah "DISKON" */
.logo {
  display: inline-flex; align-items: center; gap: .3rem; text-decoration: none;
  font-weight: 900; font-stretch: var(--sempit); font-size: 1.75rem; line-height: 1;
  text-transform: uppercase; letter-spacing: .01em;
}
.logo span {
  display: inline-block; background: var(--merah); color: #fff; padding: .2rem .45rem .15rem;
  transform: rotate(-3deg); box-shadow: 3px 3px 0 var(--hitam);
}
.logo:hover span { transform: rotate(-1deg); }

.nav ul { list-style: none; display: flex; gap: .25rem; margin: 0 0 0 auto; padding: 0; flex-wrap: wrap; }
.nav ul a {
  display: block; text-decoration: none; font-weight: 600; font-size: .95rem; color: var(--redup);
  padding: .6rem .7rem; position: relative; transition: color var(--cepat);
}
.nav ul a:hover { color: var(--tinta); }
.nav ul a[aria-current] { color: var(--tinta); }
.nav ul a[aria-current]::after {          /* coretan stabilo kuning di bawah menu aktif */
  content: ""; position: absolute; left: .55rem; right: .55rem; bottom: .3rem; height: .4rem; z-index: -1;
  background: var(--kuning); opacity: .85; transform: skew(-12deg) rotate(-1deg);
}
.nav ul a[aria-current] { color: var(--tinta); isolation: isolate; }

.tombol-tg {
  display: inline-flex; align-items: center; gap: .5rem; white-space: nowrap; min-height: 2.75rem;
  background: var(--kuning); color: var(--tinta-gelap) !important; text-decoration: none; font-weight: 800; font-size: .95rem;
  padding: .55rem 1rem; border-radius: var(--sudut); box-shadow: 3px 3px 0 var(--merah);
  transition: transform var(--cepat), box-shadow var(--cepat);
}
.tombol-tg::before {             /* ikon pesawat kertas Telegram */
  content: ""; width: 1rem; height: 1rem; flex: none; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.tombol-tg:hover { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--merah); }

/* ---------- Hero ---------- */
.hero {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 21rem); gap: 2.5rem 4rem;
  align-items: center; padding: 3rem 0 3.75rem;
}
.kicker {
  font-family: "Spidol", "Archivo", sans-serif; font-weight: 400; color: var(--kuning) !important;
  font-size: 1.15rem !important; margin: 0 0 .9rem !important; transform: rotate(-2deg); transform-origin: left;
}
.hero h1 {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase;
  font-size: clamp(2.9rem, 8.2vw, 6.4rem); line-height: .9; letter-spacing: -.005em; margin: 0;
  text-wrap: balance;
}
.hero h1 .baris { display: block; }    /* tiga baris tetap: Diskon Steam / hari ini, / dalam Rupiah */
.sorot {                          /* "dalam Rupiah" di atas sapuan stabilo kuning */
  display: inline-block; margin-top: .06em; color: var(--tinta-gelap); padding: .02em .14em 0; white-space: nowrap;
  background: linear-gradient(100deg, transparent .2em, var(--kuning) .25em, var(--kuning) calc(100% - .2em), transparent calc(100% - .15em));
  -webkit-box-decoration-break: clone; box-decoration-break: clone;
}
.hero p { font-size: 1.08rem; margin: 1.5rem 0 0; max-width: 50ch; color: var(--redup); }
.hero .event {
  display: inline-block; max-width: none; margin-top: 1.5rem;
  background: var(--merah); color: #fff; font-weight: 800; font-size: .98rem;
  padding: .55rem .95rem; transform: rotate(-1deg); box-shadow: 4px 4px 0 var(--hitam);
}
.hero .event a { color: #fff; text-decoration: none; }
.hero .event a::after { content: " →"; }
.hero .event a:hover { text-decoration: underline; }

/* "Potongan terbesar hari ini": label harga kuning yang digantung tali */
.unggulan {
  position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: .15rem;
  margin-top: 2.5rem; padding: 2.3rem 1.5rem 1.4rem; text-decoration: none;
  background: var(--kuning); color: var(--tinta-gelap) !important; border-radius: 4px 4px 14px 14px;
  box-shadow: 10px 12px 0 rgba(0, 0, 0, .45);
  transform: rotate(2.5deg); transform-origin: 50% -2.5rem;
  transition: transform 400ms cubic-bezier(.3, 1.6, .5, 1);
}
.unggulan::before {               /* lubang tali */
  content: ""; position: absolute; top: .85rem; left: 50%; width: .8rem; height: .8rem; margin-left: -.4rem;
  border-radius: 50%; background: var(--malam); box-shadow: inset 0 0 0 2px rgba(0, 0, 0, .35);
}
.unggulan::after {                /* tali */
  content: ""; position: absolute; bottom: calc(100% - 1.25rem); left: 50%; width: 2px; height: 3.5rem;
  background: linear-gradient(var(--garis-terang), var(--redup)); transform: rotate(-2.5deg); transform-origin: bottom;
}
.unggulan:hover { transform: rotate(-1deg); }
.unggulan-ket { font-family: "Spidol", "Archivo", sans-serif; font-size: 1.05rem; color: var(--merah); }
.unggulan .stiker { position: static; margin: .2rem 0 .5rem; padding: 0; background: none; box-shadow: none; }
.unggulan .stiker .potong { position: absolute; top: -1.4rem; right: -1.6rem; }
.unggulan .stiker strong { font-size: clamp(2.6rem, 6vw, 3.4rem); }
.unggulan .stiker s { color: var(--kuning-tua); }
.unggulan-nama { font-weight: 800; font-size: 1.2rem; line-height: 1.2; }
.unggulan:hover .unggulan-nama { text-decoration: underline; }

/* ---------- Papan LED berjalan (hiasan, isinya sama dengan rak) ---------- */
.led {
  position: relative; overflow: hidden; background: var(--hitam);
  border-top: 1px solid var(--garis); padding: .7rem 0;
}
.led::after {                     /* kisi titik LED */
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(circle, transparent 1.1px, rgba(12, 10, 8, .35) 1.5px) 0 0 / 4px 4px;
}
.led-isi {
  display: flex; width: max-content; gap: 3rem; margin: 0; padding: 0; list-style: none;
  font-weight: 900; font-stretch: var(--sempit); font-size: 1.45rem; line-height: 1.2; text-transform: uppercase;
  letter-spacing: .03em; color: var(--led); text-shadow: 0 0 6px rgba(255, 178, 46, .7);
  animation: jalan 70s linear infinite;
}
.led-isi li { white-space: nowrap; }
.led-isi b { color: var(--merah-terang); text-shadow: 0 0 6px rgba(255, 107, 74, .7); margin: 0 .35rem; }
.led:hover .led-isi { animation-play-state: paused; }
@keyframes jalan { to { transform: translateX(-50%); } }

/* ---------- Judul & teks umum ---------- */
main { padding: 3rem 0 5rem; }
.bagian { margin-bottom: 4.5rem; }
h1, h2, h3 { font-weight: 800; line-height: 1.1; }
h2 {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase; letter-spacing: .005em;
  font-size: clamp(1.9rem, 4.4vw, 2.8rem); line-height: 1; margin: 0 0 .6rem;
}
.bagian > h2 { display: flex; align-items: center; gap: .7rem; }
.bagian > h2::before {            /* ikon label harga kecil */
  content: ""; width: 1.6rem; height: .95rem; flex: none; background: var(--kuning);
  clip-path: polygon(28% 0, 100% 0, 100% 100%, 28% 100%, 0 50%);
}
h3 { font-size: 1.2rem; }
.judul-halaman {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase;
  font-size: clamp(2.3rem, 6vw, 4rem); line-height: .95; margin: 0 0 1.5rem; max-width: 20ch;
}
.catatan { color: var(--redup); margin: 0 0 1.75rem; max-width: 64ch; }
.jejak { font-size: .88rem; color: var(--redup); margin: 0 0 1.25rem; }
.jejak ol { list-style: none; display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; }
.jejak li + li::before { content: "/"; margin-right: .4rem; color: var(--garis-terang); }
.jejak a { color: var(--redup); }
.jejak a:hover { color: var(--tinta); }

/* ---------- Stiker potongan (bintang merah) ---------- */
.potong {
  position: relative; z-index: 1; isolation: isolate;
  display: inline-grid; place-items: center; width: 4.4rem; height: 4.4rem; flex: none;
  color: #fff; font-weight: 900; font-stretch: var(--sempit); font-size: 1.3rem; line-height: 1;
  font-variant-numeric: tabular-nums; transform: rotate(-10deg);
}
.potong::before {                 /* bentuk bintang ada di lapisan sendiri, teksnya tidak ikut terpotong */
  content: ""; position: absolute; inset: 0; z-index: -1; background: var(--merah);
  clip-path: polygon(50% 0%, 61% 11%, 75% 5%, 79% 20%, 95% 21%, 89% 36%, 100% 50%, 89% 64%, 95% 79%, 79% 80%, 75% 95%, 61% 89%, 50% 100%, 39% 89%, 25% 95%, 21% 80%, 5% 79%, 11% 64%, 0% 50%, 11% 36%, 5% 21%, 21% 20%, 25% 5%, 39% 11%);
  filter: drop-shadow(2px 3px 0 rgba(0, 0, 0, .35));
}

/* ---------- Game gratis Epic: kupon ---------- */
.gratis { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.75rem;
          grid-template-columns: repeat(auto-fill, minmax(min(100%, 21rem), 1fr)); }
.gratis > li { position: relative; }
.gratis a {
  display: block; position: relative; height: 100%; text-decoration: none;
  background: var(--kertas); color: var(--tinta-gelap); border-radius: var(--sudut); overflow: hidden;
  box-shadow: 6px 6px 0 rgba(0, 0, 0, .45); transition: transform var(--cepat), box-shadow var(--cepat);
}
.gratis a:hover { transform: translate(-2px, -2px); box-shadow: 8px 8px 0 rgba(0, 0, 0, .45); }
.gratis img { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: var(--malam-3); }
/* garis sobek kupon + dua takik di sisi, digambar dengan lingkaran warna latar (teks tidak dimask) */
.gratis h3 { position: relative; margin: 0; padding: 1.1rem 1.25rem .3rem; font-size: 1.35rem; color: var(--tinta-gelap);
             border-top: 2px dashed rgba(26, 20, 13, .35); }
.gratis h3::before, .gratis h3::after {
  content: ""; position: absolute; top: -.75rem; width: 1.4rem; height: 1.4rem; border-radius: 50%; background: var(--malam);
}
.gratis h3::before { left: -.7rem; }
.gratis h3::after { right: -.7rem; }
.stempel {
  position: absolute; top: .8rem; left: .8rem; z-index: 1;
  font-family: "Spidol", "Archivo", sans-serif; font-weight: 400; font-size: 1.15rem; letter-spacing: .04em; line-height: 1;
  background: var(--merah); color: #fff; padding: .45rem .7rem .35rem;
  outline: 2px dashed rgba(255, 255, 255, .7); outline-offset: -5px;
  transform: rotate(-6deg); box-shadow: 3px 3px 0 rgba(0, 0, 0, .4);
}
.batas { margin: 0; padding: 0 1.25rem 1.2rem; color: var(--redup-gelap); font-size: .95rem; }
.sisa { color: var(--merah-terang); font-weight: 800; }
.gratis .sisa { color: #b42010; }

/* ---------- Kontrol saring & urut ---------- */
.kontrol { display: flex; flex-wrap: wrap; gap: .75rem 1.5rem; align-items: center; margin: 0 0 2rem; }
.saring { display: flex; flex-wrap: wrap; gap: .5rem; }
.saring button, .kontrol select {
  font: inherit; font-weight: 700; font-size: .92rem; color: var(--tinta); background: transparent;
  border: 1.5px solid var(--garis-terang); border-radius: var(--sudut); padding: .5rem .95rem; min-height: 2.75rem; cursor: pointer;
  transition: color var(--cepat), border-color var(--cepat), background var(--cepat);
}
.saring button:hover, .kontrol select:hover { border-color: var(--kuning); }
.saring button[aria-pressed="true"] { background: var(--kuning); border-color: var(--kuning); color: var(--tinta-gelap); }
.kontrol select { padding-right: 2.2rem; appearance: none; -webkit-appearance: none; background-color: var(--malam-2);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b9ab93' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right .75rem center; background-size: 1rem; }
.kontrol label { display: flex; gap: .6rem; align-items: center; color: var(--redup); margin-left: auto; font-size: .92rem; }
.hasil-saring { color: var(--redup); margin: -1rem 0 1.5rem; min-height: 1.5em; }

/* ---------- Rak diskon Steam ---------- */
.rak { list-style: none; margin: 0; padding: 0; display: grid; gap: 2.25rem 1.25rem;
       grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr)); }
.barang {
  position: relative; display: flex; flex-direction: column;
  background: var(--malam-2); border-radius: var(--sudut) var(--sudut) 0 0;
  box-shadow: 0 14px 0 -6px var(--garis);          /* bibir rak di bawah label */
  transition: background var(--cepat);
}
.barang:hover { background: var(--malam-3); }
.barang[hidden] { display: none; }
.barang > a:first-child { display: block; text-decoration: none; color: var(--tinta); }
.barang img { display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; background: var(--malam-3); border-radius: var(--sudut) var(--sudut) 0 0; }
.barang h3 { font-size: 1.05rem; line-height: 1.3; margin: .85rem 1rem .25rem; }
.barang > a:first-child:hover h3 { text-decoration: underline; text-decoration-color: var(--kuning); text-decoration-thickness: 2px; text-underline-offset: 3px; }
.barang .ulasan, .barang .terendah { margin: 0 1rem; font-size: .85rem; }
.barang .ulasan { color: var(--redup); display: flex; align-items: center; gap: .35rem; }
.barang .ulasan::before {        /* ikon jempol */
  content: ""; width: .9rem; height: .9rem; flex: none; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.barang .terendah { margin-top: .4rem; color: var(--hijau); font-weight: 700; }
.barang .terendah::before { content: "▼ "; font-size: .7em; }

/* label harga kuning menempel di tepi rak (urutan diatur lewat `order`, HTML tidak berubah) */
.beli {
  order: 2; align-self: flex-start; margin: .7rem 1rem .9rem; padding: .35rem 0; min-height: 2.75rem;
  display: inline-flex; align-items: center; gap: .35rem;
  font-size: .88rem; font-weight: 700; color: var(--tautan) !important; text-decoration: none;
}
.beli::after { content: "↗"; }
.beli:hover { text-decoration: underline; }
.label-rak {
  order: 3; margin-top: auto;
  background: var(--kuning); color: var(--tinta-gelap); padding: .7rem 1rem .65rem;
  border-top: 3px solid var(--tinta-gelap);
}
.label-rak .potong { position: absolute; top: .45rem; right: .45rem; }   /* stiker ditempel di pojok sampul game */
.label-rak div { display: flex; align-items: baseline; gap: .7rem; }
.label-rak .harga { display: flex; align-items: baseline; flex-wrap: wrap; gap: .1rem .55rem; line-height: 1.1; }
.label-rak strong { white-space: nowrap; font-weight: 900; font-stretch: var(--sempit); font-size: 1.85rem; font-variant-numeric: tabular-nums; }
.label-rak s { font-size: .85rem; color: var(--kuning-tua); font-variant-numeric: tabular-nums; }
.kosong { background: var(--malam-2); border: 1.5px dashed var(--garis-terang); border-radius: var(--sudut); padding: 1.25rem; max-width: 64ch; color: var(--redup); }

/* ---------- Kotak voucher (kupon gunting) & alarm ---------- */
.voucher {
  position: relative; margin: 0 0 1.75rem; max-width: 46rem; padding: 1.6rem 1.75rem;
  background: var(--kertas); color: var(--tinta-gelap); border-radius: var(--sudut);
  outline: 2px dashed rgba(26, 20, 13, .45); outline-offset: -10px;
  box-shadow: 6px 6px 0 rgba(0, 0, 0, .45);
}
.voucher::before {                /* gunting di garis potong */
  content: "✂"; position: absolute; top: 1px; left: 1.75rem; font-size: 1.15rem; line-height: 1;
  color: var(--tinta-gelap); background: var(--kertas); padding: 0 .3rem;
}
.voucher h2 { font-size: 1.7rem; margin: 0 0 .5rem; color: var(--tinta-gelap); }
.voucher p { margin: 0 0 .7rem; color: var(--redup-gelap); }
.voucher p strong { color: var(--tinta-gelap); }
.voucher a:not(.tombol) { color: #8a2a10; }
.voucher b, .voucher .kode b {
  color: var(--tinta-gelap); background: var(--kuning); padding: .05rem .45rem; border-radius: 3px;
  font-weight: 800; letter-spacing: .04em; font-variant-numeric: tabular-nums;
}
.voucher .tombol { margin: .5rem 0 .9rem; box-shadow: 3px 3px 0 var(--tinta-gelap); }
.voucher .ungkap { font-size: .82rem; margin: 0; }
.voucher .sisa { color: #b42010; }
.voucher.lebar { max-width: none; display: flex; flex-wrap: wrap; gap: 1rem 2.5rem; align-items: center; justify-content: space-between; }
.voucher.lebar > div { flex: 1 1 28rem; }
.voucher.lebar > div > :last-child { margin-bottom: 0; }
.voucher.lebar .tombol { margin: 0; }
/* Alarm harga: catatan di papan gabus, bukan kupon */
.voucher.alarm {
  background: var(--malam-2); color: var(--tinta); outline: 0; border: 1px solid var(--garis);
  box-shadow: none;
}
.voucher.alarm::before {          /* selotip */
  content: ""; top: -.6rem; left: 2rem; width: 5.5rem; height: 1.3rem; padding: 0;
  background: rgba(255, 201, 40, .75); transform: rotate(-4deg);
}
.voucher.alarm h2 { color: var(--tinta); }
.voucher.alarm p { color: var(--redup); }
.voucher + .voucher { margin-bottom: 4.5rem; }

/* ---------- Tombol ---------- */
.tombol {
  display: inline-flex; align-items: center; justify-content: center; gap: .4rem; min-height: 2.9rem;
  background: var(--kuning); color: var(--tinta-gelap) !important; text-decoration: none; font-weight: 800;
  padding: .65rem 1.25rem; border-radius: var(--sudut); margin: 0 .6rem .6rem 0;
  box-shadow: 3px 3px 0 var(--merah); transition: transform var(--cepat), box-shadow var(--cepat);
}
.tombol:hover { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--merah); text-decoration: none; }
.tombol:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--merah); }
.tombol.kedua { background: transparent; color: var(--tinta) !important; box-shadow: inset 0 0 0 1.5px var(--garis-terang); }
.tombol.kedua:hover { box-shadow: inset 0 0 0 1.5px var(--kuning); transform: none; }

/* ---------- Tanya jawab ---------- */
.tanya { max-width: 64ch; border-top: 1.5px solid var(--garis-terang); }
.tanya details { border-bottom: 1.5px solid var(--garis-terang); }
.tanya summary {
  cursor: pointer; font-weight: 700; font-size: 1.02rem; padding: 1.05rem 3rem 1.05rem 0; position: relative; list-style: none;
}
.tanya summary::-webkit-details-marker { display: none; }
.tanya summary::after {
  content: "+"; position: absolute; right: .25rem; top: 50%; transform: translateY(-50%);
  width: 1.7rem; height: 1.7rem; display: grid; place-items: center; border-radius: 50%;
  font-size: 1.2rem; font-weight: 800; background: var(--kuning); color: var(--tinta-gelap); transition: transform var(--cepat);
}
.tanya details[open] summary::after { transform: translateY(-50%) rotate(45deg); }
.tanya summary:hover { color: var(--kuning); }
.tanya p { margin: 0; padding: 0 0 1.15rem; color: var(--redup); }

/* ---------- Halaman game ---------- */
.produk { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 2.5rem; align-items: center; margin-bottom: 2.75rem; }
.produk img { display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; border-radius: var(--sudut); background: var(--malam-3); box-shadow: 8px 8px 0 rgba(0,0,0,.45); }
/* harga besar = label kuning */
.stiker {
  position: relative; display: inline-flex; align-items: center; gap: .9rem; margin: 1rem 0 1.25rem;
  background: var(--kuning); color: var(--tinta-gelap); padding: .9rem 1.4rem .9rem 1.2rem; border-radius: var(--sudut);
  box-shadow: 6px 6px 0 rgba(0, 0, 0, .45);
}
.stiker .harga { display: flex; flex-direction: column; line-height: 1.05; }
.stiker strong { white-space: nowrap; font-weight: 900; font-stretch: var(--sempit); font-size: clamp(2.4rem, 5.5vw, 3.2rem); font-variant-numeric: tabular-nums; }
.stiker s { color: var(--kuning-tua); font-variant-numeric: tabular-nums; }
.stiker .potong { margin: -1.8rem 0 -1.8rem -2.6rem; }
.kalimat { margin: 0 0 1.5rem; max-width: 46ch; font-size: 1.05rem; color: var(--redup); }
.kalimat.baik { color: var(--hijau); font-weight: 700; }
.fakta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 0 0 3rem; }
.fakta div { background: var(--malam-2); border-top: 3px solid var(--kuning); border-radius: 0 0 var(--sudut) var(--sudut); padding: 1rem 1.2rem 1.1rem; }
.fakta dt { color: var(--redup); font-size: .78rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.fakta dd { margin: .3rem 0 0; font-weight: 900; font-stretch: var(--sempit); font-size: 1.9rem; line-height: 1.1; font-variant-numeric: tabular-nums; }
.fakta dd small { display: block; font-weight: 500; font-stretch: 100%; font-size: .85rem; color: var(--redup); margin-top: .2rem; }
.peringatan { background: rgba(255, 201, 40, .1); border-left: 4px solid var(--kuning); color: var(--tinta); padding: .85rem 1.1rem; margin: 0 0 2rem; max-width: 64ch; }

/* Riwayat harga: struk kasir kertas termal */
.struk {
  max-width: 30rem; background: var(--kertas); color: var(--tinta-gelap); padding: 2rem 1.6rem 2.2rem; position: relative;
  font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace; font-size: .92rem;
  --gigi: radial-gradient(circle at 50% 100%, transparent .4rem, #000 .45rem) 50% 100% / 1rem 51% repeat-x,
          radial-gradient(circle at 50% 0, transparent .4rem, #000 .45rem) 50% 0 / 1rem 51% repeat-x;
  -webkit-mask: var(--gigi); mask: var(--gigi);
  filter: drop-shadow(6px 6px 0 rgba(0, 0, 0, .45));
}
.struk h2 { display: block; text-align: center; font-family: "Archivo", sans-serif; font-size: 1.6rem; margin: .25rem 0; color: var(--tinta-gelap); }
.struk h2::before { display: none; }
.struk .catatan { text-align: center; font-size: .82rem; margin: 0 auto 1.1rem; color: var(--redup-gelap); }
.struk table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.struk th { font-weight: 700; color: var(--redup-gelap); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; text-align: left; padding: .5rem 0; border-bottom: 1.5px dashed var(--redup-gelap); }
.struk td { padding: .55rem .25rem .55rem 0; border-bottom: 1px dashed rgba(26, 20, 13, .25); vertical-align: top; }
.struk .angka { text-align: right; }
.struk td.angka strong { font-weight: 800; }
.struk .turun { color: #b42010; font-weight: 800; }
.struk .normal { color: var(--redup-gelap); }
.struk tfoot td { border-bottom: 0; border-top: 1.5px dashed var(--redup-gelap); padding-top: .9rem; font-weight: 800; }

/* ---------- Daftar semua game ---------- */
.cari { display: block; margin: 0 0 1.5rem; max-width: 32rem; }
.cari input {
  width: 100%; font: inherit; font-size: 1rem; color: var(--tinta); min-height: 3rem;
  padding: .75rem 1rem .75rem 2.8rem; background-color: var(--malam-2); border: 1.5px solid var(--garis-terang); border-radius: var(--sudut);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23b9ab93' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: 1rem center; background-size: 1.1rem;
}
.cari input::placeholder { color: var(--redup); }
.cari input:focus { outline: none; border-color: var(--kuning); box-shadow: 0 0 0 3px rgba(255, 201, 40, .25); }
.daftar { list-style: none; margin: 0; padding: 0; max-width: 54rem; border-top: 1.5px solid var(--garis-terang); }
.daftar li { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .8rem .25rem; border-bottom: 1px dashed var(--garis-terang); }
.daftar li[hidden] { display: none; }
.daftar a { color: var(--tinta); font-weight: 600; text-decoration: none; }
.daftar a:hover { color: var(--kuning); text-decoration: underline; }
.daftar .harga { white-space: nowrap; font-variant-numeric: tabular-nums; color: var(--redup); }
.daftar .harga b { color: #fff; background: var(--merah); font-weight: 900; font-stretch: var(--sempit); font-size: 1rem; padding: .1rem .4rem; margin-right: .5rem; display: inline-block; transform: rotate(-3deg); }

/* ---------- Artikel & halaman info ---------- */
.prosa { max-width: 68ch; font-size: 1.05rem; }
.prosa .meta { color: var(--redup); margin: -.5rem 0 2rem; font-size: .95rem; }
.prosa h2 { font-size: 1.9rem; margin: 2.75rem 0 .75rem; }
.prosa h3 { font-size: 1.25rem; margin: 2rem 0 .5rem; }
.prosa p, .prosa ul, .prosa ol { margin: 0 0 1.15rem; color: #e3d9c6; }
.prosa strong { color: var(--tinta); }
.prosa ul, .prosa ol { padding-left: 1.3rem; }
.prosa li { margin-bottom: .45rem; }
.prosa li::marker { color: var(--kuning); font-weight: 800; }
.prosa img { border-radius: var(--sudut); }
.prosa blockquote { margin: 0 0 1.25rem; padding: .9rem 1.2rem; background: var(--malam-2); border-left: 4px solid var(--kuning); }
.prosa blockquote p:last-child { margin-bottom: 0; }
.kotak-data { background: var(--malam-2); border: 1.5px dashed var(--kuning); border-radius: var(--sudut); padding: 1.1rem 1.3rem; margin: 0 0 1.75rem; }
.kotak-data p { margin: 0 0 .4rem !important; font-weight: 700; color: var(--tinta) !important; }
.kotak-data ul { margin: 0 !important; }
.daftar-artikel { list-style: none; margin: 0; padding: 0; max-width: 68ch; border-top: 1.5px solid var(--garis-terang); }
.daftar-artikel li { padding: 1.2rem 0; border-bottom: 1px dashed var(--garis-terang); }
.daftar-artikel h2 { display: block; font-stretch: 100%; text-transform: none; font-weight: 800; font-size: 1.25rem; line-height: 1.3; margin: 0 0 .35rem; }
.daftar-artikel h2::before { display: none; }
.daftar-artikel h2 a { color: var(--tinta); text-decoration: none; }
.daftar-artikel h2 a:hover { color: var(--kuning); text-decoration: underline; }
.daftar-artikel p { color: var(--redup); margin: 0; font-size: .95rem; }

/* ---------- Kaki ---------- */
.kaki { background: var(--hitam); border-top: 1px solid var(--garis); padding: 2.75rem 0 3.25rem; color: var(--redup); font-size: .9rem; }
.kaki ul { list-style: none; display: flex; flex-wrap: wrap; gap: .25rem 1.5rem; margin: 0 0 1.4rem; padding: 0 0 1.4rem; border-bottom: 1px dashed var(--garis-terang); }
.kaki a { display: inline-block; padding: .35rem 0; color: var(--tinta); font-weight: 600; text-decoration: none; }
.kaki a:hover { color: var(--kuning); text-decoration: underline; }
.kaki p { margin: 0 0 .5rem; max-width: 72ch; }

/* ---------- Layar sedang ---------- */
@media (max-width: 60rem) {
  .hero { grid-template-columns: 1fr; padding: 2.25rem 0 3rem; }
  .unggulan { max-width: 21rem; margin-left: .5rem; }
  .kontrol label { margin-left: 0; }
}

/* ---------- Layar kecil ---------- */
@media (max-width: 44rem) {
  .nav { gap: .5rem 1rem; padding: .8rem 0 .4rem; }
  .logo { font-size: 1.4rem; }
  .nav ul { order: 3; width: calc(100% + 2.5rem); margin: 0 -1.25rem; padding: 0 .75rem; overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none; }
  .nav ul::-webkit-scrollbar { display: none; }
  .nav ul a { white-space: nowrap; }
  .tombol-tg { margin-left: auto; padding: .45rem .8rem; font-size: .85rem; min-height: 2.5rem; }
  .tombol-tg::before { display: none; }
  .saring { flex-wrap: nowrap; overflow-x: auto; width: calc(100% + 2.5rem); margin: 0 -1.25rem; padding: 0 1.25rem .35rem; scrollbar-width: none; }
  .saring::-webkit-scrollbar { display: none; }
  .saring button { flex: none; white-space: nowrap; }
  .hero { padding: 1.5rem 0 2.5rem; gap: 2.25rem; }
  .hero h1 { font-size: clamp(2.6rem, 13vw, 3.6rem); }
  .hero p { font-size: 1rem; }
  .unggulan { margin-right: 1.5rem; }
  .led-isi { font-size: 1.15rem; }
  main { padding-top: 2.25rem; }
  .bagian { margin-bottom: 3.5rem; }
  .rak { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.9rem .75rem; }
  .barang h3 { font-size: .95rem; margin: .7rem .7rem .2rem; }
  .barang .ulasan, .barang .terendah { margin-left: .7rem; margin-right: .7rem; font-size: .8rem; }
  .beli { margin: .4rem .7rem .5rem; font-size: .82rem; }
  .label-rak { padding: .55rem .7rem .5rem; }
  .label-rak .harga { flex-direction: column; align-items: flex-start; gap: 0; }
  .label-rak strong { font-size: 1.35rem; }
  .label-rak s { font-size: .74rem; }
  .potong { width: 3.1rem; height: 3.1rem; font-size: .95rem; }
  .unggulan { padding: 2.1rem 1.25rem 1.2rem; }
  .unggulan .stiker strong { font-size: 2.4rem; }
  .unggulan .stiker .potong { width: 3.8rem; height: 3.8rem; font-size: 1.15rem; top: -1.2rem; right: -1.2rem; }
  .voucher { padding: 1.4rem 1.25rem; }
  .voucher.lebar .tombol { width: 100%; }
  .produk { grid-template-columns: 1fr; gap: 1.25rem; }
  .stiker .potong { margin: -1.4rem 0 -1.4rem -2rem; }
  .fakta { grid-template-columns: 1fr; gap: .6rem; }
  .daftar li { flex-wrap: wrap; gap: .3rem 1rem; }
}
@media (max-width: 22rem) {
  .rak { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
"""


def tulis_css(folder="docs"):
    """Tulis docs/gaya.css dan kembalikan alamatnya beserta penanda versi,
    supaya browser mengambil versi baru setiap kali tampilannya diubah."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "gaya.css")
    try:
        lama = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        lama = None
    if lama != CSS:
        with open(path, "w", encoding="utf-8") as f:
            f.write(CSS)
    tulis_ikon(folder)
    tulis_aset(folder)
    return "/gaya.css?v=" + hashlib.sha1(CSS.encode()).hexdigest()[:8]


# ---------- Ikon situs (favicon) ----------
# Stiker merah "GD" di latar malam, senada dengan logo GameDiskon tema sekarang. Disimpan di sini (base64) supaya tidak perlu file terpisah;
# tulis_css() menuliskannya ke folder docs setiap kali ada perubahan.
IKON = {
    "favicon.ico": (
    "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"
    ),
    "icon-192.png": (
    "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"
    ),
    "apple-touch-icon.png": (
    "iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAAwFBMVEX///////7//v7//v3//f3//fz+/f3//Pz+/Pz+/Pv98vH2"
    "0MzuoZnlc2jeSjraMiDpMBzaMB/aMB7ZMB7nLxzlLxzbLx3gLhzZLhzbLRvZLRzZLRvZLRrYLRvXLRvWLRvYLBrYKhfYJxTXJBHX"
    "IQ7WHwzWHgrWHAnOKxqjJBZnGxImFA8fEg4XEg4WEg4VEg4VEg0TEg4bDwsRDwwQDgsPCwgPCggODQoNCggOCQgMEQ0MCggMCQgI"
    "EA0JCQgBBwccjK8cAAANX0lEQVR42u2ca3uiSBOGGUJWEJUA+gJhgoB4xGgcY+Lm+P//1VvdHALdzUnNzOx10bsfdmcyk9ui+nm6"
    "qotw2//g4lroFrqFbqFb6Ba6hW6hW+gWuoVuoVvoFrqFbqFb6Ba6hW6hW+gW+nLr/v7+vwK9ud8A7f1mu3l5efm7oTebCHVzvwPW"
    "9/f3/W4fhuHfCB2jwtq97BEqAAPqCtZysRwPF+vd5i+BzqDudhHqexixLpfLhWEZN8OhYRi2tQj/NPRmm0cF2DBcJ6j22ALUkTGy"
    "7mxnPB47jnNnG+HL/Z+BTlG3Eer7ep2iLhYYdTSybMtOUNPljFa/FzrOgC0WAYQK2OEqTFCHI/SPZWHUsTO+szOwyRqPVu+/ATrR"
    "KywCCBVSAWXrcoVQxxDTIaSrZd2N8bq7Y6BmoG++ETorApgVpCAjAiPDGOKdZY2dGqhZ6OXH/vH5cHy8GPQmZd3td196RYmA5dw5"
    "EWpN1iz05+EV1vO50LQIvK+/UC3HwqgZEbBPXuPR8vN4FnSyszKoqQg4GRG4o0Tg5OUYizfE/HpoDo1Rt7v3aGetN196NR4i1GRn"
    "XQj1a90Zi6cPHOqHptA7hJrq1TIrAlYsAvZlYVNoa/wrgt41g97s1lgEFgtwK4yaEYHvYc3mRxgl9b5hpDcvy5sRFgEH76zvR83s"
    "xOHq8wlDb5pB378vR4B64XS1b01d11RN03SzHBpp3ttjc+jh+GKspgmoqqqbrj8JprNpEPiurprFlhgJ9eO2KfRqdD60rgOqptse"
    "sM7ms2CiDwaDPloDZTLz1Ntz3OW7oH2EOg1cBaH2erLc7QocXlJX7iszW2enx+nQtdLDxMFE4TTpp22iqGJWiUsX3+kInSv0X92+"
    "N1FZ6jFaRpJ3bAr9sjIqrVhXdReeO1pTyFItHzfTU7oZVFGSRIHn+fj/4Rc4Th4Eeom7HB8aSt5uvbBKpcNU7clsEj14nKX6LLC1"
    "7Be4pixIgHotJKj5xUtcdxCoDHdZ/KphiSdAq97MH/Tkr1hKcq9vB9ksNScyd82VLUQ90ai/23LDGpbIhjaKoXVzpvRl/I2vREkU"
    "pWscS7nv+1+RU+c9TiyF5jqcDA+ETuo6lsg4e5QKter7fRTjmDV62ILI4yxVs9BSOTT8fm+qFQl1ubs0hFanA4iyKFAIggiSMEuo"
    "1Vk1NH8tDSb6b4BWZxBmkbm3IB3E/lRNvw6eP1eVIL2pepIlMqGL3EWd9qViGIGXkgzRgj4nVEHz8PW+foolMqFDtlBrk0G3jEWA"
    "veXhvaVPBlz1ErneTKULrkNl7dIg0mAZFUIGDzzAe8v04ePxZGAFnvyQXZ0QEMdYfrxWWiIDevMS3rGTo1LHBD7aW6ardrkr1rPI"
    "rSuuT/giuMuh2hKZhe2OJdTwyKV/KveWHMuYJ5OEYlcmo4/yQzuh4GJB7+5Z0BoEulN3b2mBnPtiyISBYiq9/CeBTeDZtwR1DXep"
    "DY0CTRwk+GuRTFMxljHSEnmu6/mmP5OJz01JdVK7NIZmCrVKBprvMNIUYme7t7Ql8oDnmwqphB2uT7hiLXdhQ7NO1C6VpV1ZlgUi"
    "TXkOxw65C2GJ8Ov4yMqXJvUZ0HSkITtyqcALUl+ZTCbg6jyZHxraAP28OgogFBpIYV404cH4ZnN3KYq0Qxl4PkkBYu5CfT0ddHOZ"
    "fs3JSMX0YEB+GHQyQZs5nzVdxTOZBdehKfRLSG1EPcilNIRogssVZZ5PU4QBhqH7g3ziSNj96NMfT+xEJ+lBHi8ATQgvZMFcTSsr"
    "nhIEVvbCH6AOUvDA8ocmKLiOr1XuUgBtkYEmfPk63fb6JC9jYvQ7Pwl3ETkZthx1kBLJQ3XqLk2hQamXxJEJnYB4plbFyf6DFwQo"
    "Y8QrgEbPAG05gdpy5F+DLJQscK3qgqsmNArRVT6e8/gUCsdVKSMsooRVDFmiSB2OTJ/IGlo+7tIe5KYp9IKAJpNRSnIadmgfbygk"
    "2j0ozgcDxbVZ7oJ0gkp1hnwkZUBT6PuXJXE41YgT3lcuAkeMOgnmqP/le+wqUcCnEiLVsVPqTd2FDU1ZIsmQyUXTBdQAUE0dtZtg"
    "xVmThxbwMVSbEqePHxyheSn0c3PoGyLSlLd85aIZs6btUZdVcHWwu5AelZGhBu28IuiRU5oesYegTi5i1cy4PToP/Fuc1KATPNEx"
    "6M9VukyXuH6+5Kpzw1WQ06RQk98MoAco1LjrPJ9PJ16mPYrdxR9ITEvsk9DJjm5QcDWAFhn+q+CuM6Bm26PogZsu80BHHaQoaLDE"
    "yoKrJjSZHnhfqWCT3ats90USO4LE4wdOugucpKY66yDVI9zFstdVPciCy0/SXShodGpTcEdXEPPt0Th2OlVwQWmFskYExch9lklj"
    "d2FDb14IaGQuIvlYYSvKvMDo0aFIM3YBy11oaNSDRDdcbxeB7lDQZAokEo5rlzlr65qu2SXPJJ5pN7RENjTlLozjmRxoyCpERp8J"
    "6Qr1bHDBxTpIuUXtvHOhKdnFj5XZhuajvhH6mCLDEmfkQUr2Chqnz82h85bIOp557I5uVHjTp9Co4CKzhhFpsMSncncphM5bIiW7"
    "eF8pdAqkEq4z3IVhiQJ1IZAWXIdt040YjvNKTeYiz4kDX2F2dOPCm9QJCbsLmepoB1A3XP9WFFyF0LZVemLCDQ4l6ujy1CkD1X0/"
    "XZmoG1Cfj9zRAq3T1TdcBdD7cGGV+zic2gIFUgDKFrZQI3ch8XRG3SZTdxiJu+waOiIqAxxS866p45mnokujf7oC4zhBFlxXSFWo"
    "dnuHsvHMDdfmTGj4Zh16X7l2VGER7QXc72VbIhlpkTww4ZHCSPPOhmY1MhBaAGWLP801uxJ3YfQgPQU1d0RKCBu6SxE0VXAxrAye"
    "to0qADXf+kAS/tNmNWYG8+mMaKPx1GVAjRuu2tCM2mUQV1zE54krbJ3UQ4HrQZVAyf2A6CHUKLiKockqcUowgOZFt0K2q+egf6DC"
    "26SdP/1zhLHeNh4pLMzpFdHOIxtj+JqY3c7j46MRdcPFi5JI3bpQd82OsagouAqgGaMIZNMOnRrweAoyc4HsKjIskbWusHs2HSks"
    "hA5JaLSxyD75XNVgG+rEqTqusJmnbfIKT3bd4pHC86GpExAvdPtQiwcKyZa4C9mYqXVnW2eksGhAlu6M2f+byOTxg5N7aFpFoFAw"
    "9KzqsvSKJzt58U6sKLgKod8paEo/kpOSQMVPDrQ68xPoaKWfMFLYANp0XaqOFUSxwzMKLg/3//rlkZaou62allgMTV/LqdMaUxzJ"
    "0cikGzPEV0noKG2eMlLYBPqWEWpWuiBLRO4SDFiX+l9Xpz3TKx8pPFwAGoda5OosZjsvcwd5hQYKA1dnDyQnI4UnQDMmVSgByce5"
    "G7sJu+DieaEDlhhPl/WUWdF8L3KX0oKrCJo9nYfnVITCuYl+/JtRL9p0dVBDHt0gocZZ9nq61zennlo8sF5RcDWDRnnaLdhdyFJi"
    "YY7dxZzIYmbjdrvxrYziTQNXM0um7CtGCsugWSOFePZKZDLLuKNwLaKyMWrnzWU0xNtNb5D8Ke5l+3bp5Hf1SGHhKyNFg24qirXE"
    "s4ZHfW+QmAm66YSdiFHteILa90xNw1PAdabsy9ylMTRQK3iekM8Oq6AByIlqe3ISVtyAMScQVu8nvoxhTixXDKxfDtpW/Qme3AQ3"
    "FMX4hAxHJx9i6yq3PsqAIK5GdE3Xa6PWL7hKoMnLosyM7FTpy1JGDfrK1MSa67pmFNbzXsKosMQS6HBUOPutoWlkKPjQglwIZl58"
    "hjBvL/K6S8VIYVmkh07J3LfpB7NpMJ3NZoFf/DrFqe/olN9wFUNT7TwySTTIAi26RLz061AVN1xc8Rt927LZ7+9ad9G7jIvSkcJi"
    "aPZI4beh4tfDxrZlGKObm+FNqbv8UegorBBYy0KoAGstFsvlcrVaxZFmF1zFL1Fe9nWoHGuE6kBYR0PEariIFVDD8NfTxydaEXOB"
    "u5RBry4KHYfVwWFFrIY1jsMarn+9fUasHx/HA1qY+RToS0Q6yVZgxdl6MzIsKqzA+opRn47HiDZZz9vGkR4552arg1AhrMOREWdr"
    "GIaHGPXz4zUOK4F6BvRLaDhniABCHY7GzLAeY9Qi1nQdm0PXjDQhAsOMCITrp7evsD6xMoC18DvNx+fn531zaKuhCJwZ1jfEejwe"
    "nh8f9/vdQ+PRCfagW4RaLAK/fn2QItAI9XG/2z1EPwzg5Df0M9CpCCRhRSKwTMP6mQ9rjRSIUSEForBGP7ag5g84KIVeGtHL104q"
    "AoaRZkAqAh/VIpBJ1rc4WwF1n0S1LmwNaHSFgeMKepXJ1n9PyNYI9ZCEdRf9NIjtqasc2ki0Nd1YzUQgE1a8sTZnsdZLj3W4Rj+9"
    "4eMUEThksnV7EdR60Nvdfod+9sRDAxE4RiLw8HB51JrQ8XfdVaC+5kRg+12oNaHj9cBAhX+PqQh8a1hPhT7m7PUQoSba+vtYG0Fv"
    "j1kR2F5MBL4X+hLa+tuh/7bVQrfQLXQL3UK30C10C91Ct9AtdAvdQrfQLXQL3UK30C10C91Ct9AtdAv9l63/A3Gsfce8yeaeAAAA"
    "AElFTkSuQmCC"
    ),
}


def tulis_ikon(folder="docs"):
    """Tulis file ikon ke folder situs kalau belum ada atau isinya berbeda."""
    for nama, isi64 in IKON.items():
        isi = base64.b64decode(isi64)
        path = os.path.join(folder, nama)
        try:
            with open(path, "rb") as f:
                if f.read() == isi:
                    continue
        except FileNotFoundError:
            pass
        with open(path, "wb") as f:
            f.write(isi)


def tulis_aset(folder="docs"):
    """Salin huruf dan gambar pratinjau dari aset/ ke folder situs, hanya kalau isinya berbeda."""
    for nama, tujuan in FILE_ASET.items():
        sumber = os.path.join(FOLDER_ASET, nama)
        if not os.path.exists(sumber):
            sumber = os.path.join(FOLDER_REPO, nama)
        if not os.path.exists(sumber):
            # Cadangan: file yang terunggah ke folder utama repo (bukan ke aset/) tetap dipakai
            sumber = os.path.join(os.path.dirname(FOLDER_ASET), nama)
        if not os.path.exists(sumber):
            print(f"Aset {nama} tidak ditemukan di aset/ maupun folder utama, dilewati.")
            continue
        isi = open(sumber, "rb").read()
        path = os.path.join(folder, tujuan)
        try:
            with open(path, "rb") as f:
                if f.read() == isi:
                    continue
        except FileNotFoundError:
            pass
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(isi)


def gambar_epic(url, lebar=640, tinggi=360):
    """Minta CDN Epic mengecilkan gambar. Gambar asli Epic bisa 3 MB lebih (PNG 2560 px);
    dengan parameter ini jadi sekitar 40 KB. Alamat di luar cdn1.epicgames.com dibiarkan."""
    if not url or not url.startswith("https://cdn1.epicgames.com/") or "?" in url:
        return url
    return f"{url}?resize=1&w={lebar}&h={tinggi}&quality=medium"


HREF_CSS = "/gaya.css?v=" + hashlib.sha1(CSS.encode()).hexdigest()[:8]


def kepala(judul, deskripsi, kanonik="", og_gambar="", noindex=False, jsonld=None, tambahan="",
           og_tipe="website"):
    """Isi <head> yang sama untuk semua halaman.
    jsonld boleh satu dict atau daftar dict (masing-masing jadi satu <script>)."""
    og_gambar = gambar_epic(og_gambar, 1200, 675) or OG_BAWAAN
    baris = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{escape(judul)}</title>",
        f'<meta name="description" content="{escape(deskripsi)}">',
    ]
    if kanonik:
        baris.append(f'<link rel="canonical" href="{escape(kanonik)}">')
    if noindex:
        baris.append('<meta name="robots" content="noindex, follow">')
    baris += [
        f'<meta property="og:type" content="{escape(og_tipe)}">',
        '<meta property="og:site_name" content="GameDiskon">',
        '<meta property="og:locale" content="id_ID">',
        f'<meta property="og:title" content="{escape(judul)}">',
        f'<meta property="og:description" content="{escape(deskripsi)}">',
    ]
    if kanonik:
        baris.append(f'<meta property="og:url" content="{escape(kanonik)}">')
    baris += [
        f'<meta property="og:image" content="{escape(og_gambar)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="theme-color" content="#15120e">',
        '<link rel="icon" href="/favicon.ico" sizes="48x48">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        f'<link rel="preload" href="{FONT_PRELOAD}" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="{HREF_CSS}">',
    ]
    for data in (jsonld if isinstance(jsonld, list) else [jsonld] if jsonld else []):
        teks = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        baris.append(f'<script type="application/ld+json">{teks}</script>')
    if tambahan:
        baris.append(tambahan)
    return "\n".join(baris)


def pita(link_telegram=None, aktif="", hero="", setelah=""):
    """Kepala halaman: logo, menu, tombol Telegram, dan (khusus beranda) judul besar.
    setelah: isi selebar layar di bawah judul besar, misalnya papan LED berjalan di beranda."""
    menu = [("/game/", "Semua game", "game"), ("/game-gratis-epic/", "Gratis Epic", "gratis-epic"),
            ("/jadwal-steam-sale/", "Jadwal Sale", "steam-sale"),
            ("/info-game/", "Info Game", "info-game"), ("/panduan/", "Panduan", "panduan")]
    li = "".join(f'<li><a href="{u}"{" aria-current=\"page\"" if k == aktif else ""}>{t}</a></li>'
                 for u, t, k in menu)
    if link_telegram is None:
        link_telegram = LINK_TELEGRAM
    tg = (f'<a class="tombol-tg" href="https://{escape(link_telegram)}" rel="noopener">Ikuti di Telegram</a>'
          if link_telegram else "")
    return f"""<a class="lompat" href="#isi">Langsung ke isi</a>
<header class="pita">
  <div class="wadah">
    <nav class="nav" aria-label="Menu utama">
      <a class="logo" href="/">Game<span>Diskon</span></a>
      <ul>{li}</ul>
      {tg}
    </nav>{hero}
  </div>{setelah}
</header>"""


def kaki():
    return """<footer class="kaki">
  <div class="wadah">
    <ul>
      <li><a href="/game/">Semua game</a></li>
      <li><a href="/game-gratis-epic/">Game gratis Epic</a></li>
      <li><a href="/jadwal-steam-sale/">Jadwal Steam Sale</a></li>
      <li><a href="/info-game/">Info Game</a></li>
      <li><a href="/panduan/">Panduan</a></li>
      <li><a href="/tentang/">Tentang</a></li>
      <li><a href="/kebijakan-privasi/">Kebijakan Privasi</a></li>
      <li><a href="/kontak/">Kontak</a></li>
    </ul>
    <p>Selamat berburu game diskon dan game gratis! Harga dicek setiap hari dari Steam region Indonesia dan CheapShark, game gratis dari Epic Games Store. Semua tautan beli menuju toko resminya, jadi selalu cek harga di sana sebelum membayar.</p>
    <p>GameDiskon tidak berafiliasi dengan Valve maupun Epic Games. Powered by Sarathiel.</p>
  </div>
</footer>"""


def halaman_utuh(head, header, isi, script=""):
    """Rangkai satu halaman HTML lengkap."""
    return f"""<!doctype html>
<html lang="id">
<head>
{head}
</head>
<body>
{header}
<main id="isi">
  <div class="wadah">
{isi}
  </div>
</main>
{kaki()}
{script}
</body>
</html>
"""
