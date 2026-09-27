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

# Warna (sama dengan gaya.py)
KERTAS = (255, 255, 255)
RAK = (241, 243, 247)
TINTA = (22, 24, 29)
REDUP = (91, 98, 114)
BIRU = (28, 63, 170)
BIRU_TUA = (20, 46, 125)
KUNING = (255, 214, 10)
MERAH = (215, 25, 31)
HIJAU = (15, 123, 63)
COKLAT = (107, 90, 0)

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


def _stiker(potong, harga, coret, skala=1.0, miring=-3):
    """Label harga kuning dengan kotak potongan merah, sedikit miring seperti ditempel tangan."""
    f_potong = huruf(int(118 * skala))
    f_harga = huruf(int(130 * skala))
    f_coret = huruf(int(44 * skala), tebal=500, lebar=90)
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    pad = int(26 * skala)
    lebar_potong = int(uk.textlength(potong, font=f_potong)) + pad * 2 if potong else 0
    lebar_harga = int(max(uk.textlength(harga, font=f_harga), uk.textlength(coret or "", font=f_coret))) + pad * 2
    tinggi = int(210 * skala) if coret else int(170 * skala)
    bayang = int(14 * skala)
    img = Image.new("RGBA", (lebar_potong + lebar_harga + bayang, tinggi + bayang), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((bayang, bayang, lebar_potong + lebar_harga + bayang, tinggi + bayang), fill=TINTA)
    d.rectangle((0, 0, lebar_potong + lebar_harga, tinggi), fill=KUNING)
    if potong:
        d.rectangle((0, 0, lebar_potong, tinggi), fill=MERAH)
        d.text((lebar_potong / 2, tinggi / 2), potong, font=f_potong, fill=KERTAS, anchor="mm")
    x = lebar_potong + pad
    if coret:
        d.text((x, int(22 * skala)), harga, font=f_harga, fill=TINTA, anchor="la")
        yc = tinggi - int(58 * skala)
        d.text((x, yc), coret, font=f_coret, fill=COKLAT, anchor="la")
        lc = d.textlength(coret, font=f_coret)
        d.line((x, yc + int(26 * skala), x + lc, yc + int(26 * skala)), fill=COKLAT, width=max(2, int(4 * skala)))
    else:
        d.text((x, tinggi / 2), harga, font=f_harga, fill=TINTA, anchor="lm")
    return img.rotate(miring, resample=Image.BICUBIC, expand=True)


def _logo(skala=1.0):
    f = huruf(int(84 * skala))
    uk = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    a, b = "Game", "Diskon"
    la, lb = uk.textlength(a, font=f), uk.textlength(b, font=f)
    pad, tinggi, bayang = int(28 * skala), int(118 * skala), int(10 * skala)
    lebar = int(la + lb + pad * 2)
    img = Image.new("RGBA", (lebar + bayang, tinggi + bayang), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((bayang, bayang, lebar + bayang, tinggi + bayang), fill=BIRU_TUA)
    d.rectangle((0, 0, lebar, tinggi), fill=KUNING)
    d.text((pad, tinggi / 2), a, font=f, fill=TINTA, anchor="lm")
    d.text((pad + la, tinggi / 2), b, font=f, fill=MERAH, anchor="lm")
    return img.rotate(3, resample=Image.BICUBIC, expand=True)


def _tanggal(dt):
    return f"{HARI[dt.weekday()]}, {dt.day} {BULAN[dt.month - 1]} {dt.year}"


# ---------- Slide ----------
def slide_pembuka(jumlah, sekarang, ada_gratis):
    im = Image.new("RGB", (W, H), BIRU)
    d = ImageDraw.Draw(im)
    logo = _logo(1.15)
    im.paste(logo, (80, 250), logo)
    y = 520
    for baris in (f"{jumlah} diskon", "Steam", "hari ini"):
        d.text((80, y), baris, font=huruf(200), fill=KERTAS)
        y += 190
    d.text((80, y + 40), "Harga Rupiah asli, dicek langsung", font=huruf(62, 500, 100), fill=(223, 229, 255))
    d.text((80, y + 115), "ke Steam Indonesia.", font=huruf(62, 500, 100), fill=(223, 229, 255))
    if ada_gratis:
        s = _stiker("", "+ game GRATIS", "", 0.62, -2)
        im.paste(s, (80, y + 250), s)
    d.text((80, 1540), _tanggal(sekarang), font=huruf(58, 700, 100), fill=KUNING)
    return im


def slide_game(g, nomor, total, session=None):
    im = Image.new("RGB", (W, H), KERTAS)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 210), fill=BIRU)
    d.text((80, 105), f"Diskon {nomor} dari {total}", font=huruf(64, 800, 80), fill=KERTAS, anchor="lm")
    appid = re.search(r"/app/(\d+)", g["url"])
    sampul = _sampul_steam(appid.group(1), session) if appid else None
    kotak = (60, 300, W - 120, int((W - 120) * 353 / 616))
    if sampul:
        _tempel_isi(im, sampul, kotak)
    else:
        d.rectangle((kotak[0], kotak[1], kotak[0] + kotak[2], kotak[1] + kotak[3]), fill=RAK)
    y = kotak[1] + kotak[3] + 50
    f_nama = huruf(104)
    for baris in _bungkus(d, g["judul"], f_nama, W - 240, 3):
        d.text((80, y), baris, font=f_nama, fill=TINTA)
        y += 104
    d.text((80, y + 18), f"{g['rating']} ulasan positif di Steam", font=huruf(50, 500, 100), fill=REDUP)
    y += 100
    if g.get("terendah_sejak"):
        d.text((80, y), "Termurah sejak mulai dipantau", font=huruf(50, 800, 90), fill=HIJAU)
        y += 70
    s = _stiker(f"-{g['diskon']}%", _rupiah(g["harga_akhir"]), _rupiah(g["harga_awal"]), 1.0, -3)
    im.paste(s, (60, max(y + 40, 1290)), s)
    # Rel rak biru di bawah
    d.rectangle((0, H - 250, W, H - 230), fill=BIRU)
    return im


def slide_gratis(g, session=None):
    im = Image.new("RGB", (W, H), KERTAS)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 210), fill=MERAH)
    d.text((80, 105), "GRATIS di Epic Games Store", font=huruf(64, 800, 80), fill=KERTAS, anchor="lm")
    gambar = _unduh(g["gambar"], session) if g.get("gambar") else None
    kotak = (60, 320, W - 120, int((W - 120) * 9 / 16))
    if gambar:
        _tempel_isi(im, gambar, kotak)
    # Stempel bulat merah
    r = 150
    cap = Image.new("RGBA", (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cap)
    dc.ellipse((10, 10, r * 2 + 10, r * 2 + 10), fill=MERAH, outline=KERTAS, width=10)
    dc.text((r + 10, r + 10), "GRATIS", font=huruf(80), fill=KERTAS, anchor="mm")
    cap = cap.rotate(12, resample=Image.BICUBIC, expand=True)
    im.paste(cap, (W - cap.width - 20, kotak[1] - 110), cap)
    y = kotak[1] + kotak[3] + 60
    for baris in _bungkus(d, g["judul"], huruf(104), W - 240, 3):
        d.text((80, y), baris, font=huruf(104), fill=TINTA)
        y += 104
    d.text((80, y + 40), "Klaim sebelum", font=huruf(54, 500, 100), fill=REDUP)
    d.text((80, y + 110), g["berakhir"], font=huruf(96, 900, 75), fill=MERAH)
    d.text((80, y + 240), "Sekali klaim, jadi milikmu selamanya.", font=huruf(50, 500, 100), fill=TINTA)
    d.rectangle((0, H - 250, W, H - 230), fill=BIRU)
    return im


def slide_penutup(username_bot, link_channel):
    im = Image.new("RGB", (W, H), BIRU)
    d = ImageDraw.Draw(im)
    logo = _logo(1.15)
    im.paste(logo, (80, 300), logo)
    d.text((80, 560), "Daftar lengkap +", font=huruf(120), fill=KERTAS)
    d.text((80, 690), "riwayat harga:", font=huruf(120), fill=KERTAS)
    s = _stiker("", "gamediskon.my.id", "", 0.72, -2)
    im.paste(s, (70, 860), s)
    y = 1110
    if username_bot:
        d.text((80, y), "Alarm harga di Telegram:", font=huruf(54, 500, 100), fill=(223, 229, 255))
        d.text((80, y + 70), f"@{username_bot}", font=huruf(92), fill=KUNING)
        y += 220
    if link_channel:
        d.text((80, y), "Info diskon harian:", font=huruf(54, 500, 100), fill=(223, 229, 255))
        d.text((80, y + 70), link_channel, font=huruf(92), fill=KUNING)
    return im


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
