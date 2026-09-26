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

from halaman import BULAN, WIB, _rupiah, url_situs

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


# ---------- Gaya bersama (warna dan huruf sama dengan halaman utama) ----------
CSS = """
  :root {
    --latar: #14161f; --panel: #1d202b; --garis: #2a2e3b;
    --teks: #f5f5f7; --redup: #9aa0b0;
    --oranye: #ff6b35; --hijau: #2ecc71;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--latar); color: var(--teks);
         font: 400 1rem/1.6 "Poppins", system-ui, sans-serif; }
  a { color: inherit; }
  a:focus-visible { outline: 3px solid var(--oranye); outline-offset: 3px; border-radius: 4px; }
  .wadah { max-width: 60rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }

  .jejak { font-size: .9rem; color: var(--redup); margin: 0 0 2rem; }
  .jejak ol { list-style: none; display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; }
  .jejak li + li::before { content: "/"; margin-right: .4rem; color: var(--garis); }
  .jejak a { text-decoration: none; }
  .jejak a:hover { color: var(--teks); }

  h1 { font-size: clamp(1.7rem, 4.5vw, 2.6rem); line-height: 1.15; margin: 0 0 1.5rem; max-width: 22ch; }
  h2 { font-size: 1.35rem; line-height: 1.25; margin: 0 0 .25rem; }
  section { margin-bottom: 3rem; }
  .catatan { color: var(--redup); margin: .25rem 0 1.25rem; max-width: 65ch; }

  /* Bagian atas: sampul + label harga besar, bentuk label sama dengan logo channel */
  .utama { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 1.75rem; align-items: center; margin-bottom: 1.5rem; }
  .utama img { display: block; width: 100%; height: auto; aspect-ratio: 460 / 215; border-radius: .6rem; background: var(--panel); }
  .label-besar {
    display: inline-flex; align-items: baseline; gap: .8rem; flex-wrap: wrap;
    background: var(--panel); padding: .9rem 1.4rem .9rem 2.4rem;
    clip-path: polygon(1.3rem 0, 100% 0, 100% 100%, 1.3rem 100%, 0 50%);
    border-radius: 0 .6rem .6rem 0;
  }
  .label-besar.diskon { background: var(--oranye); color: #fff; }
  .label-besar strong { font-size: clamp(1.6rem, 4vw, 2.2rem); line-height: 1.1; font-variant-numeric: tabular-nums; }
  .label-besar span { font-weight: 700; }
  .label-besar s { opacity: .85; font-variant-numeric: tabular-nums; }
  .kalimat { margin: 1rem 0 0; max-width: 55ch; }
  .kalimat.baik { color: var(--hijau); font-weight: 500; }
  .tombol { display: inline-block; margin-top: 1.25rem; background: var(--oranye); color: #fff; text-decoration: none;
            font-weight: 700; padding: .75rem 1.3rem; border-radius: .6rem; }
  .tombol:hover { background: #ff7d4d; }
  .tombol.kedua { background: transparent; color: var(--teks); border: 2px solid var(--garis); margin-left: .5rem; }
  .tombol.kedua:hover { border-color: var(--oranye); }

  .fakta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0 0 3rem; border-top: 1px solid var(--garis); border-bottom: 1px solid var(--garis); }
  .fakta div { padding: 1rem 1rem 1rem 0; }
  .fakta div + div { padding-left: 1rem; border-left: 1px solid var(--garis); }
  .fakta dt { color: var(--redup); font-size: .9rem; }
  .fakta dd { margin: .15rem 0 0; font-weight: 700; font-size: 1.15rem; font-variant-numeric: tabular-nums; }
  .fakta dd small { display: block; font-weight: 400; font-size: .85rem; color: var(--redup); }

  .peringatan { background: var(--panel); border-left: 4px solid var(--oranye); border-radius: 0 .6rem .6rem 0;
                padding: .8rem 1rem; margin: 0 0 2rem; max-width: 65ch; }

  table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
  th, td { text-align: left; padding: .7rem .5rem .7rem 0; border-bottom: 1px solid var(--garis); }
  th { color: var(--redup); font-weight: 500; font-size: .9rem; }
  td.angka, th.angka { text-align: right; padding-right: 0; }
  .potong { color: var(--oranye); font-weight: 700; }

  /* Daftar semua game */
  .daftar { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--garis); }
  .daftar li { display: flex; justify-content: space-between; gap: 1rem; padding: .75rem 0; border-bottom: 1px solid var(--garis); }
  .daftar a { text-decoration: none; }
  .daftar a:hover { text-decoration: underline; text-decoration-color: var(--oranye); text-underline-offset: 3px; }
  .daftar .harga { white-space: nowrap; font-variant-numeric: tabular-nums; }

  footer { color: var(--redup); font-size: .85rem; border-top: 1px solid var(--garis); padding-top: 1.5rem; }
  .tautan-kaki { list-style: none; display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; margin: 0 0 1rem; padding: 0; }
  .tautan-kaki a { text-underline-offset: 3px; }
  .tautan-kaki a:hover { color: var(--teks); }

  @media (max-width: 40rem) {
    .utama { grid-template-columns: 1fr; }
    .fakta { grid-template-columns: 1fr; }
    .fakta div + div { padding-left: 0; border-left: 0; border-top: 1px solid var(--garis); }
    .tombol.kedua { margin-left: 0; }
  }
"""


def _kerangka(judul, deskripsi, kanonik, isi, og_gambar="", noindex=False, jsonld=None, css_tambahan=""):
    robots = '<meta name="robots" content="noindex, follow">' if noindex else ""
    data = (f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
            if jsonld else "")
    og = f'<meta property="og:image" content="{escape(og_gambar)}">' if og_gambar else ""
    return f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(judul)}</title>
<meta name="description" content="{escape(deskripsi)}">
<link rel="canonical" href="{escape(kanonik)}">
{robots}
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(judul)}">
<meta property="og:description" content="{escape(deskripsi)}">
<meta property="og:url" content="{escape(kanonik)}">
{og}
<meta name="theme-color" content="#14161f">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}{css_tambahan}</style>
{data}
</head>
<body>
  <div class="wadah">
{isi}
    <footer>
      {TAUTAN_KAKI}
      <p>Harga dicek setiap hari langsung ke Steam region Indonesia. Situs ini tidak berafiliasi dengan Valve maupun Epic Games. Selalu cek halaman toko sebelum membeli.</p>
    </footer>
  </div>
</body>
</html>
"""


# Tautan di kaki setiap halaman (juga dipakai halaman.py untuk beranda)
TAUTAN_KAKI = ('<ul class="tautan-kaki">'
               '<li><a href="/game/">Semua game</a></li>'
               '<li><a href="/tentang/">Tentang</a></li>'
               '<li><a href="/kebijakan-privasi/">Kebijakan Privasi</a></li>'
               '<li><a href="/kontak/">Kontak</a></li>'
               '</ul>')


def _jejak_sederhana(situs, nama):
    return (f'    <nav class="jejak" aria-label="Lokasi halaman"><ol>'
            f'<li><a href="{escape(situs)}">Beranda</a></li><li aria-current="page">{escape(nama)}</li></ol></nav>')


def _jejak(situs, nama=None):
    item = [(situs, "Beranda"), (f"{situs}game/", "Semua game")]
    li = [f'<li><a href="{escape(u)}">{escape(t)}</a></li>' for u, t in item]
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

    # Label harga besar
    if diskon > 0:
        coret = f"<s>{_rupiah(normal)}</s>" if normal and normal > kini else ""
        label = (f'<p class="label-besar diskon"><strong>{_rupiah(kini)}</strong>'
                 f'<span>-{diskon}%</span>{coret}</p>')
        kalimat = f"{nama} sedang diskon {diskon}% di Steam Indonesia."
    else:
        label = f'<p class="label-besar"><strong>{_rupiah(kini)}</strong></p>'
        kalimat = f"{nama} sedang tidak diskon di Steam Indonesia."

    # Kalimat tentang harga terendah
    baik = False
    if r["pernah_berubah"] and kini <= r["harga_terendah"]:
        kalimat += " Ini harga terendah sejak mulai kami pantau."
        baik = True
    elif r["pernah_berubah"]:
        kalimat += (f" Harga terendah yang pernah tercatat adalah {_rupiah(r['harga_terendah'])}"
                    f" pada {_tgl(r['tgl_terendah'])}.")

    # Deskripsi untuk Google
    if diskon > 0:
        deskripsi = (f"Harga {nama} di Steam Indonesia: {_rupiah(kini)} (diskon {diskon}%). "
                     f"Lihat harga normal, harga terendah yang pernah tercatat, dan riwayat diskonnya dalam Rupiah.")
    else:
        deskripsi = (f"Harga {nama} di Steam Indonesia: {_rupiah(kini)}. "
                     f"Lihat harga terendah yang pernah tercatat dan riwayat diskonnya dalam Rupiah.")
    judul = f"Harga {nama} di Steam Indonesia & Riwayat Diskon"

    # Pemberitahuan kalau game ini sudah lama tidak dicek
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

    baris = []
    for tgl, harga, dsk in reversed(r["riwayat"]):
        potong = f'<span class="potong">-{dsk}%</span>' if dsk else "Harga normal"
        baris.append(f"<tr><td>{_tgl(tgl)}</td><td class=\"angka\">{_rupiah(harga)}</td>"
                     f"<td class=\"angka\">{potong}</td></tr>")

    tombol_tg = (f'<a class="tombol kedua" href="https://{escape(link_telegram)}" rel="noopener">'
                 f'Dapat kabar diskon di Telegram</a>') if link_telegram else ""

    isi = f"""{_jejak(situs, nama)}
    <main>
    <h1>Harga {escape(nama)} di Steam Indonesia</h1>{peringatan}
    <div class="utama">
      <img src="{escape(gambar)}" alt="" width="460" height="215" fetchpriority="high" decoding="async">
      <div>
        {label}
        <p class="kalimat{' baik' if baik else ''}">{escape(kalimat)}</p>
        <a class="tombol" href="{escape(toko)}" rel="noopener">Buka di Steam</a>{tombol_tg}
      </div>
    </div>
    <dl class="fakta">
      <div><dt>Harga normal</dt><dd>{fakta_normal}</dd></div>
      <div><dt>Terendah tercatat</dt><dd>{fakta_terendah}</dd></div>
      <div><dt>Dipantau sejak</dt><dd>{_tgl(r['mulai'])}</dd></div>
    </dl>
    <section aria-labelledby="h-riwayat">
      <h2 id="h-riwayat">Riwayat harga</h2>
      <p class="catatan">Setiap baris adalah hari ketika harganya berubah. Harga dicek setiap hari; halaman ini diperbarui saat harganya berubah.</p>
      <table>
        <thead><tr><th scope="col">Tanggal</th><th scope="col" class="angka">Harga</th><th scope="col" class="angka">Diskon</th></tr></thead>
        <tbody>{"".join(baris)}</tbody>
      </table>
    </section>
    </main>"""
    noindex = _hari_sejak(r["mulai"], hari_ini) < MIN_HARI_INDEKS
    return url, _kerangka(judul, deskripsi, url, isi, og_gambar=gambar, noindex=noindex,
                          jsonld=_jsonld_jejak(situs, nama, url)), noindex


# ---------- Halaman daftar semua game ----------
def _html_daftar(semua, situs):
    url = f"{situs}game/"
    urut = sorted(semua, key=lambda r: r["nama"].casefold())
    item = []
    for r in urut:
        harga = _rupiah(r["harga_kini"])
        if r["diskon_kini"]:
            harga = f'<span class="potong">-{r["diskon_kini"]}%</span> {harga}'
        item.append(f'<li><a href="/{jalur_game(r["appid"], r["slug"])}">{escape(r["nama"])}</a>'
                    f'<span class="harga">{harga}</span></li>')
    judul = "Daftar Game yang Dipantau Harganya di Steam Indonesia"
    deskripsi = (f"{len(urut)} game Steam yang harganya dicek setiap hari dalam Rupiah. "
                 f"Buka halaman tiap game untuk melihat harga terendah dan riwayat diskonnya.")
    isi = f"""{_jejak(situs)}
    <main>
    <h1>Semua game yang dipantau</h1>
    <section>
      <p class="catatan">{len(urut)} game, diurutkan menurut nama. Harga di bawah adalah harga terakhir yang tercatat di Steam region Indonesia; buka halaman game untuk melihat harga terendah dan riwayatnya.</p>
      <ul class="daftar">{"".join(item)}</ul>
    </section>
    </main>"""
    return url, _kerangka(judul, deskripsi, url, isi)


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


def buat_halaman_game(riwayat, folder="docs", link_telegram=""):
    """Buat semua halaman game + halaman daftar.
    Kembalikan daftar (url, lastmod) halaman yang boleh diindeks, untuk sitemap."""
    situs = url_situs()
    if not situs:
        return []
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
        url, html = _html_daftar(semua, situs)
        _tulis_jika_berubah(os.path.join(folder, "game", "index.html"), html)
        terbaru = max(r["tgl_kini"] for r in semua)
        untuk_sitemap.insert(0, (url, terbaru))

    print(f"Halaman game: {len(semua)} game, {jumlah_berubah} halaman baru/berubah, "
          f"{len(untuk_sitemap)} masuk sitemap.")
    return untuk_sitemap
