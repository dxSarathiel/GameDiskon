"""
Video vertikal harian (1080x1920) untuk TikTok dan YouTube Shorts.

Isi: pembuka, 3-5 diskon Steam terbaik, game gratis Epic (kalau ada), dan penutup ke situs.
Tampilannya sama dengan situs: pita biru, label harga kuning, potongan merah.
Selain video, dibuat juga naskah untuk suara TTS, judul, dan tagar yang siap disalin.

Butuh: Pillow dan imageio-ffmpeg (ffmpeg ikut terpasang lewat pip, tidak perlu apt).
"""

import os
import random
import re
import subprocess
from datetime import datetime, timedelta, timezone
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIB = timezone(timedelta(hours=7))
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

W, H = 1080, 1920
FPS = 30
DURASI = {"pembuka": 2.6, "game": 3.2, "gratis": 3.2, "penutup": 3.4}
TRANSISI = 0.35
MAKS_GAME = 5

# Warna tema "Dark Gaming" (sama dengan token di gaya.py)
LATAR = (10, 13, 19)          # --latar
PANEL = (18, 23, 34)          # --panel
PANEL_2 = (25, 32, 48)        # --panel-2
GARIS = (38, 47, 66)          # --garis
TINTA = (238, 241, 247)       # --tinta
REDUP = (155, 165, 186)       # --redup
LIME = (184, 242, 41)         # --lime: diskon & aksi utama
SIAN = (92, 210, 255)         # --sian: tautan
MAGENTA = (255, 77, 141)      # --magenta: GRATIS & hitung mundur
UNGU = (123, 97, 255)         # --ungu: cahaya latar
KUNING = (255, 210, 63)       # --kuning

LEBAR_JUDUL = 118             # lebar huruf untuk judul (uppercase, lebar)
SEMPIT = 75                   # lebar huruf untuk angka

FOLDER_FONT = "fonts"
URL_FONT = "https://github.com/google/fonts/raw/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf"
FILE_FONT = os.path.join(FOLDER_FONT, "Archivo-variabel.ttf")


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
        img = _unduh(f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/{nama}", session)
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


def _pill(teks, font, isi, latar, pad_x=26, pad_y=14, cahaya=None):
    """Label berbentuk kapsul (seperti .stempel dan .potong di situs)."""
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    kiri, atas, kanan, bawah = uk.textbbox((0, 0), teks, font=font)
    w, h = int(kanan - kiri + pad_x * 2), int(bawah - atas + pad_y * 2)
    ruang = 40 if cahaya else 0
    img = Image.new("RGBA", (w + ruang * 2, h + ruang * 2), (0, 0, 0, 0))
    if cahaya:
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((ruang, ruang, ruang + w, ruang + h), radius=h // 2, fill=cahaya)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((ruang, ruang, ruang + w, ruang + h), radius=h // 2, fill=latar)
    d.text((ruang + pad_x - kiri, ruang + pad_y - atas), teks, font=font, fill=isi)
    return img, ruang


def _tempel(kanvas, img, x, y, ruang=0):
    kanvas.alpha_composite(img, (int(x - ruang), int(y - ruang)))


def _latar(w=W, h=H, kuat=1.0):
    """Latar gelap dengan cahaya ungu & lime yang lembut dan grid halus ala HUD (seperti pita di situs)."""
    im = Image.new("RGBA", (w, h), LATAR + (255,))
    cahaya = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cahaya)
    dc.ellipse((int(w * 0.35), int(-h * 0.18), int(w * 1.35), int(h * 0.42)), fill=UNGU + (int(95 * kuat),))
    dc.ellipse((int(-w * 0.45), int(h * 0.72), int(w * 0.55), int(h * 1.25)), fill=LIME + (int(34 * kuat),))
    im.alpha_composite(cahaya.filter(ImageFilter.GaussianBlur(min(w, h) // 6)))
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dg = ImageDraw.Draw(grid)
    jarak = max(40, w // 24)
    for x in range(0, w, jarak):
        dg.line((x, 0, x, h), fill=(255, 255, 255, 12))
    for y in range(0, h, jarak):
        dg.line((0, y, w, y), fill=(255, 255, 255, 12))
    topeng = Image.linear_gradient("L").resize((w, h)).point(lambda v: 255 - v)   # memudar ke bawah
    grid.putalpha(Image.composite(grid.getchannel("A"), Image.new("L", (w, h), 0), topeng))
    im.alpha_composite(grid)
    return im


def _ikon_tag(ukuran):
    """Tanda logo: kotak lime membulat berisi ikon tag harga gelap (sama dengan favicon)."""
    s = ukuran / 24
    img = Image.new("RGBA", (ukuran, ukuran), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, ukuran - 1, ukuran - 1), radius=int(ukuran * 0.22), fill=LIME)
    k = 0.62                         # tag menempati 62% kotak
    o = ukuran * (1 - k) / 2
    t = lambda x, y: (o + x * s * k, o + y * s * k)
    titik = [t(3, 3), t(13, 3), t(20.6, 10.6), t(21.2, 12), t(20.6, 13.4), t(13.4, 20.6), t(12, 21.2), t(10.6, 20.6), t(3, 13), t(3, 3)]
    d.line(titik, fill=LATAR, width=max(2, int(2.4 * s * k)), joint="curve")
    cx, cy = t(7.5, 7.5); r = 1.6 * s * k
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=LATAR)
    return img


def _logo(skala=1.0):
    """Ikon tag + tulisan GAMEDISKON (DISKON berwarna lime), seperti di pita situs."""
    f = huruf(int(64 * skala), 900, LEBAR_JUDUL)
    ikon = _ikon_tag(int(78 * skala))
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lg = uk.textlength("GAME", font=f); ld = uk.textlength("DISKON", font=f)
    jarak = int(22 * skala)
    img = Image.new("RGBA", (ikon.width + jarak + int(lg + ld) + 10, ikon.height), (0, 0, 0, 0))
    img.alpha_composite(ikon, (0, 0))
    d = ImageDraw.Draw(img)
    x = ikon.width + jarak
    d.text((x, ikon.height / 2), "GAME", font=f, fill=TINTA, anchor="lm")
    d.text((x + lg, ikon.height / 2), "DISKON", font=f, fill=LIME, anchor="lm")
    return img


def _label_harga(potong, harga, coret, skala=1.0):
    """Chip potongan lime + harga besar + harga coret (seperti .label-rak di situs)."""
    f_potong = huruf(int(92 * skala), 900, SEMPIT)
    f_harga = huruf(int(128 * skala), 900, SEMPIT)
    f_coret = huruf(int(44 * skala), 500, 100)
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    chip, ruang = _pill(potong, f_potong, LATAR, LIME, int(26 * skala), int(16 * skala), cahaya=LIME + (110,)) if potong else (None, 0)
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


def _kartu(kanvas, kotak, radius=40, garis=GARIS, isi=PANEL):
    x, y, w, h = kotak
    d = ImageDraw.Draw(kanvas)
    d.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=isi, outline=garis, width=3)


def _tempel_gambar_kartu(kanvas, img, kotak, radius=40):
    """Gambar di bagian atas kartu: sudut atas membulat, sudut bawah lurus."""
    x, y, w, h = kotak
    rasio = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * rasio) + 1, int(img.height * rasio) + 1), Image.LANCZOS).convert("RGBA")
    kiri, atas = (img.width - w) // 2, (img.height - h) // 2
    img = img.crop((kiri, atas, kiri + w, atas + h))
    topeng = Image.new("L", (w, h), 0)
    dt = ImageDraw.Draw(topeng)
    dt.rounded_rectangle((0, 0, w, h + radius), radius=radius, fill=255)
    kanvas.paste(img, (x, y), topeng)


def _judul_besar(d, baris, x, y, ukuran, warna_akhir=LIME, jarak=None):
    """Judul uppercase lebar; baris terakhir berwarna lime (seperti gradasi judul di situs)."""
    # Kecilkan otomatis sampai baris terpanjang muat sebelum area tombol TikTok di kanan
    while ukuran > 60:
        f = huruf(ukuran, 900, LEBAR_JUDUL)
        if max(d.textlength(b.upper(), font=f) for b in baris) <= KANAN_AMAN - x:
            break
        ukuran -= 4
    jarak = jarak or int(ukuran * 0.98)
    for i, b in enumerate(baris):
        d.text((x, y), b.upper(), font=f, fill=warna_akhir if i == len(baris) - 1 else TINTA)
        y += jarak
    return y


def _tanggal(dt):
    return f"{HARI[dt.weekday()]}, {dt.day} {BULAN[dt.month - 1]} {dt.year}"


def _kicker(d, teks, x, y, warna=LIME, ukuran=40):
    """Label kecil uppercase berjarak huruf lebar (seperti .unggulan-ket di situs)."""
    f = huruf(ukuran, 800, 100)
    cx = x
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
    d = ImageDraw.Draw(im)
    logo = _logo(1.0)
    im.alpha_composite(logo, (TEPI, 230))
    _kicker(d, f"Diskon Steam  {sekarang.day} {BULAN[sekarang.month - 1]}", TEPI, 470)
    y = _judul_besar(d, [f"{jumlah} diskon", "Steam", "hari ini"], TEPI, 540, 170)
    f = huruf(54, 500, 100)
    d.text((TEPI, y + 50), "Harga Rupiah asli, dicek langsung", font=f, fill=REDUP)
    d.text((TEPI, y + 120), "ke Steam Indonesia.", font=f, fill=REDUP)
    if ada_gratis:
        p, r = _pill("+ GAME GRATIS", huruf(46, 900, 100), LATAR, MAGENTA, 34, 18, cahaya=MAGENTA + (120,))
        _tempel(im, p, TEPI, y + 250, r)
    d.text((TEPI, BAWAH_AMAN - 40), _tanggal(sekarang), font=huruf(46, 700, 100), fill=REDUP)
    return im.convert("RGB")


def _progres(d, nomor, total, y):
    """Bar kecil 'diskon ke-n dari total' di bagian atas."""
    lebar = (KANAN_AMAN - TEPI - (total - 1) * 14) / total
    for i in range(total):
        x = TEPI + i * (lebar + 14)
        d.rounded_rectangle((x, y, x + lebar, y + 10), radius=5, fill=LIME if i < nomor else GARIS)


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
        _kicker(d, "Termurah sejak dipantau", kartu_x + 50, y, LIME, 36)
        y += 70
    label, r = _label_harga(f"-{g['diskon']}%", _rupiah(g["harga_akhir"]), _rupiah(g["harga_awal"]), 1.0)
    _tempel(im, label, kartu_x + 44, y + 30, r)
    return im.convert("RGB")


def slide_gratis(g, session=None):
    im = _latar(kuat=0.8)
    d = ImageDraw.Draw(im)
    _kicker(d, "Gratis di Epic Games Store", TEPI, 235, MAGENTA)
    gambar = _unduh(g["gambar"], session) if g.get("gambar") else None
    kartu_x, kartu_w = TEPI - 12, KANAN_AMAN - TEPI + 60
    gambar_h = int(kartu_w * 9 / 16)
    y0 = 320
    f_nama = huruf(84, 800, 100)
    baris_nama = _bungkus(d, g["judul"], f_nama, kartu_w - 100, 3)
    isi_h = 60 + len(baris_nama) * 92 + 330
    _kartu(im, (kartu_x, y0, kartu_w, gambar_h + isi_h), garis=(90, 40, 64))
    if gambar:
        _tempel_gambar_kartu(im, gambar, (kartu_x + 3, y0 + 3, kartu_w - 6, gambar_h))
    stempel, r = _pill("GRATIS", huruf(48, 900, 100), LATAR, MAGENTA, 30, 16, cahaya=MAGENTA + (140,))
    _tempel(im, stempel, kartu_x + 36, y0 + 36, r)
    d = ImageDraw.Draw(im)
    y = y0 + gambar_h + 55
    for b in baris_nama:
        d.text((kartu_x + 50, y), b, font=f_nama, fill=TINTA)
        y += 92
    d.text((kartu_x + 50, y + 30), "Klaim sebelum", font=huruf(46, 500, 100), fill=REDUP)
    d.text((kartu_x + 50, y + 95), g["berakhir"], font=huruf(96, 900, SEMPIT), fill=MAGENTA)
    d.text((kartu_x + 50, y + 225), "Sekali klaim, jadi milikmu selamanya.", font=huruf(42, 500, 100), fill=TINTA)
    return im.convert("RGB")


def slide_penutup(username_bot, link_channel):
    im = _latar(kuat=1.2)
    d = ImageDraw.Draw(im)
    im.alpha_composite(_logo(1.0), (TEPI, 300))
    y = _judul_besar(d, ["Daftar", "lengkap +", "riwayat", "harga"], TEPI, 500, 130)
    tombol, r = _pill("gamediskon.my.id", huruf(66, 900, 100), LATAR, LIME, 44, 26, cahaya=LIME + (120,))
    _tempel(im, tombol, TEPI, y + 50, r)
    y += 260
    f_ket, f_isi = huruf(46, 500, 100), huruf(76, 900, SEMPIT)
    if username_bot:
        d.text((TEPI, y), "Alarm harga di Telegram", font=f_ket, fill=REDUP)
        d.text((TEPI, y + 62), f"@{username_bot}", font=f_isi, fill=SIAN)
        y += 200
    if link_channel:
        d.text((TEPI, y), "Info diskon harian", font=f_ket, fill=REDUP)
        d.text((TEPI, y + 62), link_channel, font=f_isi, fill=SIAN)
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


# ---------- Teks pendamping ----------
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
    Kembalikan dict {path, durasi, naskah, judul, keterangan, tagar}, atau None kalau datanya kurang."""
    steam = steam[:MAKS_GAME]
    if len(steam) < 2:
        print("Video dilewati: diskon Steam kurang dari 2.")
        return None
    _siapkan_font()
    sekarang = datetime.now(WIB)
    segmen, acak = susun_teks(steam, epic, sekarang)

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
             "path": path_mp4, "durasi": durasi}
    return hasil
