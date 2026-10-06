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
    "dela-gothic-jp.woff2": "fonts/dela-gothic-jp.woff2",   # huruf Jepang (Dela Gothic One, OFL), subset 15 huruf
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
/* Huruf Jepang untuk label & efek suara manga (Dela Gothic One, OFL). Subset 15 huruf, 3 KB:
   割引 無料 本日特価 近日 セール ゲーム. Kalau menambah huruf baru, unduh ulang subset-nya. */
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
/* efek suara manga セール: katakana besar bergaris di belakang judul */
.sfx {
  position: absolute; z-index: -1; left: -1.5rem; top: .5rem; pointer-events: none; user-select: none;
  font-size: clamp(7rem, 15vw, 13rem); line-height: 1; letter-spacing: -.02em; white-space: nowrap;
  color: transparent; -webkit-text-stroke: 1.5px rgba(246, 225, 70, .16); transform: rotate(-7deg);
}
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
    "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"
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
