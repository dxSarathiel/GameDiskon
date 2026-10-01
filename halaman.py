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

from gaya import USERNAME_BOT_ALARM, gambar_epic, halaman_utuh, kepala, pita, tulis_css

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

# Judul dan meta deskripsi beranda (tampil di tab browser dan hasil pencarian Google).
# Ubah di sini kalau ingin merevisinya lagi.
# Judul di bawah 60 karakter supaya tidak terpotong di Google; kata kunci utama di depan.
JUDUL_BERANDA = "Game Diskon | List Game Gratis & Diskon Setiap Hari"
DESKRIPSI_BERANDA = ("Game Diskon hadirkan informasi tentang game diskon & gratis dengan harga Rupiah "
                     "di Steam dan Epic Games Store. Dapatkan game-game tersebut sebelum ketinggalan.")


# Akun resmi GameDiskon di tempat lain (untuk data terstruktur "sameAs" di beranda)
PROFIL_SOSIAL = ["https://t.me/diskongame", "https://www.tiktok.com/@game.diskon"]

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

# Halaman "tidak ditemukan" milik situs sendiri (dibuat halaman.py)
ErrorDocument 404 /404.html

# Simpan file statis di cache browser. gaya.css aman disimpan lama karena alamatnya
# berubah (?v=...) setiap kali tampilannya diubah. Halaman HTML tidak disimpan lama.
<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/css "access plus 1 year"
ExpiresByType font/woff2 "access plus 1 year"
ExpiresByType application/font-woff2 "access plus 1 year"
ExpiresByType image/png "access plus 1 week"
ExpiresByType image/x-icon "access plus 1 week"
ExpiresByType image/vnd.microsoft.icon "access plus 1 week"
ExpiresByType text/html "access plus 0 seconds"
</IfModule>
<IfModule mod_mime.c>
AddType font/woff2 .woff2
</IfModule>

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
          <img src="{escape(gambar_epic(g['gambar']))}" alt="" width="640" height="360" {gambar_attr} decoding="async">
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


def _papan_led(steam, jumlah=12):
    """Papan LED berjalan di bawah judul beranda: potongan terbesar hari ini.
    Hanya hiasan (aria-hidden): isinya sama dengan rak di bawahnya. Daftarnya ditulis dua kali
    supaya putarannya menyambung tanpa jeda."""
    if not steam:
        return ""
    teratas = sorted(steam, key=lambda g: (-g["diskon"], g["harga_akhir"]))[:jumlah]
    item = "".join(f'<li>{escape(g["judul"])}<b>-{g["diskon"]}%</b>{_rupiah(g["harga_akhir"])}</li>'
                   for g in teratas)
    return f"""
  <div class="led" aria-hidden="true"><ul class="led-isi">{item}{item}</ul></div>"""


def _jsonld_beranda(situs, deskripsi):
    """Data terstruktur beranda: nama situs (WebSite) dan pengelolanya (Organization)."""
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": f"{situs}#situs", "name": "GameDiskon", "alternateName": "Game Diskon",
             "url": situs, "description": deskripsi, "inLanguage": "id",
             "publisher": {"@id": f"{situs}#pengelola"}},
            {"@type": "Organization", "@id": f"{situs}#pengelola", "name": "GameDiskon", "url": situs,
             "logo": f"{situs}icon-192.png", "email": "kontak@gamediskon.my.id", "sameAs": PROFIL_SOSIAL},
        ],
    }


def _tulis_404(folder):
    """docs/404.html: dipakai Apache (ErrorDocument) untuk alamat yang tidak ada."""
    head = kepala("Halaman tidak ditemukan | GameDiskon",
                  "Halaman yang kamu cari tidak ada atau sudah dipindah.", noindex=True)
    isi = """
    <div class="prosa">
      <h1 class="judul-halaman">Halaman ini tidak ditemukan</h1>
      <p>Alamatnya mungkin salah ketik, atau halamannya sudah dipindah. Coba mulai dari sini:</p>
      <ul>
        <li><a href="/">Diskon Steam hari ini</a></li>
        <li><a href="/game-gratis-epic/">Game gratis Epic minggu ini</a></li>
        <li><a href="/game/">Semua game yang dipantau harganya</a></li>
        <li><a href="/jadwal-steam-sale/">Jadwal Steam Sale</a></li>
      </ul>
    </div>"""
    with open(os.path.join(folder, "404.html"), "w", encoding="utf-8") as f:
        f.write(halaman_utuh(head, pita(), isi))


def buat_halaman(epic, steam, folder="docs", link_telegram="", nama_channel="",
                 google_verifikasi="", event=None, halaman_lain=None, info_terbaru=None):
    """halaman_lain: daftar (url, lastmod) tambahan untuk sitemap, misalnya halaman game."""
    os.makedirs(folder, exist_ok=True)
    tulis_css(folder)
    sekarang = datetime.now(WIB)
    situs = url_situs()
    steam = steam[:MAKS_ITEM_HALAMAN]

    judul_halaman = JUDUL_BERANDA
    deskripsi = DESKRIPSI_BERANDA
    og_gambar = (epic[0]["gambar"] if epic else steam[0]["gambar"] if steam else "")

    # --- Event sale (Autumn Sale, Winter Sale, dst.) ---
    teks_event = ""
    if event:
        if event["status"] == "berlangsung":
            teks_event = f"{event['nama']} sedang berlangsung, {event['periode']}."
        else:
            teks_event = f"{event['nama']} dimulai {event.get('mulai_wib') or event['mulai_teks']}."

    # --- Judul besar di pita biru ---
    ringkas = []
    if steam:
        ringkas.append(f"{len(steam)} diskon lolos saringan")
    if epic:
        ringkas.append(f"{len(epic)} game gratis di Epic")
    kalimat = (f"Dicek {HARI[sekarang.weekday()]}, {_tanggal_panjang(sekarang)} pukul {sekarang:%H.%M} WIB"
               + (f": {' dan '.join(ringkas)}." if ringkas else "."))
    event_html = (f'\n        <p class="event"><a href="/jadwal-steam-sale/">{escape(teks_event)}</a></p>'
                  if teks_event else "")
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
        <p class="kicker">Promo game PC, dicek tiap hari</p>
        <h1><span class="baris">Diskon Steam</span> <span class="baris">hari ini,</span> <span class="sorot">dalam Rupiah</span></h1>
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
      <p class="catatan">Klaim sebelum batas waktunya, dan game jadi milikmu selamanya. <a href="/panduan/cara-klaim-game-gratis-epic-games/">Cara klaimnya</a>, atau lihat <a href="/game-gratis-epic/">jadwal game gratis Epic minggu depan</a>.</p>
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
    head = kepala(judul_halaman, deskripsi, kanonik=situs, og_gambar=og_gambar, tambahan=tambahan,
                  jsonld=_jsonld_beranda(situs, deskripsi))
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
    bagian_info = ""
    if info_terbaru:
        item = "".join(f'<li><h2><a href="/info-game/{escape(t["slug"])}/">{escape(t["judul"])}</a></h2>'
                       f'<p>{escape(t["jenis"])}. {escape(t["deskripsi"])}</p></li>' for t in info_terbaru[:3])
        bagian_info = f"""
    <section class="bagian" aria-labelledby="h-info">
      <h2 id="h-info">Info Game terbaru</h2>
      <ul class="daftar-artikel">{item}</ul>
      <p class="catatan" style="margin-top:1rem"><a href="/info-game/">Semua Info Game</a></p>
    </section>"""
    html = halaman_utuh(head, pita(link_telegram, hero=hero, setelah=_papan_led(steam)), bagian_epic + bagian_steam + ajakan_alarm + blok_beranda() + bagian_info + tanya,
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
        _tulis_404(folder)

    return os.path.join(folder, "index.html")
