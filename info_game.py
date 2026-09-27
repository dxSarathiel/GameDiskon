"""
Rubrik "Info Game" di gamediskon.my.id/info-game/

Tiga jenis tulisan:
  1. Laporan harga mingguan  -> otomatis, dari data harga kita sendiri (harga_idr.json), terbit tiap Senin
  2. Game gratis Epic mendatang -> otomatis, begitu Epic mengumumkan game gratis minggu depan
  3. Ringkasan mingguan       -> DITULIS PEMILIK, file Markdown di folder info-game/ (terbit tiap Minggu)

Bot juga mengirim daftar kandidat kabar (dari feed resmi/media game) ke chat pribadi pemilik setiap Sabtu,
sebagai bahan ringkasan hari Minggu. Tulisan berisi pendapat pemilik; sumber asli selalu ditautkan.
"""

import glob
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import format_datetime, parsedate_to_datetime
from html import escape

import requests

from halaman import BULAN, WIB, _rupiah, url_situs
from halaman_artikel import _baca, _ke_html
from gaya import gambar_epic
from halaman_game import _kerangka, _tulis_jika_berubah, jalur_game, ringkas

FOLDER_TULISAN = "info-game"                 # tulisan pemilik (Markdown), di-commit manual
FILE_EPIC = os.path.join("docs", "data", "epic-mendatang.json")   # catatan game gratis Epic yang sudah diumumkan
PENULIS = "Sarathiel"
MIN_PERUBAHAN_LAPORAN = 3                    # laporan mingguan hanya terbit kalau ada cukup perubahan harga
MAKS_BARIS_LAPORAN = 10

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Feed untuk daftar kandidat kabar hari Sabtu (hanya judul + tautan, dikirim ke pemilik, tidak diterbitkan)
FEED_KANDIDAT = {
    "Steam (resmi)": "https://store.steampowered.com/feeds/news/app/593110/",
    "PC Gamer": "https://www.pcgamer.com/rss/",
    "GameSpot": "https://www.gamespot.com/feeds/news/",
}
KATA_PENTING = ["sale", "free", "discount", "price", "steam", "epic", "launch", "release", "bundle",
                "deal", "fest", "demo", "weekend", "gratis", "diskon"]


def _tgl(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def _tgl_pendek(d):
    return f"{d.day} {BULAN[d.month - 1][:3]}"


# ======================================================================
# 1. Laporan harga mingguan (otomatis dari riwayat harga)
# ======================================================================
def _harga_pada(riwayat_game, hari):
    """Harga (sen) dan diskon yang berlaku pada tanggal tertentu, atau None kalau belum dipantau."""
    hasil = None
    for tgl, harga, dsk in sorted(riwayat_game, key=lambda e: e[0]):
        if tgl <= hari:
            hasil = (harga, dsk)
    return hasil


def laporan_mingguan(riwayat, hari_ini):
    """Satu laporan untuk setiap minggu (Senin-Minggu) yang sudah lewat dan punya cukup perubahan harga."""
    mulai_data = min((g.get("mulai") or "9999") for g in riwayat.values()) if riwayat else None
    if not mulai_data:
        return []
    awal = datetime.strptime(mulai_data, "%Y-%m-%d").date()
    senin = awal + timedelta(days=(7 - awal.weekday()) % 7)      # Senin pertama setelah data mulai
    laporan = []
    while senin + timedelta(days=7) <= hari_ini:
        minggu = senin + timedelta(days=6)
        sebelum, akhir = (senin - timedelta(days=1)).isoformat(), minggu.isoformat()
        turun, naik, termurah = [], [], []
        for appid, g in riwayat.items():
            rw = g.get("riwayat") or []
            a, b = _harga_pada(rw, sebelum), _harga_pada(rw, akhir)
            if not a or not b:
                continue
            r = ringkas(appid, g)
            info = {"appid": appid, "nama": g.get("nama") or appid, "slug": r["slug"] if r else "",
                    "dari": a[0], "ke": b[0], "diskon": b[1]}
            if b[0] < a[0]:
                turun.append(info)
                harga_minggu_ini = [e[1] for e in rw if e[0] <= akhir]
                if len({e[1] for e in rw if e[0] <= akhir}) > 1 and b[0] <= min(harga_minggu_ini):
                    termurah.append(info)
            elif b[0] > a[0]:
                naik.append(info)
        if len(turun) + len(naik) >= MIN_PERUBAHAN_LAPORAN:
            laporan.append(_tulis_laporan(senin, minggu, turun, naik, termurah))
        senin += timedelta(days=7)
    return laporan


def _baris_harga(i):
    tautan = f'/{jalur_game(i["appid"], i["slug"])}'
    potong = f" (diskon {i['diskon']}%)" if i["diskon"] else ""
    return (f'<li><a href="{tautan}">{escape(i["nama"])}</a>: {_rupiah(i["dari"])} menjadi '
            f'<strong>{_rupiah(i["ke"])}</strong>{potong}</li>')


def _tulis_laporan(senin, minggu, turun, naik, termurah):
    turun.sort(key=lambda i: i["ke"] / max(i["dari"], 1))      # penurunan terbesar (persentase) di atas
    naik.sort(key=lambda i: i["ke"] - i["dari"], reverse=True)
    terbit = minggu + timedelta(days=1)
    periode = f"{_tgl_pendek(senin)} – {_tgl_pendek(minggu)} {minggu.year}"
    judul = f"Laporan Harga Steam Indonesia Minggu Ini ({periode})"
    deskripsi = (f"{len(turun)} game Steam turun harga dan {len(naik)} naik dalam sepekan ({periode}). "
                 f"Rangkuman perubahan harga dalam Rupiah dari data pantauan GameDiskon.")
    bagian = [f"<p>Selama sepekan ({periode}), dari game yang kami pantau setiap hari di Steam Indonesia, "
              f"<strong>{len(turun)} game turun harga</strong> dan <strong>{len(naik)} game naik harga</strong>. "
              f"Kenaikan harga biasanya berarti diskonnya sudah berakhir.</p>"]
    if termurah:
        bagian.append("<h2>Sedang di harga termurahnya</h2><p>Game-game ini sekarang ada di harga paling murah "
                      "sejak mulai kami pantau:</p><ul>" + "".join(_baris_harga(i) for i in termurah[:MAKS_BARIS_LAPORAN]) + "</ul>")
    lain = [i for i in turun if i not in termurah[:MAKS_BARIS_LAPORAN]]   # jangan tulis game yang sama dua kali
    if lain:
        judul_turun = "Turun harga lainnya" if termurah else "Turun harga"
        bagian.append(f"<h2>{judul_turun}</h2><ul>" + "".join(_baris_harga(i) for i in lain[:MAKS_BARIS_LAPORAN]) + "</ul>")
        if len(lain) > MAKS_BARIS_LAPORAN:
            bagian.append(f"<p>Dan {len(lain) - MAKS_BARIS_LAPORAN} game lain. Lihat semuanya di "
                          f'<a href="/game/">daftar game</a>.</p>')
    if naik:
        bagian.append("<h2>Naik harga (diskon berakhir)</h2><p>Kalau salah satunya ada di daftar incaranmu, "
                      "pasang alarm supaya dikabari saat diskon lagi.</p><ul>"
                      + "".join(_baris_harga(i) for i in naik[:MAKS_BARIS_LAPORAN]) + "</ul>")
    bagian.append('<p>Harga diambil langsung dari Steam region Indonesia setiap sore. Riwayat lengkap setiap game '
                  'bisa dilihat di <a href="/game/">daftar game</a>.</p>')
    return {"slug": f"laporan-harga-{senin.isoformat()}", "judul": judul, "deskripsi": deskripsi,
            "tanggal": terbit.isoformat(), "jenis": "Laporan harga", "html": "\n".join(bagian), "otomatis": True}


# ======================================================================
# 2. Game gratis Epic mendatang (otomatis)
# ======================================================================
def perbarui_epic_mendatang(session=None):
    """Ambil game gratis Epic yang akan datang dan simpan ke catatan (supaya tulisannya tetap ada setelah lewat)."""
    try:
        catatan = json.load(open(FILE_EPIC, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        catatan = {}
    r = (session or requests).get(
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
        params={"locale": "en-US", "country": "ID", "allowCountries": "ID"}, timeout=30)
    r.raise_for_status()
    for el in r.json()["data"]["Catalog"]["searchStore"]["elements"]:
        for grup in ((el.get("promotions") or {}).get("upcomingPromotionalOffers") or []):
            for p in grup.get("promotionalOffers", []):
                if (p.get("discountSetting") or {}).get("discountPercentage") != 0:
                    continue
                mulai = p["startDate"][:10]
                slug = (el.get("catalogNs") or {}).get("mappings") or [{}]
                slug = (slug[0] or {}).get("pageSlug") or el.get("productSlug") or el.get("urlSlug") or ""
                gambar = next((i["url"] for i in el.get("keyImages", []) if i.get("type") in
                               ("OfferImageWide", "DieselStoreFrontWide", "Thumbnail")), "")
                daftar = catatan.setdefault(mulai, [])
                if el["title"] not in [g["judul"] for g in daftar]:
                    daftar.append({"judul": el["title"], "mulai": p["startDate"], "berakhir": p["endDate"],
                                   "dicatat": datetime.now(WIB).date().isoformat(),
                                   "url": f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games",
                                   "gambar": gambar})
    os.makedirs(os.path.dirname(FILE_EPIC), exist_ok=True)
    with open(FILE_EPIC, "w", encoding="utf-8") as f:
        json.dump(catatan, f, ensure_ascii=False, indent=1)
    return catatan


def _waktu_wib(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(WIB)
    return f"{HARI[t.weekday()]}, {t.day} {BULAN[t.month - 1]} pukul {t:%H.%M} WIB"


def tulisan_epic(catatan):
    tulisan = []
    for mulai, daftar in sorted(catatan.items()):
        if not daftar:
            continue
        nama = [g["judul"] for g in daftar]
        gabung = nama[0] if len(nama) == 1 else ", ".join(nama[:-1]) + " dan " + nama[-1]
        tgl_umum = datetime.strptime(mulai, "%Y-%m-%d")
        # Pakai tanggal, bukan "Minggu Depan": judul tetap benar walaupun tulisannya dibaca bulan depan
        judul = f"Game Gratis Epic {tgl_umum.day} {BULAN[tgl_umum.month - 1]} {tgl_umum.year}: {gabung}"
        deskripsi = (f"Epic Games Store akan menggratiskan {gabung} mulai {tgl_umum.day} {BULAN[tgl_umum.month - 1]}. "
                     f"Jadwal klaim dalam WIB dan caranya.")
        item = []
        for g in daftar:
            gambar = (f'<img src="{escape(gambar_epic(g["gambar"]))}" alt="{escape(g["judul"])}" width="640" height="360" '
                      f'loading="lazy" decoding="async" style="width:100%;height:auto;border-radius:3px">'
                      if g["gambar"] else "")
            item.append(f'<h2>{escape(g["judul"])}</h2>{gambar}<p>Gratis mulai <strong>{_waktu_wib(g["mulai"])}</strong> '
                        f'sampai <strong>{_waktu_wib(g["berakhir"])}</strong>. '
                        f'<a href="{escape(g["url"])}" rel="noopener">Halaman game di Epic</a>.</p>')
        html = (f"<p>Epic Games Store sudah mengumumkan game gratis untuk minggu berikutnya. "
                f"Sekali klaim, game jadi milikmu selamanya.</p>" + "".join(item)
                + '<p>Belum pernah klaim? Ikuti <a href="/panduan/cara-klaim-game-gratis-epic-games/">panduan '
                  'cara klaim game gratis Epic</a>. Saat game ini sudah bisa diklaim, kami kabari juga di channel Telegram. '
                  'Daftar yang selalu terbaru ada di halaman <a href="/game-gratis-epic/">game gratis Epic minggu ini</a>.</p>')
        # Terbit pada hari bot pertama kali melihat pengumumannya
        terbit = min(g.get("dicatat") or mulai for g in daftar)
        tulisan.append({"slug": f"epic-gratis-{mulai}", "judul": judul, "deskripsi": deskripsi, "tanggal": terbit,
                        "jenis": "Game gratis", "html": html, "otomatis": True,
                        "gambar": next((g["gambar"] for g in daftar if g.get("gambar")), "")})
    return tulisan


# ======================================================================
# 3. Ringkasan mingguan tulisan pemilik (Markdown di folder info-game/)
# ======================================================================
def tulisan_pemilik(folder=FOLDER_TULISAN):
    hasil = []
    for path in sorted(glob.glob(os.path.join(folder, "*.md"))):
        kepala, isi = _baca(path)
        if kepala.get("draf", "").lower() in ("ya", "yes", "true", "1"):
            continue
        if not all(kepala.get(k) for k in ("judul", "deskripsi", "tanggal")):
            print(f"Info Game {path} dilewati: kepala belum lengkap (judul, deskripsi, tanggal).")
            continue
        try:
            datetime.strptime(kepala["tanggal"], "%Y-%m-%d")
        except ValueError:
            print(f"Info Game {path} dilewati: format tanggal harus TTTT-BB-HH.")
            continue
        hasil.append({"slug": os.path.splitext(os.path.basename(path))[0].lower(), "judul": kepala["judul"],
                      "deskripsi": kepala["deskripsi"], "tanggal": kepala["tanggal"], "jenis": "Kabar mingguan",
                      "html": _ke_html(isi, []), "otomatis": False})
    return hasil


# ======================================================================
# Halaman, daftar, dan RSS
# ======================================================================
def _html_tulisan(t, situs):
    url = f"{situs}info-game/{t['slug']}/"
    oleh = "Disusun otomatis oleh GameDiskon" if t["otomatis"] else f"Ditulis oleh {escape(PENULIS)}"
    badan = f"""    <nav class="jejak" aria-label="Lokasi halaman"><ol><li><a href="/">Beranda</a></li><li><a href="/info-game/">Info Game</a></li><li aria-current="page">{escape(t['judul'])}</li></ol></nav>
    <div class="prosa">
      <article>
        <h1 class="judul-halaman">{escape(t['judul'])}</h1>
        <p class="meta">{escape(t['jenis'])}. {oleh}, {_tgl(t['tanggal'])}.</p>
{t['html']}
      </article>
    </div>"""
    jsonld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": t["judul"],
              "description": t["deskripsi"], "datePublished": t["tanggal"], "dateModified": t["tanggal"],
              "author": {"@type": "Organization" if t["otomatis"] else "Person",
                         "name": "GameDiskon" if t["otomatis"] else PENULIS},
              "publisher": {"@type": "Organization", "name": "GameDiskon", "url": situs},
              "mainEntityOfPage": url, "inLanguage": "id"}
    if t.get("gambar"):
        jsonld["image"] = gambar_epic(t["gambar"], 1200, 675)
    return url, _kerangka(t["judul"], t["deskripsi"], url, badan, jsonld=jsonld, aktif="info-game",
                          og_gambar=t.get("gambar", ""), og_tipe="article")


def _html_daftar(daftar, situs):
    url = f"{situs}info-game/"
    item = "".join(f'<li><h2><a href="/info-game/{t["slug"]}/">{escape(t["judul"])}</a></h2>'
                   f'<p>{escape(t["jenis"])}, {_tgl(t["tanggal"])}. {escape(t["deskripsi"])}</p></li>' for t in daftar)
    badan = f"""    <nav class="jejak" aria-label="Lokasi halaman"><ol><li><a href="/">Beranda</a></li><li aria-current="page">Info Game</li></ol></nav>
    <div>
      <h1 class="judul-halaman">Info Game</h1>
      <p class="catatan">Kabar seputar harga, sale, dan game gratis di Steam dan Epic untuk pemain di Indonesia. Laporan harga setiap Senin, kabar mingguan setiap Minggu. <a href="/info-game/feed.xml">RSS</a>.</p>
      <ul class="daftar-artikel">{item}</ul>
    </div>"""
    return url, _kerangka("Info Game: Kabar Harga, Sale, dan Game Gratis",
                          "Kabar terbaru seputar harga game Steam Indonesia, jadwal sale, dan game gratis Epic.",
                          url, badan, aktif="info-game").replace("</head>", f'<link rel="alternate" type="application/rss+xml" title="Info Game GameDiskon" href="{situs}info-game/feed.xml">\n</head>', 1)


def _rss(daftar, situs):
    item = []
    for t in daftar[:20]:
        waktu = datetime.strptime(t["tanggal"], "%Y-%m-%d").replace(hour=17, tzinfo=WIB)
        url = f"{situs}info-game/{t['slug']}/"
        item.append(f"<item><title>{escape(t['judul'])}</title><link>{url}</link><guid>{url}</guid>"
                    f"<pubDate>{format_datetime(waktu)}</pubDate><description>{escape(t['deskripsi'])}</description></item>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>Info Game GameDiskon</title><link>{situs}info-game/</link>"
            "<description>Kabar harga, sale, dan game gratis untuk pemain di Indonesia</description><language>id</language>"
            + "".join(item) + "</channel></rss>\n")


def buat_info_game(riwayat, folder="docs", session=None, hari_ini=None, catat_masalah=print):
    """Buat semua halaman Info Game. Kembalikan (entri sitemap, daftar tulisan terbaru di atas)."""
    situs = url_situs()
    if not situs:
        return [], []
    hari_ini = hari_ini or datetime.now(WIB).date()
    try:
        catatan_epic = perbarui_epic_mendatang(session)
    except Exception as err:
        catat_masalah(f"Info Game: data Epic mendatang gagal diambil ({err}); catatan lama dipakai.")
        try:
            catatan_epic = json.load(open(FILE_EPIC, encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            catatan_epic = {}
    semua = laporan_mingguan(riwayat, hari_ini) + tulisan_epic(catatan_epic) + tulisan_pemilik()
    # Tulisan bertanggal masa depan belum diterbitkan
    semua = [t for t in semua if t["tanggal"] <= hari_ini.isoformat()]
    semua.sort(key=lambda t: (t["tanggal"], t["slug"]), reverse=True)

    hasil = []
    for t in semua:
        url, html = _html_tulisan(t, situs)
        _tulis_jika_berubah(os.path.join(folder, "info-game", t["slug"], "index.html"), html)
        hasil.append((url, t["tanggal"]))
    url, html = _html_daftar(semua, situs)
    _tulis_jika_berubah(os.path.join(folder, "info-game", "index.html"), html)
    _tulis_jika_berubah(os.path.join(folder, "info-game", "feed.xml"), _rss(semua, situs))
    if semua:
        hasil.insert(0, (url, semua[0]["tanggal"]))
    print(f"Info Game: {len(semua)} tulisan terbit.")
    return hasil, semua


# ======================================================================
# Daftar kandidat kabar untuk pemilik (setiap Sabtu)
# ======================================================================
def kandidat_kabar(session=None, hari=7, maks=12):
    """Judul + tautan dari beberapa feed, 7 hari terakhir, yang paling relevan dengan harga/sale/game gratis di atas."""
    batas = datetime.now(WIB) - timedelta(days=hari)
    hasil = []
    for sumber, url in FEED_KANDIDAT.items():
        try:
            r = (session or requests).get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 GameDiskonBot"})
            akar = ET.fromstring(r.content)
        except Exception as err:
            print(f"Feed {sumber} gagal: {err}")
            continue
        for it in akar.iter("item"):
            judul, link = (it.findtext("title") or "").strip(), (it.findtext("link") or "").strip()
            try:
                waktu = parsedate_to_datetime(it.findtext("pubDate"))
            except Exception:
                continue
            if waktu < batas or not judul:
                continue
            skor = sum(1 for k in KATA_PENTING if k in judul.lower()) + (1 if "resmi" in sumber else 0)
            hasil.append({"sumber": sumber, "judul": judul, "link": link, "waktu": waktu, "skor": skor})
    hasil.sort(key=lambda x: (x["skor"], x["waktu"]), reverse=True)
    # Paling banyak 5 per sumber, supaya daftarnya beragam
    terpilih, per_sumber = [], {}
    for k in hasil:
        if per_sumber.get(k["sumber"], 0) < 5:
            terpilih.append(k)
            per_sumber[k["sumber"]] = per_sumber.get(k["sumber"], 0) + 1
    return terpilih[:maks]


def pesan_kandidat(kandidat, hari_ini):
    minggu = hari_ini + timedelta(days=(6 - hari_ini.weekday()) % 7)
    nama_file = f"{minggu.isoformat()}-kabar-game-minggu-ini.md"
    baris = [f"📰 <b>Bahan kabar mingguan</b> (terbit Minggu, {minggu.day} {BULAN[minggu.month - 1]})", ""]
    if kandidat:
        for k in kandidat:
            baris.append(f'• <a href="{escape(k["link"])}">{escape(k["judul"])}</a> ({escape(k["sumber"])})')
    else:
        baris.append("Belum ada kandidat dari feed minggu ini. Kamu bisa pakai bahan sendiri.")
    templat = (f"---\njudul: Kabar Game Minggu Ini ({minggu.day} {BULAN[minggu.month - 1]} {minggu.year})\n"
               f"deskripsi: (satu-dua kalimat ringkasan)\ntanggal: {minggu.isoformat()}\n---\n\n"
               "## (judul kabar pertama)\n\n(2-4 kalimat pendapatmu) [Sumber](tautan)\n")
    baris += ["", "Pilih 4–5 yang menarik, tulis 2–4 kalimat pendapatmu untuk masing-masing, dan tautkan sumbernya. "
              f"Simpan sebagai file baru <code>info-game/{nama_file}</code> di GitHub. Templat:",
              f"<pre>{escape(templat)}</pre>"]
    return "\n".join(baris)
