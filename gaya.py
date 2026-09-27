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
FOLDER_ASET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aset")
FILE_ASET = {                      # nama di aset/ -> alamat di situs
    "archivo-latin.woff2": "fonts/archivo-latin.woff2",
    "archivo-latin-ext.woff2": "fonts/archivo-latin-ext.woff2",
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

/* =========================================================
   GameDiskon — tema "Dark Gaming" (v2)
   Pengganti langsung gaya.css lama: semua nama class sama,
   jadi template di generator bot tidak perlu diubah.
   Font tetap Archivo, di-host sendiri lewat @font-face di atas
   (file .woff2 di docs/fonts/), dipakai dalam dua lebar:
   lebar untuk judul, sempit untuk angka.
   ========================================================= */

/* ---------- Token ---------- */
:root {
  color-scheme: dark;
  --latar: #0a0d13;        /* kanvas paling gelap */
  --panel: #121722;        /* kartu */
  --panel-2: #192030;      /* kartu saat hover, input */
  --garis: #262f42;
  --garis-terang: #36415a;
  --tinta: #eef1f7;        /* teks utama  — 17.6:1 di --latar */
  --redup: #9ba5ba;        /* teks kedua  —  7.9:1 di --latar, 7.1:1 di --panel */
  --lime: #b8f229;         /* warna diskon & aksi utama */
  --lime-tua: #9bd40f;
  --sian: #5cd2ff;         /* tautan */
  --magenta: #ff4d8d;      /* GRATIS & hitung mundur */
  --ungu: #7b61ff;         /* cahaya latar */
  --kuning: #ffd23f;       /* kode promo */
  --lebar-judul: 118%;
  --sempit: 75%;
  --lebar-isi: 76rem;
  --sudut: 14px;
  --sudut-kecil: 8px;
  --cepat: 180ms cubic-bezier(.2, .7, .3, 1);
}

*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body {
  margin: 0; background: var(--latar); color: var(--tinta);
  font-family: "Archivo", system-ui, sans-serif; font-size: 1rem; line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
img { max-width: 100%; height: auto; }
a { color: var(--sian); text-underline-offset: 3px; transition: color var(--cepat); }
a:hover { color: #9fe4ff; }
:focus-visible { outline: 2px solid var(--lime); outline-offset: 3px; border-radius: 4px; }
::selection { background: var(--lime); color: var(--latar); }
.wadah { max-width: var(--lebar-isi); margin: 0 auto; padding: 0 1.25rem; }
.lompat { position: absolute; left: -999px; }
.lompat:focus { left: 1rem; top: 1rem; z-index: 50; background: var(--lime); color: var(--latar); padding: .5rem 1rem; border-radius: var(--sudut-kecil); font-weight: 800; }

/* ---------- Kepala + hero ---------- */
.pita {
  position: relative; isolation: isolate; overflow: hidden;
  background:
    radial-gradient(60rem 28rem at 85% -10%, rgba(123, 97, 255, .35), transparent 60%),
    radial-gradient(40rem 22rem at 5% 110%, rgba(184, 242, 41, .12), transparent 60%),
    var(--latar);
  border-bottom: 1px solid var(--garis);
}
/* grid halus ala HUD */
.pita::before {
  content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 44px 44px;
  -webkit-mask-image: linear-gradient(to bottom, #000 30%, transparent 95%);
          mask-image: linear-gradient(to bottom, #000 30%, transparent 95%);
}
.pita a { color: var(--tinta); }
.nav { display: flex; align-items: center; gap: 1.75rem; padding: 1.1rem 0; flex-wrap: wrap; }
.logo {
  display: inline-flex; align-items: center; gap: .1rem; text-decoration: none;
  font-weight: 900; font-stretch: var(--lebar-judul); font-size: 1.35rem; line-height: 1;
  letter-spacing: -.01em; text-transform: uppercase;
}
.logo::before {                  /* ikon tag harga kecil */
  content: ""; width: 1.55rem; height: 1.55rem; margin-right: .5rem; border-radius: 6px;
  background: var(--lime) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230a0d13' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8Z'/%3E%3Ccircle cx='7.5' cy='7.5' r='1.5'/%3E%3C/svg%3E") center / 62% no-repeat;
  box-shadow: 0 0 18px rgba(184, 242, 41, .45);
}
.logo span { color: var(--lime); }
.nav ul { list-style: none; display: flex; gap: .35rem; margin: 0 0 0 auto; padding: 0; flex-wrap: wrap; }
.nav ul a {
  display: block; text-decoration: none; font-weight: 600; font-size: .95rem; color: var(--redup);
  padding: .5rem .85rem; border-radius: 999px; transition: color var(--cepat), background var(--cepat);
}
.nav ul a:hover, .nav ul a[aria-current] { color: var(--tinta); background: rgba(255,255,255,.07); }
.tombol-tg {
  display: inline-flex; align-items: center; gap: .5rem; white-space: nowrap;
  background: var(--lime); color: var(--latar) !important; text-decoration: none; font-weight: 800; font-size: .95rem;
  padding: .6rem 1.1rem; border-radius: 999px; transition: background var(--cepat), box-shadow var(--cepat);
}
.tombol-tg::before {             /* ikon pesawat kertas Telegram */
  content: ""; width: 1rem; height: 1rem; flex: none;
  background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M21.9 4.3 18.7 19.4c-.2 1-.9 1.3-1.7.8l-4.8-3.6-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.9 8.9-8c.4-.3-.1-.5-.6-.2l-11 6.9-4.7-1.5c-1-.3-1-1 .2-1.5L20.6 3c.9-.3 1.6.2 1.3 1.3Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.tombol-tg:hover { background: #d4ff66; box-shadow: 0 0 24px rgba(184, 242, 41, .4); }

.hero {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 23rem); gap: 2.5rem 3.5rem;
  align-items: center; padding: 3.5rem 0 4.5rem;
}
.hero h1 {
  font-weight: 900; font-stretch: var(--lebar-judul); text-transform: uppercase;
  font-size: clamp(2.3rem, 6.2vw, 4.6rem); line-height: .98; letter-spacing: -.02em; margin: 0; max-width: 16ch;
}
/* baris terakhir judul ("dalam Rupiah") tidak bisa disasar tanpa ubah HTML,
   jadi seluruh judul diberi gradasi putih → lime yang halus */
.hero h1 {
  background: linear-gradient(172deg, #fff 0%, #fff 52%, var(--lime) 105%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { font-size: 1.08rem; margin: 1.35rem 0 0; max-width: 52ch; color: var(--redup); }
.hero .event {
  display: inline-flex; align-items: center; gap: .6rem; max-width: none; margin-top: 1.5rem;
  background: rgba(255, 210, 63, .1); color: var(--kuning); border: 1px solid rgba(255, 210, 63, .35);
  font-weight: 700; font-size: .95rem; padding: .45rem .9rem; border-radius: 12px;
}
.hero .event::before {
  content: ""; width: .5rem; height: .5rem; border-radius: 50%; background: var(--kuning);
  box-shadow: 0 0 0 4px rgba(255, 210, 63, .2); animation: denyut 2s infinite;
}
@keyframes denyut { 50% { box-shadow: 0 0 0 7px rgba(255, 210, 63, 0); } }

/* kartu "potongan terbesar hari ini" */
.unggulan {
  display: flex; flex-direction: column; align-items: flex-start; gap: .2rem; text-decoration: none;
  color: var(--tinta); padding: 1.4rem 1.5rem 1.5rem; border-radius: var(--sudut);
  background: linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.02));
  border: 1px solid rgba(255,255,255,.12);
  box-shadow: 0 20px 60px -20px rgba(0,0,0,.8), inset 0 1px 0 rgba(255,255,255,.08);
  -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
  transition: border-color var(--cepat), box-shadow var(--cepat);
}
.unggulan:hover { border-color: rgba(184, 242, 41, .6); box-shadow: 0 20px 60px -20px rgba(184,242,41,.35), inset 0 1px 0 rgba(255,255,255,.08); }
.unggulan-ket {
  font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: var(--lime);
}
.unggulan .stiker { margin: .6rem 0 .9rem; }
.unggulan .stiker strong { font-size: clamp(1.9rem, 4vw, 2.4rem); }
.unggulan-nama { font-weight: 800; font-size: 1.35rem; line-height: 1.2; }
.pita .unggulan:hover .unggulan-nama { color: var(--lime); }

/* ---------- Judul & teks umum ---------- */
main { padding: 3rem 0 5rem; }
.bagian { margin-bottom: 4.5rem; }
h1, h2, h3 { font-weight: 800; line-height: 1.1; letter-spacing: -.01em; }
h2 {
  font-stretch: var(--lebar-judul); text-transform: uppercase; font-weight: 900;
  font-size: clamp(1.5rem, 3.2vw, 2.1rem); margin: 0 0 .5rem;
  display: flex; align-items: center; gap: .75rem;
}
.bagian > h2::before {           /* penanda aksen di kiri judul bagian */
  content: ""; width: .35rem; height: 1.1em; border-radius: 2px; background: var(--lime);
  box-shadow: 0 0 14px rgba(184, 242, 41, .6); flex: none;
}
h3 { font-size: 1.2rem; }
.judul-halaman { font-stretch: var(--lebar-judul); font-weight: 900; font-size: clamp(1.9rem, 4.6vw, 3.1rem); margin: 0 0 1.5rem; max-width: 24ch; }
.catatan { color: var(--redup); margin: 0 0 1.75rem; max-width: 64ch; }
.jejak { font-size: .88rem; color: var(--redup); margin: 0 0 1.25rem; }
.jejak ol { list-style: none; display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; }
.jejak li + li::before { content: "›"; margin-right: .4rem; color: var(--garis-terang); }
.jejak a { color: var(--redup); text-decoration: none; }
.jejak a:hover { color: var(--tinta); }

/* ---------- Game gratis Epic ---------- */
.gratis { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.5rem;
          grid-template-columns: repeat(auto-fill, minmax(min(100%, 21rem), 1fr)); }
.gratis a {
  display: block; position: relative; height: 100%; text-decoration: none; color: var(--tinta);
  background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut); overflow: hidden;
  transition: border-color var(--cepat), box-shadow var(--cepat), background var(--cepat);
}
.gratis a:hover { border-color: rgba(255, 77, 141, .7); background: var(--panel-2); box-shadow: 0 0 0 1px rgba(255,77,141,.25), 0 18px 40px -18px rgba(255,77,141,.45); }
.gratis img { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: var(--panel-2); transition: filter var(--cepat); }
.gratis a:hover img { filter: brightness(1.08) saturate(1.1); }
.stempel {
  position: absolute; top: .85rem; left: .85rem; z-index: 1;
  background: var(--magenta); color: var(--latar); font-weight: 900; font-size: .8rem; letter-spacing: .12em;
  padding: .35rem .7rem; border-radius: 999px; box-shadow: 0 6px 20px rgba(255, 77, 141, .5);
}
.gratis h3 { margin: 1rem 1.2rem .3rem; font-size: 1.35rem; }
.batas { margin: 0 1.2rem 1.2rem; color: var(--redup); font-size: .95rem; }
.sisa { color: var(--magenta); font-weight: 800; }

/* ---------- Kontrol saring & urut ---------- */
.kontrol { display: flex; flex-wrap: wrap; gap: .75rem 1.5rem; align-items: center; margin: 0 0 2rem; }
.saring { display: flex; flex-wrap: wrap; gap: .5rem; }
.saring button, .kontrol select {
  font: inherit; font-weight: 600; font-size: .92rem; color: var(--redup); background: var(--panel);
  border: 1px solid var(--garis); border-radius: 999px; padding: .55rem 1rem; min-height: 2.75rem; cursor: pointer;
  transition: color var(--cepat), border-color var(--cepat), background var(--cepat);
}
.saring button:hover, .kontrol select:hover { color: var(--tinta); border-color: var(--garis-terang); }
.saring button[aria-pressed="true"] { background: var(--lime); border-color: var(--lime); color: var(--latar); font-weight: 800; }
.kontrol select { padding-right: 2.2rem; appearance: none; -webkit-appearance: none;
  background: var(--panel) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239ba5ba' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") right .8rem center / 1rem no-repeat; }
.kontrol label { display: flex; gap: .6rem; align-items: center; color: var(--redup); margin-left: auto; font-size: .92rem; }
.hasil-saring { color: var(--redup); margin: -1rem 0 1.5rem; min-height: 1.5em; }

/* ---------- Rak diskon Steam: kartu game ---------- */
.rak { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.25rem;
       grid-template-columns: repeat(auto-fill, minmax(min(100%, 15.5rem), 1fr)); }
.barang {
  position: relative; display: flex; flex-direction: column; overflow: hidden;
  background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut);
  transition: border-color var(--cepat), box-shadow var(--cepat), background var(--cepat);
}
.barang:hover { border-color: rgba(184, 242, 41, .55); background: var(--panel-2); box-shadow: 0 18px 40px -20px rgba(184, 242, 41, .35); }
.barang[hidden] { display: none; }
.barang > a:first-child { display: block; text-decoration: none; color: var(--tinta); }
.barang img { display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; background: var(--panel-2); transition: filter var(--cepat); }
.barang:hover img { filter: brightness(1.08) saturate(1.1); }
.barang h3 { font-size: 1.05rem; line-height: 1.3; margin: .85rem 1rem .25rem; }
.barang > a:hover h3 { color: var(--lime); }
.barang .ulasan, .barang .terendah { margin: 0 1rem; font-size: .85rem; }
.barang .ulasan { color: var(--redup); display: flex; align-items: center; gap: .35rem; }
.barang .ulasan::before {        /* ikon jempol */
  content: ""; width: .9rem; height: .9rem; flex: none; background: #66c0f4;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M2 21h4V9H2v12Zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.4-.6.9-.6 1.4v10a2 2 0 0 0 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2Z'/%3E%3C/svg%3E") center / contain no-repeat;
}
.barang .terendah { margin-top: .35rem; color: var(--lime); font-weight: 700; }

/* label harga dipindah ke atas tombol beli lewat `order`, tanpa ubah HTML */
.label-rak { order: 2; margin-top: auto; padding: 1rem 1rem .75rem; }
.label-rak div { display: flex; align-items: center; gap: .7rem; }
.potong {
  display: inline-flex; align-items: center; background: var(--lime); color: var(--latar);
  font-weight: 900; font-stretch: var(--sempit); font-size: 1.25rem; line-height: 1;
  padding: .4rem .5rem; border-radius: 6px; font-variant-numeric: tabular-nums;
}
.label-rak .harga { display: flex; flex-direction: column; line-height: 1.1; }
.label-rak strong { white-space: nowrap; font-weight: 900; font-size: 1.3rem; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.label-rak s { font-size: .8rem; color: var(--redup); font-variant-numeric: tabular-nums; }
.beli {
  order: 3; display: flex; align-items: center; justify-content: center; gap: .4rem;
  margin: 0 1rem 1rem; min-height: 2.75rem; padding: .55rem 1rem;
  font-size: .9rem; font-weight: 700; text-decoration: none; color: var(--tinta) !important;
  border: 1px solid var(--garis-terang); border-radius: var(--sudut-kecil);
  transition: background var(--cepat), border-color var(--cepat), color var(--cepat);
}
.beli::after { content: "↗"; font-weight: 800; }
.beli:hover { background: var(--lime); border-color: var(--lime); color: var(--latar) !important; }
.kosong { background: var(--panel); border: 1px dashed var(--garis-terang); border-radius: var(--sudut); padding: 1.25rem; max-width: 64ch; color: var(--redup); }

/* ---------- Kotak voucher & alarm ---------- */
.voucher {
  position: relative; overflow: hidden; margin: 0 0 1.5rem; max-width: 46rem; padding: 1.6rem 1.75rem;
  background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut);
}
.voucher::before {               /* garis aksen menyala di sisi kiri */
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--kuning);
  box-shadow: 0 0 22px rgba(255, 210, 63, .6);
}
.voucher h2 { font-size: 1.35rem; margin: 0 0 .5rem; }
.voucher p { margin: 0 0 .7rem; color: var(--redup); }
.voucher p strong { color: var(--tinta); }
.voucher b, .voucher .kode b {
  color: var(--kuning); background: rgba(255, 210, 63, .1); border: 1px dashed rgba(255, 210, 63, .5);
  padding: .05rem .45rem; border-radius: 5px; font-weight: 800; letter-spacing: .03em; font-variant-numeric: tabular-nums;
}
.voucher .tombol { margin: .5rem 0 .9rem; }
.voucher .ungkap { font-size: .82rem; margin: 0; }
.voucher.lebar { max-width: none; display: flex; flex-wrap: wrap; gap: 1rem 2.5rem; align-items: center; justify-content: space-between; }
.voucher.lebar > div { flex: 1 1 28rem; }
.voucher.lebar > div > :last-child { margin-bottom: 0; }
.voucher.lebar .tombol { margin: 0; }
.voucher.alarm {
  background:
    radial-gradient(30rem 12rem at 100% 0%, rgba(123, 97, 255, .25), transparent 70%),
    var(--panel);
}
.voucher.alarm::before { background: var(--ungu); box-shadow: 0 0 22px rgba(123, 97, 255, .8); }
.voucher.alarm .tombol { background: #6246ea; color: #fff !important; }
.voucher.alarm .tombol:hover { background: #5236d6; box-shadow: 0 0 24px rgba(123, 97, 255, .5); }
.voucher + .voucher { margin-bottom: 4.5rem; }

/* ---------- Tanya jawab ---------- */
.tanya { max-width: 64ch; display: grid; gap: .6rem; }
.tanya details { background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut-kecil); transition: border-color var(--cepat); }
.tanya details[open] { border-color: var(--garis-terang); }
.tanya summary {
  cursor: pointer; font-weight: 700; font-size: 1rem; padding: 1rem 3rem 1rem 1.2rem; position: relative; list-style: none;
}
.tanya summary::-webkit-details-marker { display: none; }
.tanya summary::after {
  content: "+"; position: absolute; right: 1.2rem; top: 50%; transform: translateY(-50%);
  font-size: 1.4rem; font-weight: 400; color: var(--lime); transition: transform var(--cepat);
}
.tanya details[open] summary::after { transform: translateY(-50%) rotate(45deg); }
.tanya summary:hover { color: var(--lime); }
.tanya p { margin: 0; padding: 0 1.2rem 1.1rem; color: var(--redup); }

/* ---------- Halaman game ---------- */
.produk { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 2.5rem; align-items: center; margin-bottom: 2.5rem; }
.produk img {
  display: block; width: 100%; aspect-ratio: 460 / 215; object-fit: cover; border-radius: var(--sudut);
  background: var(--panel-2); border: 1px solid var(--garis); box-shadow: 0 30px 60px -30px rgba(0,0,0,.9);
}
.stiker { display: inline-flex; align-items: center; gap: .9rem; margin: .5rem 0 1.25rem; }
.stiker .potong { font-size: 2rem; padding: .55rem .65rem; border-radius: var(--sudut-kecil); box-shadow: 0 0 30px rgba(184, 242, 41, .35); }
.stiker .harga { display: flex; flex-direction: column; line-height: 1.05; }
.stiker strong { white-space: nowrap; font-weight: 900; font-size: clamp(2rem, 4.8vw, 2.8rem); letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.stiker s { color: var(--redup); font-variant-numeric: tabular-nums; }
.kalimat { margin: 0 0 1.5rem; max-width: 46ch; font-size: 1.05rem; color: var(--redup); }
.kalimat.baik { color: var(--lime); font-weight: 700; }
.tombol {
  display: inline-flex; align-items: center; justify-content: center; min-height: 2.9rem;
  background: var(--lime); color: var(--latar) !important; text-decoration: none; font-weight: 800;
  padding: .7rem 1.3rem; border-radius: var(--sudut-kecil); margin: 0 .5rem .5rem 0;
  transition: background var(--cepat), box-shadow var(--cepat);
}
.tombol:hover { background: #d4ff66; box-shadow: 0 0 26px rgba(184, 242, 41, .4); }
.tombol.kedua { background: transparent; color: var(--tinta) !important; box-shadow: inset 0 0 0 1px var(--garis-terang); }
.tombol.kedua:hover { background: rgba(255,255,255,.06); box-shadow: inset 0 0 0 1px var(--tinta); }
.fakta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 0 0 3rem; }
.fakta div { background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut); padding: 1.1rem 1.25rem; }
.fakta dt { color: var(--redup); font-size: .78rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.fakta dd { margin: .35rem 0 0; font-weight: 900; font-size: 1.5rem; line-height: 1.15; font-variant-numeric: tabular-nums; }
.fakta dd small { display: block; font-weight: 500; font-size: .85rem; color: var(--redup); margin-top: .2rem; }
.peringatan { background: rgba(255, 210, 63, .08); border: 1px solid rgba(255, 210, 63, .35); color: #ffe38a; border-radius: var(--sudut-kecil); padding: .85rem 1.1rem; margin: 0 0 2rem; max-width: 64ch; }

/* Riwayat harga — tetap struk bergerigi, versi gelap */
.struk {
  max-width: 32rem; background: var(--panel); padding: 2rem 1.6rem 2.2rem; position: relative;
  --gigi: radial-gradient(circle at 50% 100%, transparent .4rem, #000 .45rem) 50% 100% / 1rem 51% repeat-x,
          radial-gradient(circle at 50% 0, transparent .4rem, #000 .45rem) 50% 0 / 1rem 51% repeat-x;
  -webkit-mask: var(--gigi); mask: var(--gigi);
}
.struk h2 { justify-content: center; font-size: 1.35rem; margin: .25rem 0; }
.struk .catatan { text-align: center; font-size: .88rem; margin: 0 auto 1.1rem; }
.struk table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.struk th { font-weight: 700; color: var(--redup); font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; text-align: left; padding: .5rem 0; border-bottom: 1px dashed var(--garis-terang); }
.struk td { padding: .6rem 0; border-bottom: 1px dashed var(--garis); }
.struk .angka { text-align: right; }
.struk td.angka strong { font-weight: 800; }
.struk .turun { color: var(--lime); font-weight: 800; }
.struk .normal { color: var(--redup); }
.struk tfoot td { border-bottom: 0; padding-top: 1rem; font-weight: 800; color: var(--lime); }

/* ---------- Daftar semua game ---------- */
.cari { display: block; margin: 0 0 1.5rem; max-width: 32rem; position: relative; }
.cari input {
  width: 100%; font: inherit; font-size: 1rem; color: var(--tinta); min-height: 3rem;
  padding: .75rem 1rem .75rem 2.8rem; background: var(--panel); border: 1px solid var(--garis-terang); border-radius: 999px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239ba5ba' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: 1rem center; background-size: 1.1rem;
  transition: border-color var(--cepat), box-shadow var(--cepat);
}
.cari input::placeholder { color: var(--redup); }
.cari input:focus { outline: none; border-color: var(--lime); box-shadow: 0 0 0 3px rgba(184, 242, 41, .2); }
.daftar { list-style: none; margin: 0; padding: 0; max-width: 54rem; background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut); overflow: hidden; }
.daftar li { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .8rem 1.2rem; border-bottom: 1px solid var(--garis); transition: background var(--cepat); }
.daftar li:last-child { border-bottom: 0; }
.daftar li:hover { background: var(--panel-2); }
.daftar li[hidden] { display: none; }
.daftar a { color: var(--tinta); font-weight: 600; text-decoration: none; }
.daftar a:hover { color: var(--lime); }
.daftar .harga { white-space: nowrap; font-variant-numeric: tabular-nums; color: var(--redup); }
.daftar .harga b { color: var(--latar); background: var(--lime); font-weight: 900; font-stretch: var(--sempit); font-size: 1rem; padding: .1rem .35rem; border-radius: 4px; margin-right: .5rem; }

/* ---------- Artikel & halaman info ---------- */
.prosa { max-width: 68ch; font-size: 1.05rem; }
.prosa .meta { color: var(--redup); margin: -.5rem 0 2rem; font-size: .95rem; }
.prosa h2 { font-size: 1.5rem; margin: 2.75rem 0 .75rem; }
.prosa h3 { font-size: 1.25rem; margin: 2rem 0 .5rem; }
.prosa p, .prosa ul, .prosa ol { margin: 0 0 1.15rem; color: #d3d9e5; }
.prosa strong { color: var(--tinta); }
.prosa ul, .prosa ol { padding-left: 1.3rem; }
.prosa li { margin-bottom: .45rem; }
.prosa li::marker { color: var(--lime); font-weight: 800; }
.prosa img { border-radius: var(--sudut); }
.prosa blockquote { margin: 0 0 1.25rem; padding: .9rem 1.2rem; background: var(--panel); border-left: 3px solid var(--sian); border-radius: 0 var(--sudut-kecil) var(--sudut-kecil) 0; }
.prosa blockquote p:last-child { margin-bottom: 0; }
.kotak-data { background: rgba(184, 242, 41, .07); border: 1px solid rgba(184, 242, 41, .35); border-radius: var(--sudut); padding: 1.1rem 1.3rem; margin: 0 0 1.75rem; }
.kotak-data p { margin: 0 0 .4rem !important; font-weight: 700; color: var(--tinta) !important; }
.kotak-data ul { margin: 0 !important; }
.kotak-data a { color: var(--lime); font-weight: 700; }
.daftar-artikel { list-style: none; margin: 0; padding: 0; max-width: 68ch; display: grid; gap: .9rem; }
.daftar-artikel li { background: var(--panel); border: 1px solid var(--garis); border-radius: var(--sudut); padding: 1.3rem 1.4rem; transition: border-color var(--cepat), background var(--cepat); }
.daftar-artikel li:hover { border-color: var(--garis-terang); background: var(--panel-2); }
.daftar-artikel h2 { display: block; font-stretch: 100%; text-transform: none; font-weight: 800; font-size: 1.25rem; line-height: 1.3; margin: 0 0 .4rem; }
.daftar-artikel h2::before { display: none; }
.daftar-artikel h2 a { color: var(--tinta); text-decoration: none; }
.daftar-artikel h2 a:hover { color: var(--lime); }
.daftar-artikel p { color: var(--redup); margin: 0; font-size: .95rem; }

/* ---------- Kaki ---------- */
.kaki { background: #07090d; border-top: 1px solid var(--garis); padding: 2.75rem 0 3.25rem; color: var(--redup); font-size: .9rem; }
.kaki ul { list-style: none; display: flex; flex-wrap: wrap; gap: .5rem 1.75rem; margin: 0 0 1.4rem; padding: 0 0 1.4rem; border-bottom: 1px solid var(--garis); }
.kaki a { color: var(--tinta); font-weight: 600; text-decoration: none; }
.kaki a:hover { color: var(--lime); }
.kaki p { margin: 0 0 .5rem; max-width: 72ch; }

/* ---------- Layar sedang ---------- */
@media (max-width: 60rem) {
  .hero { grid-template-columns: 1fr; padding: 2.5rem 0 3.5rem; }
  .unggulan { max-width: 26rem; }
  .kontrol label { margin-left: 0; }
}

/* ---------- Layar kecil ---------- */
@media (max-width: 44rem) {
  .nav { gap: .75rem 1rem; padding: .9rem 0; }
  .logo { font-size: 1.05rem; }
  .logo::before { width: 1.35rem; height: 1.35rem; margin-right: .4rem; }
  .nav ul { margin: 0; order: 3; width: 100%; overflow-x: auto; flex-wrap: nowrap; gap: .25rem; margin-left: -.85rem; }
  .nav ul a { padding: .55rem .85rem; white-space: nowrap; }
  .tombol-tg { margin-left: auto; padding: .5rem .8rem; font-size: .82rem; gap: .4rem; }
  .tombol-tg::before { display: none; }
  .saring { flex-wrap: nowrap; overflow-x: auto; width: calc(100% + 2.5rem); margin: 0 -1.25rem; padding: 0 1.25rem .25rem; scrollbar-width: none; }
  .saring::-webkit-scrollbar { display: none; }
  .saring button { flex: none; white-space: nowrap; }
  .hero { padding: 1.5rem 0 2.75rem; gap: 1.75rem; }
  .hero h1 { font-size: clamp(2rem, 9.5vw, 2.8rem); }
  .hero p { font-size: 1rem; }
  main { padding-top: 2.25rem; }
  .bagian { margin-bottom: 3.5rem; }
  .rak { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
  .barang h3 { font-size: .95rem; margin: .7rem .7rem .2rem; }
  .barang .ulasan, .barang .terendah { margin-left: .7rem; margin-right: .7rem; font-size: .8rem; }
  .label-rak { padding: .8rem .7rem .6rem; }
  .label-rak div { gap: .45rem; }
  .potong { font-size: 1.05rem; padding: .35rem .4rem; }
  .label-rak strong { font-size: 1.05rem; }
  .label-rak s { font-size: .74rem; }
  .beli { margin: 0 .7rem .7rem; font-size: .85rem; }
  .voucher { padding: 1.35rem 1.25rem 1.35rem 1.5rem; }
  .voucher.lebar .tombol { width: 100%; }
  .produk { grid-template-columns: 1fr; gap: 1.25rem; }
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
# Stiker kuning "GD" dari logo GameDiskon. Disimpan di sini (base64) supaya tidak perlu file terpisah;
# tulis_css() menuliskannya ke folder docs setiap kali ada perubahan.
IKON = {
    "favicon.ico": (
    "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"
    ),
    "icon-192.png": (
    "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAMAAABlApw1AAAAwFBMVEXfphipmCBjamLkXhZhVxaWkE0uLBoyTpkcOqLcNxuJeBJO"
    "YIYJKJEAKn8bPqk2RmvbwhsmOnQcQK4bPqgZQqxBPBgcQbEAf396gVKBfEcbPqr+1gkWGB3XGR4TLXwAAAAdQK3+4gUGCh4XNY8I"
    "JIMXMHvUCyDuyA4hQqXVEiDVuBDZJxwAAP8KPbYbPqoAVaoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAACBUZ/BAAAAMHRSTlP/////////+yb////uA7P///+sSRz/UAL///7/////AP3//////////////wEJcQMttXbJAAAL"
    "QElEQVR42u2diZLaOhBFZQNmGJYQZkmeWWwxDAKz/f/fPUk2GKytJQxjVUWppLLPPVLrdmsxRomk7Q97+uP753EyitP4R1sajybH"
    "z/eLKKEhifwhU38cxClt8Y83rmJwZAzDPQSAyj98jpoh/hpi9Hng4gwApz+087tNEl9CdOkw/DnpAegfH+Mmys8R4iOXqATY75O3"
    "SVPl5wiTN6ZSAcC6v8nyc4TKIKBr/S+ThsvnCJOXa4IS4JC8pB7oZ4PwQsUKAENf9OcEwyrAyR/9OcHpFsAr/TcEOcBw/xJ7pJ+V"
    "SC/74RXAaTjxSj/zouGpBDhR/489azQfnM4AbALE3rViGiCeAUY+Aox4NkAsAxw91M+DaMgB9ofUT4CUrdEQHQc/B4APwSFB+/0h"
    "9hUgPuz36JC8eaqfErwlB3Q6jPwFGB1OyMsccJUL0P7oM8Bxj5KBzwCDBHnrQYUPoTeP9TMfQke/AY5o5DfAyH+A2POGUr/1pw0d"
    "AXiBj5onPd1sLMICNUx4Ib272XgDwIWXIdPvh50OItO/wAoB/XSnn3/R7fap8DGa4inG0ynuxJvGAtyE+WbTDcMOQtMpF35pQQNH"
    "gEY4i5bLL3m0jAnBN8qLNm7UHGCnjKW1dLsszMfjaqffNLKBDQF6vPAyzDf9MAzEaJG3Lv/X6Q8B8B4vv3o3pDM0IAQi/Nz69N99"
    "0fZsgIq18GhBBNtI5w2Hq68FbU8DuM2g3Q23FgKLFilAZ/DNABaGqYDqEV5NRFPiKvwCEKxygK/HAYiJqDNG7n1eaWi1eBQAKBHd"
    "3ciidoDCWi7S+6zPCalZ+KX9XtUHIE1EpPZOr9rQN8CGEKDTyxqXJiL0gGjRAiycAApvuScR3Q3QyQFWtgDX1rLh0TJ2SUT3A8B8"
    "FIklI/uBWcvzokXloy4AadzNExF+kHCM+f9MaDwa+oZ8LxwANnFIw+VRyqkqhFqtVm9HW6/XQkj3tUA+KgF4jHLElPd28zVr2+12"
    "Tr+v1/NeiygRzj5qG0KkTu00Vq6UU92Vtl3v0F2JQAJQY+dz5Vsufa5s65a8y/B/kHpUBEhRfQA7nfCSoEe0PmoFQCdBB1t6itJM"
    "cAuiX0kA8lF3AG4pQfBKvwVInqNxaz2HEbRkXyGD1KOSRBaC1KOgHUWzZd5ms6gdiHaCERCAEmBHH5UA9M1xg9pM++y6LZdRu4oA"
    "B5jPZTPvF8CGXABQe3Yr/swQvVb/Jli/LIhAPiqrRrU2hMftpVQ+R/i4HQQyhxMgMQL/OgIQbY04U8rng5Dd6OhtoQDbnuRrDcw2"
    "JCmn40Cj/1Unn7fMxYbkQ4AAiUAE0Ppo26h/FhFHANGIxgAftQLAAP2zZdtkQ1t5ZbETQpf8XjiFUKiMf4B+SvCK9QA9WiJtQTH0"
    "a+UEoCrnshmwlV2JRKEsazOD3Zqd9Oyjq7gegPYSpn/ZvnQl2QkAudFiBIghNwBKgO4IoIoT7baKQJHM7201hsp6tA6AaQQGuJoF"
    "gsxLpCOzD0E2JqQAHfAALOVZOVL7aKlS80cW9agEgK/rQRa6nH2027KBWZ67WQMgiSHRSM31KBiASMqGgBtKoJnGoo9eSgYsOpRo"
    "pL9WTiHUh0TQ8lw9YxSJbGqVl24WHUoAwOaNCSnAhgAiqCwZcKCuJ4im8heymTiLQ+O6HgowjdROI5sfAVaqVM8PoSIFrOtl5bSs"
    "GiKRpuqUxNerehYj+CwG+CgUAOmKTgFvWc5ijQ1JCqVqBsqMB2UKAPMcjm6rjOu8EFFzDQCJAGBD5noUxSAbEgCui2a+zuHKI6o8"
    "yNgeC54afVQywcVUZlzXywFCgAnd8hXKp8Iul1AxbHdlpWe0oWnoBiDYkAHgvAUt2+VX+yg2FxPYCYC2sUUaMO2P3uejpnW9AgCZ"
    "K6FMdxxAUDZ18NGt0kdjKwCJjwoAS6FuyZVnwSst8CJHHxXKOWM9CgQQR2B5ybX4Wvms2CutKxEYD8pQDLIhCcA51xKUK58tbxYH"
    "kdpHW7oJbluPKgC6ZoCiiz/OfV5tY0CcCBN8i2xtSAHQBwAYtoqQupvJ1FjpgS8cKFyomggkW4qRHqCcI+pu1jgUeF2PFDc8kXlF"
    "TLSbpWW5bVNQqwFUk8AdIPdR5WYLyIbMAMaLW3IAcVmcKWIEo3sAkBnA5KNQAKKKEaLcpVb66Lo3hQOYfFQVQqFpSXnp4siwQypJ"
    "BDvlkl8CYFjXqwAEG1InAlUMZcotuHO+leQIZHtQpgIwZ7I7fPSyPwoBMFyAVV05E2zo9Q4fXUM3eLfi3pypHlUlsmo5J9n7yQvq"
    "O3wUC0syyUmfyUehADof5bVQFKmOmhQAGBPzzpbZR5UhJNjQhyJGso/2a0DXLwjuo7QeZbeIdmvQjQO9j4IBlOVcsZLBmWrnSFb2"
    "81tEc0A1bVzXKwH65vOB22WxmJI19aji/HtHrC8coBhoQ7Ijvky/fX32UclBmcWdFYOPqq8eE+MR0/X+rg4AfuEA2V+AVY+AeVl8"
    "uzekTNXg83r5pSGDj6oAJOt6pEm2Upu1BZgjhwcJ4ACysi0qb9dIKorI7t6TYgAMB2XqEOoCbqoso3F+6y+TVkTEBmDdc7o/agEg"
    "v2rQDlAQKK5wZRYXt7Y74vQggQ2A9K4BrSIUh8W6elTs/x3CTg8SoBicCGTTWH9gD/dR1e1ds4/aAMCve9jZkOb+tPkCrAZAcuHA"
    "bghAANt1b6e5wW6sR5UA0vN6bDcEBh9lt8LnuxYipqvCOh+1A5CctkpkG+vR/D77btfiT0CYbzrr1vWaEJI9SGC+NLSMMomPbq+U"
    "8ztniD8pCnvMRZsINACy83pzEFHruexTlPVo/vjD7qwcWz2ho71woAMYO1w8YxXqOWNHpY+2nJRD1vXqclp1/VI7Btx4suLIe3l1"
    "eQ7f8VQU1vmoPYBuDIoVAl05RHylXNPjOLqDMjWA7v5opLi9XoRMFmT39bmFj+oAlPfwMRGrt5vnB+p+EE1z4cAJgCrM2lFZw7Gf"
    "fbyShz2zqPNR3eO46Vj3n5KAnQfPiise2fSBj1ye61FbgJiYnnKbEpJl5JEPjOYzqaO2IQ1AGqPpz7Xz6XkQhr9+F9WcLBFoAOye"
    "KKtZ+ThXvlqtBqtiV8J6BJ4NkD/tWvT5ggmnyr9ZcwQAPM9Up3IUdKjy7xVvVeWOAN0nxbmgfKFoq7ghAJU+HxiVn5tlHqjfhrjy"
    "MQr+C8PfoD4vO38h/6yeJwEU1pL3+aLo82+Qci6cSZd/XJIeIKgpEXFrCQtrgSq/Fp5a3RvVL4vdTFFjLXLp8VfxkSip+0eTuAFI"
    "EhG0z1dFn8M+XQsSQn0Xa9EkIm202AmHAWxIvYlIbi2O0iEAXQKIFgc7d4sW+4/noTaETX3+e2GlvDbhIADJORM3RadEtLKwlhoB"
    "qonor2Miql04MIT6+QcLja+txTYRPUg5ECDodMJ+N7VPROYc+gSAsn01IVqcAPIPZku/LLo8fmoDfkxbvHpUInpSCMVfPzJDHwDQ"
    "GOH2AA9KRM8CaJxwB4Bmtn8f3//DLfV/BP69g+OnAbx/jYv3L9Lx/lVG3r9Myv/Xefn+QjXvX2nn/UsFvX+to/cv1vT/1ab+v1zW"
    "+9f7+v+CZe9fce3/S8b9f807nwYeEaTFBCgB/CK40n8BoJbqDQHTP0yqANRUPSFg+g+JCMCiyAcvSidl/NwCsN8+Nn0QUur/1/pv"
    "AJL9PnmbNBkhTSdvTKUKIB+EuKkIVFel+0WA5PQneT92m4iQpt3je/Knol8AYH6aHD5HzTrMYGpGn4ekdE8NQMJz9PtxEDcDgqsY"
    "0M5nFU8CAWBrNPY33z+Pk9FPl0hpPJocP98vooT2PxfRDm0RAwuhAAAAAElFTkSuQmCC"
    ),
    "apple-touch-icon.png": (
    "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"
    "AAAAAElFTkSuQmCC"
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
        '<meta name="theme-color" content="#0a0d13">',
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


def pita(link_telegram=None, aktif="", hero=""):
    """Pita biru di atas: logo, menu, tombol Telegram, dan (khusus beranda) judul besar."""
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
  </div>
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
