"""
Membuat gambar ringkasan diskon (JPG) untuk dikirim ke Telegram.
Semua bahan gratis: Pillow, font Poppins (lisensi OFL, diunduh otomatis),
cover game dari Steam dan Epic.
"""

import os
from datetime import datetime, timedelta, timezone
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

# ---------- Tampilan (boleh diubah) ----------
LEBAR = 1080
MAKS_KARTU = 4

WARNA_BG_ATAS = (20, 22, 31)
WARNA_BG_BAWAH = (10, 11, 15)
WARNA_KARTU = (29, 32, 43)
WARNA_AKSEN = (255, 107, 53)     # oranye: badge diskon
WARNA_GRATIS = (46, 204, 113)    # hijau: badge gratis & label terendah
WARNA_TEKS = (245, 245, 247)
WARNA_REDUP = (150, 155, 170)

FOLDER_FONT = "fonts"
URL_FONT = "https://github.com/google/fonts/raw/main/ofl/poppins/{}"

# Ukuran tata letak
PAD = 60
KARTU_H = 240
KARTU_JARAK = 18
COVER_H = 206
COVER_W = 440
RADIUS = 20

WIB = timezone(timedelta(hours=7))


# ---------- Font ----------
def _font(nama_file, ukuran):
    path = os.path.join(FOLDER_FONT, nama_file)
    if not os.path.exists(path):
        try:
            os.makedirs(FOLDER_FONT, exist_ok=True)
            r = requests.get(URL_FONT.format(nama_file), timeout=30)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        except Exception as err:
            print(f"Font {nama_file} gagal diunduh ({err}), pakai font bawaan.")
            return ImageFont.load_default(size=ukuran)
    return ImageFont.truetype(path, ukuran)


class Font:
    def __init__(self):
        self.label = _font("Poppins-Medium.ttf", 24)
        self.kecil = _font("Poppins-Medium.ttf", 26)
        self.sedang = _font("Poppins-Medium.ttf", 28)
        self.judul = _font("Poppins-Bold.ttf", 32)
        self.harga = _font("Poppins-Bold.ttf", 38)
        self.badge = _font("Poppins-Bold.ttf", 32)
        self.besar = _font("Poppins-Bold.ttf", 64)


# ---------- Bantuan gambar ----------
def _gradien(w, h):
    bg = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / max(h - 1, 1)
        warna = tuple(int(a + (b - a) * t) for a, b in zip(WARNA_BG_ATAS, WARNA_BG_BAWAH))
        d.line([(0, y), (w, y)], fill=warna)
    return bg


def _ambil_cover(url, session):
    """Unduh cover, potong tengah ke rasio kartu. Kalau gagal, kotak polos."""
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGB")
        rasio_target = COVER_W / COVER_H
        w, h = img.size
        if w / h > rasio_target:
            w_baru = int(h * rasio_target)
            kiri = (w - w_baru) // 2
            img = img.crop((kiri, 0, kiri + w_baru, h))
        else:
            h_baru = int(w / rasio_target)
            atas = (h - h_baru) // 2
            img = img.crop((0, atas, w, atas + h_baru))
        return img.resize((COVER_W, COVER_H), Image.LANCZOS)
    except Exception as err:
        print(f"Cover gagal diambil ({err}).")
        return Image.new("RGB", (COVER_W, COVER_H), (45, 49, 62))


def _tempel_bulat(kanvas, img, xy, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0], img.size[1]], radius, fill=255)
    kanvas.paste(img, xy, mask)


def _bungkus(draw, teks, font, lebar_maks, maks_baris=2):
    """Pecah teks jadi beberapa baris; baris terakhir diberi '…' kalau kepanjangan."""
    kata = teks.split()
    baris, sekarang = [], ""
    for i, k in enumerate(kata):
        coba = f"{sekarang} {k}".strip()
        if draw.textlength(coba, font=font) <= lebar_maks:
            sekarang = coba
            continue
        if sekarang:
            baris.append(sekarang)
        sekarang = k
        if len(baris) == maks_baris - 1:
            sisa = " ".join(kata[i:])
            while draw.textlength(sisa + "…", font=font) > lebar_maks and len(sisa) > 1:
                sisa = sisa[:-1]
            if sisa != " ".join(kata[i:]):
                sisa = sisa.rstrip() + "…"
            baris.append(sisa)
            return baris
    if sekarang:
        baris.append(sekarang)
    return baris[:maks_baris]


def _badge(draw, x, y, teks, font, warna):
    lebar = draw.textlength(teks, font=font) + 32
    draw.rounded_rectangle([x, y, x + lebar, y + 54], 14, fill=warna)
    draw.text((x + 16, y + 27), teks, font=font, fill=(255, 255, 255), anchor="lm")
    return x + lebar


def _rupiah(sen):
    return "Rp " + f"{sen // 100:,}".replace(",", ".")


# ---------- Kartu ----------
def _kartu(kanvas, draw, f, y, item, cover):
    x0, x1 = PAD, LEBAR - PAD
    draw.rounded_rectangle([x0, y, x1, y + KARTU_H], RADIUS, fill=WARNA_KARTU)
    _tempel_bulat(kanvas, cover, (x0 + 17, y + 17), 14)

    tx = x0 + 17 + COVER_W + 28          # awal kolom teks
    lebar_teks = x1 - 24 - tx

    # Baris atas: nama toko (+ rating), dan label terendah
    if item["jenis"] == "epic":
        atas = "EPIC GAMES STORE"
    else:
        atas = f"STEAM  ·  {item['rating']} positif"
    draw.text((tx, y + 30), atas, font=f.label, fill=WARNA_REDUP, anchor="lm")

    # Judul (maks 2 baris)
    for i, b in enumerate(_bungkus(draw, item["judul"], f.judul, lebar_teks)):
        draw.text((tx, y + 58 + i * 40), b, font=f.judul, fill=WARNA_TEKS)

    # Baris harga
    by = y + 152
    if item["jenis"] == "epic":
        xb = _badge(draw, tx, by, "GRATIS", f.badge, WARNA_GRATIS)
        draw.text((xb + 18, by + 4), "Klaim sebelum", font=f.kecil, fill=WARNA_REDUP)
        draw.text((xb + 18, by + 32), item["berakhir"], font=f.kecil, fill=WARNA_TEKS)
    else:
        xb = _badge(draw, tx, by, f"-{item['diskon']}%", f.badge, WARNA_AKSEN)
        draw.text((xb + 18, by - 6), _rupiah(item["harga_akhir"]), font=f.harga, fill=WARNA_TEKS)
        coret = _rupiah(item["harga_awal"])
        cx, cy = xb + 20, by + 42
        draw.text((cx, cy), coret, font=f.kecil, fill=WARNA_REDUP)
        lebar_coret = draw.textlength(coret, font=f.kecil)
        tengah = cy + 19
        draw.line([(cx, tengah), (cx + lebar_coret, tengah)], fill=WARNA_REDUP, width=2)
        if item.get("terendah_sejak"):
            # Label ditempel di pojok kiri bawah cover supaya tidak bertabrakan dengan teks
            label = "TERENDAH TERCATAT"
            lw = draw.textlength(label, font=f.label) + 28
            lx, ly = x0 + 17 + 12, y + 17 + COVER_H - 12 - 38
            draw.rounded_rectangle([lx, ly, lx + lw, ly + 38], 10, fill=WARNA_GRATIS)
            draw.text((lx + 14, ly + 19), label, font=f.label, fill=(255, 255, 255), anchor="lm")


# ---------- Fungsi utama ----------
def buat_gambar(epic, steam, path_keluar, session, nama_channel="", link_channel=""):
    """Buat JPG berisi maksimal MAKS_KARTU item: game gratis Epic dulu, lalu diskon Steam.
    Kembalikan path file, atau None kalau tidak ada item."""
    items = [dict(g, jenis="epic") for g in epic] + [dict(g, jenis="steam") for g in steam]
    items = items[:MAKS_KARTU]
    if not items:
        return None

    f = Font()
    header_h = 250
    footer_h = 100 if link_channel else 50
    tinggi = header_h + len(items) * KARTU_H + (len(items) - 1) * KARTU_JARAK + footer_h

    kanvas = _gradien(LEBAR, tinggi)
    draw = ImageDraw.Draw(kanvas)

    # Header
    if nama_channel:
        draw.text((PAD, 62), nama_channel.upper(), font=f.sedang, fill=WARNA_AKSEN)
    draw.text((PAD, 96), "Diskon Hari Ini", font=f.besar, fill=WARNA_TEKS)
    tanggal = datetime.now(WIB).strftime("%d/%m/%Y")
    draw.text((PAD, 182), f"{tanggal}  ·  Harga Steam Indonesia", font=f.sedang, fill=WARNA_REDUP)

    # Kartu
    y = header_h
    for item in items:
        cover = _ambil_cover(item["gambar"], session)
        _kartu(kanvas, draw, f, y, item, cover)
        y += KARTU_H + KARTU_JARAK

    # Footer
    if link_channel:
        draw.text((LEBAR // 2, tinggi - 55), f"Info lengkap & link: {link_channel}",
                  font=f.sedang, fill=WARNA_REDUP, anchor="mm")

    kanvas.save(path_keluar, "JPEG", quality=92, optimize=True)
    return path_keluar
