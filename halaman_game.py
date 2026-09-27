"""
Halaman per game untuk gamediskon.my.id (Tahap 2).

Dari data harga_idr.json dibuat:
  docs/game/<appid>-<slug>/index.html  -> harga sekarang, harga normal, terendah tercatat, riwayat
  docs/game/index.html                  -> daftar semua game yang dipantau

Isi halaman game hanya berubah kalau harganya berubah, supaya upload harian tetap ringan.
Game yang datanya masih sedikit diberi tanda "noindex" dan belum masuk sitemap,
supaya Google tidak menilai situs ini penuh halaman tipis.
"""

import json
import os
import re
import unicodedata
from datetime import datetime
from html import escape

from gaya import USERNAME_BOT_ALARM, halaman_utuh, kepala, pita, tulis_css
from halaman import BULAN, WIB, _rupiah, url_situs

try:
    from afiliasi import blok_halaman_game
except Exception as err:          # afiliasi.py bermasalah: halaman tetap dibuat tanpa kotak voucher
    print("afiliasi.py bermasalah, kotak voucher dilewati:", err)

    def blok_halaman_game(harga_sen):
        return ""

MIN_HARI_INDEKS = 14        # halaman game boleh diindeks Google setelah datanya >= sekian hari
BATAS_TIDAK_DIPANTAU = 3    # kalau tidak dicek selama > sekian hari, tampilkan pemberitahuan


# ---------- Alamat halaman ----------
def buat_slug(nama):
    """'Ori and the Will of the Wisps' -> 'ori-and-the-will-of-the-wisps'"""
    teks = unicodedata.normalize("NFKD", nama or "").encode("ascii", "ignore").decode()
    teks = re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-")
    return teks[:60].rstrip("-")


def jalur_game(appid, slug):
    """Alamat relatif dari akar situs, misalnya 'game/1057090-ori-and-the-will-of-the-wisps/'."""
    return f"game/{appid}-{slug}/" if slug else f"game/{appid}/"


# ---------- Bantuan tanggal ----------
def _tgl(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def _hari_sejak(iso, hari_ini):
    return (hari_ini - datetime.strptime(iso, "%Y-%m-%d").date()).days


# ---------- Ringkasan data satu game ----------
def ringkas(appid, g):
    """Olah catatan mentah satu game menjadi angka-angka yang ditampilkan."""
    riwayat = sorted(g.get("riwayat") or [], key=lambda e: e[0])
    if not riwayat:
        return None
    tgl_kini, harga_kini, diskon_kini = riwayat[-1]
    harga_terendah = min(e[1] for e in riwayat)
    entri_terendah = next(e for e in riwayat if e[1] == harga_terendah)
    normal = g.get("normal")
    if not normal:
        # Harga tanpa diskon yang pernah tercatat, kalau ada
        tanpa_diskon = [e[1] for e in riwayat if e[2] == 0]
        normal = tanpa_diskon[-1] if tanpa_diskon else None
    return {
        "appid": appid,
        "nama": g.get("nama") or f"Steam App {appid}",
        "slug": g.get("slug") or buat_slug(g.get("nama")),
        "mulai": g.get("mulai") or riwayat[0][0],
        "cek": g.get("cek") or tgl_kini,
        "riwayat": riwayat,
        "tgl_kini": tgl_kini,
        "harga_kini": harga_kini,
        "diskon_kini": diskon_kini,
        "normal": normal,
        "harga_terendah": harga_terendah,
        "tgl_terendah": entri_terendah[0],
        "diskon_terendah": entri_terendah[2],
        "pernah_berubah": len({e[1] for e in riwayat}) > 1,
    }


# ---------- Kerangka halaman (tampilan dari gaya.py) ----------
def _kerangka(judul, deskripsi, kanonik, isi, og_gambar="", noindex=False, jsonld=None,
              css_tambahan="", aktif="", script="", og_tipe="website"):
    """css_tambahan tidak dipakai lagi (semua gaya ada di gaya.py); dibiarkan supaya kode lama tetap jalan."""
    head = kepala(judul, deskripsi, kanonik=kanonik, og_gambar=og_gambar, noindex=noindex, jsonld=jsonld,
                  og_tipe=og_tipe)
    return halaman_utuh(head, pita(aktif=aktif), isi, script=script)


def _jejak_sederhana(situs, nama):
    return (f'    <nav class="jejak" aria-label="Lokasi halaman"><ol>'
            f'<li><a href="/">Beranda</a></li><li aria-current="page">{escape(nama)}</li></ol></nav>')


def _jejak(situs, nama=None):
    li = ['<li><a href="/">Beranda</a></li>', '<li><a href="/game/">Semua game</a></li>']
    if nama:
        li.append(f'<li aria-current="page">{escape(nama)}</li>')
    return f'    <nav class="jejak" aria-label="Lokasi halaman"><ol>{"".join(li)}</ol></nav>'


def _jsonld_jejak(situs, nama, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Beranda", "item": situs},
            {"@type": "ListItem", "position": 2, "name": "Semua game", "item": f"{situs}game/"},
            {"@type": "ListItem", "position": 3, "name": nama, "item": url},
        ],
    }


# ---------- Halaman satu game ----------
def _html_game(r, situs, link_telegram, hari_ini):
    url = situs + jalur_game(r["appid"], r["slug"])
    nama = r["nama"]
    gambar = f"https://cdn.akamai.steamstatic.com/steam/apps/{r['appid']}/header.jpg"
    toko = f"https://store.steampowered.com/app/{r['appid']}/"
    kini, normal, diskon = r["harga_kini"], r["normal"], r["diskon_kini"]

    # Stiker harga besar
    coret = f"<s>{_rupiah(normal)}</s>" if diskon > 0 and normal and normal > kini else ""
    potong = f'<span class="potong">-{diskon}%</span>' if diskon > 0 else ""
    stiker = (f'<p class="stiker">{potong}<span class="harga"><strong>{_rupiah(kini)}</strong>{coret}</span></p>')
    if diskon > 0:
        kalimat = f"{nama} sedang diskon {diskon}% di Steam Indonesia."
    else:
        kalimat = f"{nama} sedang tidak diskon di Steam Indonesia."

    baik = False
    if r["pernah_berubah"] and kini <= r["harga_terendah"]:
        kalimat += " Ini harga termurah sejak mulai kami pantau."
        baik = True
    elif r["pernah_berubah"]:
        kalimat += (f" Harga termurah yang pernah tercatat adalah {_rupiah(r['harga_terendah'])}"
                    f" pada {_tgl(r['tgl_terendah'])}.")

    if diskon > 0:
        deskripsi = (f"Harga {nama} di Steam Indonesia: {_rupiah(kini)} (diskon {diskon}%). "
                     f"Lihat harga normal, harga terendah yang pernah tercatat, dan riwayat diskonnya dalam Rupiah.")
    else:
        deskripsi = (f"Harga {nama} di Steam Indonesia: {_rupiah(kini)}. "
                     f"Lihat harga terendah yang pernah tercatat dan riwayat diskonnya dalam Rupiah.")
    judul = f"Harga {nama} di Steam Indonesia & Riwayat Diskon"

    peringatan = ""
    if _hari_sejak(r["cek"], hari_ini) > BATAS_TIDAK_DIPANTAU:
        peringatan = (f'\n    <p class="peringatan">Harga game ini tidak lagi dicek harian sejak {_tgl(r["cek"])}. '
                      f'Harga di bawah mungkin sudah berubah, cek langsung di Steam.</p>')

    fakta_normal = _rupiah(normal) if normal else "Belum tercatat"
    if r["pernah_berubah"]:
        keterangan = _tgl(r["tgl_terendah"])
        if r["diskon_terendah"]:
            keterangan += f", diskon {r['diskon_terendah']}%"
        fakta_terendah = f"{_rupiah(r['harga_terendah'])}<small>{keterangan}</small>"
    else:
        fakta_terendah = f"{_rupiah(r['harga_terendah'])}<small>belum pernah berubah</small>"

    # Struk riwayat harga: yang terbaru di atas
    baris = []
    for tgl, harga, dsk in reversed(r["riwayat"]):
        ket = f'<span class="turun">-{dsk}%</span>' if dsk else '<span class="normal">normal</span>'
        baris.append(f'<tr><td>{_tgl(tgl)}</td><td class="angka">{ket}</td>'
                     f'<td class="angka"><strong>{_rupiah(harga)}</strong></td></tr>')

    if USERNAME_BOT_ALARM:
        # Membuka bot dengan game ini langsung terpilih (/start <appid>)
        tombol_tg = (f'<a class="tombol kedua" href="https://t.me/{escape(USERNAME_BOT_ALARM)}?start={r["appid"]}" rel="noopener">'
                     f'🔔 Pasang alarm harga</a>')
    elif link_telegram:
        tombol_tg = (f'<a class="tombol kedua" href="https://{escape(link_telegram)}" rel="noopener">'
                     f'Ikuti kabar diskon di Telegram</a>')
    else:
        tombol_tg = ""

    isi = f"""{_jejak(situs, nama)}
    <h1 class="judul-halaman">Harga {escape(nama)} di Steam Indonesia</h1>{peringatan}
    <div class="produk">
      <img src="{escape(gambar)}" alt="{escape(nama)}" width="460" height="215" fetchpriority="high" decoding="async">
      <div>
        {stiker}
        <p class="kalimat{' baik' if baik else ''}">{escape(kalimat)}</p>
        <a class="tombol" href="{escape(toko)}" rel="noopener">Buka di Steam</a>{tombol_tg}
      </div>
    </div>
    <dl class="fakta">
      <div><dt>Harga normal</dt><dd>{fakta_normal}</dd></div>
      <div><dt>Termurah tercatat</dt><dd>{fakta_terendah}</dd></div>
      <div><dt>Dipantau sejak</dt><dd>{_tgl(r['mulai'])}</dd></div>
    </dl>{blok_halaman_game(kini)}
    <section class="struk" aria-labelledby="h-riwayat">
      <h2 id="h-riwayat">Riwayat harga</h2>
      <p class="catatan">Setiap baris adalah hari ketika harganya berubah. Dicek setiap hari.</p>
      <table>
        <thead><tr><th scope="col">Tanggal</th><th scope="col" class="angka">Diskon</th><th scope="col" class="angka">Harga</th></tr></thead>
        <tbody>{"".join(baris)}</tbody>
        <tfoot><tr><td colspan="2">Termurah tercatat</td><td class="angka">{_rupiah(r['harga_terendah'])}</td></tr></tfoot>
      </table>
    </section>"""
    noindex = _hari_sejak(r["mulai"], hari_ini) < MIN_HARI_INDEKS
    return url, _kerangka(judul, deskripsi, url, isi, og_gambar=gambar, noindex=noindex,
                          jsonld=_jsonld_jejak(situs, nama, url), aktif="game"), noindex


# ---------- Halaman daftar semua game ----------
SKRIP_CARI = """<script>
(function () {
  var kotak = document.querySelector('.cari'), input = kotak && kotak.querySelector('input');
  if (!input) return;
  kotak.hidden = false;
  var baris = document.querySelectorAll('.daftar li'), info = document.querySelector('.hasil-saring');
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase(), n = 0;
    baris.forEach(function (li) {
      var cocok = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
      li.hidden = !cocok; if (cocok) n++;
    });
    info.textContent = q ? n + ' game ditemukan.' : '';
  });
})();
</script>"""


def _html_daftar(semua, situs):
    url = f"{situs}game/"
    urut = sorted(semua, key=lambda r: r["nama"].casefold())
    item = []
    for r in urut:
        harga = _rupiah(r["harga_kini"])
        if r["diskon_kini"]:
            harga = f'<b>-{r["diskon_kini"]}%</b>{harga}'
        item.append(f'<li><a href="/{jalur_game(r["appid"], r["slug"])}">{escape(r["nama"])}</a>'
                    f'<span class="harga">{harga}</span></li>')
    judul = "Daftar Game yang Dipantau Harganya di Steam Indonesia"
    deskripsi = (f"{len(urut)} game Steam yang harganya dicek setiap hari dalam Rupiah. "
                 f"Buka halaman tiap game untuk melihat harga terendah dan riwayat diskonnya.")
    isi = f"""{_jejak(situs)}
    <h1 class="judul-halaman">Semua game yang dipantau</h1>
    <p class="catatan">{len(urut)} game, diurutkan menurut nama. Harganya harga terakhir yang tercatat di Steam region Indonesia. Buka salah satu untuk melihat riwayat harganya.</p>
    <label class="cari" hidden>
      <span class="catatan">Cari nama game</span>
      <input type="search" placeholder="Misalnya: Hades" autocomplete="off">
    </label>
    <p class="hasil-saring" aria-live="polite"></p>
    <ul class="daftar">{"".join(item)}</ul>"""
    return url, _kerangka(judul, deskripsi, url, isi, aktif="game", script=SKRIP_CARI)


# ---------- Titik masuk ----------
def _tulis_jika_berubah(path, isi):
    """Tulis file hanya kalau isinya berbeda, supaya upload FTP dan commit tetap kecil."""
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == isi:
                return False
    except FileNotFoundError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(isi)
    return True


def _tulis_data_harga(semua, folder):
    """docs/data/harga.json: harga terbaru semua game, dibaca bot alarm harga di hosting.
    Isinya sama dengan yang tampil di halaman publik (tidak ada data pengguna)."""
    data = {
        "diperbarui": datetime.now(WIB).strftime("%Y-%m-%d %H:%M WIB"),
        "kolom": ["nama", "slug", "harga", "normal", "diskon", "termurah"],
        "game": {r["appid"]: [r["nama"], r["slug"], r["harga_kini"], r["normal"] or 0,
                              r["diskon_kini"], r["harga_terendah"]] for r in semua},
    }
    os.makedirs(os.path.join(folder, "data"), exist_ok=True)
    with open(os.path.join(folder, "data", "harga.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def buat_halaman_game(riwayat, folder="docs", link_telegram=""):
    """Buat semua halaman game + halaman daftar.
    Kembalikan daftar (url, lastmod) halaman yang boleh diindeks, untuk sitemap."""
    situs = url_situs()
    if not situs:
        return []
    tulis_css(folder)
    hari_ini = datetime.now(WIB).date()
    semua, untuk_sitemap, jumlah_berubah = [], [], 0
    for appid, g in riwayat.items():
        r = ringkas(appid, g)
        if not r:
            continue
        semua.append(r)
        url, html, noindex = _html_game(r, situs, link_telegram, hari_ini)
        path = os.path.join(folder, jalur_game(appid, r["slug"]), "index.html")
        jumlah_berubah += _tulis_jika_berubah(path, html)
        if not noindex:
            untuk_sitemap.append((url, r["tgl_kini"]))

    if semua:
        _tulis_data_harga(semua, folder)
        url, html = _html_daftar(semua, situs)
        _tulis_jika_berubah(os.path.join(folder, "game", "index.html"), html)
        terbaru = max(r["tgl_kini"] for r in semua)
        untuk_sitemap.insert(0, (url, terbaru))

    print(f"Halaman game: {len(semua)} game, {jumlah_berubah} halaman baru/berubah, "
          f"{len(untuk_sitemap)} masuk sitemap.")
    return untuk_sitemap
