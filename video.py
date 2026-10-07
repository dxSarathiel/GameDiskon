"""
Video vertikal harian (1080x1920) untuk TikTok dan YouTube Shorts.

Isi: pembuka, 3-5 diskon Steam terbaik, game gratis Epic (kalau ada), dan penutup ke situs.
Tampilannya sama dengan situs (tema "Shonen Sale"): tinta gelap, satu aksen kuning, label miring 割.
Selain video, dibuat juga naskah untuk suara TTS, judul, dan tagar yang siap disalin.

Butuh: Pillow dan imageio-ffmpeg (ffmpeg ikut terpasang lewat pip, tidak perlu apt).
Video animasi (utama) butuh Node.js 22+ dan ffmpeg/ffprobe di PATH; lihat video_hf/README.md.
Kalau tidak tersedia, otomatis memakai video slide Pillow.
"""

import math
import os
import random
import re
import subprocess
import time
import wave
from datetime import datetime, timedelta, timezone
from io import BytesIO

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WIB = timezone(timedelta(hours=7))
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

W, H = 1080, 1920
FPS = 30
DURASI = {"pembuka": 2.6, "game": 3.2, "gratis": 3.2, "penutup": 3.4}
TRANSISI = 0.35
MAKS_GAME = 5

# Warna tema "Shonen Sale" (sama dengan token di gaya.py): tinta gelap + satu aksen kuning
LATAR = (10, 11, 18)          # --tinta
PANEL = (18, 20, 30)          # --tinta-2
PANEL_2 = (27, 30, 43)        # --tinta-3
GARIS = (38, 42, 58)          # --garis
TINTA = (241, 242, 246)       # --putih
REDUP = (167, 172, 190)       # --redup
KUNING = (246, 225, 70)       # --kuning: satu-satunya aksen (label, potongan, tombol)
HIJAU = (91, 227, 154)        # --hijau: harga termurah (status, bukan hiasan)

LEBAR_JUDUL = 74              # lebar huruf judul (--sempit di situs)
SEMPIT = 74                   # lebar huruf untuk angka
MIRING = 10                   # kemiringan judul dalam derajat (skewX di situs)

FOLDER_FONT = "fonts"
URL_FONT = "https://github.com/google/fonts/raw/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf"
FILE_FONT = os.path.join(FOLDER_FONT, "Archivo-variabel.ttf")
# Huruf Jepang Dela Gothic One (subset situs: 割引 無料 本日特価 近日 セール ゲーム); ikut di repo
_REPO = os.path.dirname(os.path.abspath(__file__))
FILE_FONT_JP = [os.path.join(_REPO, "aset", "dela-gothic-jp.woff2"), os.path.join(_REPO, "dela-gothic-jp.woff2")]


# ---------- Huruf ----------
def _siapkan_font():
    if not os.path.exists(FILE_FONT):
        os.makedirs(FOLDER_FONT, exist_ok=True)
        r = requests.get(URL_FONT, timeout=60)
        r.raise_for_status()
        with open(FILE_FONT, "wb") as f:
            f.write(r.content)


def huruf(ukuran, tebal=900, lebar=68):
    """Archivo: tebal 100-900, lebar 62-125 (68 = sempit ala poster promo)."""
    f = ImageFont.truetype(FILE_FONT, ukuran)
    try:
        f.set_variation_by_axes([tebal, lebar])
    except Exception:
        pass
    return f


def huruf_jp(ukuran):
    """Dela Gothic One untuk tanda Jepang; None kalau file tidak ada (hiasan Jepang dilewati)."""
    for path in FILE_FONT_JP:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, ukuran)
            except OSError:          # Pillow tanpa dukungan woff2
                return None
    return None


# ---------- Bentuk khas tema ----------
def _jajar(x, y, w, h, miring):
    """Jajar genjang (--jajar di situs): sisi kiri & kanan miring."""
    return [(x + miring, y), (x + w, y), (x + w - miring, y + h), (x, y + h)]


def _sudut_potong(x, y, w, h, potong):
    """Panel dengan pojok kanan atas dipotong (--sudut-potong di situs)."""
    return [(x, y), (x + w - potong, y), (x + w, y + potong), (x + w, y + h), (x, y + h)]


def _miringkan(img, derajat=MIRING):
    """skewX: bagian atas bergeser ke kanan, poros di tengah tinggi. Mengembalikan (gambar, geser_kiri)."""
    k = math.tan(math.radians(derajat))
    w, h = img.size
    tambah = int(k * h) + 2
    hasil = Image.new("RGBA", (w + tambah, h), (0, 0, 0, 0))
    hasil.paste(img, (tambah // 2, 0))
    return hasil.transform(hasil.size, Image.AFFINE, (1, k, -k * h / 2, 0, 1, 0), Image.BICUBIC), tambah // 2


def _sfx(kanvas, teks, ukuran, kanan, atas, sudut=8, alfa=70):
    """Efek suara manga: huruf Jepang besar, hanya garis luar kuning transparan (seperti セール di situs)."""
    f = huruf_jp(ukuran)
    if not f:
        return
    tebal = max(3, ukuran // 70)
    kiri_, atas_, kanan_, bawah_ = f.getbbox(teks, stroke_width=tebal)
    ukuran_lapis = (kanan_ - kiri_ + 8, bawah_ - atas_ + 8)
    luar, dalam = Image.new("L", ukuran_lapis, 0), Image.new("L", ukuran_lapis, 0)
    xy = (4 - kiri_, 4 - atas_)
    ImageDraw.Draw(luar).text(xy, teks, font=f, fill=255, stroke_width=tebal, stroke_fill=255)
    ImageDraw.Draw(dalam).text(xy, teks, font=f, fill=255)
    lapis = Image.new("RGBA", ukuran_lapis, KUNING + (0,))
    lapis.putalpha(ImageChops.subtract(luar, dalam).point(lambda v: v * alfa // 255))
    lapis = lapis.rotate(sudut, expand=True, resample=Image.BICUBIC)
    x = int(kanan - lapis.width)
    if x < 0:
        lapis, x = lapis.crop((-x, 0, lapis.width, lapis.height)), 0
    kanvas.alpha_composite(lapis, (x, int(atas)))


def _ledakan(teks_jp, teks, ukuran):
    """Gelembung ledakan manga kuning (seperti stempel 無料 di situs), sedikit diputar."""
    img = Image.new("RGBA", (ukuran, ukuran), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, titik = ukuran / 2, []
    for i in range(32):
        a = math.radians(i * 360 / 32)
        r = c * (0.98 if i % 2 == 0 else 0.76) * (0.94 if i % 4 == 2 else 1)
        titik.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(titik, fill=KUNING)
    jp = huruf_jp(int(ukuran * 0.27))
    f = huruf(int(ukuran * (0.13 if jp else 0.2)), 900, 100)
    if jp:
        d.text((c, c - ukuran * 0.06), teks_jp, font=jp, fill=LATAR, anchor="mm")
        d.text((c, c + ukuran * 0.17), teks, font=f, fill=LATAR, anchor="mm")
    else:
        d.text((c, c), teks, font=f, fill=LATAR, anchor="mm")
    return img.rotate(10, resample=Image.BICUBIC)


# ---------- Bantuan gambar ----------
def _unduh(url, session=None):
    try:
        r = (session or requests).get(url, timeout=20)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def _sampul_steam(appid, session=None):
    """Sampul resolusi lebih besar dulu, lalu yang standar."""
    for nama in ("capsule_616x353.jpg", "header.jpg"):
        img = _unduh(f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/{nama}", session)
        if img:
            return img
    return None


def _tempel_isi(kanvas, img, kotak, sudut=10):
    """Tempel gambar memenuhi kotak (dipotong seperlunya) dengan sudut sedikit membulat."""
    x, y, w, h = kotak
    rasio = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * rasio) + 1, int(img.height * rasio) + 1), Image.LANCZOS)
    kiri, atas = (img.width - w) // 2, (img.height - h) // 2
    img = img.crop((kiri, atas, kiri + w, atas + h))
    topeng = Image.new("L", (w, h), 0)
    ImageDraw.Draw(topeng).rounded_rectangle((0, 0, w, h), radius=sudut, fill=255)
    kanvas.paste(img, (x, y), topeng)


def _bungkus(d, teks, font, lebar_maks, maks_baris=3):
    kata, baris, kini = teks.split(), [], ""
    for k in kata:
        coba = (kini + " " + k).strip()
        if d.textlength(coba, font=font) <= lebar_maks:
            kini = coba
        else:
            if kini:
                baris.append(kini)
            kini = k
    if kini:
        baris.append(kini)
    if len(baris) > maks_baris:
        baris = baris[:maks_baris]
        while d.textlength(baris[-1] + "…", font=font) > lebar_maks and " " in baris[-1]:
            baris[-1] = baris[-1].rsplit(" ", 1)[0]
        baris[-1] += "…"
    return baris


def _rupiah(sen):
    return "Rp " + f"{sen // 100:,}".replace(",", ".")


def _label(teks, font, isi, latar, pad_x=26, pad_y=14):
    """Label jajar genjang (seperti .potong dan tombol di situs). Mengembalikan (gambar, ruang=0)."""
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    kiri, atas, kanan, bawah = uk.textbbox((0, 0), teks, font=font)
    h = int(bawah - atas + pad_y * 2)
    miring = int(h * 0.22)
    w = int(kanan - kiri + pad_x * 2 + miring)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(_jajar(0, 0, w, h, miring), fill=latar)
    d.text((pad_x + miring / 2 - kiri, pad_y - atas), teks, font=font, fill=isi)
    return img, 0


def _tempel(kanvas, img, x, y, ruang=0):
    kanvas.alpha_composite(img, (int(x - ruang), int(y - ruang)))


_LATAR_JADI = {}


def _latar(w=W, h=H, kuat=1.0):
    """Latar tinta gelap dengan garis kecepatan manga dan screentone titik di kanan atas (seperti hero situs)."""
    kunci = (w, h, kuat)
    if kunci not in _LATAR_JADI:
        im = Image.new("RGBA", (w, h), LATAR + (255,))
        garis = Image.new("L", (w, h), 0)
        dg = ImageDraw.Draw(garis)
        cx, cy = w * 0.8, h * 0.28
        for i in range(60):
            a = math.radians(i * 6 + (2 if i % 2 else 0))
            lebar = 0.012 if i % 3 == 0 else 0.007
            r1, r2 = w * 0.32, h * 1.3
            dg.polygon([(cx + r1 * math.cos(a - lebar), cy + r1 * math.sin(a - lebar)),
                        (cx + r2 * math.cos(a - lebar), cy + r2 * math.sin(a - lebar)),
                        (cx + r2 * math.cos(a + lebar), cy + r2 * math.sin(a + lebar)),
                        (cx + r1 * math.cos(a + lebar), cy + r1 * math.sin(a + lebar))],
                       fill=int(255 * min(1.0, 0.6 * kuat)))
        im.paste(GARIS + (255,), (0, 0, w, h), garis)
        tone = Image.new("L", (w, h), 0)
        dt = ImageDraw.Draw(tone)
        for y in range(0, h, 14):
            for x in range(0, w, 14):
                dt.ellipse((x - 2, y - 2, x + 2, y + 2), fill=255)
        arah = Image.new("L", (w, h), 0)
        ImageDraw.Draw(arah).ellipse((int(w * 0.3), int(-h * 0.25), int(w * 1.4), int(h * 0.35)), fill=int(50 * kuat))
        tone = ImageChops.multiply(tone, arah.filter(ImageFilter.GaussianBlur(w // 8)))
        im.paste(TINTA + (255,), (0, 0, w, h), tone)
        _LATAR_JADI[kunci] = im
    return _LATAR_JADI[kunci].copy()


def _logo(skala=1.0):
    """Label kuning miring 割 + GAMEDISKON sempit (DISKON kuning), seperti .logo di situs."""
    f = huruf(int(76 * skala), 900, LEBAR_JUDUL)
    tinggi, lebar_label = int(80 * skala), int(92 * skala)
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lg = uk.textlength("GAME", font=f); ld = uk.textlength("DISKON", font=f)
    jarak = int(20 * skala)
    img = Image.new("RGBA", (lebar_label + jarak + int(lg + ld) + 10, tinggi), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(_jajar(0, 0, lebar_label, tinggi, int(tinggi * 0.16)), fill=KUNING)
    jp = huruf_jp(int(48 * skala))
    if jp:
        d.text((lebar_label / 2, tinggi / 2 + 2 * skala), "割", font=jp, fill=LATAR, anchor="mm")
    x = lebar_label + jarak
    d.text((x, tinggi / 2), "GAME", font=f, fill=TINTA, anchor="lm")
    d.text((x + lg, tinggi / 2), "DISKON", font=f, fill=KUNING, anchor="lm")
    return img


def _label_harga(potong, harga, coret, skala=1.0):
    """Label potongan kuning miring + harga besar + harga coret (seperti .label-rak di situs)."""
    f_potong = huruf(int(92 * skala), 900, SEMPIT)
    f_harga = huruf(int(128 * skala), 900, SEMPIT)
    f_coret = huruf(int(44 * skala), 500, 100)
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    chip, ruang = _label(potong, f_potong, LATAR, KUNING, int(26 * skala), int(16 * skala)) if potong else (None, 0)
    lh = uk.textlength(harga, font=f_harga)
    tinggi = max(chip.height - 2 * ruang if chip else 0, int(150 * skala))
    lebar = (chip.width - 2 * ruang + int(30 * skala) if chip else 0) + int(max(lh, uk.textlength(coret or "", font=f_coret))) + 20
    img = Image.new("RGBA", (lebar + 2 * ruang, tinggi + int(70 * skala) + 2 * ruang), (0, 0, 0, 0))
    x = ruang
    if chip:
        img.alpha_composite(chip, (0, int(ruang + (tinggi - (chip.height - 2 * ruang)) / 2 - ruang)))
        x += chip.width - 2 * ruang + int(30 * skala)
    d = ImageDraw.Draw(img)
    d.text((x, ruang + tinggi / 2), harga, font=f_harga, fill=TINTA, anchor="lm")
    if coret:
        yc = ruang + tinggi + int(8 * skala)
        d.text((x, yc), coret, font=f_coret, fill=REDUP)
        lc = d.textlength(coret, font=f_coret)
        d.line((x, yc + int(27 * skala), x + lc, yc + int(27 * skala)), fill=REDUP, width=max(2, int(3 * skala)))
    return img, ruang


def _kartu(kanvas, kotak, potong=44, garis=GARIS, isi=PANEL):
    """Panel bersudut potong dengan garis kuning di sisi kiri (seperti kartu unggulan di situs)."""
    x, y, w, h = kotak
    d = ImageDraw.Draw(kanvas)
    d.polygon(_sudut_potong(x, y, w, h, potong), fill=isi, outline=garis, width=3)
    d.rectangle((x, y, x + 9, y + h), fill=KUNING)


def _tempel_gambar_kartu(kanvas, img, kotak, potong=42):
    """Gambar di bagian atas kartu, pojok kanan atas ikut dipotong."""
    x, y, w, h = kotak
    rasio = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * rasio) + 1, int(img.height * rasio) + 1), Image.LANCZOS).convert("RGBA")
    kiri, atas = (img.width - w) // 2, (img.height - h) // 2
    img = img.crop((kiri, atas, kiri + w, atas + h))
    topeng = Image.new("L", (w, h), 0)
    ImageDraw.Draw(topeng).polygon(_sudut_potong(0, 0, w, h, potong), fill=255)
    kanvas.paste(img, (x, y), topeng)


def _judul_besar(kanvas, baris, x, y, ukuran, jarak=None):
    """Judul uppercase sempit yang miring; baris terakhir di pita kuning (seperti judul beranda situs)."""
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # Kecilkan otomatis sampai semua baris (termasuk pita) muat sebelum area tombol TikTok di kanan
    while ukuran > 60:
        f = huruf(ukuran, 900, LEBAR_JUDUL)
        lebar = [uk.textlength(b.upper(), font=f) for b in baris]
        lebar[-1] += ukuran * 0.75
        if max(lebar) + ukuran * 0.25 <= KANAN_AMAN - x:
            break
        ukuran -= 4
    jarak = jarak or int(ukuran * 1.02)
    for i, b in enumerate(baris):
        teks = b.upper()
        kiri, atas, kanan, bawah = f.getbbox(teks)
        if i < len(baris) - 1:
            lapis = Image.new("RGBA", (int(kanan) + 8, int(bawah + ukuran * 0.1)), (0, 0, 0, 0))
            ImageDraw.Draw(lapis).text((0, 0), teks, font=f, fill=TINTA)
            lapis, geser = _miringkan(lapis)
            kanvas.alpha_composite(lapis, (int(x - geser), int(y)))
            y += jarak
        else:
            px, py = int(ukuran * 0.26), int(ukuran * 0.13)
            h = int(bawah - atas + py * 2)
            m = int(h * 0.22)
            w = int(kanan - kiri + px * 2 + m)
            pita = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dp = ImageDraw.Draw(pita)
            dp.polygon(_jajar(0, 0, w, h, m), fill=KUNING)
            dp.text((px + m / 2 - kiri, py - atas), teks, font=f, fill=LATAR)
            pita, geser = _miringkan(pita)
            kanvas.alpha_composite(pita, (int(x - geser - px // 4), int(y + atas - py)))
            y += jarak + py
    return y


def _tanggal(dt):
    return f"{HARI[dt.weekday()]}, {dt.day} {BULAN[dt.month - 1]} {dt.year}"


def _kicker(d, teks, x, y, warna=KUNING, ukuran=40):
    """Label kecil uppercase berjarak huruf lebar, diawali balok miring (seperti .kicker di situs)."""
    f = huruf(ukuran, 800, 100)
    _, atas, _, bawah = f.getbbox("A")
    bw, bh = int(ukuran * 1.1), int(ukuran * 0.38)
    by = y + (atas + bawah) / 2 - bh / 2
    d.polygon(_jajar(x, by, bw, bh, int(bh * 0.6)), fill=warna)
    cx = x + bw + int(ukuran * 0.4)
    for ch in teks.upper():
        d.text((cx, y), ch, font=f, fill=warna)
        cx += d.textlength(ch, font=f) + ukuran * 0.12
    return cx


# ---------- Slide ----------
TEPI = 72                  # jarak dari tepi kiri
KANAN_AMAN = W - 150       # hindari tombol TikTok di sisi kanan
BAWAH_AMAN = H - 380       # hindari keterangan TikTok di bawah


def slide_pembuka(jumlah, sekarang, ada_gratis):
    im = _latar(kuat=1.2)
    _sfx(im, "セール", 320, W + 30, 380)
    im.alpha_composite(_logo(1.0), (TEPI, 230))
    d = ImageDraw.Draw(im)
    _kicker(d, f"Diskon Steam  {sekarang.day} {BULAN[sekarang.month - 1]}", TEPI, 470)
    y = _judul_besar(im, [f"{jumlah} diskon", "Steam", "hari ini"], TEPI, 550, 170)
    d = ImageDraw.Draw(im)
    f = huruf(54, 500, 100)
    d.text((TEPI, y + 50), "Harga Rupiah asli, dicek langsung", font=f, fill=REDUP)
    d.text((TEPI, y + 120), "ke Steam Indonesia.", font=f, fill=REDUP)
    if ada_gratis:
        p, r = _label("+ GAME GRATIS", huruf(46, 900, 100), LATAR, KUNING, 34, 18)
        _tempel(im, p, TEPI, y + 250, r)
        d = ImageDraw.Draw(im)
    d.text((TEPI, BAWAH_AMAN - 40), _tanggal(sekarang), font=huruf(46, 700, 100), fill=REDUP)
    return im.convert("RGB")


def _progres(d, nomor, total, y):
    """Bar kecil 'diskon ke-n dari total' di bagian atas."""
    lebar = (KANAN_AMAN - TEPI - (total - 1) * 14) / total
    for i in range(total):
        x = TEPI + i * (lebar + 14)
        d.polygon(_jajar(x, y, lebar, 12, 6), fill=KUNING if i < nomor else GARIS)


def slide_game(g, nomor, total, session=None):
    im = _latar(kuat=0.8)
    d = ImageDraw.Draw(im)
    _progres(d, nomor, total, 190)
    _kicker(d, f"Diskon {nomor} dari {total}", TEPI, 235)
    appid = re.search(r"/app/(\d+)", g["url"])
    sampul = _sampul_steam(appid.group(1), session) if appid else None
    kartu_x, kartu_w = TEPI - 12, KANAN_AMAN - TEPI + 60
    gambar_h = int(kartu_w * 353 / 616)
    y0 = 320
    # tinggi isi kartu dihitung dulu supaya kartu pas
    f_nama = huruf(84, 800, 100)
    baris_nama = _bungkus(d, g["judul"], f_nama, kartu_w - 100, 3)
    isi_h = 60 + len(baris_nama) * 92 + 80 + (70 if g.get("terendah_sejak") else 0) + 330
    _kartu(im, (kartu_x, y0, kartu_w, gambar_h + isi_h))
    if sampul:
        _tempel_gambar_kartu(im, sampul, (kartu_x + 3, y0 + 3, kartu_w - 6, gambar_h))
    d = ImageDraw.Draw(im)
    y = y0 + gambar_h + 55
    for b in baris_nama:
        d.text((kartu_x + 50, y), b, font=f_nama, fill=TINTA)
        y += 92
    d.text((kartu_x + 50, y + 14), f"{g['rating']} ulasan positif di Steam", font=huruf(46, 500, 100), fill=REDUP)
    y += 90
    if g.get("terendah_sejak"):
        _kicker(d, "Termurah sejak dipantau", kartu_x + 50, y, HIJAU, 36)
        y += 70
    label, r = _label_harga(f"-{g['diskon']}%", _rupiah(g["harga_akhir"]), _rupiah(g["harga_awal"]), 1.0)
    _tempel(im, label, kartu_x + 44, y + 30, r)
    return im.convert("RGB")


def slide_gratis(g, session=None):
    im = _latar(kuat=0.8)
    d = ImageDraw.Draw(im)
    _kicker(d, "Gratis di Epic Games Store", TEPI, 235)
    gambar = _unduh(g["gambar"], session) if g.get("gambar") else None
    kartu_x, kartu_w = TEPI - 12, KANAN_AMAN - TEPI + 60
    gambar_h = int(kartu_w * 9 / 16)
    y0 = 320
    f_nama = huruf(84, 800, 100)
    baris_nama = _bungkus(d, g["judul"], f_nama, kartu_w - 100, 3)
    isi_h = 60 + len(baris_nama) * 92 + 330
    _kartu(im, (kartu_x, y0, kartu_w, gambar_h + isi_h))
    if gambar:
        _tempel_gambar_kartu(im, gambar, (kartu_x + 3, y0 + 3, kartu_w - 6, gambar_h))
    im.alpha_composite(_ledakan("無料", "GRATIS", 250), (kartu_x - 20, y0 - 40))
    d = ImageDraw.Draw(im)
    y = y0 + gambar_h + 55
    for b in baris_nama:
        d.text((kartu_x + 50, y), b, font=f_nama, fill=TINTA)
        y += 92
    d.text((kartu_x + 50, y + 30), "Klaim sebelum", font=huruf(46, 500, 100), fill=REDUP)
    d.text((kartu_x + 50, y + 95), g["berakhir"], font=huruf(96, 900, SEMPIT), fill=KUNING)
    d.text((kartu_x + 50, y + 225), "Sekali klaim, jadi milikmu selamanya.", font=huruf(42, 500, 100), fill=TINTA)
    return im.convert("RGB")


def slide_penutup(username_bot, link_channel):
    im = _latar(kuat=1.2)
    _sfx(im, "割引", 300, W + 30, 1520)
    im.alpha_composite(_logo(1.0), (TEPI, 300))
    y = _judul_besar(im, ["Daftar", "lengkap +", "riwayat", "harga"], TEPI, 500, 130)
    tombol, r = _label("gamediskon.my.id", huruf(66, 900, 100), LATAR, KUNING, 44, 26)
    _tempel(im, tombol, TEPI, y + 50, r)
    d = ImageDraw.Draw(im)
    y += 260
    f_ket, f_isi = huruf(46, 500, 100), huruf(76, 900, SEMPIT)
    if username_bot:
        d.text((TEPI, y), "Alarm harga di Telegram", font=f_ket, fill=REDUP)
        d.text((TEPI, y + 62), f"@{username_bot}", font=f_isi, fill=KUNING)
        y += 200
    if link_channel:
        d.text((TEPI, y), "Info diskon harian", font=f_ket, fill=REDUP)
        d.text((TEPI, y + 62), link_channel, font=f_isi, fill=KUNING)
    return im.convert("RGB")


# ---------- Rakit video ----------
def _ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def rakit_mp4(slide, path_mp4, folder_kerja):
    """slide: daftar (PIL.Image, durasi). Transisi silang antar slide, dengan trek audio hening."""
    os.makedirs(folder_kerja, exist_ok=True)
    masukan, durasi = [], []
    for i, (im, dur) in enumerate(slide):
        p = os.path.join(folder_kerja, f"slide{i:02d}.png")
        im.save(p)
        masukan += ["-loop", "1", "-t", f"{dur:.2f}", "-framerate", str(FPS), "-i", p]
        durasi.append(dur)
    n = len(slide)
    filt, akhir, offset = [], "[0:v]", 0.0
    for i in range(n):
        filt.append(f"[{i}:v]scale={W}:{H},setsar=1,format=yuv420p[v{i}]")
    akhir = "[v0]"
    for i in range(1, n):
        offset += durasi[i - 1] - TRANSISI
        keluar = f"[x{i}]"
        filt.append(f"{akhir}[v{i}]xfade=transition=fade:duration={TRANSISI}:offset={offset:.2f}{keluar}")
        akhir = keluar
    total = sum(durasi) - TRANSISI * (n - 1)
    perintah = [_ffmpeg(), "-y", "-loglevel", "error", *masukan,
                "-f", "lavfi", "-t", f"{total:.2f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-filter_complex", ";".join(filt), "-map", akhir, "-map", f"{n}:a",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-r", str(FPS), "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", path_mp4]
    subprocess.run(perintah, check=True)
    return total


# ---------- Rakit video dengan HyperFrames (animasi) ----------
# Template animasi ada di folder video_hf/ (lihat video_hf/rakit.py). Kalau langkah mana pun
# gagal, buat_video() kembali ke rakit_mp4() di atas, jadi posting harian tidak terlewat.
# Set VIDEO_HYPERFRAMES=0 untuk mematikan jalur ini tanpa mengubah kode.
FOLDER_HF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_hf")
BATAS_RENDER = 900            # detik; render di runner GitHub biasanya beberapa menit


def _muat_rakit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("rakit_hf", os.path.join(FOLDER_HF, "rakit.py"))
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _hf_siap():
    """Pastikan alat render ada. Kembalikan path npm, atau lempar RuntimeError."""
    import shutil
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm (Node.js) tidak ditemukan")
    for alat in ("ffmpeg", "ffprobe"):
        if not shutil.which(alat):
            raise RuntimeError(f"{alat} tidak ada di PATH")
    return npm


def _kabari_pemilik(teks):
    """Kirim pesan singkat ke pemilik bot di Telegram saat jalur cadangan video terpakai.
    Jalur cadangan tidak menggagalkan workflow, jadi tanpa pesan ini pemilik tidak tahu.
    Tidak pernah melempar exception; tanpa TELEGRAM_TOKEN/TELEGRAM_OWNER_ID (mis. uji lokal) diam saja."""
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    pemilik = os.environ.get("TELEGRAM_OWNER_ID", "").strip()
    if not token or not pemilik:
        return
    run = [os.environ.get(k, "") for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")]
    if all(run):
        teks += f"\nLog: {run[0]}/{run[1]}/actions/runs/{run[2]}"
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20,
                      data={"chat_id": pemilik, "text": teks, "disable_web_page_preview": "true"})
    except Exception as e:
        print(f"Gagal mengabari pemilik lewat Telegram: {e}")


def _ringkas(e, maks=300):
    teks = str(e).strip() or type(e).__name__
    return teks if len(teks) <= maks else teks[:maks] + "…"


# ---------- Suara TTS otomatis: ElevenLabs, cadangan Microsoft Edge TTS ----------
# Urutan: ElevenLabs (kalau secret ELEVENLABS_API_KEY ada) -> Microsoft Edge TTS (gratis, tanpa API key)
# -> tanpa suara. Suara ElevenLabs bawaan Iwan, ganti lewat ELEVENLABS_VOICE_ID (biaya ~1 kredit per huruf).
# Suara Edge bawaan id-ID-ArdiNeural, ganti lewat EDGE_TTS_VOICE (mis. id-ID-GadisNeural).
SUARA_BAWAAN = "1kNciG1jHVSuFBPoxdRZ"       # "Iwan - Informative, Authentic and Clear"
SUARA_EDGE = "id-ID-ArdiNeural"
MODEL_TTS = "eleven_multilingual_v2"
RAPIKAN_SUARA = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse,"
                 "loudnorm=I={keras}:TP=-1.5:LRA=11")
# Target keras per klip supaya video jadi sekitar -14 LUFS (standar TikTok). Suara Edge lebih padat,
# jadi targetnya lebih rendah.
KERAS_ELEVENLABS, KERAS_EDGE = -15, -17.5


def _teks_tts(teks):
    """'40,000' dibaca '40 koma 000' oleh TTS bahasa Indonesia; jadikan '40.000' (empat puluh ribu)."""
    return re.sub(r"(?<=\d),(?=\d{3}\b)", ".", teks)


def _tts_elevenlabs(teks, api_key, voice_id, session=None):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
    for coba in range(3):
        r = (session or requests).post(url, timeout=90,
                                       headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
                                       json={"text": teks, "model_id": MODEL_TTS})
        if r.status_code == 429 and coba < 2:      # batas proses bersamaan: tunggu, coba lagi
            time.sleep(4 * (coba + 1))
            continue
        if r.status_code >= 400:
            # Sertakan penjelasan ElevenLabs (mis. izin API key, kuota, suara pustaka di paket gratis)
            try:
                detail = r.json().get("detail", {})
                alasan = detail.get("message") or detail.get("status") if isinstance(detail, dict) else detail
            except ValueError:
                alasan = r.text[:200]
            raise RuntimeError(f"ElevenLabs HTTP {r.status_code}: {alasan or r.reason}")
        return r.content


def _tts_edge(teks, voice):
    """Microsoft Edge TTS (paket edge-tts): gratis, tanpa API key. Kembalikan audio MP3."""
    import asyncio
    import edge_tts

    async def jalan():
        data = bytearray()
        async for potong in edge_tts.Communicate(teks, voice).stream():
            if potong["type"] == "audio":
                data.extend(potong["data"])
        return bytes(data)

    hasil = asyncio.run(jalan())
    if not hasil:
        raise RuntimeError(f"Edge TTS ({voice}) tidak mengembalikan audio")
    return hasil


def buat_suara(segmen, ada_gratis, session=None):
    """Satu klip per adegan, dibuat berurutan. Hening di awal/akhir dipotong dan keras disamakan.
    Coba ElevenLabs dulu (bila ada API key), lalu Microsoft Edge TTS sebagai cadangan.
    Kembalikan {"pembuka": {file, durasi}, "game": [...], "gratis": ..., "penutup": ...}.
    Melempar exception kalau semua penyedia suara gagal."""
    import shutil
    folder = os.path.join(FOLDER_HF, "assets", "suara")
    daftar = ([("pembuka", segmen["pembuka"])]
              + [(f"game-{i}", t) for i, t in enumerate(segmen["game"], 1)]
              + ([("gratis", segmen["gratis"])] if ada_gratis and segmen["gratis"] else [])
              + [("penutup", segmen["penutup"])])

    def rakit(buat_mp3, keras):
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)
        klip = {}
        for nama, teks in daftar:
            mp3, wav = os.path.join(folder, nama + ".mp3"), os.path.join(folder, nama + ".wav")
            with open(mp3, "wb") as f:
                f.write(buat_mp3(_teks_tts(teks)))
            subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", mp3, "-af", RAPIKAN_SUARA.format(keras=keras),
                            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", wav], check=True)
            os.remove(mp3)
            with wave.open(wav) as w:
                durasi = w.getnframes() / w.getframerate()
            klip[nama] = {"file": f"assets/suara/{nama}.wav", "durasi": round(durasi, 3)}
        return {"pembuka": klip["pembuka"],
                "game": [klip[f"game-{i}"] for i in range(1, len(segmen["game"]) + 1)],
                "gratis": klip.get("gratis"), "penutup": klip["penutup"]}

    suara_edge = os.environ.get("EDGE_TTS_VOICE", "").strip() or SUARA_EDGE
    api_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if api_key:
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or SUARA_BAWAAN
        try:
            suara = rakit(lambda t: _tts_elevenlabs(t, api_key, voice_id, session), KERAS_ELEVENLABS)
            print(f"Suara TTS siap (ElevenLabs {voice_id}, sekitar {sum(len(t) for _, t in daftar)} kredit).")
            return suara
        except Exception as e:
            print(f"Suara ElevenLabs gagal, pakai suara cadangan Microsoft Edge: {e}")
            _kabari_pemilik(f"⚠️ Suara ElevenLabs gagal, video memakai suara cadangan Microsoft Edge "
                            f"({suara_edge}): {_ringkas(e)}")
    suara = rakit(lambda t: _tts_edge(t, suara_edge), KERAS_EDGE)
    print(f"Suara TTS siap (Microsoft Edge {suara_edge}).")
    return suara


def rakit_mp4_hyperframes(steam, epic, segmen, sekarang, username_bot, link_channel, path_mp4, session=None, suara=None):
    """Isi template HyperFrames dengan data hari ini (dan suara TTS bila ada), lalu render.
    Kembalikan (durasi, dengan_suara). Melempar exception kalau ada yang gagal."""
    import shutil
    npm = _hf_siap()

    # Sampul diunduh dulu: saat render tidak boleh ada unduhan dari jaringan
    folder_sampul = os.path.join(FOLDER_HF, "assets", "sampul")
    shutil.rmtree(folder_sampul, ignore_errors=True)
    os.makedirs(folder_sampul)

    def simpan(img, nama):
        if not img:
            return ""
        img.save(os.path.join(folder_sampul, nama), "JPEG", quality=90)
        return f"assets/sampul/{nama}"

    data_steam = []
    for i, g in enumerate(steam, 1):
        appid = re.search(r"/app/(\d+)", g["url"])
        data_steam.append({
            "judul": g["judul"], "rating": g["rating"], "diskon": g["diskon"],
            "harga_awal": g["harga_awal"], "harga_akhir": g["harga_akhir"],
            "terendah_sejak": g.get("terendah_sejak"),
            "sampul": simpan(_sampul_steam(appid.group(1), session) if appid else None, f"steam-{i}.jpg"),
        })
    data_epic = []
    if epic:
        g = epic[0]
        data_epic.append({"judul": g["judul"], "berakhir": g["berakhir"],
                          "gambar": simpan(_unduh(g["gambar"], session) if g.get("gambar") else None, "epic.jpg")})

    data = {"tanggal": sekarang.date().isoformat(), "username_bot": username_bot, "link_channel": link_channel,
            "steam": data_steam, "epic": data_epic,
            "naskah": {"pembuka": segmen["pembuka"], "game": segmen["game"],
                       "gratis": segmen["gratis"], "penutup": segmen["penutup"]},
            "suara": suara}
    hasil = _muat_rakit().rakit(data, FOLDER_HF)

    # Render memakai versi CLI yang dikunci di video_hf/package.json
    sementara = os.path.join(FOLDER_HF, "renders", "harian.mp4")
    os.makedirs(os.path.dirname(sementara), exist_ok=True)
    if os.path.exists(sementara):
        os.remove(sementara)
    subprocess.run([npm, "run", "render", "--", "-f", str(FPS), "-o", sementara, "--quiet"],
                   cwd=FOLDER_HF, check=True, timeout=BATAS_RENDER)

    if hasil["dengan_suara"]:
        # Suara sudah dicampur oleh HyperFrames; cukup pindahkan indeks ke depan untuk unggahan
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", sementara, "-c", "copy",
                        "-movflags", "+faststart", path_mp4], check=True)
    else:
        # Trek audio hening (sama seperti jalur lama), supaya aman diunggah ke TikTok/Shorts
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", sementara,
                        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "64k",
                        "-shortest", "-movflags", "+faststart", path_mp4], check=True)
    return hasil["durasi"], hasil["dengan_suara"]


# ---------- Naskah suara dan teks pendamping ----------
# Naskah ditulis seperti orang ngobrol: kalimat pendek-panjang bergantian, ada reaksi,
# pertanyaan, dan jeda (koma, titik, tanda tanya, tanda seru) supaya TTS membacanya dengan ekspresi.
# Pilihan kalimat diacak dengan "benih" tanggal hari itu: tiap hari beda, tapi hasil hari yang sama tetap sama.

KATA_PER_DETIK = 2.6        # kecepatan bicara TTS yang wajar dalam bahasa Indonesia


def rupiah_lisan(sen):
    """'Rp 13.999' -> '13 ribuan', 'Rp 1.250.000' -> '1,2 jutaan'."""
    rp = sen // 100
    if rp >= 1_000_000:
        return f"{rp / 1_000_000:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " jutaan"
    if rp >= 1000:
        return f"{rp // 1000} ribuan"
    return f"{rp} rupiah"


def hemat_lisan(sen):
    rp = sen // 100
    if rp >= 100_000:
        return f"{rp // 10_000 * 10} ribu lebih"
    return f"{rp // 1000} ribu lebih"


def nama_lisan(judul):
    """Nama game dipendekkan seperti orang menyebutnya: tanpa subjudul dan label edisi."""
    n = re.sub(r"[™®©!]", "", judul)
    n = re.split(r"\s[-–—]\s|:", n)[0]
    n = re.sub(r"\b(Enhanced Edition|Definitive Edition|Director'?s Cut|Complete Edition|GOTY|"
               r"Game of the Year( Edition)?|Remastered|Deluxe Edition)\b.*$", "", n, flags=re.I)
    return n.strip() or judul


def _hari_berakhir(g):
    try:
        t = datetime.fromisoformat(g["berakhir_iso"]).astimezone(WIB)
        return HARI[t.weekday()] + (" malam" if t.hour >= 18 else "")
    except Exception:
        return ""


def _banding(sen):
    """Perbandingan harga dengan jajanan sehari-hari, hanya untuk harga yang sangat murah."""
    rp = sen // 100
    if rp <= 10_000:
        return "Lebih murah dari semangkuk mie ayam."
    if rp <= 17_000:
        return "Masih lebih murah dari segelas kopi susu kekinian."
    if rp <= 25_000:
        return "Kira-kira seharga sekali makan siang."
    return ""


class _Pemilih:
    """Memilih kalimat secara acak tanpa mengulang kalimat yang sudah dipakai dalam satu naskah."""
    def __init__(self, acak):
        self.acak, self.terpakai = acak, set()

    def __call__(self, pilihan):
        segar = [p for p in pilihan if p not in self.terpakai] or list(pilihan)
        p = self.acak.choice(segar)
        self.terpakai.add(p)
        return p


def _segmen_game(g, pilih, urutan, total, sudah_disebut, pakai_reaksi):
    """Kalimat untuk satu slide game: inti harga, ditambah satu reaksi kalau diminta.
    Pola kalimat (bukan kalimat jadinya) yang dicatat, supaya pola yang sama tidak terpakai dua kali."""
    rating = int(str(g["rating"]).rstrip("%") or 0)
    v = {"nama": nama_lisan(g["judul"]), "harga": rupiah_lisan(g["harga_akhir"]),
         "awal": rupiah_lisan(g["harga_awal"]), "d": g["diskon"], "rating": rating,
         "hemat": hemat_lisan(g["harga_awal"] - g["harga_akhir"])}

    if sudah_disebut:
        pola = ["Iya, beneran. Diskonnya {d} persen.", "Nggak salah lihat kok. Potongannya {d} persen."]
    elif urutan == 1:
        pola = ["Mulai dari {nama}. Sekarang cuma {harga}.",
                "Pertama, {nama}... turun {d} persen, jadi {harga}!",
                "Kita buka pakai {nama}, dari {awal} jadi {harga}."]
    elif urutan == total:
        pola = ["Terakhir, {nama}. Sekarang tinggal {harga}.",
                "Dan yang terakhir... {nama}, cuma {harga}."]
    else:
        pola = ["{nama}, sekarang cuma {harga}.",
                "Terus ada {nama}. Turun {d} persen, jadi {harga}.",
                "Kalau {nama}? {harga} aja.",
                "{nama}, dari {awal}... jadi {harga}!",
                "Nah, {nama}. Harganya sekarang {harga}.",
                "Ada juga {nama}, diskon {d} persen."]
    teks = pilih(pola).format(**v)
    if not pakai_reaksi:
        return teks

    reaksi = []
    if g.get("terendah_sejak"):
        reaksi += ["Ini harga paling murah sejak kami pantau.", "Belum pernah semurah ini, lho."]
    if g["diskon"] >= 90:
        reaksi += ["Ini sih hampir dikasih.", "Potongannya nggak main-main.", "Hematnya {hemat}!"]
    elif g["diskon"] >= 75:
        reaksi += ["Lumayan banget, kan?", "Pas buat yang dari dulu penasaran."]
    if rating >= 95:
        reaksi += ["Ulasannya {rating} persen positif. Aman.", "Yang udah main, hampir semuanya suka."]
    banding = _banding(g["harga_akhir"])
    if banding:
        reaksi.append(banding)
    return teks + (" " + pilih(reaksi).format(**v) if reaksi else "")


def susun_teks(steam, epic, sekarang):
    """Naskah dibagi per slide, supaya lama tiap slide bisa disesuaikan dengan panjang kalimatnya."""
    kunci = sekarang.strftime("%Y-%m-%d") + "".join(g["kunci"] for g in steam)
    acak = random.Random(kunci)
    pilih = _Pemilih(acak)
    n, g0 = len(steam), steam[0]
    nama0, harga0 = nama_lisan(g0["judul"]), rupiah_lisan(g0["harga_akhir"])

    pembuka, sebut_g0 = acak.choice([
        (f"Stop dulu scroll-nya. {nama0} lagi {harga0} di Steam!", True),
        (f"{harga0} dapet {nama0}? Hari ini bisa.", True),
        (f"Dompet aman hari ini. Ada {n} game Steam yang lagi jatuh harga.", False),
        (f"Yang nungguin diskon, ini dia. {n} game Steam, harga Rupiah asli.", False),
        (f"Hari ini Steam lagi baik banget. Ada {n} game yang turun jauh.", False),
        (f"Kalau lagi cari game murah, pas banget. Ini {n} yang paling worth it hari ini.", False),
    ])
    segmen = {"pembuka": pembuka, "game": [], "gratis": "", "penutup": ""}

    # Reaksi hanya untuk 2-3 game, supaya tidak monoton dan tidak kepanjangan
    dapat_reaksi = set(acak.sample(range(n), k=min(n, 2 if epic else 3)))
    for i, g in enumerate(steam, 1):
        segmen["game"].append(_segmen_game(g, pilih, i, n, i == 1 and sebut_g0, (i - 1) in dapat_reaksi))

    if epic:
        g = epic[0]
        hari = _hari_berakhir(g)
        batas = f"sampai {hari}" if hari else "minggu ini"
        segmen["gratis"] = pilih([
            "Oh iya, hampir lupa. {nama} lagi gratis di Epic, {batas}. Klaim aja dulu, mainnya belakangan.",
            "Bonus buat kamu: {nama} gratis di Epic, {batas}. Gratis beneran, bukan trial.",
        ]).format(nama=nama_lisan(g["judul"]), batas=batas)
    segmen["penutup"] = pilih([
        "Daftar lengkapnya ada di gamediskon titik my titik id. Mau nunggu lebih murah lagi? Pasang alarm di bot Telegram kami.",
        "Semuanya, lengkap sama riwayat harganya, ada di gamediskon titik my titik id. Gas, sebelum diskonnya habis!",
        "Cek sisanya di gamediskon titik my titik id. Kalau belum cocok harganya, pasang alarm aja, nanti dikabari.",
    ])
    return segmen, acak


def susun_pendamping(steam, epic, sekarang, username_bot, acak):
    """Judul untuk Shorts, keterangan, dan tagar."""
    tgl = f"{sekarang.day} {BULAN[sekarang.month - 1]}"
    n, g0 = len(steam), steam[0]
    nama0, harga0 = nama_lisan(g0["judul"]), rupiah_lisan(g0["harga_akhir"]).replace("ribuan", "Ribuan")
    judul = acak.choice([
        f"{nama0} Cuma {harga0}?! {n} Diskon Steam Hari Ini",
        f"Diskon Steam {g0['diskon']}%: {nama0} Jadi {harga0} ({tgl})",
        f"{n} Game Steam Lagi Murah Banget Hari Ini ({tgl})",
    ])
    buka = acak.choice([
        "Diskon Steam hari ini, harga Rupiah asli (bukan konversi dolar).",
        "Yang lagi murah di Steam Indonesia hari ini 👇",
        f"Harga Steam Indonesia {tgl}, ini yang paling worth it.",
    ])
    daftar = "\n".join(f"• {g['judul']}: {_rupiah(g['harga_akhir'])} (-{g['diskon']}%)" for g in steam)
    gratis = f"\n🆓 Gratis di Epic: {epic[0]['judul']}" if epic else ""
    keterangan = (f"{buka}\n\n{daftar}{gratis}\n\nDaftar lengkap + riwayat harga: gamediskon.my.id"
                  + (f"\nAlarm harga: @{username_bot}" if username_bot else ""))
    tagar = "#diskonsteam #steamsale #gamepc #gamemurah #infogame #steamindonesia" + (" #epicgames #gamegratis" if epic else "")
    return judul, keterangan, tagar


def _lama(teks, minimal, maksimal):
    """Lama slide = waktu membaca kalimatnya + jeda napas, dibatasi."""
    return max(minimal, min(maksimal, len(teks.split()) / KATA_PER_DETIK + 0.6))


def buat_video(steam, epic, path_mp4="video_harian.mp4", username_bot="", link_channel="", session=None):
    """Buat video + teks pendamping. steam/epic: daftar deal dari radar_diskon.py.
    Kembalikan dict {path, durasi, naskah, judul, keterangan, tagar, dengan_suara}, atau None kalau datanya kurang."""
    steam = steam[:MAKS_GAME]
    if len(steam) < 2:
        print("Video dilewati: diskon Steam kurang dari 2.")
        return None
    _siapkan_font()
    sekarang = datetime.now(WIB)
    segmen, acak = susun_teks(steam, epic, sekarang)

    # Utama: video animasi HyperFrames + suara TTS (ElevenLabs, cadangan Edge). Cadangan video: slide Pillow tanpa suara.
    durasi, dengan_suara = None, False
    if os.environ.get("VIDEO_HYPERFRAMES", "1") != "0":
        try:
            _hf_siap()                 # cek alat dulu supaya kredit TTS tidak terpakai sia-sia
            suara = None
            try:
                suara = buat_suara(segmen, bool(epic), session)
            except Exception as e:
                print(f"Suara TTS gagal, video dibuat tanpa suara: {e}")
                _kabari_pemilik(f"⚠️ Video hari ini dibuat TANPA suara (ElevenLabs dan Microsoft Edge gagal): {_ringkas(e)}")
            durasi, dengan_suara = rakit_mp4_hyperframes(steam, epic, segmen, sekarang, username_bot,
                                                         link_channel, path_mp4, session, suara)
            print(f"Video HyperFrames selesai ({durasi:.1f} detik, {'dengan' if dengan_suara else 'tanpa'} suara).")
        except Exception as e:
            print(f"HyperFrames gagal, pakai video slide biasa: {e}")
            _kabari_pemilik(f"⚠️ Video hari ini memakai slide biasa, bukan animasi (HyperFrames gagal): {_ringkas(e)}")
    if durasi is None:
        # Lama tiap slide mengikuti panjang kalimatnya, supaya suara TTS pas dengan gambar
        slide = [(slide_pembuka(len(steam), sekarang, bool(epic)), _lama(segmen["pembuka"], 2.4, 4.5))]
        for i, (g, teks) in enumerate(zip(steam, segmen["game"]), 1):
            slide.append((slide_game(g, i, len(steam), session), _lama(teks, 2.6, 6.0)))
        if epic:
            slide.append((slide_gratis(epic[0], session), _lama(segmen["gratis"], 3.0, 6.5)))
        slide.append((slide_penutup(username_bot, link_channel), _lama(segmen["penutup"], 3.4, 7.0)))
        durasi = rakit_mp4(slide, path_mp4, "video_kerja")

    urutan = [segmen["pembuka"], *segmen["game"]] + ([segmen["gratis"]] if epic else []) + [segmen["penutup"]]
    judul, keterangan, tagar = susun_pendamping(steam, epic, sekarang, username_bot, acak)
    hasil = {"naskah": "\n\n".join(urutan), "judul": judul, "keterangan": keterangan, "tagar": tagar,
             "path": path_mp4, "durasi": durasi, "dengan_suara": dengan_suara}
    return hasil