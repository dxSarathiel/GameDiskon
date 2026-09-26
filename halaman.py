"""
Membuat halaman web statis (docs/index.html) untuk GitHub Pages.
Halaman menampilkan SEMUA diskon yang layak hari ini (bukan hanya yang baru
diposting), jadi selalu lengkap walaupun channel hari itu hanya memposting sedikit.
"""

import os
from datetime import datetime, timedelta, timezone
from html import escape

WIB = timezone(timedelta(hours=7))
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
MAKS_ITEM_HALAMAN = 60


def url_situs():
    """Alamat GitHub Pages, ditebak dari nama repo yang sedang menjalankan workflow."""
    repo = os.getenv("GITHUB_REPOSITORY", "")          # contoh: "sarathiel/radar-diskon"
    if "/" not in repo:
        return ""
    pemilik, nama = repo.split("/", 1)
    pemilik = pemilik.lower()
    if nama.lower() == f"{pemilik}.github.io":
        return f"https://{pemilik}.github.io/"
    return f"https://{pemilik}.github.io/{nama}/"


def _rupiah(sen):
    return "Rp " + f"{sen // 100:,}".replace(",", ".")


def _tanggal_panjang(dt):
    return f"{dt.day} {BULAN[dt.month - 1]} {dt.year}"


def _baris_steam(g, pertama):
    gambar_attr = 'fetchpriority="high"' if pertama else 'loading="lazy"'
    terendah = ""
    if g.get("terendah_sejak"):
        mulai = datetime.strptime(g["terendah_sejak"], "%Y-%m-%d")
        terendah = (f'<p class="terendah">Terendah sejak dicatat '
                    f'({mulai.day} {BULAN[mulai.month - 1][:3]} {mulai.year})</p>')
    return f"""
      <li class="baris">
        <a class="sampul" href="{escape(g['url'])}" rel="noopener" tabindex="-1" aria-hidden="true">
          <img src="{escape(g['gambar'])}" alt="" width="460" height="215" {gambar_attr} decoding="async">
        </a>
        <div class="info">
          <h3><a href="{escape(g['url'])}" rel="noopener">{escape(g['judul'])}</a></h3>
          <p class="ulasan">{escape(g['rating'])} ulasan positif di Steam</p>
          {terendah}
        </div>
        <div class="harga">
          <span class="label">-{g['diskon']}%</span>
          <span class="angka">
            <strong>{_rupiah(g['harga_akhir'])}</strong>
            <s>{_rupiah(g['harga_awal'])}</s>
          </span>
        </div>
      </li>"""


def _kartu_epic(g, pertama):
    gambar_attr = 'fetchpriority="high"' if pertama else ''
    return f"""
      <li class="gratis">
        <a href="{escape(g['url'])}" rel="noopener">
          <img src="{escape(g['gambar'])}" alt="" width="640" height="360" {gambar_attr} decoding="async">
          <span class="judul-gratis">{escape(g['judul'])}</span>
          <span class="batas">Klaim sebelum {escape(g['berakhir'])}</span>
        </a>
      </li>"""


def buat_halaman(epic, steam, folder="docs", link_telegram="", nama_channel="",
                 google_verifikasi=""):
    os.makedirs(folder, exist_ok=True)
    sekarang = datetime.now(WIB)
    situs = url_situs()
    steam = steam[:MAKS_ITEM_HALAMAN]

    judul_halaman = f"Diskon Steam Hari Ini dalam Rupiah & Game Gratis Epic ({_tanggal_panjang(sekarang)})"
    if steam:
        g0 = steam[0]
        deskripsi = (f"{len(steam)} diskon Steam pilihan dengan harga asli region Indonesia, "
                     f"mulai dari {g0['judul']} {_rupiah(g0['harga_akhir'])} (-{g0['diskon']}%). "
                     f"Diperbarui setiap hari.")
    else:
        deskripsi = "Diskon Steam pilihan dengan harga asli region Indonesia dan game gratis Epic. Diperbarui setiap hari."
    if epic:
        deskripsi = f"Gratis di Epic: {', '.join(g['judul'] for g in epic)}. " + deskripsi
    og_gambar = (epic[0]["gambar"] if epic else steam[0]["gambar"] if steam else "")

    tombol = ""
    if link_telegram:
        tombol = (f'<a class="tombol" href="https://{escape(link_telegram)}" rel="noopener">'
                  f'Ikuti di Telegram</a>')

    bagian_epic = ""
    if epic:
        kartu = "".join(_kartu_epic(g, i == 0) for i, g in enumerate(epic))
        bagian_epic = f"""
    <section aria-labelledby="h-gratis">
      <h2 id="h-gratis">Gratis di Epic Games Store</h2>
      <p class="catatan">Klaim sebelum batas waktunya dan game jadi milikmu selamanya.</p>
      <ul class="daftar-gratis">{kartu}
      </ul>
    </section>"""

    if steam:
        baris = "".join(_baris_steam(g, i == 0 and not epic) for i, g in enumerate(steam))
        bagian_steam = f"""
    <section aria-labelledby="h-steam">
      <h2 id="h-steam">Diskon Steam, harga Indonesia</h2>
      <p class="catatan">Diskon minimal 50% untuk game dengan ulasan minimal 85% positif. Harga dicek langsung ke Steam region Indonesia.</p>
      <ol class="papan">{baris}
      </ol>
    </section>"""
    else:
        bagian_steam = """
    <section aria-labelledby="h-steam">
      <h2 id="h-steam">Diskon Steam, harga Indonesia</h2>
      <p class="catatan">Belum ada diskon yang lolos saringan hari ini. Cek lagi besok sore.</p>
    </section>"""

    meta_google = (f'<meta name="google-site-verification" content="{escape(google_verifikasi)}">'
                   if google_verifikasi else "")
    kanonik = f'<link rel="canonical" href="{situs}">' if situs else ""
    og_url = f'<meta property="og:url" content="{situs}">' if situs else ""

    html = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(judul_halaman)}</title>
<meta name="description" content="{escape(deskripsi)}">
{kanonik}
{meta_google}
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(judul_halaman)}">
<meta property="og:description" content="{escape(deskripsi)}">
<meta property="og:image" content="{escape(og_gambar)}">
{og_url}
<meta name="theme-color" content="#14161f">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --latar: #14161f; --panel: #1d202b; --garis: #2a2e3b;
    --teks: #f5f5f7; --redup: #9aa0b0;
    --oranye: #ff6b35; --hijau: #2ecc71;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--latar); color: var(--teks);
    font: 400 1rem/1.6 "Poppins", system-ui, sans-serif;
  }}
  a {{ color: inherit; }}
  a:focus-visible {{ outline: 3px solid var(--oranye); outline-offset: 3px; border-radius: 4px; }}
  .wadah {{ max-width: 60rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }}

  header {{ display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: 1.5rem; margin-bottom: 3rem; }}
  .nama {{ color: var(--oranye); font-weight: 500; margin: 0 0 .25rem; }}
  h1 {{ font-size: clamp(1.9rem, 5vw, 3rem); line-height: 1.1; margin: 0; font-weight: 700; max-width: 18ch; }}
  .diperbarui {{ color: var(--redup); margin: .75rem 0 0; font-size: .95rem; }}
  .tombol {{
    display: inline-block; background: var(--oranye); color: #fff; text-decoration: none;
    font-weight: 700; padding: .8rem 1.4rem; border-radius: .6rem; white-space: nowrap;
  }}
  .tombol:hover {{ background: #ff7d4d; }}

  section {{ margin-bottom: 3.5rem; }}
  h2 {{ font-size: 1.5rem; line-height: 1.25; margin: 0; }}
  .catatan {{ color: var(--redup); margin: .25rem 0 1.25rem; max-width: 65ch; }}

  /* Game gratis: sampul besar, karena ini yang paling dicari */
  .daftar-gratis {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 1rem;
                   grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); }}
  .gratis a {{ display: block; text-decoration: none; background: var(--panel); border-radius: 1rem;
              overflow: hidden; border: 2px solid transparent; }}
  .gratis a:hover {{ border-color: var(--hijau); }}
  .gratis img {{ display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; object-fit: cover; }}
  .judul-gratis {{ display: block; font-weight: 700; font-size: 1.15rem; padding: .9rem 1rem 0; }}
  .batas {{ display: block; color: var(--hijau); font-weight: 500; padding: 0 1rem 1rem; }}

  /* Papan harga: baris-baris seperti label harga di rak toko */
  .papan {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--garis); }}
  .baris {{ display: grid; grid-template-columns: 9.5rem 1fr auto; gap: 1.25rem; align-items: center;
           padding: 1rem 0; border-bottom: 1px solid var(--garis); }}
  .sampul img {{ display: block; width: 100%; height: auto; aspect-ratio: 460 / 215; border-radius: .5rem; background: var(--panel); }}
  .info h3 {{ font-size: 1.05rem; line-height: 1.35; margin: 0; }}
  .info h3 a {{ text-decoration: none; }}
  .info h3 a:hover {{ text-decoration: underline; text-decoration-color: var(--oranye); text-underline-offset: 3px; }}
  .ulasan {{ color: var(--redup); font-size: .9rem; margin: .2rem 0 0; }}
  .terendah {{ color: var(--hijau); font-size: .9rem; font-weight: 500; margin: .2rem 0 0; }}
  .harga {{ display: flex; align-items: center; gap: .9rem; }}
  .label {{
    /* bentuk label harga: ujung kiri runcing, sama dengan logo channel */
    background: var(--oranye); color: #fff; font-weight: 700; font-size: 1.05rem;
    padding: .35rem .8rem .35rem 1.3rem;
    clip-path: polygon(.8rem 0, 100% 0, 100% 100%, .8rem 100%, 0 50%);
    border-radius: 0 .4rem .4rem 0;
  }}
  .angka {{ display: flex; flex-direction: column; align-items: flex-end; font-variant-numeric: tabular-nums; min-width: 7.5rem; }}
  .angka strong {{ font-size: 1.25rem; }}
  .angka s {{ color: var(--redup); font-size: .9rem; }}

  details {{ border-bottom: 1px solid var(--garis); padding: .9rem 0; }}
  summary {{ cursor: pointer; font-weight: 500; }}
  details p {{ color: var(--redup); margin: .6rem 0 0; max-width: 65ch; }}

  footer {{ color: var(--redup); font-size: .85rem; border-top: 1px solid var(--garis); padding-top: 1.5rem; }}

  @media (max-width: 40rem) {{
    .baris {{ grid-template-columns: 7rem 1fr; }}
    .harga {{ grid-column: 1 / -1; justify-content: space-between; }}
  }}
</style>
</head>
<body>
  <div class="wadah">
    <header>
      <div>
        <p class="nama">{escape(nama_channel)}</p>
        <h1>Diskon Steam hari ini, harga Rupiah asli</h1>
        <p class="diperbarui">Diperbarui {_tanggal_panjang(sekarang)}, pukul {sekarang:%H.%M} WIB</p>
      </div>
      {tombol}
    </header>
    <main>{bagian_epic}{bagian_steam}
    <section aria-labelledby="h-tanya">
      <h2 id="h-tanya">Pertanyaan umum</h2>
      <details>
        <summary>Kenapa harga di sini bisa beda dengan situs diskon lain?</summary>
        <p>Banyak situs menampilkan harga dolar atau hasil konversinya. Steam memakai harga regional, jadi harga di Indonesia bisa jauh berbeda, dan diskon di luar negeri belum tentu berlaku di sini. Semua harga di halaman ini dicek langsung ke Steam region Indonesia.</p>
      </details>
      <details>
        <summary>Seberapa sering halaman ini diperbarui?</summary>
        <p>Setiap hari sekitar pukul 18.00 WIB. Harga bisa berubah sewaktu-waktu, jadi selalu cek halaman toko sebelum membeli.</p>
      </details>
      <details>
        <summary>Apa arti label "Terendah sejak dicatat"?</summary>
        <p>Harga game itu sedang paling murah sejak mulai dipantau di sini. Label hanya muncul untuk game yang harganya sudah dicatat minimal 30 hari.</p>
      </details>
    </section>
    </main>
    <footer>
      <p>Data harga dari Steam (region Indonesia) dan CheapShark, game gratis dari Epic Games Store. Halaman ini tidak berafiliasi dengan Valve maupun Epic Games. Semua link mengarah ke toko resmi.</p>
    </footer>
  </div>
</body>
</html>
"""
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # Jangan proses dengan Jekyll: lebih cepat dan tidak ada aturan nama file yang aneh
    open(os.path.join(folder, ".nojekyll"), "w").close()

    if situs:
        with open(os.path.join(folder, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"  <url><loc>{situs}</loc><lastmod>{sekarang:%Y-%m-%d}</lastmod></url>\n"
                "</urlset>\n"
            )
    return os.path.join(folder, "index.html")
