"""
Membuat halaman web statis (docs/index.html, sitemap.xml, robots.txt, .htaccess).
Halaman per game dibuat terpisah oleh halaman_game.py
yang di-upload ke hosting gamediskon.my.id.
Halaman menampilkan SEMUA diskon yang layak hari ini (bukan hanya yang baru
diposting), jadi selalu lengkap walaupun channel hari itu hanya memposting sedikit.
"""

import os
from datetime import datetime, timedelta, timezone
from html import escape

from gaya import USERNAME_BOT_ALARM, halaman_utuh, kepala, pita, tulis_css

try:
    from afiliasi import blok_beranda
except Exception as err:          # afiliasi.py bermasalah: beranda tetap dibuat tanpa ajakan voucher
    print("afiliasi.py bermasalah, ajakan voucher dilewati:", err)

    def blok_beranda():
        return ""

WIB = timezone(timedelta(hours=7))
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MAKS_ITEM_HALAMAN = 60


# Alamat situs utama. Dipakai untuk tautan kanonik, sitemap, dan link di postingan Telegram.
ALAMAT_SITUS = "https://gamediskon.my.id/"
# .htaccess: pengalihan http/www ke alamat utama. Ubah ke False kalau hosting bermasalah.
BUAT_HTACCESS = True


def url_situs():
    """Alamat situs utama (domain sendiri di hosting Rumahweb)."""
    return ALAMAT_SITUS


def _tulis_htaccess(folder, situs):
    """Pengaturan server Apache di hosting: alihkan http:// dan www ke alamat utama,
    dan sembunyikan daftar isi folder. Hanya dibuat kalau alamat situs memakai https."""
    if not BUAT_HTACCESS or not situs.startswith("https://"):
        return
    host = situs[len("https://"):].strip("/")
    host_regex = host.replace(".", "\\.")
    isi = f"""# Dibuat otomatis oleh halaman.py setiap hari. Perubahan manual akan tertimpa.

# Jangan tampilkan daftar isi folder kepada pengunjung
Options -Indexes

<IfModule mod_rewrite.c>
RewriteEngine On

# Pemeriksaan sertifikat HTTPS (AutoSSL) jangan dialihkan
RewriteRule ^\\.well-known/ - [L]

# www.{host} -> {host}
RewriteCond %{{HTTP_HOST}} !^{host_regex}$ [NC]
RewriteCond %{{HTTP_HOST}} ^www\\. [NC]
RewriteRule ^ https://{host}%{{REQUEST_URI}} [L,R=301]

# http:// -> https://
RewriteCond %{{HTTPS}} !=on
RewriteCond %{{HTTP:X-Forwarded-Proto}} !=https
RewriteRule ^ https://{host}%{{REQUEST_URI}} [L,R=301]
</IfModule>
"""
    with open(os.path.join(folder, ".htaccess"), "w", encoding="utf-8") as f:
        f.write(isi)


def _rupiah(sen):
    return "Rp " + f"{sen // 100:,}".replace(",", ".")


def _tanggal_panjang(dt):
    return f"{dt.day} {BULAN[dt.month - 1]} {dt.year}"


def _tgl_pendek(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} {BULAN[d.month - 1][:3]} {d.year}"


def _barang_steam(g, urutan):
    """Satu barang di rak: sampul, nama, ulasan, dan label harga kuning di tepi rak."""
    gambar_attr = 'fetchpriority="high"' if urutan == 0 else 'loading="lazy"'
    tujuan = f'/{g["halaman"]}' if g.get("halaman") else g["url"]
    rel = '' if g.get("halaman") else ' rel="noopener"'
    terendah = ""
    if g.get("terendah_sejak"):
        terendah = f'<p class="terendah">Termurah sejak {_tgl_pendek(g["terendah_sejak"])}</p>'
    rating = int(str(g["rating"]).rstrip("%") or 0)
    return f"""
      <li class="barang" data-urut="{urutan}" data-harga="{g['harga_akhir']}" data-diskon="{g['diskon']}"
          data-ulasan="{rating}" data-terendah="{1 if g.get('terendah_sejak') else 0}">
        <a href="{escape(tujuan)}"{rel}>
          <img src="{escape(g['gambar'])}" alt="" width="460" height="215" {gambar_attr} decoding="async">
          <h3>{escape(g['judul'])}</h3>
          <p class="ulasan">{rating}% ulasan positif</p>
          {terendah}
        </a>
        <a class="beli" href="{escape(g['url'])}" rel="noopener">Beli di Steam</a>
        <div class="label-rak">
          <div>
            <span class="potong">-{g['diskon']}%</span>
            <span class="harga"><strong>{_rupiah(g['harga_akhir'])}</strong><s>{_rupiah(g['harga_awal'])}</s></span>
          </div>
        </div>
      </li>"""


def _kartu_epic(g, pertama):
    gambar_attr = 'fetchpriority="high"' if pertama else ''
    iso = g.get("berakhir_iso", "")
    return f"""
      <li>
        <a href="{escape(g['url'])}" rel="noopener">
          <span class="stempel" aria-hidden="true">GRATIS</span>
          <img src="{escape(g['gambar'])}" alt="" width="640" height="360" {gambar_attr} decoding="async">
          <h3>{escape(g['judul'])}</h3>
          <p class="batas">Klaim sebelum {escape(g['berakhir'])}<span class="sisa" data-berakhir="{escape(iso)}"></span></p>
        </a>
      </li>"""


# Skrip kecil: hitung mundur game gratis, dan tombol saring/urut di rak diskon.
# Tanpa JavaScript halaman tetap lengkap; tombolnya saja yang tidak muncul.
SKRIP_BERANDA = """<script>
(function () {
  // Hitung mundur batas klaim game gratis
  document.querySelectorAll('.sisa[data-berakhir]').forEach(function (el) {
    var akhir = Date.parse(el.dataset.berakhir);
    if (!akhir) return;
    var ms = akhir - Date.now();
    if (ms <= 0) { el.textContent = '. Sudah berakhir.'; return; }
    var jam = Math.floor(ms / 36e5), hari = Math.floor(jam / 24);
    el.textContent = hari > 0 ? '. Sisa ' + hari + ' hari ' + (jam % 24) + ' jam.' : '. Sisa ' + jam + ' jam lagi!';
  });

  // Saring dan urutkan rak diskon
  var rak = document.querySelector('.rak'), kontrol = document.querySelector('.kontrol');
  if (!rak || !kontrol) return;
  kontrol.hidden = false;
  var barang = Array.prototype.slice.call(rak.children), info = document.querySelector('.hasil-saring');
  var saringan = {
    semua: function () { return true; },
    sembilan: function (b) { return +b.dataset.diskon >= 90; },
    murah: function (b) { return +b.dataset.harga < 2000000; },
    ulasan: function (b) { return +b.dataset.ulasan >= 95; },
    terendah: function (b) { return b.dataset.terendah === '1'; }
  };
  var urutan = {
    pilihan: function (a, b) { return a.dataset.urut - b.dataset.urut; },
    termurah: function (a, b) { return a.dataset.harga - b.dataset.harga; },
    diskon: function (a, b) { return b.dataset.diskon - a.dataset.diskon || a.dataset.harga - b.dataset.harga; },
    ulasan: function (a, b) { return b.dataset.ulasan - a.dataset.ulasan; }
  };
  var aktif = 'semua', pilih = kontrol.querySelector('select');
  function terapkan() {
    var n = 0;
    barang.sort(urutan[pilih.value]).forEach(function (b) {
      var tampil = saringan[aktif](b); b.hidden = !tampil; if (tampil) n++; rak.appendChild(b);
    });
    info.textContent = aktif === 'semua' ? '' : n + ' game cocok dengan saringan ini.';
  }
  kontrol.querySelectorAll('button').forEach(function (t) {
    t.addEventListener('click', function () {
      aktif = t.dataset.saring;
      kontrol.querySelectorAll('button').forEach(function (x) { x.setAttribute('aria-pressed', x === t); });
      terapkan();
    });
  });
  pilih.addEventListener('change', terapkan);
})();
</script>"""


def buat_halaman(epic, steam, folder="docs", link_telegram="", nama_channel="",
                 google_verifikasi="", event=None, halaman_lain=None):
    """halaman_lain: daftar (url, lastmod) tambahan untuk sitemap, misalnya halaman game."""
    os.makedirs(folder, exist_ok=True)
    tulis_css(folder)
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

    # --- Event sale (Autumn Sale, Winter Sale, dst.) ---
    teks_event = ""
    if event:
        if event["status"] == "berlangsung":
            judul_halaman = f"{event['nama']}: Diskon Harian dalam Rupiah ({_tanggal_panjang(sekarang)})"
            teks_event = f"{event['nama']} sedang berlangsung, {event['periode']}."
        else:
            teks_event = f"{event['nama']} dimulai {event['mulai_teks']}."
        deskripsi = f"{teks_event} {deskripsi}"

    # --- Judul besar di pita biru ---
    ringkas = []
    if steam:
        ringkas.append(f"{len(steam)} diskon lolos saringan")
    if epic:
        ringkas.append(f"{len(epic)} game gratis di Epic")
    kalimat = (f"Dicek {HARI[sekarang.weekday()]}, {_tanggal_panjang(sekarang)} pukul {sekarang:%H.%M} WIB"
               + (f": {' dan '.join(ringkas)}." if ringkas else "."))
    event_html = f'\n        <p class="event">{escape(teks_event)}</p>' if teks_event else ""
    unggulan = ""
    if steam:
        # Potongan paling besar hari ini (kalau sama, yang paling murah) ditempel sebagai stiker
        g = max(steam, key=lambda x: (x["diskon"], -x["harga_akhir"]))
        tujuan = f'/{g["halaman"]}' if g.get("halaman") else g["url"]
        unggulan = f"""
      <a class="unggulan" href="{escape(tujuan)}">
        <span class="unggulan-ket">Potongan terbesar hari ini</span>
        <span class="stiker"><span class="potong">-{g['diskon']}%</span><span class="harga"><strong>{_rupiah(g['harga_akhir'])}</strong><s>{_rupiah(g['harga_awal'])}</s></span></span>
        <span class="unggulan-nama">{escape(g['judul'])}</span>
      </a>"""
    hero = f"""
    <div class="hero">
      <div>
        <h1>Diskon Steam hari ini, dalam Rupiah</h1>
        <p>{escape(kalimat)} Harga diambil langsung dari Steam region Indonesia, bukan hasil konversi dolar.</p>{event_html}
      </div>{unggulan}
    </div>"""

    # --- Game gratis Epic ---
    bagian_epic = ""
    if epic:
        kartu = "".join(_kartu_epic(g, i == 0) for i, g in enumerate(epic))
        bagian_epic = f"""
    <section class="bagian" aria-labelledby="h-gratis">
      <h2 id="h-gratis">Gratis di Epic Games Store</h2>
      <p class="catatan">Klaim sebelum batas waktunya, dan game jadi milikmu selamanya. <a href="/panduan/cara-klaim-game-gratis-epic-games/">Cara klaimnya</a>.</p>
      <ul class="gratis">{kartu}
      </ul>
    </section>"""

    # --- Rak diskon Steam ---
    if steam:
        barang = "".join(_barang_steam(g, i) for i, g in enumerate(steam))
        # Tombol ini hanya muncul kalau memang ada game yang sedang di harga termurahnya
        tombol_terendah = ('          <button type="button" data-saring="terendah" aria-pressed="false">'
                           'Termurah sejak dipantau</button>\n'
                           if any(g.get("terendah_sejak") for g in steam) else "")
        bagian_steam = f"""
    <section class="bagian" aria-labelledby="h-steam">
      <h2 id="h-steam">Rak diskon Steam</h2>
      <p class="catatan">Potongan minimal 50% untuk game dengan ulasan minimal 85% positif. Klik game untuk melihat riwayat harganya.</p>
      <div class="kontrol" hidden>
        <div class="saring" role="group" aria-label="Saring diskon">
          <button type="button" data-saring="semua" aria-pressed="true">Semua</button>
          <button type="button" data-saring="sembilan" aria-pressed="false">Diskon 90% ke atas</button>
          <button type="button" data-saring="murah" aria-pressed="false">Di bawah Rp 20.000</button>
          <button type="button" data-saring="ulasan" aria-pressed="false">Ulasan 95% ke atas</button>
{tombol_terendah}        </div>
        <label>Urutkan
          <select>
            <option value="pilihan">Pilihan kami</option>
            <option value="termurah">Harga termurah</option>
            <option value="diskon">Diskon terbesar</option>
            <option value="ulasan">Ulasan terbaik</option>
          </select>
        </label>
      </div>
      <p class="hasil-saring" aria-live="polite"></p>
      <ol class="rak">{barang}
      </ol>
      <p class="catatan" style="margin-top:2rem"><a href="/game/">Lihat semua game yang dipantau harganya</a></p>
    </section>"""
    else:
        bagian_steam = """
    <section class="bagian" aria-labelledby="h-steam">
      <h2 id="h-steam">Rak diskon Steam</h2>
      <p class="kosong">Belum ada diskon yang lolos saringan hari ini. Rak diisi ulang setiap sore, jadi cek lagi besok.</p>
    </section>"""

    tanya = """
    <section class="bagian" aria-labelledby="h-tanya">
      <h2 id="h-tanya">Pertanyaan umum</h2>
      <div class="tanya">
        <details>
          <summary>Kenapa harga di sini bisa beda dengan situs diskon lain?</summary>
          <p>Banyak situs menampilkan harga dolar atau hasil konversinya. Steam memakai harga regional, jadi harga di Indonesia bisa jauh berbeda, dan diskon di luar negeri belum tentu berlaku di sini. Semua harga di halaman ini dicek langsung ke Steam region Indonesia.</p>
        </details>
        <details>
          <summary>Seberapa sering halaman ini diperbarui?</summary>
          <p>Setiap sore. Harga bisa berubah sewaktu-waktu, jadi selalu cek halaman toko sebelum membeli.</p>
        </details>
        <details>
          <summary>Apa arti tulisan "Termurah sejak" di bawah nama game?</summary>
          <p>Harga game itu sedang paling murah sejak tanggal tersebut. Tulisan ini hanya muncul untuk game yang harganya sudah dicatat minimal 30 hari.</p>
        </details>
      </div>
    </section>"""

    tambahan = (f'<meta name="google-site-verification" content="{escape(google_verifikasi)}">'
                if google_verifikasi else "")
    head = kepala(judul_halaman, deskripsi, kanonik=situs, og_gambar=og_gambar, tambahan=tambahan)
    ajakan_alarm = ""
    if USERNAME_BOT_ALARM:
        ajakan_alarm = f"""
    <aside class="voucher lebar alarm" aria-labelledby="h-alarm">
      <div>
        <h2 id="h-alarm">Menunggu harga lebih murah?</h2>
        <p>Pasang alarm harga di Telegram. Ketik nama game, pilih target harganya, dan kamu akan dikabari saat harganya di Steam Indonesia turun sampai target itu.</p>
      </div>
      <a class="tombol" href="https://t.me/{escape(USERNAME_BOT_ALARM)}" rel="noopener">🔔 Pasang alarm harga</a>
    </aside>"""
    html = halaman_utuh(head, pita(link_telegram, hero=hero), bagian_epic + bagian_steam + ajakan_alarm + blok_beranda() + tanya,
                        script=SKRIP_BERANDA)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # File penanda lama dari masa GitHub Pages; tidak dipakai di hosting, tapi tidak mengganggu
    open(os.path.join(folder, ".nojekyll"), "w").close()

    if situs:
        with open(os.path.join(folder, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f"  <url><loc>{situs}</loc><lastmod>{sekarang:%Y-%m-%d}</lastmod></url>\n"
                + "".join(f"  <url><loc>{escape(u)}</loc><lastmod>{t}</lastmod></url>\n"
                          for u, t in (halaman_lain or []))
                + "</urlset>\n"
            )
        # robots.txt: izinkan semua mesin pencari dan tunjukkan lokasi sitemap
        with open(os.path.join(folder, "robots.txt"), "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\n\nSitemap: {situs}sitemap.xml\n")
        # .htaccess: satukan semua alamat (http, www) ke alamat utama situs
        _tulis_htaccess(folder, situs)

    return os.path.join(folder, "index.html")
