"""
Artikel panduan untuk gamediskon.my.id.

Cara menulis artikel baru:
  1. Buat file baru di folder artikel/ di repo, misalnya artikel/kalender-steam-sale.md
  2. Isi bagian kepala seperti ini (di antara dua baris ---), lalu tulis isinya di bawahnya:

       ---
       judul: Judul yang tampil di halaman dan di Google
       deskripsi: Satu-dua kalimat ringkasan (tampil di hasil pencarian Google)
       tanggal: 2026-09-27
       diperbarui: 2026-10-05      (opsional, isi kalau artikel diubah isinya)
       draf: ya                    (opsional; selama "ya", artikel TIDAK diterbitkan)
       ---

  3. Nama file menjadi alamat halaman: artikel/kalender-steam-sale.md -> /panduan/kalender-steam-sale/

Isi artikel ditulis dengan Markdown: ## Subjudul, **tebal**, *miring*, - daftar, 1. langkah,
[teks tautan](https://alamat). Baris khusus [[gratis-epic]] diganti otomatis dengan daftar
game gratis Epic yang sedang berlaku hari itu.
"""

import glob
import os
from datetime import datetime
from html import escape

import markdown

from halaman import url_situs
from halaman_game import _jejak_sederhana, _kerangka, _tgl, _tulis_jika_berubah

FOLDER_ARTIKEL = "artikel"
PENULIS = "Sarathiel"

CSS_ARTIKEL = """
  .prosa { max-width: 68ch; }
  .prosa .meta { color: var(--redup); font-size: .95rem; margin: -.75rem 0 2rem; }
  .prosa h2 { font-size: 1.4rem; margin: 2.5rem 0 .6rem; }
  .prosa h3 { font-size: 1.1rem; margin: 1.75rem 0 .4rem; }
  .prosa p, .prosa ul, .prosa ol { margin: 0 0 1.1rem; }
  .prosa ul, .prosa ol { padding-left: 1.3rem; }
  .prosa li { margin-bottom: .45rem; }
  .prosa li::marker { color: var(--oranye); font-weight: 700; }
  .prosa a { color: var(--oranye); text-underline-offset: 3px; }
  .prosa strong { color: #fff; }
  .prosa blockquote { margin: 0 0 1.25rem; padding: .8rem 1.1rem; background: var(--panel);
                      border-left: 4px solid var(--oranye); border-radius: 0 .6rem .6rem 0; }
  .prosa blockquote p:last-child { margin-bottom: 0; }
  .prosa table { margin: 0 0 1.25rem; }
  .prosa .kotak-data { background: var(--panel); border-radius: .8rem; padding: 1rem 1.2rem; margin: 0 0 1.25rem; }
  .prosa .kotak-data p { margin: 0 0 .5rem; color: var(--redup); font-size: .9rem; }
  .prosa .kotak-data ul { margin: 0; }
  .daftar-artikel { list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--garis); max-width: 68ch; }
  .daftar-artikel li { padding: 1.1rem 0; border-bottom: 1px solid var(--garis); }
  .daftar-artikel h2 { font-size: 1.2rem; margin: 0 0 .25rem; }
  .daftar-artikel h2 a { text-decoration: none; }
  .daftar-artikel h2 a:hover { text-decoration: underline; text-decoration-color: var(--oranye); text-underline-offset: 3px; }
  .daftar-artikel p { color: var(--redup); margin: 0; }
"""


# ---------- Membaca file artikel ----------
def _baca(path):
    teks = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    kepala, isi = {}, teks
    if teks.startswith("---\n"):
        akhir = teks.find("\n---", 4)
        if akhir != -1:
            for baris in teks[4:akhir].splitlines():
                if ":" in baris:
                    k, v = baris.split(":", 1)
                    kepala[k.strip().lower()] = v.split("  (")[0].strip()
            isi = teks[akhir + 4:].lstrip("\n")
    return kepala, isi


def _artikel_valid(path):
    kepala, isi = _baca(path)
    slug = os.path.splitext(os.path.basename(path))[0].lower()
    if kepala.get("draf", "").lower() in ("ya", "yes", "true", "1"):
        return None
    wajib = [k for k in ("judul", "deskripsi", "tanggal") if not kepala.get(k)]
    if wajib:
        print(f"Artikel {path} dilewati: kepala belum lengkap ({', '.join(wajib)}).")
        return None
    try:
        for k in ("tanggal", "diperbarui"):
            if kepala.get(k):
                datetime.strptime(kepala[k], "%Y-%m-%d")
    except ValueError:
        print(f"Artikel {path} dilewati: format tanggal harus TTTT-BB-HH, misalnya 2026-09-27.")
        return None
    return {"slug": slug, "judul": kepala["judul"], "deskripsi": kepala["deskripsi"],
            "tanggal": kepala["tanggal"], "diperbarui": kepala.get("diperbarui") or kepala["tanggal"],
            "isi": isi}


# ---------- Data otomatis di dalam artikel ----------
def _blok_gratis_epic(epic_semua):
    if not epic_semua:
        return ('<div class="kotak-data"><p>Game gratis Epic minggu ini</p>'
                '<ul><li>Data minggu ini belum tersedia. Cek <a href="/">beranda</a>.</li></ul></div>')
    item = "".join(f'<li><a href="{escape(g["url"])}" rel="noopener">{escape(g["judul"])}</a>, '
                   f'klaim sebelum {escape(g["berakhir"])}</li>' for g in epic_semua)
    return (f'<div class="kotak-data"><p>Game gratis Epic yang sedang berlaku (diperbarui otomatis setiap hari)</p>'
            f'<ul>{item}</ul></div>')


def _ke_html(isi, epic_semua):
    html = markdown.markdown(isi, extensions=["extra", "sane_lists"], output_format="html")
    # Tautan keluar dibuka dengan rel="noopener"; tautan di dalam situs dibiarkan
    html = html.replace('<a href="http', '<a rel="noopener" href="http')
    return html.replace("<p>[[gratis-epic]]</p>", _blok_gratis_epic(epic_semua))


# ---------- Halaman ----------
def _html_artikel(a, situs, epic_semua):
    url = f"{situs}panduan/{a['slug']}/"
    meta = f"Ditulis oleh {escape(PENULIS)}, {_tgl(a['tanggal'])}"
    if a["diperbarui"] != a["tanggal"]:
        meta += f". Diperbarui {_tgl(a['diperbarui'])}"
    jejak = (f'    <nav class="jejak" aria-label="Lokasi halaman"><ol>'
             f'<li><a href="{escape(situs)}">Beranda</a></li>'
             f'<li><a href="/panduan/">Panduan</a></li>'
             f'<li aria-current="page">{escape(a["judul"])}</li></ol></nav>')
    badan = f"""{jejak}
    <div class="prosa">
      <article>
        <h1 class="judul-halaman">{escape(a['judul'])}</h1>
        <p class="meta">{meta}.</p>
{_ke_html(a['isi'], epic_semua)}
      </article>
    </div>"""
    jsonld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": a["judul"], "description": a["deskripsi"],
        "datePublished": a["tanggal"], "dateModified": a["diperbarui"],
        "author": {"@type": "Person", "name": PENULIS},
        "publisher": {"@type": "Organization", "name": "GameDiskon", "url": situs},
        "mainEntityOfPage": url, "inLanguage": "id",
    }
    return url, _kerangka(a["judul"], a["deskripsi"], url, badan, jsonld=jsonld, aktif="panduan", og_tipe="article")


def _html_daftar(daftar, situs):
    url = f"{situs}panduan/"
    item = "".join(f'<li><h2><a href="/panduan/{a["slug"]}/">{escape(a["judul"])}</a></h2>'
                   f'<p>{escape(a["deskripsi"])}</p></li>' for a in daftar)
    badan = f"""{_jejak_sederhana(situs, "Panduan")}
    <div>
      <h1 class="judul-halaman">Panduan berburu game murah</h1>
      <p class="catatan">Cara mendapatkan game gratis dan harga termurah di Steam dan Epic Games Store, khusus untuk pemain di Indonesia.</p>
      <ul class="daftar-artikel">{item}</ul>
    </div>"""
    deskripsi = "Panduan mendapatkan game gratis dan diskon termurah di Steam dan Epic Games Store untuk pemain di Indonesia."
    return url, _kerangka("Panduan Berburu Game Murah dan Gratis", deskripsi, url, badan, aktif="panduan")


def buat_halaman_artikel(epic_semua=None, folder="docs", folder_artikel=FOLDER_ARTIKEL):
    """Buat halaman untuk setiap artikel yang sudah terbit + halaman daftar /panduan/.
    Kembalikan (url, lastmod) untuk sitemap."""
    situs = url_situs()
    if not situs:
        return []
    daftar = [a for a in (_artikel_valid(p) for p in glob.glob(os.path.join(folder_artikel, "*.md"))) if a]
    if not daftar:
        return []
    daftar.sort(key=lambda a: a["tanggal"], reverse=True)   # terbaru di atas

    hasil = []
    for a in daftar:
        url, html = _html_artikel(a, situs, epic_semua or [])
        _tulis_jika_berubah(os.path.join(folder, "panduan", a["slug"], "index.html"), html)
        hasil.append((url, a["diperbarui"]))
    url, html = _html_daftar(daftar, situs)
    _tulis_jika_berubah(os.path.join(folder, "panduan", "index.html"), html)
    hasil.insert(0, (url, max(a["diperbarui"] for a in daftar)))
    print(f"Artikel: {len(daftar)} terbit.")
    return hasil
