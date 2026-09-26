"""
Halaman informasi situs (Tahap 3): Tentang, Kebijakan Privasi, dan Kontak.
  docs/tentang/index.html
  docs/kebijakan-privasi/index.html
  docs/kontak/index.html

Isinya jarang berubah. Kalau situs mulai memakai iklan (AdSense), link afiliasi,
atau alat statistik pengunjung, PERBARUI kebijakan privasi dan TANGGAL_BERLAKU.
"""

import os
from html import escape

from halaman import url_situs
from halaman_game import _jejak_sederhana, _kerangka, _tgl, _tulis_jika_berubah

# ---------- Pengaturan ----------
PENGELOLA = "Sarathiel"
EMAIL_KONTAK = "kontak@gamediskon.my.id"               # contoh: "kontak@gamediskon.my.id" (buat dulu di cPanel -> Email Accounts)
TANGGAL_BERLAKU = "2026-09-27"  # ubah setiap kali isi kebijakan privasi diubah


def _email_html():
    if not EMAIL_KONTAK:
        return ""
    e = escape(EMAIL_KONTAK)
    return f'<a href="mailto:{e}">{e}</a>'


def _tentang(situs, link_telegram, nama_channel):
    tg = (f' Kabar diskon baru juga dikirim setiap hari ke channel Telegram '
          f'<a href="https://{escape(link_telegram)}" rel="noopener">{escape(nama_channel)}</a>.'
          if link_telegram else "")
    return "Tentang", "Tentang GameDiskon", (
        "GameDiskon mencatat harga game Steam dalam Rupiah setiap hari dan merangkum diskon serta game gratis "
        "yang benar-benar berlaku untuk pembeli di Indonesia."
    ), f"""
      <p>GameDiskon mencatat harga game Steam langsung dari toko Steam region Indonesia setiap hari, lalu merangkum diskon dan game gratis yang benar-benar berlaku untuk pembeli di Indonesia.{tg}</p>

      <h2>Kenapa harga Rupiah?</h2>
      <p>Banyak situs diskon menampilkan harga dolar atau hasil konversinya. Steam memakai harga regional, jadi harga di Indonesia sering jauh berbeda, dan diskon di negara lain belum tentu berlaku di sini. Karena itu semua harga di situs ini diambil dari Steam region Indonesia, bukan dikonversi.</p>

      <h2>Cara kerjanya</h2>
      <p>Setiap sore, sistem otomatis mengambil daftar kandidat diskon dari CheapShark, mengecek harga Rupiah-nya satu per satu ke Steam, dan mengambil daftar game gratis dari Epic Games Store. Diskon yang ditampilkan di beranda harus memenuhi tiga syarat: potongan minimal 50% di harga Indonesia, ulasan positif minimal 85%, dan minimal 500 ulasan, supaya yang muncul memang game yang layak dibeli.</p>
      <p>Setiap perubahan harga dicatat. Dari catatan itulah halaman tiap game menampilkan harga normal, harga terendah yang pernah tercatat, dan riwayat diskonnya.</p>

      <h2>Yang perlu diketahui</h2>
      <p>Harga bisa berubah sewaktu-waktu di antara dua pengecekan, jadi selalu lihat harga di halaman toko sebelum membeli. GameDiskon tidak berafiliasi dengan Valve, Epic Games, maupun CheapShark. Semua tombol beli mengarah langsung ke toko resminya.</p>

      <h2>Pengelola</h2>
      <p>GameDiskon dikelola oleh {escape(PENGELOLA)}. Punya pertanyaan, menemukan harga yang salah, atau ingin bekerja sama? Kunjungi <a href="{situs}kontak/">halaman kontak</a>.</p>"""


def _kebijakan(situs):
    email = _email_html()
    kontak = (f"kirim email ke {email}" if email else f'gunakan <a href="{situs}kontak/">halaman kontak</a>')
    return "Kebijakan Privasi", "Kebijakan Privasi GameDiskon", (
        "Data apa yang dikumpulkan saat mengunjungi GameDiskon, layanan pihak ketiga yang dipakai, dan cara menghubungi pengelola."
    ), f"""
      <p>Berlaku sejak {_tgl(TANGGAL_BERLAKU)}. Halaman ini menjelaskan data apa yang terlibat saat kamu mengunjungi {escape(situs)} dan bagaimana data itu digunakan.</p>

      <h2>Data yang kami kumpulkan</h2>
      <p>Situs ini tidak memiliki akun, formulir pendaftaran, atau kolom komentar, dan tidak meminta data pribadi apa pun darimu. Situs ini juga tidak memasang cookie dan tidak memakai alat pelacak atau statistik pengunjung.</p>

      <h2>Catatan server</h2>
      <p>Seperti hampir semua situs web, server penyedia hosting kami secara otomatis mencatat informasi teknis setiap kunjungan, misalnya alamat IP, jenis browser, halaman yang dibuka, dan waktunya. Catatan ini digunakan untuk menjaga keamanan dan kelancaran situs, tidak dipakai untuk mengenali pengunjung, dan tidak dijual kepada siapa pun.</p>

      <h2>Layanan pihak ketiga</h2>
      <p>Untuk menampilkan halaman, browser-mu mengambil beberapa berkas langsung dari layanan lain. Saat itu, layanan tersebut menerima alamat IP dan informasi teknis browser-mu, sesuai kebijakan privasi masing-masing:</p>
      <ul>
        <li>Google Fonts (Google), untuk jenis huruf.</li>
        <li>Server gambar Steam (Valve) dan Epic Games, untuk gambar sampul game.</li>
      </ul>
      <p>Tombol dan tautan ke Steam, Epic Games Store, dan Telegram membawamu ke situs mereka. Di sana, kebijakan privasi mereka yang berlaku.</p>

      <h2>Perubahan kebijakan</h2>
      <p>Kalau kelak situs ini menambahkan iklan, tautan afiliasi, atau alat statistik pengunjung, kebijakan ini akan diperbarui lebih dulu dan tanggal berlakunya diubah.</p>

      <h2>Pertanyaan</h2>
      <p>Untuk pertanyaan tentang privasi, {kontak}.</p>"""


def _kontak(situs, link_telegram, nama_channel):
    email = _email_html()
    if email:
        utama = f"<p>Hubungi pengelola GameDiskon lewat email: {email}.</p>"
    else:
        utama = "<p>Alamat email untuk menghubungi pengelola sedang disiapkan.</p>"
    tg = (f'<p>Untuk kabar diskon harian, ikuti channel Telegram '
          f'<a href="https://{escape(link_telegram)}" rel="noopener">{escape(nama_channel)}</a>.</p>'
          if link_telegram else "")
    return "Kontak", "Hubungi GameDiskon", (
        "Cara menghubungi pengelola GameDiskon untuk pertanyaan, laporan harga yang salah, atau kerja sama."
    ), f"""
      {utama}

      <h2>Yang bisa kamu sampaikan</h2>
      <ul>
        <li>Harga atau diskon yang tampil salah atau sudah tidak berlaku.</li>
        <li>Saran game yang sebaiknya ikut dipantau.</li>
        <li>Pertanyaan tentang privasi atau isi situs.</li>
        <li>Tawaran kerja sama.</li>
      </ul>
      {tg}"""


CSS_PROSA = """
  .prosa { max-width: 65ch; }
  .prosa h2 { margin: 2.25rem 0 .5rem; }
  .prosa p, .prosa ul { margin: 0 0 1rem; }
  .prosa ul { padding-left: 1.2rem; }
  .prosa li { margin-bottom: .35rem; }
  .prosa a { color: var(--oranye); text-underline-offset: 3px; }
"""


def buat_halaman_info(folder="docs", link_telegram="", nama_channel=""):
    """Buat halaman Tentang, Kebijakan Privasi, Kontak. Kembalikan (url, lastmod) untuk sitemap."""
    situs = url_situs()
    if not situs:
        return []
    halaman = {
        "tentang": _tentang(situs, link_telegram, nama_channel),
        "kebijakan-privasi": _kebijakan(situs),
        "kontak": _kontak(situs, link_telegram, nama_channel),
    }
    hasil = []
    for jalur, (nama, judul, deskripsi, isi) in halaman.items():
        url = f"{situs}{jalur}/"
        badan = f"""{_jejak_sederhana(situs, nama)}
    <main class="prosa">
      <h1>{escape(judul)}</h1>
{isi}
    </main>"""
        html = _kerangka(judul, deskripsi, url, badan, css_tambahan=CSS_PROSA)
        _tulis_jika_berubah(os.path.join(folder, jalur, "index.html"), html)
        hasil.append((url, TANGGAL_BERLAKU))
    return hasil
