"""
Dua halaman tetap yang isinya diperbarui otomatis setiap hari:

  /game-gratis-epic/   -> game gratis Epic yang berlaku sekarang + yang akan gratis minggu depan
  /jadwal-steam-sale/  -> jadwal Steam Sale (dari EVENT_SALE di radar_diskon.py) dalam WIB

Kenapa alamatnya tetap (bukan bertanggal): orang mencari "game gratis epic minggu ini" dan
"jadwal steam sale" setiap minggu. Satu alamat yang selalu terbaru mengumpulkan nilai di Google
dari waktu ke waktu, sedangkan tulisan bertanggal di Info Game cepat basi.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from html import escape

from gaya import USERNAME_BOT_ALARM, gambar_epic
from halaman import BULAN, HARI, SKRIP_BERANDA, WIB, _barang_steam, _kartu_epic, url_situs
from halaman_game import _kerangka, _tulis_jika_berubah

FILE_EPIC = os.path.join("docs", "data", "epic-mendatang.json")   # ditulis info_game.py
MAKS_DISKON_SALE = 8        # jumlah diskon Steam yang ditampilkan di halaman jadwal sale

# Steam Sale biasanya mulai dan selesai pukul 10.00 waktu Pasifik (Seattle).
try:
    from zoneinfo import ZoneInfo
    PASIFIK = ZoneInfo("America/Los_Angeles")
except Exception:                          # data zona waktu tidak tersedia: anggap musim panas (UTC-7)
    PASIFIK = timezone(timedelta(hours=-7))
JAM_SALE_PASIFIK = 10


# ---------- Bantuan ----------
def _wib(dt):
    t = dt.astimezone(WIB)
    return f"{HARI[t.weekday()]}, {t.day} {BULAN[t.month - 1]} {t.year} pukul {t:%H.%M} WIB"


def _wib_pendek(dt):
    t = dt.astimezone(WIB)
    return f"{t.day} {BULAN[t.month - 1]} {t.year}, {t:%H.%M} WIB"


def _iso_ke_dt(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _jejak(nama):
    return (f'    <nav class="jejak" aria-label="Lokasi halaman"><ol>'
            f'<li><a href="/">Beranda</a></li><li aria-current="page">{escape(nama)}</li></ol></nav>')


def _jsonld_jejak(situs, nama, url):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Beranda", "item": situs},
        {"@type": "ListItem", "position": 2, "name": nama, "item": url}]}


def _gabung(nama):
    return nama[0] if len(nama) == 1 else ", ".join(nama[:-1]) + " dan " + nama[-1]


def _ajakan_alarm():
    if not USERNAME_BOT_ALARM:
        return ""
    return (f'<a href="https://t.me/{escape(USERNAME_BOT_ALARM)}" rel="noopener">bot alarm harga GameDiskon</a>')


# ======================================================================
# 1. /game-gratis-epic/
# ======================================================================
def _epic_mendatang(sekarang):
    """Game Epic yang diumumkan tapi belum mulai gratis, dari catatan info_game.py."""
    try:
        catatan = json.load(open(FILE_EPIC, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []
    hasil = []
    for daftar in catatan.values():
        for g in daftar:
            try:
                if _iso_ke_dt(g["mulai"]) > sekarang:
                    hasil.append(g)
            except (KeyError, ValueError):
                continue
    return sorted(hasil, key=lambda g: g["mulai"])


def _kartu_mendatang(g):
    gambar = ""
    if g.get("gambar"):
        gambar = (f'<img src="{escape(gambar_epic(g["gambar"]))}" alt="" width="640" height="360" '
                  f'loading="lazy" decoding="async">')
    return f"""
      <li>
        <a href="{escape(g['url'])}" rel="noopener">
          <span class="stempel" aria-hidden="true">SEGERA</span>
          {gambar}
          <h3>{escape(g['judul'])}</h3>
          <p class="batas">Gratis mulai {escape(_wib(_iso_ke_dt(g['mulai'])))}</p>
        </a>
      </li>"""


def buat_halaman_epic(epic_semua, info_semua=None, folder="docs"):
    """Kembalikan entri sitemap [(url, lastmod)].
    Kalau data Epic hari ini kosong (misalnya gagal diambil), halaman kemarin dibiarkan."""
    situs = url_situs()
    if not situs:
        return []
    url = f"{situs}game-gratis-epic/"
    path = os.path.join(folder, "game-gratis-epic", "index.html")
    sekarang = datetime.now(WIB)
    if not epic_semua:
        print("Halaman game gratis Epic tidak diperbarui: data Epic hari ini kosong.")
        return [(url, sekarang.date().isoformat())] if os.path.exists(path) else []

    mendatang = _epic_mendatang(sekarang)
    nama_kini = [g["judul"] for g in epic_semua]
    akhir = min((_iso_ke_dt(g["berakhir_iso"]) for g in epic_semua if g.get("berakhir_iso")), default=None)

    kartu = "".join(_kartu_epic(g, i == 0) for i, g in enumerate(epic_semua))
    kalimat_akhir = (f" Bisa diklaim sampai <strong>{escape(_wib(akhir))}</strong>." if akhir else "")
    isi = [f"""{_jejak("Game gratis Epic")}
    <h1 class="judul-halaman">Game gratis Epic minggu ini</h1>
    <p class="catatan">Dicek {HARI[sekarang.weekday()]}, {sekarang.day} {BULAN[sekarang.month - 1]} {sekarang.year}. Saat ini Epic Games Store menggratiskan {escape(_gabung(nama_kini))}.{kalimat_akhir} Sekali klaim, game jadi milikmu selamanya.</p>
    <section class="bagian" aria-labelledby="h-kini">
      <h2 id="h-kini">Bisa diklaim sekarang</h2>
      <p class="catatan">Belum pernah klaim? Ikuti <a href="/panduan/cara-klaim-game-gratis-epic-games/">panduan cara klaim game gratis Epic</a>.</p>
      <ul class="gratis">{kartu}
      </ul>
    </section>"""]

    if mendatang:
        nama_depan = _gabung([g["judul"] for g in mendatang])
        isi.append(f"""
    <section class="bagian" aria-labelledby="h-depan">
      <h2 id="h-depan">Gratis minggu depan</h2>
      <p class="catatan">Epic sudah mengumumkan {escape(nama_depan)}. Jamnya sudah diubah ke WIB.</p>
      <ul class="gratis">{"".join(_kartu_mendatang(g) for g in mendatang)}
      </ul>
    </section>""")
    else:
        isi.append("""
    <section class="bagian" aria-labelledby="h-depan">
      <h2 id="h-depan">Gratis minggu depan</h2>
      <p class="catatan">Epic belum mengumumkan game gratis berikutnya. Biasanya diumumkan bersamaan dengan pergantian game setiap Kamis malam WIB. Halaman ini dicek ulang setiap hari.</p>
    </section>""")

    jam_ganti = ""
    if akhir:
        t = akhir.astimezone(WIB)
        jam_ganti = (f" Minggu ini pergantiannya {HARI[t.weekday()]} pukul {t:%H.%M} WIB."
                     f" Jamnya bisa bergeser satu jam saat Amerika Serikat berganti jam musim panas.")
    alarm = _ajakan_alarm()
    isi.append(f"""
    <section class="bagian" aria-labelledby="h-kapan">
      <h2 id="h-kapan">Kapan game gratis Epic berganti?</h2>
      <div class="prosa">
        <p>Epic Games Store mengganti game gratisnya seminggu sekali, biasanya hari Kamis malam waktu Indonesia.{escape(jam_ganti)} Setelah lewat batas waktunya, game kembali ke harga normal dan tidak bisa diklaim lagi.</p>
        <p>Supaya tidak ketinggalan, ikuti channel Telegram GameDiskon: setiap ada game gratis baru, kabarnya langsung dikirim.{f" Untuk game Steam yang kamu incar, pakai {alarm}." if alarm else ""}</p>
      </div>
    </section>""")

    arsip = [t for t in (info_semua or []) if t.get("jenis") == "Game gratis"]
    if arsip:
        item = "".join(f'<li><h2><a href="/info-game/{escape(t["slug"])}/">{escape(t["judul"])}</a></h2>'
                       f'<p>{escape(t["deskripsi"])}</p></li>' for t in arsip[:8])
        isi.append(f"""
    <section class="bagian" aria-labelledby="h-arsip">
      <h2 id="h-arsip">Pengumuman game gratis Epic</h2>
      <ul class="daftar-artikel">{item}</ul>
    </section>""")

    judul = "Game Gratis Epic Minggu Ini & Minggu Depan (Jadwal WIB)"
    deskripsi = f"Game gratis Epic Games Store minggu ini: {_gabung(nama_kini)}."
    if akhir:
        t = akhir.astimezone(WIB)
        deskripsi += f" Klaim sebelum {t.day} {BULAN[t.month - 1]} pukul {t:%H.%M} WIB."
    for ekor in (" Plus jadwal game gratis minggu depan dan cara klaimnya.", " Plus jadwal minggu depan."):
        if len(deskripsi + ekor) <= 160:        # batas kira-kira yang tampil di Google
            deskripsi += ekor
            break
    html = _kerangka(judul, deskripsi, url, "".join(isi), og_gambar=epic_semua[0].get("gambar", ""),
                     jsonld=_jsonld_jejak(situs, "Game gratis Epic", url), aktif="gratis-epic",
                     script=SKRIP_BERANDA)
    _tulis_jika_berubah(path, html)
    return [(url, sekarang.date().isoformat())]


# ======================================================================
# 2. /jadwal-steam-sale/
# ======================================================================
def _waktu_sale(tanggal_iso):
    """'2026-10-01' -> datetime 1 Okt 2026 10.00 waktu Pasifik (= 2 Okt 00.00 WIB saat musim panas)."""
    d = datetime.strptime(tanggal_iso, "%Y-%m-%d")
    return d.replace(hour=JAM_SALE_PASIFIK, tzinfo=PASIFIK)


SKRIP_HITUNG_SALE = """<script>
(function () {
  document.querySelectorAll('[data-mulai]').forEach(function (el) {
    var mulai = Date.parse(el.dataset.mulai), ms = mulai - Date.now();
    if (!mulai || ms <= 0) return;
    var jam = Math.floor(ms / 36e5), hari = Math.floor(jam / 24);
    el.textContent = 'Mulai dalam ' + (hari > 0 ? hari + ' hari ' + (jam % 24) + ' jam.' : jam + ' jam lagi!');
  });
})();
</script>"""


def buat_halaman_steam_sale(event_sale, steam_layak=None, folder="docs"):
    """event_sale: daftar EVENT_SALE dari radar_diskon.py. Kembalikan entri sitemap [(url, lastmod)]."""
    situs = url_situs()
    if not situs or not event_sale:
        return []
    url = f"{situs}jadwal-steam-sale/"
    sekarang = datetime.now(WIB)

    daftar = []
    for ev in event_sale:
        try:
            mulai, selesai = _waktu_sale(ev["mulai"]), _waktu_sale(ev["selesai"])
        except (KeyError, ValueError):
            continue
        if sekarang < mulai:
            status = "Akan datang"
        elif sekarang < selesai:
            status = "Berlangsung"
        else:
            status = "Sudah selesai"
        daftar.append({**ev, "dt_mulai": mulai, "dt_selesai": selesai, "status": status})
    if not daftar:
        return []
    daftar.sort(key=lambda e: e["dt_mulai"])
    tahun = sorted({e["dt_mulai"].year for e in daftar if e["status"] != "Sudah selesai"} or
                   {daftar[-1]["dt_mulai"].year})
    tahun_teks = str(tahun[0]) if len(tahun) == 1 else f"{tahun[0]}–{tahun[-1]}"

    # Event yang paling relevan: yang sedang berlangsung, kalau tidak ada yang berikutnya
    utama = (next((e for e in daftar if e["status"] == "Berlangsung"), None)
             or next((e for e in daftar if e["status"] == "Akan datang"), None))

    isi = [f"""{_jejak("Jadwal Steam Sale")}
    <h1 class="judul-halaman">Jadwal Steam Sale {tahun_teks}</h1>
    <p class="catatan">Tanggal dari jadwal resmi Valve untuk developer (Steamworks). Steam Sale biasanya dimulai dan berakhir pukul 10.00 waktu Pasifik, jadi di Indonesia mulainya sekitar tengah malam WIB. Semua jam di bawah sudah dalam WIB.</p>"""]

    if utama:
        emoji = escape(utama.get("emoji", ""))
        if utama["status"] == "Berlangsung":
            teks = (f"<p><strong>Sedang berlangsung</strong> sampai {escape(_wib(utama['dt_selesai']))}.</p>"
                    f'<p><a class="tombol" href="https://store.steampowered.com/specials" rel="noopener">Buka halaman sale di Steam</a></p>')
        else:
            teks = (f"<p>Mulai <strong>{escape(_wib(utama['dt_mulai']))}</strong>, "
                    f"berakhir {escape(_wib(utama['dt_selesai']))}.</p>"
                    f'<p class="sisa" data-mulai="{utama["dt_mulai"].isoformat()}"></p>')
        isi.append(f"""
    <aside class="voucher lebar" aria-labelledby="h-utama">
      <div>
        <h2 id="h-utama">{emoji} {escape(utama['nama'])}</h2>
        {teks}
      </div>
    </aside>""")

    baris = "".join(
        f"<tr><td>{escape(e['nama'])}</td><td>{escape(_wib_pendek(e['dt_mulai']))}</td>"
        f"<td>{escape(_wib_pendek(e['dt_selesai']))}</td><td>{escape(e['status'])}</td></tr>" for e in daftar)
    isi.append(f"""
    <section class="bagian struk" aria-labelledby="h-jadwal">
      <h2 id="h-jadwal">Semua jadwal</h2>
      <table>
        <thead><tr><th scope="col">Event</th><th scope="col">Mulai (WIB)</th><th scope="col">Selesai (WIB)</th><th scope="col">Status</th></tr></thead>
        <tbody>{baris}</tbody>
      </table>
    </section>""")

    if steam_layak:
        teratas = sorted(steam_layak, key=lambda g: (-g["diskon"], g["harga_akhir"]))[:MAKS_DISKON_SALE]
        judul_rak = (f"Diskon terbaik {utama['nama']} hari ini" if utama and utama["status"] == "Berlangsung"
                     else "Sudah diskon besar hari ini, tanpa menunggu sale")
        isi.append(f"""
    <section class="bagian" aria-labelledby="h-rak">
      <h2 id="h-rak">{escape(judul_rak)}</h2>
      <p class="catatan">Harga Steam Indonesia dalam Rupiah, dicek hari ini. <a href="/">Lihat semua diskon</a>.</p>
      <ol class="rak">{"".join(_barang_steam(g, i + 1) for i, g in enumerate(teratas))}
      </ol>
    </section>""")

    alarm = _ajakan_alarm()
    isi.append(f"""
    <section class="bagian" aria-labelledby="h-tips">
      <h2 id="h-tips">Tips berburu diskon saat Steam Sale</h2>
      <div class="prosa">
        <ul>
          <li>Cek riwayat harga game incaranmu di <a href="/game/">daftar game yang dipantau</a>. Kalau harga sale-nya sama dengan harga termurah yang pernah tercatat, itu saat yang pas untuk membeli.</li>
          <li>Isi saldo Steam Wallet sebelum sale dimulai, supaya tidak terburu-buru saat tengah malam.</li>
          <li>{f"Pasang alarm harga lewat {alarm}, supaya dikabari saat harganya turun sampai targetmu." if alarm else "Ikuti channel Telegram GameDiskon untuk kabar diskon harian."}</li>
        </ul>
      </div>
    </section>""")

    if utama:
        t = utama["dt_mulai"].astimezone(WIB)
        jawaban = (f"{utama['nama']} dimulai {_wib(utama['dt_mulai'])}. Steam memulai sale pukul 10.00 waktu Pasifik, "
                   f"yang sama dengan pukul {t:%H.%M} WIB.")
        isi.append(f"""
    <section class="bagian" aria-labelledby="h-tanya">
      <h2 id="h-tanya">Pertanyaan umum</h2>
      <div class="tanya">
        <details>
          <summary>Jam berapa {escape(utama['nama'])} dimulai di Indonesia?</summary>
          <p>{escape(jawaban)}</p>
        </details>
        <details>
          <summary>Apakah semua game pasti diskon saat Steam Sale?</summary>
          <p>Tidak. Setiap developer memilih sendiri apakah gamenya ikut sale dan berapa potongannya. Karena itu harga di sini dicek langsung ke Steam region Indonesia setiap hari.</p>
        </details>
      </div>
    </section>""")

    nama_pendek = [e["nama"].replace("Steam ", "").rsplit(" 20", 1)[0] for e in daftar if e["status"] != "Sudah selesai"]
    judul = f"Jadwal Steam Sale {tahun_teks} dalam WIB"
    if nama_pendek:
        judul += ": " + " & ".join(nama_pendek[:2])
    if utama:
        t = utama["dt_mulai"].astimezone(WIB)
        deskripsi = (f"{utama['nama']}: {'sedang berlangsung' if utama['status'] == 'Berlangsung' else 'mulai'} "
                     f"{t.day} {BULAN[t.month - 1]} {t.year} pukul {t:%H.%M} WIB. "
                     f"Jadwal lengkap Steam Sale dalam WIB dan diskon terbaik hari ini dalam Rupiah.")
    else:
        deskripsi = "Jadwal Steam Sale dalam WIB dan diskon Steam terbaik hari ini dalam Rupiah."
    html = _kerangka(judul, deskripsi, url, "".join(isi), jsonld=_jsonld_jejak(situs, "Jadwal Steam Sale", url),
                     aktif="steam-sale", script=SKRIP_HITUNG_SALE)
    _tulis_jika_berubah(os.path.join(folder, "jadwal-steam-sale", "index.html"), html)
    return [(url, sekarang.date().isoformat())]
