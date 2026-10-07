"""
Membuat gambar merek GameDiskon tema "Shonen Sale":
- og-gamediskon.png (1200x630, gambar pratinjau saat tautan dibagikan)
- favicon.ico (16/32/48), icon-192.png, apple-touch-icon.png (180)

Jalankan dari akar repo:  python aset/buat_merek.py
og-gamediskon.png ditulis ke aset/ dan akar repo; ikon ditulis sebagai base64 ke blok IKON di gaya.py.
Butuh Pillow >= 10 (bisa membaca .woff2) dan font di aset/ + akar repo.
"""

import base64
import io
import math
import os
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASET = os.path.join(REPO, "aset")

# Token warna, sama dengan :root di gaya.py
TINTA = (10, 11, 18)
TINTA_2 = (18, 20, 30)
GARIS = (38, 42, 58)
PUTIH = (241, 242, 246)
REDUP = (167, 172, 190)
KUNING = (246, 225, 70)

S = 2  # gambar dibuat 2x lalu diperkecil supaya tepi miring halus


def _cari(nama):
    for folder in (ASET, REPO):
        path = os.path.join(folder, nama)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(nama)


def archivo(ukuran, tebal=900, lebar=74):
    f = ImageFont.truetype(_cari("archivo-latin.woff2"), ukuran)
    f.set_variation_by_axes([tebal, lebar])  # urutan sumbu: Weight, Width
    return f


def dela(ukuran):
    return ImageFont.truetype(_cari("dela-gothic-jp.woff2"), ukuran)


def jajar(x, y, w, h, miring):
    """Jajar genjang seperti --jajar di CSS (sisi kiri & kanan miring)."""
    return [(x + miring, y), (x + w, y), (x + w - miring, y + h), (x, y + h)]


def bintang(draw, cx, cy, r, warna):
    """Bintang lima sudut berpusat di (cx, cy)."""
    titik = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.45
        titik.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(titik, fill=warna)


def miringkan(img, derajat):
    """skewX ke kanan (atas bergeser ke kanan), pusat di tengah tinggi."""
    k = math.tan(math.radians(derajat))
    w, h = img.size
    tambah = int(abs(k) * h) + 2
    hasil = Image.new(img.mode, (w + tambah, h), (0, 0, 0, 0))
    hasil.paste(img, (tambah // 2, 0))
    return hasil.transform(hasil.size, Image.AFFINE, (1, k, -k * h / 2, 0, 1, 0), Image.BICUBIC)


def teks_lapis(teks, font, warna, pad=0):
    """Teks di lapisan transparan seukuran kotaknya."""
    kiri, atas, kanan, bawah = font.getbbox(teks)
    img = Image.new("RGBA", (kanan - kiri + pad * 2, bawah - atas + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - kiri, pad - atas), teks, font=font, fill=warna)
    return img


def teks_garis(teks, font, warna, tebal):
    """Hanya garis luar huruf (seperti -webkit-text-stroke dengan isi transparan)."""
    kiri, atas, kanan, bawah = font.getbbox(teks, stroke_width=tebal)
    ukuran = (kanan - kiri + 4, bawah - atas + 4)
    luar = Image.new("L", ukuran, 0)
    dalam = Image.new("L", ukuran, 0)
    xy = (2 - kiri, 2 - atas)
    ImageDraw.Draw(luar).text(xy, teks, font=font, fill=255, stroke_width=tebal, stroke_fill=255)
    ImageDraw.Draw(dalam).text(xy, teks, font=font, fill=255)
    topeng = ImageChops.subtract(luar, dalam)
    alfa = warna[3] if len(warna) > 3 else 255
    img = Image.new("RGBA", ukuran, tuple(warna[:3]) + (0,))
    img.putalpha(topeng.point(lambda v: v * alfa // 255))
    return img


# ---------- Gambar pratinjau 1200x630 ----------
def buat_og():
    W, H = 1200 * S, 630 * S
    img = Image.new("RGBA", (W, H), TINTA + (255,))

    # Garis kecepatan dari titik di kanan, memudar ke kiri
    garis = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(garis)
    cx, cy = 960 * S, 250 * S
    for i in range(54):
        sudut = i * (360 / 54) + (7 if i % 2 else 0)
        lebar = 0.9 if i % 3 else 1.6
        r1, r2 = 230 * S, 1100 * S
        a1, a2 = math.radians(sudut - lebar / 2), math.radians(sudut + lebar / 2)
        d.polygon([(cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)), (cx + r2 * math.cos(a1), cy + r2 * math.sin(a1)),
                   (cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)), (cx + r1 * math.cos(a2), cy + r1 * math.sin(a2))],
                  fill=GARIS + (255,))
    pudar = Image.linear_gradient("L").rotate(90, expand=True).resize((W, H))  # kiri gelap -> kanan terang
    pudar = pudar.point(lambda v: max(0, (v - 90)) * 255 // 165)
    garis.putalpha(ImageChops.multiply(garis.getchannel("A"), pudar))
    img.alpha_composite(garis)

    # Screentone titik-titik di pojok kanan atas
    tone = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tone)
    jarak, r = 12 * S, 1.6 * S
    for y in range(0, H, jarak):
        for x in range(0, W, jarak):
            d.ellipse([x - r, y - r, x + r, y + r], fill=PUTIH + (52,))
    arah = Image.new("L", (W, H), 0)
    ImageDraw.Draw(arah).ellipse([620 * S, -420 * S, 1700 * S, 420 * S], fill=255)
    arah = arah.filter(ImageFilter.GaussianBlur(70 * S))
    tone.putalpha(ImageChops.multiply(tone.getchannel("A"), arah))
    img.alpha_composite(tone)

    # Katakana besar セール bergaris luar sebagai efek suara
    sfx = teks_garis("セール", dela(250 * S), KUNING + (70,), 3 * S).rotate(8, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(sfx, (W - sfx.width + 40 * S, 70 * S))

    # Logo: label kuning 割 + GAMEDISKON
    x0, y0 = 72 * S, 58 * S
    d = ImageDraw.Draw(img)
    d.polygon(jajar(x0, y0, 66 * S, 58 * S, 9 * S), fill=KUNING)
    hanko = teks_lapis("割", dela(36 * S), TINTA)
    img.alpha_composite(hanko, (x0 + (66 * S - hanko.width) // 2, y0 + (58 * S - hanko.height) // 2 + S))
    f_logo = archivo(50 * S)
    game = teks_lapis("GAME", f_logo, PUTIH)
    diskon = teks_lapis("DISKON", f_logo, KUNING)
    ty = y0 + (58 * S - game.height) // 2
    img.alpha_composite(game, (x0 + 84 * S, ty))
    img.alpha_composite(diskon, (x0 + 84 * S + game.width + 2 * S, ty))

    # Judul miring, baris kedua di pita kuning
    f_judul = archivo(96 * S)
    b1 = miringkan(teks_lapis("DISKON STEAM HARI INI,", f_judul, PUTIH, pad=4 * S), 10)
    img.alpha_composite(b1, (66 * S, 186 * S))

    b2 = teks_lapis("DALAM RUPIAH", f_judul, TINTA, pad=4 * S)
    pita = Image.new("RGBA", (b2.width + 64 * S, b2.height + 30 * S), (0, 0, 0, 0))
    ImageDraw.Draw(pita).polygon(jajar(0, 0, pita.width, pita.height, 20 * S), fill=KUNING)
    pita.alpha_composite(b2, (32 * S, 15 * S))
    pita = miringkan(pita, 10)
    img.alpha_composite(pita, (58 * S, 306 * S))

    # Keterangan
    f_ket = archivo(30 * S, tebal=500, lebar=100)
    ket = "Harga asli Steam Indonesia  ·  Game gratis Epic  ·  Riwayat harga"
    d.text((74 * S, 466 * S), ket, font=f_ket, fill=REDUP)

    # Marquee kuning miring di bawah, berisi alamat situs (bintang digambar: Archivo tidak punya ★)
    f_mq = archivo(30 * S)
    isi = ["GAMEDISKON.MY.ID", "DISKON STEAM DALAM RUPIAH", "GAME GRATIS EPIC"]
    mq = Image.new("RGBA", (W + 200 * S, 58 * S), KUNING + (255,))
    dm = ImageDraw.Draw(mq)
    x, i = 172 * S, 0
    while x < mq.width:
        dm.text((x, 30 * S), isi[i % len(isi)], font=f_mq, fill=TINTA, anchor="lm")
        x += f_mq.getlength(isi[i % len(isi)]) + 36 * S
        bintang(dm, x, 29 * S, 11 * S, TINTA)
        x += 36 * S
        i += 1
    mq = mq.rotate(1.6, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(mq, (-100 * S, 548 * S))

    return img.convert("RGB").resize((1200, 630), Image.LANCZOS)


# ---------- Ikon ----------
def ikon_tab(px):
    """Favicon kecil: blok kuning penuh, pojok kanan atas dipotong, huruf 割 gelap."""
    B = px * 8
    img = Image.new("RGBA", (B, B), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    p = B * 0.2
    d.polygon([(0, 0), (B - p, 0), (B, p), (B, B), (0, B)], fill=KUNING)
    huruf = teks_lapis("割", dela(int(B * 0.78)), TINTA)
    img.alpha_composite(huruf, ((B - huruf.width) // 2, (B - huruf.height) // 2 + B // 40))
    return img.resize((px, px), Image.LANCZOS)


def ikon_app(px):
    """Ikon besar (Android/iOS): latar malam, label kuning miring berisi 割, garis kecepatan tipis."""
    B = px * 4
    img = Image.new("RGBA", (B, B), TINTA + (255,))
    d = ImageDraw.Draw(img)
    c = B / 2
    for i in range(36):
        a = math.radians(i * 10 + 5)
        a1, a2 = a - 0.02, a + 0.02
        d.polygon([(c + B * .36 * math.cos(a1), c + B * .36 * math.sin(a1)), (c + B * math.cos(a1), c + B * math.sin(a1)),
                   (c + B * math.cos(a2), c + B * math.sin(a2)), (c + B * .36 * math.cos(a2), c + B * .36 * math.sin(a2))],
                  fill=GARIS)
    w, h = B * 0.64, B * 0.56
    d.polygon(jajar((B - w) / 2, (B - h) / 2, w, h, B * 0.07), fill=KUNING)
    huruf = teks_lapis("割", dela(int(B * 0.4)), TINTA)
    img.alpha_composite(huruf, ((B - huruf.width) // 2, (B - huruf.height) // 2 + B // 80))
    return img.resize((px, px), Image.LANCZOS).convert("RGB")


def _png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def buat_ikon():
    ico = io.BytesIO()
    ikon_tab(48).save(ico, "ICO", sizes=[(16, 16), (32, 32), (48, 48)],
                      append_images=[ikon_tab(16), ikon_tab(32)])
    return {
        "favicon.ico": ico.getvalue(),
        "icon-192.png": _png(ikon_app(192)),
        "apple-touch-icon.png": _png(ikon_app(180)),
    }


def tulis_ke_gaya(ikon):
    """Ganti isi blok IKON = {...} di gaya.py dengan ikon baru (base64, 100 huruf per baris)."""
    path = os.path.join(REPO, "gaya.py")
    sumber = open(path, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in sumber else "\n"   # pertahankan akhir baris file
    bagian = []
    for nama, isi in ikon.items():
        b64 = base64.b64encode(isi).decode()
        baris = nl.join(f'    "{b64[i:i + 100]}"' for i in range(0, len(b64), 100))
        bagian.append(f'    "{nama}": ({nl}{baris}{nl}    ),')
    blok = "IKON = {" + nl + nl.join(bagian) + nl + "}" + nl
    baru, n = re.subn(r"IKON = \{\r?\n.*?\r?\n\}\r?\n", lambda _: blok, sumber, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("Blok IKON di gaya.py tidak ditemukan")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(baru)


if __name__ == "__main__":
    og = buat_og()
    for path in (os.path.join(ASET, "og-gamediskon.png"), os.path.join(REPO, "og-gamediskon.png")):
        og.save(path, "PNG", optimize=True)
    ikon = buat_ikon()
    tulis_ke_gaya(ikon)
    for nama, isi in ikon.items():
        print(f"{nama}: {len(isi)} byte")
    print("og-gamediskon.png:", os.path.getsize(os.path.join(ASET, "og-gamediskon.png")), "byte")
