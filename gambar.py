"""
Membuat gambar ringkasan diskon (JPG) untuk dikirim ke Telegram.
Tampilannya sama dengan situs dan video (tema "Shonen Sale"): tinta gelap, satu aksen kuning,
logo 割, panel bersudut potong, label miring. Bentuk, warna, dan huruf diambil dari video.py.
Semua bahan gratis: Pillow, huruf Archivo & Dela Gothic One (OFL), cover game dari Steam dan Epic.
"""

from datetime import datetime, timedelta, timezone
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

import video
from video import HIJAU, KUNING, LATAR, PANEL, REDUP, SEMPIT, TINTA

# ---------- Tampilan (boleh diubah) ----------
LEBAR = 1080
MAKS_KARTU = 4

# Ukuran tata letak
PAD = 60
KARTU_H = 240
KARTU_JARAK = 20
COVER_H = 206
COVER_W = 440

WIB = timezone(timedelta(hours=7))


# ---------- Huruf ----------
_FONT_SIAP = None


def _huruf(ukuran, tebal=900, lebar=100):
    """Archivo dari video.py; kalau unduhan gagal, pakai huruf bawaan supaya gambar tetap jadi."""
    global _FONT_SIAP
    if _FONT_SIAP is None:
        try:
            video._siapkan_font()
            _FONT_SIAP = True
        except Exception as err:
            print(f"Huruf Archivo gagal diunduh ({err}), pakai huruf bawaan.")
            _FONT_SIAP = False
    if _FONT_SIAP:
        return video.huruf(ukuran, tebal, lebar)
    return ImageFont.load_default(size=ukuran)


# ---------- Bantuan gambar ----------
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
        return Image.new("RGB", (COVER_W, COVER_H), video.PANEL_2)


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


def _rupiah(sen):
    return "Rp " + f"{sen // 100:,}".replace(",", ".")


# ---------- Kartu ----------
def _kartu(kanvas, y, item, cover):
    x0, x1 = PAD, LEBAR - PAD
    video._kartu(kanvas, (x0, y, x1 - x0, KARTU_H), potong=30, isi=PANEL)
    kanvas.paste(cover, (x0 + 17, y + 17))
    draw = ImageDraw.Draw(kanvas)

    tx = x0 + 17 + COVER_W + 28          # awal kolom teks
    lebar_teks = x1 - 30 - tx

    # Baris atas: nama toko (+ rating)
    atas = "EPIC GAMES STORE" if item["jenis"] == "epic" else f"STEAM  ·  {item['rating']} POSITIF"
    draw.text((tx, y + 26), atas, font=_huruf(22, 800), fill=REDUP)

    # Judul (maks 2 baris)
    f_judul = _huruf(34, 800)
    for i, b in enumerate(_bungkus(draw, item["judul"], f_judul, lebar_teks)):
        draw.text((tx, y + 58 + i * 40), b, font=f_judul, fill=TINTA)

    # Baris harga
    by = y + 152
    if item["jenis"] == "epic":
        # Gelembung 無料 menempel di pojok cover, seperti stempel di situs
        kanvas.alpha_composite(video._ledakan("無料", "GRATIS", 128), (x0 - 8, y - 14))
        draw = ImageDraw.Draw(kanvas)
        draw.text((tx, by + 2), "Klaim sebelum", font=_huruf(24, 500), fill=REDUP)
        draw.text((tx, by + 30), item["berakhir"], font=_huruf(40, 900, SEMPIT), fill=KUNING)
    else:
        label, _ = video._label(f"-{item['diskon']}%", _huruf(36, 900, SEMPIT), LATAR, KUNING, 14, 9)
        kanvas.alpha_composite(label, (tx, by + 2))
        draw = ImageDraw.Draw(kanvas)
        hx = tx + label.width + 16
        draw.text((hx, by - 6), _rupiah(item["harga_akhir"]), font=_huruf(44, 900, SEMPIT), fill=TINTA)
        coret, f_coret = _rupiah(item["harga_awal"]), _huruf(24, 500)
        cy = by + 44
        draw.text((hx, cy), coret, font=f_coret, fill=REDUP)
        tengah = cy + f_coret.getbbox(coret)[3] * 0.6
        draw.line([(hx, tengah), (hx + draw.textlength(coret, font=f_coret), tengah)], fill=REDUP, width=2)
        if item.get("terendah_sejak"):
            # Label status hijau di pojok kiri bawah cover supaya tidak bertabrakan dengan teks
            status, _ = video._label("TERENDAH TERCATAT", _huruf(20, 900), LATAR, HIJAU, 12, 7)
            kanvas.alpha_composite(status, (x0 + 29, y + 17 + COVER_H - 12 - status.height))


# ---------- Fungsi utama ----------
def buat_gambar(epic, steam, path_keluar, session, nama_channel="", link_channel="", label_event=""):
    """Buat JPG berisi maksimal MAKS_KARTU item: game gratis Epic dulu, lalu diskon Steam.
    Kembalikan path file, atau None kalau tidak ada item."""
    items = [dict(g, jenis="epic") for g in epic] + [dict(g, jenis="steam") for g in steam]
    items = items[:MAKS_KARTU]
    if not items:
        return None

    header_h = 300
    footer_h = 110 if link_channel else 50
    tinggi = header_h + len(items) * KARTU_H + (len(items) - 1) * KARTU_JARAK + footer_h

    kanvas = video._latar(LEBAR, tinggi, 0.9)
    _huruf(10)                           # unduh Archivo sekali; hasilnya menentukan _FONT_SIAP

    # Header: logo, kicker, judul berpita kuning, tanggal
    if _FONT_SIAP:
        kanvas.alpha_composite(video._logo(0.6), (PAD, 48))
        if nama_channel:
            video._kicker(ImageDraw.Draw(kanvas), nama_channel, PAD, 128, KUNING, 24)
        video._judul_besar(kanvas, ["Diskon hari ini"], PAD, 170, 66)
    else:
        ImageDraw.Draw(kanvas).text((PAD, 170), "DISKON HARI INI", font=_huruf(66), fill=TINTA)
    draw = ImageDraw.Draw(kanvas)
    tanggal = datetime.now(WIB).strftime("%d/%m/%Y")
    f_sub = _huruf(26, 600)
    teks_tgl = f"{tanggal}  ·  "
    draw.text((PAD, 258), teks_tgl, font=f_sub, fill=REDUP)
    draw.text((PAD + draw.textlength(teks_tgl, font=f_sub), 258), label_event or "Harga Steam Indonesia",
              font=f_sub, fill=KUNING if label_event else REDUP)

    # Kartu
    y = header_h + 6
    for item in items:
        _kartu(kanvas, y, item, _ambil_cover(item["gambar"], session))
        y += KARTU_H + KARTU_JARAK

    # Footer
    if link_channel:
        draw = ImageDraw.Draw(kanvas)
        f_kaki = _huruf(28, 600)
        awal, link = "Info lengkap & link: ", link_channel
        lebar = draw.textlength(awal, font=f_kaki) + draw.textlength(link, font=_huruf(28, 900))
        x = (LEBAR - lebar) / 2
        draw.text((x, tinggi - 70), awal, font=f_kaki, fill=REDUP)
        draw.text((x + draw.textlength(awal, font=f_kaki), tinggi - 70), link, font=_huruf(28, 900), fill=KUNING)

    kanvas.convert("RGB").save(path_keluar, "JPEG", quality=92, optimize=True)
    return path_keluar
