"""
Sistem tampilan bersama untuk semua halaman gamediskon.my.id.

Tema: "Shonen Sale", tampilan menu game Jepang masa kini dengan sedikit rasa manga: panel
bersudut potong, satu aksen kuning elektrik, screentone, garis kecepatan, katakana efek suara.
Semua halaman memakai satu file gaya: docs/gaya.css.
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
    "dela-gothic-jp.woff2": "fonts/dela-gothic-jp.woff2",   # huruf Jepang (Dela Gothic One, OFL), subset 19 huruf
    "og-gamediskon.png": "og-gamediskon.png",
}
FONT_PRELOAD = ["/fonts/archivo-latin.woff2", "/fonts/dela-gothic-jp.woff2"]

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
/* Huruf Jepang untuk label & efek suara manga (Dela Gothic One, OFL). Subset 19 huruf, 3 KB:
   割引 無料 本日特価 近日 セール ゲーム サラシエル. Kalau menambah huruf baru, unduh ulang subset-nya. */
@font-face {
  font-family: "Manga"; font-style: normal; font-weight: 400; font-display: swap;
  src: url(/fonts/dela-gothic-jp.woff2) format("woff2");
  unicode-range: U+3099, U+30B1-30B2, U+30BB-30BC, U+30E0, U+30EB, U+30FC, U+4FA1, U+5272, U+5F15, U+6599, U+65E5, U+672C, U+7121, U+7279, U+8FD1;
}

/* =========================================================
   GameDiskon, tema "Shonen Sale" (v4)
   Tampilan menu game Jepang masa kini dengan sedikit rasa manga:
   panel bersudut potong, huruf tebal sempit yang miring, satu aksen
   kuning elektrik, screentone titik-titik, garis kecepatan di belakang
   game unggulan, gelembung ledakan 無料, dan katakana besar セール
   sebagai efek suara. Semua nama class lama tetap dipakai.
   Aturan bentuk: panel dipotong di pojok kanan atas (--potong),
   tombol & label berbentuk jajar genjang. Satu aksen: kuning.
   ========================================================= */

/* ---------- Token ---------- */
:root {
  color-scheme: dark;
  --tinta: #0a0b12;         /* latar halaman (hitam kebiruan) */
  --tinta-2: #12141e;       /* panel */
  --tinta-3: #1b1e2b;       /* panel disorot, input */
  --tinta-0: #06070b;       /* kaki */
  --garis: #262a3a;
  --garis-terang: #3b4058;
  --putih: #f1f2f6;         /* teks utama        17:1 di --tinta */
  --redup: #a7acbe;         /* teks kedua         8,4:1 di --tinta, 7,1:1 di --tinta-3 */
  --kuning: #f6e146;        /* aksen: isi tombol, label, sorotan (teks --tinta 14:1) */
  --kuning-redup: rgba(246, 225, 70, .14);
  --hijau: #5be39a;         /* harga termurah (status, bukan hiasan) */
  --lebar-isi: 78rem;
  --potong: 14px;           /* potongan pojok panel */
  --miring: 9px;            /* kemiringan tombol & label */
  --sempit: 74%;            /* lebar huruf judul */
  --cepat: 200ms cubic-bezier(.16, 1, .3, 1);
  --titik: radial-gradient(circle, rgba(241, 242, 246, .2) 1.1px, transparent 1.7px) 0 0 / 7px 7px;
  --sudut-potong: polygon(0 0, calc(100% - var(--potong)) 0, 100% var(--potong), 100% 100%, 0 100%);
  --jajar: polygon(var(--miring) 0, 100% 0, calc(100% - var(--miring)) 100%, 0 100%);
}

*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; scroll-padding-top: 1rem; }
body {
  margin: 0; background: var(--tinta); color: var(--putih);
  font-family: "Archivo", system-ui, sans-serif; font-size: 1rem; line-height: 1.6;
  font-size-adjust: from-font;
  -webkit-font-smoothing: antialiased;
}
img { max-width: 100%; height: auto; }
a { color: var(--kuning); text-underline-offset: 3px; text-decoration-thickness: 1px; transition: color var(--cepat); }
a:hover { color: var(--putih); text-decoration-thickness: 2px; }
:focus-visible { outline: 2px solid var(--kuning); outline-offset: 3px; }
::selection { background: var(--kuning); color: var(--tinta); }
.wadah { max-width: var(--lebar-isi); margin: 0 auto; padding: 0 1.5rem; }
.lompat { position: absolute; left: -999px; }
.lompat:focus { left: 1rem; top: 1rem; z-index: 50; background: var(--kuning); color: var(--tinta); padding: .5rem 1rem; font-weight: 800; }
[lang="ja"] { font-family: "Manga", "Archivo", sans-serif; font-weight: 400; }

/* ---------- Kepala ---------- */
.pita { position: relative; isolation: isolate; overflow: hidden; border-bottom: 1px solid var(--garis); }
/* screentone manga di pojok kanan atas */
.pita::before {
  content: ""; position: absolute; z-index: -1; pointer-events: none;
  top: 0; right: 0; width: min(60rem, 75%); height: 36rem; background: var(--titik);
  -webkit-mask-image: radial-gradient(ellipse at 100% 0, #000 5%, transparent 68%);
          mask-image: radial-gradient(ellipse at 100% 0, #000 5%, transparent 68%);
}
.pita a { color: var(--putih); }
.nav { display: flex; align-items: center; gap: 2rem; min-height: 4.25rem; padding: .6rem 0; }

/* Logo: label kuning miring 割 + GameDiskon */
.logo {
  display: inline-flex; align-items: center; gap: .6rem; text-decoration: none; flex: none;
  font-weight: 900; font-stretch: var(--sempit); font-size: 1.6rem; line-height: 1; text-transform: uppercase; letter-spacing: .01em;
}
.logo b { font-weight: 900; color: var(--kuning); }
.logo-hanko {
  display: inline-grid; place-items: center; width: 2.4rem; height: 2.1rem; flex: none;
  background: var(--kuning); color: var(--tinta); clip-path: var(--jajar);
  font-size: 1.25rem; line-height: 1; padding-top: .08em;
  transition: transform var(--cepat);
}
.logo:hover .logo-hanko { transform: translateX(2px); }

.nav ul { list-style: none; display: flex; gap: .15rem; margin: 0 0 0 auto; padding: 0; }
.nav ul a {
  display: block; text-decoration: none; font-weight: 700; font-size: .92rem; color: var(--redup);
  padding: .55rem .8rem; position: relative; white-space: nowrap; isolation: isolate;
  transition: color var(--cepat);
}
.nav ul a::before {               /* sorotan menu ala game: blok kuning miring */
  content: ""; position: absolute; inset: .2rem 0; z-index: -1; background: var(--kuning); clip-path: var(--jajar);
  transform: scaleX(0); transform-origin: left; transition: transform var(--cepat);
}
.nav ul a:hover { color: var(--putih); }
.nav ul a[aria-current] { color: var(--tinta); }
.nav ul a[aria-current]::before { transform: scaleX(1); }

.tombol-tg {
  display: inline-flex; align-items: center; gap: .5rem; white-space: nowrap; min-height: 2.6rem; flex: none;
  color: var(--putih) !important; text-decoration: none; font-weight: 800; font-size: .86rem; text-transform: uppercase; letter-spacing: .04em;
  padding: .5rem 1.15rem; background: var(--tinta-3); clip-path: var(--jajar);
  transition: background var(--cepat), color var(--cepat);
}
.tombol-tg::before {             /* ikon pesawat kertas Telegram */
  content: ""; width: 1rem; height: 1rem; flex: none; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.tombol-tg:hover { background: var(--kuning); color: var(--tinta) !important; }

/* ---------- Hero ---------- */
.hero {
  position: relative; isolation: isolate;
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 32rem); grid-template-rows: auto 1fr; gap: 1.75rem 4rem;
  align-items: start; padding: 3.25rem 0 4rem;
}
.hero-judul { grid-column: 1; grid-row: 1; align-self: end; }
.hero-teks { grid-column: 1; grid-row: 2; }
/* efek suara manga サラシエル: katakana besar bergaris di belakang judul (SVG, lihat halaman.py) */
.sfx {
  position: absolute; z-index: -1; left: -1.5rem; top: .5rem; pointer-events: none; user-select: none;
  font-size: clamp(7rem, 15vw, 13rem); line-height: 1; letter-spacing: -.02em; white-space: nowrap;
  color: transparent; -webkit-text-stroke: 1.5px rgba(246, 225, 70, .16); transform: rotate(-7deg);
}
.sfx svg { display: block; height: .8em; width: auto; overflow: visible; }
.sfx path { fill: none; stroke: rgba(246, 225, 70, .16); stroke-width: 1.5px; vector-effect: non-scaling-stroke; }
.hero > :not(.sfx) { animation: masuk 650ms cubic-bezier(.16, 1, .3, 1) both; }
.hero-teks { animation-delay: 90ms !important; }
.unggulan { animation-delay: 160ms !important; }
@keyframes masuk { from { opacity: 0; transform: translateX(-24px); } }
.kicker {
  display: inline-flex; align-items: center; gap: .6rem; margin: 0 0 1.1rem !important;
  font-size: .8rem !important; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--kuning) !important;
}
.kicker::before { content: ""; width: 1.6rem; height: .5rem; background: var(--kuning); clip-path: var(--jajar); flex: none; }
.kicker a { color: var(--kuning); text-decoration: none; }
.kicker a:hover { color: var(--putih); }
.kicker a::after { content: " \2192"; }
.hero h1 {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase;
  font-size: clamp(2.4rem, 4.4vw, 3.9rem); line-height: 1; letter-spacing: -.005em; margin: 0;
  font-stretch: 68%;
}
.hero h1 .baris { display: block; transform: skewX(-8deg); transform-origin: bottom left; }
.sorot {                          /* "dalam Rupiah" di atas blok kuning miring, seperti kartu judul game */
  display: inline-block; margin-top: .14em; padding: .06em .32em .02em .24em;
  background: var(--kuning); color: var(--tinta); transform: skewX(-8deg); transform-origin: bottom left;
  clip-path: polygon(.18em 0, 100% 0, calc(100% - .18em) 100%, 0 100%);
}
.hero-teks p { font-size: 1.1rem; margin: 0; max-width: 42ch; color: var(--redup); }
.hero-aksi { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 1.75rem; }
.hero-aksi .tombol { margin: 0; }

/* Game unggulan: kartu karakter dengan garis kecepatan di belakangnya */
.unggulan {
  grid-column: 2; grid-row: 1 / span 2; align-self: center; position: relative; isolation: isolate;
  display: grid; grid-template-columns: minmax(0, 1fr) auto; text-decoration: none; color: var(--putih) !important;
  transition: transform var(--cepat);
}
.unggulan::before {               /* garis kecepatan manga */
  content: ""; position: absolute; z-index: -1; inset: -40% -30%; pointer-events: none;
  background: repeating-conic-gradient(from 3deg at 50% 50%, rgba(246, 225, 70, .22) 0deg 1.1deg, transparent 1.1deg 7deg);
  -webkit-mask-image: radial-gradient(closest-side, transparent 38%, #000 52%, transparent 86%);
          mask-image: radial-gradient(closest-side, transparent 38%, #000 52%, transparent 86%);
}
.unggulan:hover { transform: translateY(-4px); }
.unggulan-gambar { grid-column: 1; grid-row: 1; position: relative; overflow: hidden; clip-path: var(--sudut-potong); background: var(--tinta-3); }
.unggulan-gambar img { display: block; width: 100%; aspect-ratio: 616 / 353; object-fit: cover; transition: transform 600ms cubic-bezier(.16, 1, .3, 1); }
.unggulan:hover .unggulan-gambar img { transform: scale(1.05); }
.unggulan-gambar::after {         /* screentone di pojok kiri bawah sampul */
  content: ""; position: absolute; inset: 0; pointer-events: none; background: var(--titik);
  -webkit-mask-image: linear-gradient(35deg, #000, transparent 40%);
          mask-image: linear-gradient(35deg, #000, transparent 40%);
}
.unggulan-gambar .potong { position: absolute; top: .9rem; left: .9rem; font-size: 1.35rem; }
.noren {                          /* label vertikal 本日特価 di sisi kartu */
  grid-column: 2; grid-row: 1 / span 2; writing-mode: vertical-rl; text-orientation: upright;
  display: flex; align-items: center; justify-content: center; padding: 1rem .55rem; margin-left: .45rem;
  background: var(--kuning); color: var(--tinta); font-size: 1.35rem; letter-spacing: .18em; line-height: 1;
  clip-path: polygon(0 0, 100% .6rem, 100% 100%, 0 calc(100% - .6rem));
}
.unggulan-isi {                   /* papan nama menumpang di tepi bawah sampul */
  grid-column: 1; grid-row: 2; position: relative; margin: -1.6rem 1.4rem 0 -.6rem;
  padding: .9rem 1.2rem 1rem; background: var(--tinta-2); border-left: 4px solid var(--kuning);
  display: flex; flex-direction: column; gap: .1rem; box-shadow: 0 14px 30px rgba(0, 0, 0, .45);
}
.unggulan-ket { font-size: .72rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: var(--kuning); }
.unggulan-nama { font-weight: 800; font-size: 1.15rem; line-height: 1.25; }
.unggulan .harga { display: flex; align-items: baseline; flex-wrap: wrap; gap: .1rem .8rem; margin-top: .35rem; }
.unggulan .harga strong { font-weight: 900; font-stretch: var(--sempit); font-size: clamp(2.1rem, 3.4vw, 2.7rem); line-height: 1; font-variant-numeric: tabular-nums; }
.unggulan .harga s { color: var(--redup); font-variant-numeric: tabular-nums; }

/* ---------- Pita berjalan kuning (hiasan, isinya sama dengan rak) ---------- */
.led {
  position: relative; overflow: hidden; background: var(--kuning); color: var(--tinta);
  padding: .7rem 0; margin: 0 -2%; transform: rotate(-1deg); transform-origin: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, .5);
}
.led-isi {
  display: flex; width: max-content; gap: 2.5rem; margin: 0; padding: 0; list-style: none;
  font-weight: 900; font-stretch: var(--sempit); font-size: 1.15rem; line-height: 1.2; text-transform: uppercase;
  letter-spacing: .02em; animation: jalan 75s linear infinite;
}
.led-isi li { white-space: nowrap; display: flex; align-items: center; gap: .5rem; }
.led-isi li::before { content: "\2605"; font-size: .8em; margin-right: .6rem; }
.led-isi b { background: var(--tinta); color: var(--kuning); padding: .05rem .4rem; clip-path: polygon(4px 0, 100% 0, calc(100% - 4px) 100%, 0 100%); }
.led:hover .led-isi { animation-play-state: paused; }
@keyframes jalan { to { transform: translateX(-50%); } }

/* ---------- Judul & teks umum ---------- */
main { padding: 4.5rem 0 6rem; }
.bagian { margin-bottom: 5.5rem; }
h1, h2, h3 { font-weight: 800; line-height: 1.12; }
h2 {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase; letter-spacing: .005em;
  font-size: clamp(1.9rem, 3.8vw, 2.8rem); line-height: 1; margin: 0 0 .75rem;
}
.bagian > h2 { display: flex; align-items: center; gap: .8rem; }
.bagian > h2::before {            /* blok kuning miring di depan judul bagian */
  content: ""; width: .55em; height: .85em; flex: none; background: var(--kuning); clip-path: polygon(40% 0, 100% 0, 60% 100%, 0 100%);
}
.bagian > h2::after {             /* garis menu yang memudar ke kanan */
  content: ""; flex: 1 1 2rem; min-width: 2rem; height: 2px; margin-left: .5rem;
  background: linear-gradient(90deg, var(--garis-terang), transparent);
}
h3 { font-size: 1.15rem; }
.judul-halaman {
  font-weight: 900; font-stretch: var(--sempit); text-transform: uppercase;
  font-size: clamp(2.4rem, 5.6vw, 4rem); line-height: .98; margin: 0 0 1.5rem; max-width: 22ch; text-wrap: balance;
}
.catatan { color: var(--redup); margin: 0 0 2rem; max-width: 64ch; }
.jejak { font-size: .85rem; color: var(--redup); margin: 0 0 1.25rem; }
.jejak ol { list-style: none; display: flex; flex-wrap: wrap; gap: .45rem; margin: 0; padding: 0; }
.jejak li + li::before { content: "/"; margin-right: .45rem; color: var(--kuning); }
.jejak a { color: var(--redup); }
.jejak a:hover { color: var(--putih); }

/* ---------- Label potongan (jajar genjang kuning) ---------- */
.potong {
  position: relative; z-index: 1; display: inline-flex; align-items: center; flex: none;
  background: var(--kuning); color: var(--tinta); clip-path: var(--jajar);
  padding: .3rem .85rem .25rem; font-weight: 900; font-stretch: var(--sempit); font-size: 1.15rem; line-height: 1;
  font-variant-numeric: tabular-nums;
}

/* ---------- Game gratis Epic ---------- */
.gratis { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.5rem;
          grid-template-columns: repeat(auto-fill, minmax(min(100%, 22rem), 1fr)); }
.gratis > li { position: relative; }
.gratis a {
  display: flex; flex-direction: column; position: relative; height: 100%; text-decoration: none;
  background: var(--tinta-2); color: var(--putih); clip-path: var(--sudut-potong);
  transition: transform var(--cepat), background var(--cepat);
}
.gratis a::after {                /* garis kuning di dasar kartu, memanjang saat disorot */
  content: ""; position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: var(--kuning);
  transform: scaleX(.18); transform-origin: left; transition: transform var(--cepat);
}
.gratis a:hover { background: var(--tinta-3); transform: translateY(-3px); }
.gratis a:hover::after { transform: scaleX(1); }
.gratis img { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: var(--tinta-3); }
.gratis h3 { margin: 0; padding: 1.15rem 1.3rem .3rem; font-size: 1.3rem; color: var(--putih); }
/* Gelembung ledakan manga: 無料 / 近日 */
.stempel {
  position: absolute; top: .4rem; left: .4rem; z-index: 1; width: 6rem; height: 6rem;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .15rem;
  color: var(--tinta); font-size: .6rem; font-weight: 900; letter-spacing: .12em; line-height: 1;
  transform: rotate(-10deg); isolation: isolate; filter: drop-shadow(3px 4px 0 var(--tinta));
}
.stempel::before {
  content: ""; position: absolute; inset: 0; z-index: -1; background: var(--kuning);
  clip-path: polygon(50% 0%, 59% 15%, 75% 5%, 75% 22%, 93% 18%, 85% 34%, 100% 42%, 86% 53%, 97% 68%, 80% 70%, 82% 88%, 66% 80%, 58% 97%, 48% 83%, 35% 98%, 31% 81%, 14% 88%, 17% 70%, 0% 66%, 13% 53%, 2% 38%, 18% 34%, 12% 16%, 30% 21%, 33% 3%, 44% 15%);
}
.stempel [lang="ja"] { font-size: 1.45rem; letter-spacing: .02em; }
.batas { margin: 0; padding: 0 1.3rem 1.4rem; color: var(--redup); font-size: .95rem; }
.sisa { color: var(--kuning); font-weight: 800; }

/* ---------- Kontrol saring & urut ---------- */
.kontrol { display: flex; flex-wrap: wrap; gap: .75rem 1.5rem; align-items: center; margin: 0 0 2rem; }
.saring { display: flex; flex-wrap: wrap; gap: .4rem; }
.saring button {
  font: inherit; font-weight: 800; font-size: .86rem; text-transform: uppercase; letter-spacing: .03em;
  color: var(--putih); background: var(--tinta-3); border: 0; clip-path: var(--jajar);
  padding: .55rem 1.15rem; min-height: 2.75rem; cursor: pointer;
  transition: color var(--cepat), background var(--cepat);
}
.saring button:hover { background: var(--garis-terang); }
.saring button:active { transform: translateY(1px); }
.saring button[aria-pressed="true"] { background: var(--kuning); color: var(--tinta); }
.kontrol select {
  font: inherit; font-weight: 700; font-size: .9rem; color: var(--putih); background-color: var(--tinta-3);
  border: 1px solid var(--garis-terang); padding: .5rem 2.2rem .5rem .9rem; min-height: 2.75rem; cursor: pointer;
  appearance: none; -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f6e146' stroke-width='2.5' stroke-linecap='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right .75rem center; background-size: 1rem;
}
.kontrol select:hover { border-color: var(--kuning); }
.kontrol label { display: flex; gap: .6rem; align-items: center; color: var(--redup); margin-left: auto; font-size: .9rem; }
.hasil-saring { color: var(--redup); margin: -1rem 0 1.5rem; min-height: 1.5em; }

/* ---------- Rak diskon Steam ---------- */
.rak { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.25rem;
       grid-template-columns: repeat(auto-fill, minmax(min(100%, 16rem), 1fr)); }
.barang {
  position: relative; display: flex; flex-direction: column;
  background: var(--tinta-2); clip-path: var(--sudut-potong);
  transition: transform var(--cepat), background var(--cepat);
}
.barang::after {                  /* garis kuning di dasar kartu */
  content: ""; position: absolute; left: 0; bottom: 0; height: 3px; width: 100%; background: var(--kuning);
  transform: scaleX(0); transform-origin: left; transition: transform var(--cepat);
}
.barang:hover { background: var(--tinta-3); transform: translateY(-3px); }
.barang:hover::after { transform: scaleX(1); }
.barang[hidden] { display: none; }
.barang > a:first-child { display: block; text-decoration: none; color: var(--putih); overflow: hidden; }
.barang img { display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; background: var(--tinta-3); transition: transform 500ms cubic-bezier(.16, 1, .3, 1); }
.barang:hover img { transform: scale(1.05); }
.barang h3 { font-size: 1rem; font-weight: 800; line-height: 1.3; margin: .9rem 1rem .3rem; }
.barang > a:first-child:hover h3 { color: var(--kuning); }
.barang .ulasan, .barang .terendah { margin: 0 1rem; font-size: .82rem; }
.barang .ulasan { color: var(--redup); display: flex; align-items: center; gap: .4rem; }
.barang .ulasan::before {        /* ikon jempol */
  content: ""; width: .85rem; height: .85rem; flex: none; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.barang .terendah { margin-top: .35rem; color: var(--hijau); font-weight: 700; }
.barang .terendah::before { content: "\25BC  "; font-size: .65em; }

/* Baris harga di dasar kartu; urutan diatur lewat `order`, HTML tidak berubah */
.label-rak { order: 2; margin-top: auto; padding: 1rem 1rem .4rem; }
.label-rak .potong { position: absolute; top: .65rem; left: .65rem; font-size: 1rem; }
.label-rak div { display: flex; align-items: baseline; }
.label-rak .harga { display: flex; align-items: baseline; flex-wrap: wrap; gap: .1rem .6rem; line-height: 1.1; padding-top: .75rem; border-top: 1px dashed var(--garis-terang); width: 100%; }
.label-rak strong { white-space: nowrap; font-weight: 900; font-stretch: var(--sempit); font-size: 1.75rem; font-variant-numeric: tabular-nums; }
.label-rak s { font-size: .82rem; color: var(--redup); font-variant-numeric: tabular-nums; }
.beli {
  order: 3; align-self: flex-start; margin: 0 1rem .75rem; padding: .3rem 0; min-height: 2.5rem;
  display: inline-flex; align-items: center; gap: .35rem;
  font-size: .8rem; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: var(--redup) !important; text-decoration: none;
}
.beli::after { content: "\2197"; color: var(--kuning); }
.beli:hover { color: var(--kuning) !important; }
.kosong { background: var(--tinta-2); border: 1px dashed var(--garis-terang); padding: 1.25rem; max-width: 64ch; color: var(--redup); }

/* ---------- Panel voucher & alarm ---------- */
.voucher {
  position: relative; margin: 0 0 1.75rem; max-width: 48rem; padding: 1.75rem 1.9rem 1.75rem 2.2rem;
  background: var(--tinta-2); color: var(--putih); clip-path: var(--sudut-potong);
}
.voucher::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--kuning); }
.voucher h2 { font-size: clamp(1.5rem, 2.8vw, 2rem); margin: 0 0 .55rem; color: var(--putih); }
.voucher h2::before, .voucher h2::after { display: none; }
.voucher p { margin: 0 0 .75rem; color: var(--redup); }
.voucher p strong { color: var(--putih); }
.voucher b, .voucher .kode b {
  color: var(--kuning); background: var(--kuning-redup); border: 1px dashed var(--kuning); padding: .05rem .45rem;
  font-weight: 800; letter-spacing: .05em; font-variant-numeric: tabular-nums;
}
.voucher .tombol { margin: .5rem 0 .9rem; }
.voucher .ungkap { font-size: .8rem; margin: 0; }
.voucher.lebar { max-width: none; display: flex; flex-wrap: wrap; gap: 1rem 3rem; align-items: center; justify-content: space-between; }
.voucher.lebar > div { flex: 1 1 28rem; }
.voucher.lebar > div > :last-child { margin-bottom: 0; }
.voucher.lebar .tombol { margin: 0; }
/* Alarm harga: panel dengan screentone di sisi kanan */
.voucher.alarm { isolation: isolate; }
.voucher.alarm::after {
  content: ""; position: absolute; z-index: -1; inset: 0 0 0 auto; width: 60%; pointer-events: none; background: var(--titik);
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 75%);
          mask-image: linear-gradient(90deg, transparent, #000 75%);
}
.voucher + .voucher { margin-bottom: 5.5rem; }

/* ---------- Tombol (jajar genjang) ---------- */
.tombol {
  position: relative; overflow: hidden; isolation: isolate;
  display: inline-flex; align-items: center; justify-content: center; gap: .45rem; min-height: 2.9rem; white-space: nowrap;
  background: var(--kuning); color: var(--tinta) !important; text-decoration: none;
  font-weight: 900; font-size: .9rem; text-transform: uppercase; letter-spacing: .05em;
  padding: .65rem 1.6rem; margin: 0 .6rem .6rem 0; clip-path: var(--jajar);
  transition: transform var(--cepat), background var(--cepat);
}
.tombol::after {                  /* kilau yang menyapu saat disorot */
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(105deg, transparent 35%, rgba(255, 255, 255, .55) 50%, transparent 65%);
  transform: translateX(-110%); transition: transform 500ms cubic-bezier(.16, 1, .3, 1);
}
.tombol:hover { text-decoration: none; }
.tombol:hover::after { transform: translateX(110%); }
.tombol:active { transform: translateY(1px); }
.tombol.kedua { background: var(--tinta-3); color: var(--putih) !important; }
.tombol.kedua::after { background: linear-gradient(105deg, transparent 35%, rgba(246, 225, 70, .25) 50%, transparent 65%); }
.tombol.kedua:hover { background: var(--garis-terang); }

/* ---------- Tanya jawab ---------- */
.tanya { max-width: 70ch; display: grid; gap: .5rem; }
.tanya details { background: var(--tinta-2); clip-path: var(--sudut-potong); }
.tanya summary {
  cursor: pointer; font-weight: 700; font-size: 1.02rem; padding: 1.1rem 3.5rem 1.1rem 1.25rem; position: relative; list-style: none;
  transition: color var(--cepat);
}
.tanya summary::-webkit-details-marker { display: none; }
.tanya summary::after {
  content: "+"; position: absolute; right: 1rem; top: 50%; transform: translateY(-50%);
  width: 1.9rem; height: 1.6rem; display: grid; place-items: center; clip-path: var(--jajar);
  font-size: 1.15rem; font-weight: 900; background: var(--kuning); color: var(--tinta); transition: transform var(--cepat);
}
.tanya details[open] summary::after { content: "\2212"; }
.tanya summary:hover { color: var(--kuning); }
.tanya p { margin: 0; padding: 0 1.25rem 1.2rem; color: var(--redup); }

/* ---------- Halaman game ---------- */
.produk { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 2.75rem; align-items: center; margin-bottom: 3rem; }
.produk img { display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; background: var(--tinta-3); clip-path: var(--sudut-potong); }
/* harga besar dengan label potongan */
.stiker {
  position: relative; display: inline-flex; align-items: center; gap: 1.1rem; margin: 0 0 1.25rem;
  background: var(--tinta-2); color: var(--putih); padding: 1rem 1.6rem 1rem 1.2rem;
  border-left: 5px solid var(--kuning); clip-path: var(--sudut-potong);
}
.stiker .harga { display: flex; flex-direction: column; line-height: 1.05; }
.stiker strong { white-space: nowrap; font-weight: 900; font-stretch: var(--sempit); font-size: clamp(2.5rem, 5.4vw, 3.3rem); font-variant-numeric: tabular-nums; }
.stiker s { color: var(--redup); font-variant-numeric: tabular-nums; margin-top: .2rem; }
.stiker .potong { font-size: 1.3rem; }
.kalimat { margin: 0 0 1.5rem; max-width: 46ch; font-size: 1.05rem; color: var(--redup); }
.kalimat.baik { color: var(--hijau); font-weight: 700; }
.fakta { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 13rem), 1fr)); gap: 1rem; margin: 0 0 3.5rem; }
.fakta div { position: relative; background: var(--tinta-2); clip-path: var(--sudut-potong); padding: 1.1rem 1.25rem 1.2rem; }
.fakta div::before { content: ""; position: absolute; left: 1.25rem; top: 0; width: 2rem; height: 3px; background: var(--kuning); }
.fakta dt { color: var(--redup); font-size: .74rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.fakta dd { margin: .35rem 0 0; font-weight: 900; font-stretch: var(--sempit); font-size: 1.9rem; line-height: 1.1; font-variant-numeric: tabular-nums; }
.fakta dd small { display: block; font-weight: 500; font-stretch: 100%; font-size: .84rem; color: var(--redup); margin-top: .25rem; }
.peringatan { background: var(--kuning-redup); border-left: 4px solid var(--kuning); color: var(--putih); padding: .9rem 1.15rem; margin: 0 0 2rem; max-width: 64ch; }

/* Riwayat harga & jadwal: layar status game */
.struk {
  max-width: 36rem; margin-bottom: 5.5rem; background: var(--tinta-2); color: var(--putih); padding: 1.75rem 1.75rem 1.5rem;
  clip-path: var(--sudut-potong); font-variant-numeric: tabular-nums;
}
.struk h2 { font-size: 1.7rem; margin: 0 0 .4rem; display: flex; align-items: center; gap: .6rem; }
.struk h2::before { content: ""; width: .55em; height: .85em; flex: none; background: var(--kuning); clip-path: polygon(40% 0, 100% 0, 60% 100%, 0 100%); }
.struk h2::after { display: none; }
.struk .catatan { font-size: .88rem; margin: 0 0 1.25rem; }
.struk table { width: 100%; border-collapse: collapse; font-size: .94rem; }
.struk th { font-weight: 800; color: var(--kuning); font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; text-align: left; padding: .5rem .5rem .6rem 0; border-bottom: 2px solid var(--garis-terang); }
.struk td { padding: .65rem .5rem .65rem 0; border-bottom: 1px solid var(--garis); vertical-align: top; }
.struk tbody tr:last-child td { border-bottom: 0; }
.struk .angka { text-align: right; padding-right: 0; }
.struk td.angka strong { font-weight: 800; }
.struk .turun { color: var(--kuning); font-weight: 800; }
.struk .normal { color: var(--redup); }
.struk tfoot td { border-bottom: 0; border-top: 2px solid var(--garis-terang); padding-top: 1rem; font-weight: 800; }
.struk tfoot td.angka { color: var(--hijau); }

/* ---------- Daftar semua game ---------- */
.cari { display: block; margin: 0 0 1.5rem; max-width: 34rem; }
.cari input {
  width: 100%; font: inherit; font-size: 1rem; color: var(--putih); min-height: 3rem;
  padding: .75rem 1rem .75rem 2.8rem; background-color: var(--tinta-2); border: 1px solid var(--garis-terang); border-left: 4px solid var(--kuning);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a7acbe' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: 1rem center; background-size: 1.1rem;
  transition: border-color var(--cepat), box-shadow var(--cepat);
}
.cari input::placeholder { color: var(--redup); }
.cari input:focus { outline: none; border-color: var(--kuning); box-shadow: 0 0 0 3px var(--kuning-redup); }
.daftar { list-style: none; margin: 0; padding: 0; max-width: 56rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 25rem), 1fr)); gap: .5rem 1.5rem; }
.daftar li { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .75rem 0; border-bottom: 1px dashed var(--garis-terang); }
.daftar li[hidden] { display: none; }
.daftar a { color: var(--putih); font-weight: 700; text-decoration: none; }
.daftar a:hover { color: var(--kuning); }
.daftar .harga { white-space: nowrap; font-variant-numeric: tabular-nums; color: var(--redup); font-size: .92rem; }
.daftar .harga b { color: var(--tinta); background: var(--kuning); font-weight: 900; font-stretch: var(--sempit); font-size: .95rem; padding: .1rem .55rem; margin-right: .55rem; display: inline-block; clip-path: polygon(5px 0, 100% 0, calc(100% - 5px) 100%, 0 100%); }

/* ---------- Artikel & halaman info ---------- */
.prosa { max-width: 68ch; font-size: 1.05rem; }
.prosa .meta { color: var(--redup); margin: -.5rem 0 2rem; font-size: .95rem; }
.prosa h2 { font-size: clamp(1.6rem, 3vw, 2.1rem); margin: 3rem 0 .8rem; }
.prosa h3 { font-size: 1.2rem; margin: 2rem 0 .5rem; }
.prosa p, .prosa ul, .prosa ol { margin: 0 0 1.15rem; color: #d6d8e1; }
.prosa strong { color: var(--putih); }
.prosa ul, .prosa ol { padding-left: 1.3rem; }
.prosa li { margin-bottom: .45rem; }
.prosa li::marker { color: var(--kuning); font-weight: 800; }
.prosa img { clip-path: var(--sudut-potong); }
.prosa blockquote { margin: 0 0 1.25rem; padding: .95rem 1.25rem; background: var(--tinta-2); border-left: 4px solid var(--kuning); }
.prosa blockquote p:last-child { margin-bottom: 0; }
.kotak-data { position: relative; background: var(--tinta-2); clip-path: var(--sudut-potong); border-left: 4px solid var(--kuning); padding: 1.15rem 1.35rem; margin: 0 0 1.75rem; }
.kotak-data p { margin: 0 0 .4rem !important; font-weight: 800; color: var(--putih) !important; }
.kotak-data ul { margin: 0 !important; }
.daftar-artikel { list-style: none; margin: 0; padding: 0; max-width: 70ch; display: grid; gap: .5rem; }
.daftar-artikel li { padding: 1.15rem 1.35rem; background: var(--tinta-2); clip-path: var(--sudut-potong); border-left: 4px solid var(--garis-terang); transition: border-color var(--cepat); }
.daftar-artikel li:hover { border-left-color: var(--kuning); }
.daftar-artikel h2 { display: block; font-stretch: 100%; text-transform: none; letter-spacing: 0; font-weight: 800; font-size: 1.2rem; line-height: 1.3; margin: 0 0 .4rem; }
.daftar-artikel h2::before, .daftar-artikel h2::after { display: none; }
.daftar-artikel h2 a { color: var(--putih); text-decoration: none; }
.daftar-artikel h2 a:hover { color: var(--kuning); }
.daftar-artikel p { color: var(--redup); margin: 0; font-size: .95rem; }

/* ---------- Kaki ---------- */
.kaki { position: relative; overflow: hidden; isolation: isolate; background: var(--tinta-0); border-top: 3px solid var(--kuning); padding: 3.25rem 0 3.5rem; color: var(--redup); font-size: .9rem; }
.kaki::before {                   /* screentone */
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none; background: var(--titik);
  -webkit-mask-image: linear-gradient(200deg, #000, transparent 45%);
          mask-image: linear-gradient(200deg, #000, transparent 45%);
}
.kaki::after {                    /* katakana ゲーム割引 bergaris, efek suara manga */
  content: "\30B2\30FC\30E0\5272\5F15"; position: absolute; z-index: -1; right: -1rem; bottom: -2.5rem; pointer-events: none;
  font-family: "Manga", sans-serif; font-size: 9rem; line-height: 1; white-space: nowrap;
  color: transparent; -webkit-text-stroke: 1.5px rgba(246, 225, 70, .12); transform: rotate(-5deg);
}
.kaki ul { list-style: none; display: flex; flex-wrap: wrap; gap: .25rem 1.75rem; margin: 0 0 1.5rem; padding: 0 0 1.5rem; border-bottom: 1px dashed var(--garis-terang); }
.kaki a { display: inline-block; padding: .35rem 0; color: var(--putih); font-weight: 700; text-decoration: none; }
.kaki a:hover { color: var(--kuning); }
.kaki p { margin: 0 0 .5rem; max-width: 72ch; }

/* ---------- Layar sedang ---------- */
@media (max-width: 64rem) {
  .nav { gap: 1rem; }
  .nav ul a { padding: .55rem .55rem; font-size: .88rem; }
  .hero { grid-template-columns: minmax(0, 1fr) minmax(0, 28rem); gap: 1.5rem 2.5rem; }
}
@media (max-width: 60rem) {
  .hero { grid-template-columns: 1fr; grid-template-rows: none; padding: 2.25rem 0 3rem; gap: 2rem; }
  .hero-judul, .hero-teks, .unggulan { grid-column: 1; grid-row: auto; }
  .unggulan { max-width: 36rem; margin-right: .5rem; }
  .kontrol label { margin-left: 0; }
}

/* ---------- Layar kecil ---------- */
@media (max-width: 48rem) {
  .wadah { padding: 0 1rem; }
  .nav { flex-wrap: wrap; gap: .4rem .5rem; padding: .7rem 0 .2rem; min-height: 0; }
  .logo { font-size: 1.35rem; }
  .logo-hanko { width: 2.1rem; height: 1.85rem; font-size: 1.1rem; }
  .nav ul { order: 3; width: calc(100% + 2rem); margin: 0 -1rem; padding: 0 .5rem; overflow-x: auto; scrollbar-width: none; }
  .nav ul::-webkit-scrollbar { display: none; }
  .tombol-tg { margin-left: auto; padding: .4rem .85rem; font-size: .74rem; letter-spacing: 0; min-height: 2.4rem; }
  .saring { flex-wrap: nowrap; overflow-x: auto; width: calc(100% + 2rem); margin: 0 -1rem; padding: 0 1rem .35rem; scrollbar-width: none; }
  .saring::-webkit-scrollbar { display: none; }
  .saring button { flex: none; white-space: nowrap; }
  .hero { padding: 1.75rem 0 2.75rem; }
  .hero h1 { font-size: clamp(2.3rem, 12.5vw, 3.2rem); }
  .sfx { font-size: 6.5rem; left: -.5rem; top: 1rem; }
  .hero-teks p { font-size: 1rem; }
  .hero-aksi { margin-top: 1.4rem; }
  .hero-aksi .tombol { flex: 1 1 auto; }
  .noren { font-size: 1.05rem; padding: .8rem .4rem; }
  .unggulan-isi { margin: -1.2rem .8rem 0 -.3rem; padding: .8rem 1rem .9rem; }
  .led-isi { font-size: 1rem; }
  main { padding: 3rem 0 4rem; }
  .bagian { margin-bottom: 4rem; }
  .rak { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
  .barang h3 { font-size: .92rem; margin: .7rem .7rem .2rem; }
  .barang .ulasan, .barang .terendah { margin-left: .7rem; margin-right: .7rem; font-size: .76rem; }
  .label-rak { padding: .75rem .7rem .3rem; }
  .label-rak .harga { flex-direction: column; align-items: flex-start; gap: .1rem; padding-top: .6rem; }
  .label-rak strong { font-size: 1.4rem; }
  .label-rak s { font-size: .74rem; }
  .label-rak .potong { font-size: .85rem; top: .45rem; left: .45rem; padding: .25rem .7rem .2rem; }
  .beli { margin: 0 .7rem .5rem; font-size: .72rem; }
  .stempel { width: 5rem; height: 5rem; }
  .stempel [lang="ja"] { font-size: 1.2rem; }
  .voucher { padding: 1.4rem 1.25rem 1.4rem 1.6rem; }
  .voucher.lebar .tombol { width: 100%; }
  .produk { grid-template-columns: 1fr; gap: 1.5rem; }
  .fakta { grid-template-columns: 1fr; gap: .6rem; }
  .daftar li { flex-wrap: wrap; gap: .3rem 1rem; }
  .struk { padding: 1.25rem 1.1rem 1rem; }
  .struk table { font-size: .86rem; }
  .kaki::after { font-size: 5.5rem; bottom: -1.5rem; }
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
# Label kuning 割 (tema "Shonen Sale"), dibuat ulang dengan: python aset/buat_merek.py. Disimpan di sini (base64) supaya tidak perlu file terpisah;
# tulis_css() menuliskannya ke folder docs setiap kali ada perubahan.
IKON = {
    "favicon.ico": (
    "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"
    ),
    "icon-192.png": (
    "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"
    ),
    "apple-touch-icon.png": (
    "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"
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
        '<meta name="theme-color" content="#0a0b12">',
        '<link rel="icon" href="/favicon.ico" sizes="48x48">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
    ]
    baris += [f'<link rel="preload" href="{f}" as="font" type="font/woff2" crossorigin>' for f in FONT_PRELOAD]
    baris += [f'<link rel="stylesheet" href="{HREF_CSS}">']
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
      <a class="logo" href="/"><span class="logo-hanko" lang="ja" aria-hidden="true">割</span><span>Game<b>Diskon</b></span></a>
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
