"""
Halaman per game untuk gamediskon.my.id (Tahap 2).

Dari data harga_idr.json dibuat:
  docs/game/<appid>-<slug>/index.html  -> harga sekarang, harga normal, terendah tercatat, riwayat
  docs/game/index.html                  -> daftar semua game yang dipantau

Isi halaman game hanya berubah kalau harganya berubah, supaya upload harian tetap ringan.
Karena itu kalimat di halaman tidak memuat hitungan yang berganti tiap hari (mis. "sudah 49 hari");
perbandingan antar game dibulatkan supaya tidak ikut berubah setiap ada game baru.
Game yang datanya masih sedikit diberi tanda "noindex" dan belum masuk sitemap,
supaya Google tidak menilai situs ini penuh halaman tipis.
"""

import json
import os
import re
import sys
import unicodedata
import zlib
from datetime import datetime, timedelta
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
MIN_GAME_PER_GENRE = 20     # perbandingan harga segenre hanya ditampilkan kalau genrenya berisi >= sekian game
MAKS_KUTIPAN_STEAM = 220    # panjang kutipan deskripsi resmi Steam (huruf); sisanya dibaca di Steam


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
        "diskon_maks": max(e[2] for e in riwayat),
        "jumlah_perubahan": len(riwayat) - 1,
        "info": g.get("info") or {},
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
# ---------- Isi tambahan halaman game (supaya tiap halaman punya isi yang khas) ----------
def _gabung(daftar):
    daftar = [d for d in daftar if d]
    if len(daftar) <= 1:
        return "".join(daftar)
    return ", ".join(daftar[:-1]) + " dan " + daftar[-1]


_TETAP = {"Steam", "Remote", "Play", "Cloud", "Workshop", "Valve", "Anti-Cheat", "Early", "Access"}


def _huruf_kecil(teks):
    """'Pencapaian Steam' -> 'pencapaian Steam', 'RPG' tetap 'RPG' (nama dan singkatan dipertahankan)."""
    return " ".join(w if (w in _TETAP or w.isupper()) else w.lower() for w in teks.split())


def _kutipan_pendek(teks, maks=MAKS_KUTIPAN_STEAM):
    """Ambil satu-dua kalimat pertama deskripsi Steam. Deskripsi lengkapnya sama persis dengan yang ada
    di Steam dan situs lain, jadi di sini cukup cuplikannya."""
    teks = " ".join((teks or "").split())
    if len(teks) <= maks:
        return teks
    kalimat = re.split(r"(?<=[.!?])\s+", teks)
    hasil = kalimat[0]
    for k in kalimat[1:]:
        if len(hasil) >= 80 or len(hasil) + 1 + len(k) > maks:
            break
        hasil += " " + k
    if len(hasil) > maks:
        hasil = hasil[:maks].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return hasil


def _bagian_tentang(r):
    """Tentang game: kalimat Indonesia dari data toko Steam + deskripsi resmi + fakta."""
    info, nama = r["info"], r["nama"]
    if not (info.get("genre") or info.get("developer") or info.get("deskripsi")):
        return ""
    kalimat = f"{nama} adalah game"
    if info.get("genre"):
        kalimat += f" {_gabung([_huruf_kecil(g) for g in info['genre']])}"
    if info.get("developer"):
        kalimat += f" buatan {_gabung(info['developer'])}"
    if info.get("publisher") and info.get("publisher") != info.get("developer"):
        kalimat += f", diterbitkan oleh {_gabung(info['publisher'])}"
    if info.get("rilis"):
        kalimat += f", dirilis {info['rilis']}"
    kalimat += "."
    if info.get("fitur"):
        kalimat += f" Fitur yang tercantum di Steam antara lain {_gabung([_huruf_kecil(f) for f in info['fitur'][:4]])}."
    cuplikan = _kutipan_pendek(info.get("deskripsi"))
    kutipan = (f'\n      <p>Cuplikan deskripsi resmi di Steam:</p>\n      <blockquote lang="en"><p>{escape(cuplikan)}</p></blockquote>'
               if cuplikan else "")
    fakta = [(k, v) for k, v in (("Genre", ", ".join(info.get("genre") or [])),
                                 ("Developer", ", ".join(info.get("developer") or [])),
                                 ("Publisher", ", ".join(info.get("publisher") or [])),
                                 ("Tanggal rilis", info.get("rilis") or "")) if v]
    dl = "".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in fakta)
    return f"""
    <section class="bagian" aria-labelledby="h-tentang">
      <h2 id="h-tentang">Tentang {escape(nama)}</h2>
      <div class="prosa">
      <p>{escape(kalimat)}</p>{kutipan}
      </div>
      <dl class="fakta">{dl}</dl>
    </section>"""


def _periode_diskon(riwayat):
    """Periode diskon yang tercatat, urut dari yang paling lama:
    (tgl_mulai, tgl_selesai atau None kalau masih berlangsung, diskon_terbesar, harga_termurah)."""
    periode, buka = [], None
    for tgl, harga, dsk in riwayat:
        if dsk > 0:
            if buka is None:
                buka = [tgl, None, dsk, harga]
            else:
                buka[2], buka[3] = max(buka[2], dsk), min(buka[3], harga)
        elif buka is not None:
            buka[1] = tgl
            periode.append(tuple(buka))
            buka = None
    if buka is not None:
        periode.append(tuple(buka))
    return periode


def _harga_saat_event(r, ev):
    """Harga termurah game ini selama satu event sale.
    Kembalikan (harga, diskon) kalau diskon, (None, 0) kalau dipantau tapi tidak diskon,
    atau None kalau game ini belum dipantau saat event itu."""
    try:
        # Sale Steam mulai dan selesai pukul 10.00 waktu Pasifik (sekitar tengah malam WIB). Jadi pengecekan
        # harian bot yang jatuh di dalam masa sale adalah tanggal WIB sehari setelah "mulai" sampai "selesai".
        awal = (datetime.strptime(ev["mulai"], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        akhir = ev["selesai"]
    except (KeyError, TypeError, ValueError):
        return None
    if r["mulai"] > akhir or awal > akhir:
        return None
    sebelum = [e for e in r["riwayat"] if e[0] <= awal]       # harga yang berlaku di hari pertama sale
    berlaku = sebelum[-1:] + [e for e in r["riwayat"] if awal < e[0] <= akhir]
    diskon = [e for e in berlaku if e[2] > 0]
    if diskon:
        terbaik = min(diskon, key=lambda e: e[1])
        return terbaik[1], terbaik[2]
    return (None, 0) if r["mulai"] <= awal else None


def _baris_event(r, hari_ini, event_sale):
    """Kalimat per event sale yang sudah dimulai: berapa harga game ini saat itu."""
    baris = []
    for ev in event_sale or ():
        try:
            if datetime.strptime(ev["mulai"], "%Y-%m-%d").date() > hari_ini:
                continue
        except (KeyError, TypeError, ValueError):
            continue
        hasil = _harga_saat_event(r, ev)
        if hasil is None:
            continue
        harga, dsk = hasil
        waktu = f"{_tgl(ev['mulai'])} sampai {_tgl(ev['selesai'])}"
        if harga is None:
            baris.append(f"{ev['nama']} ({waktu}): tidak ikut diskon.")
        else:
            baris.append(f"{ev['nama']} ({waktu}): {_rupiah(harga)}, diskon {dsk}%.")
    return baris


def _banding_genre(r, harga_genre):
    """Posisi harga hari ini di antara game segenre. Dibulatkan ke persepuluhan supaya kalimatnya
    tidak berubah setiap ada game baru atau harga game lain bergeser sedikit."""
    pilihan = [(len(harga_genre[g]), g) for g in (r["info"].get("genre") or [])
               if len(harga_genre.get(g, ())) >= MIN_GAME_PER_GENRE]
    if not pilihan:
        return ""
    _, genre = min(pilihan)                      # genre paling spesifik (paling sedikit gamenya)
    lain = harga_genre[genre]
    lebih_mahal = sum(1 for h in lain if h > r["harga_kini"])
    lebih_murah = sum(1 for h in lain if h < r["harga_kini"])
    nama_genre = _huruf_kecil(genre)
    if lebih_mahal >= lebih_murah:
        n = round(lebih_mahal * 10 / len(lain))
        if n >= 10:
            return f"Harga hari ini termasuk yang paling murah di antara game {nama_genre} yang kami pantau."
        if n >= 6:
            return f"Harga hari ini lebih murah dari sekitar {n} dari 10 game {nama_genre} yang kami pantau."
    else:
        n = round(lebih_murah * 10 / len(lain))
        if n >= 10:
            return f"Harga hari ini termasuk yang paling mahal di antara game {nama_genre} yang kami pantau."
        if n >= 6:
            return f"Harga hari ini lebih mahal dari sekitar {n} dari 10 game {nama_genre} yang kami pantau."
    return f"Harga hari ini berada di kisaran tengah game {nama_genre} yang kami pantau."


def _bagian_saran(r, hari_ini, konteks=None):
    """Beli sekarang atau tunggu: kesimpulan dan alasannya, dihitung dari data pantauan sendiri."""
    konteks = konteks or {}
    nama, kini = r["nama"], r["harga_kini"]
    terendah, tgl_terendah = r["harga_terendah"], _tgl(r["tgl_terendah"])
    periode = _periode_diskon(r["riwayat"])
    if r["diskon_kini"] > 0 and not r["pernah_berubah"]:
        saran = "Sedang diskon."
        alasan = (f"{nama} diskon {r['diskon_kini']}% menjadi {_rupiah(kini)}. Harganya belum berubah sejak kami pantau, "
                  f"jadi belum ada harga lain sebagai pembanding.")
    elif r["diskon_kini"] > 0 and kini <= terendah:
        saran = "Beli sekarang."
        alasan = (f"Harga hari ini, {_rupiah(kini)} (diskon {r['diskon_kini']}%), adalah harga termurah "
                  f"yang pernah kami catat untuk {nama}.")
    elif r["diskon_kini"] > 0:
        selisih = kini - terendah
        if selisih * 10 <= kini:
            saran = "Layak dibeli."
            alasan = (f"Harga hari ini {_rupiah(kini)} (diskon {r['diskon_kini']}%), hanya {_rupiah(selisih)} di atas "
                      f"harga termurah yang pernah kami catat ({_rupiah(terendah)} pada {tgl_terendah}).")
        else:
            saran = "Bisa menunggu."
            alasan = (f"{nama} memang sedang diskon {r['diskon_kini']}% menjadi {_rupiah(kini)}, tetapi pernah "
                      f"{_rupiah(selisih)} lebih murah: {_rupiah(terendah)} pada {tgl_terendah}.")
    elif r["pernah_berubah"] and terendah < kini:
        saran = "Tunggu diskon."
        potongan = f" (diskon {r['diskon_terendah']}%)" if r["diskon_terendah"] else ""
        alasan = (f"Hari ini {nama} dijual {_rupiah(kini)} tanpa diskon, padahal pernah turun ke "
                  f"{_rupiah(terendah)}{potongan} pada {tgl_terendah}.")
    else:
        saran = "Belum ada pola diskon."
        alasan = f"Sejak kami pantau, {nama} belum pernah lebih murah dari {_rupiah(kini)}."

    pantau = f"Kami memantau harga {nama} di Steam Indonesia setiap hari sejak {_tgl(r['mulai'])}."
    if periode:
        pantau += f" Selama itu tercatat {len(periode)} kali diskon, yang terbesar {r['diskon_maks']}%."
    banding = _banding_genre(r, konteks.get("harga_genre") or {})
    if banding:
        pantau += " " + banding

    event = _baris_event(r, hari_ini, konteks.get("event_sale"))
    daftar_event = ""
    if event:
        daftar_event = ("\n      <p>Harga saat event sale:</p>\n      <ul>"
                        + "".join(f"<li>{escape(b)}</li>" for b in event) + "</ul>")
    return f"""
    <section class="bagian prosa" aria-labelledby="h-saran">
      <h2 id="h-saran">Beli {escape(nama)} sekarang atau tunggu?</h2>
      <p><strong>{escape(saran)}</strong> {escape(alasan)}</p>
      <p>{escape(pantau)}</p>{daftar_event}
    </section>"""


def _bagian_tanya(r):
    nama, kini = r["nama"], r["harga_kini"]
    if r["diskon_kini"]:
        j1 = f"Ya. Hari ini {nama} diskon {r['diskon_kini']}% di Steam Indonesia, menjadi {_rupiah(kini)}."
    else:
        j1 = f"Tidak. Hari ini {nama} dijual dengan harga normal {_rupiah(kini)} di Steam Indonesia."
    j2 = (f"Harga termurah yang pernah kami catat adalah {_rupiah(r['harga_terendah'])}"
          + (f" (diskon {r['diskon_terendah']}%)" if r["diskon_terendah"] else "") + f", pada {_tgl(r['tgl_terendah'])}.")
    periode = _periode_diskon(r["riwayat"])
    if not periode:
        j3 = f"Belum bisa diperkirakan. Sejak kami pantau, {nama} belum pernah diskon."
    else:
        mulai, selesai, dsk, _ = periode[-1]
        if selesai is None:
            j3 = f"{nama} sedang diskon sekarang. Diskon {dsk}% ini tercatat sejak {_tgl(mulai)}."
        else:
            j3 = f"Diskon terakhir yang kami catat sebesar {dsk}%, dari {_tgl(mulai)} sampai {_tgl(selesai)}."
        if len(periode) > 1:
            j3 += f" Sejak dipantau, game ini sudah {len(periode)} kali diskon."
    j3 += " Pasang alarm harga supaya dikabari begitu harganya turun."
    tanya = [(f"Apakah {nama} sedang diskon di Steam?", j1),
             (f"Berapa harga termurah {nama} di Steam Indonesia?", j2),
             (f"Kapan {nama} diskon lagi?", j3)]
    isi = "".join(f"<details><summary>{escape(t)}</summary><p>{escape(j)}</p></details>" for t, j in tanya)
    return f"""
    <section class="bagian" aria-labelledby="h-tanya">
      <h2 id="h-tanya">Pertanyaan seputar harga {escape(nama)}</h2>
      <div class="tanya">{isi}</div>
      <p class="catatan">Jadwal sale berikutnya: <a href="/jadwal-steam-sale/">Jadwal Steam Sale</a>.</p>
    </section>"""


def _pilih_terkait(r, aktif, jumlah=6):
    """Game lain yang sedang diskon: utamakan yang genrenya sama, lalu diskon terbesar."""
    genre = set(r["info"].get("genre") or [])
    kandidat = [x for x in aktif if x["appid"] != r["appid"]]
    kandidat.sort(key=lambda x: (-len(genre & set(x["info"].get("genre") or [])), -x["diskon_kini"],
                                 zlib.crc32(f"{r['appid']}-{x['appid']}".encode())))   # urutan tetap, bukan acak tiap run
    return kandidat[:jumlah]


def _bagian_terkait(r, aktif):
    terkait = _pilih_terkait(r, aktif)
    if not terkait:
        return ""
    item = "".join(f'<li><a href="/{jalur_game(x["appid"], x["slug"])}">{escape(x["nama"])}</a>'
                   f'<span class="harga"><b>-{x["diskon_kini"]}%</b>{_rupiah(x["harga_kini"])}</span></li>' for x in terkait)
    return f"""
    <section class="bagian" aria-labelledby="h-terkait">
      <h2 id="h-terkait">Game lain yang sedang diskon</h2>
      <ul class="daftar">{item}</ul>
      <p class="catatan"><a href="/game/">Lihat semua game yang dipantau</a></p>
    </section>"""


def _html_game(r, situs, link_telegram, hari_ini, aktif=(), konteks=None):
    url = situs + jalur_game(r["appid"], r["slug"])
    nama = r["nama"]
    gambar = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{r['appid']}/header.jpg"
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
                     f'Pasang alarm harga</a>')
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
    </dl>{_bagian_saran(r, hari_ini, konteks)}{blok_halaman_game(kini)}{_bagian_tentang(r)}
    <section class="struk" aria-labelledby="h-riwayat">
      <h2 id="h-riwayat">Riwayat harga</h2>
      <p class="catatan">Satu baris per perubahan harga.</p>
      <table>
        <thead><tr><th scope="col">Tanggal</th><th scope="col" class="angka">Diskon</th><th scope="col" class="angka">Harga</th></tr></thead>
        <tbody>{"".join(baris)}</tbody>
        <tfoot><tr><td colspan="2">Termurah tercatat</td><td class="angka">{_rupiah(r['harga_terendah'])}</td></tr></tfoot>
      </table>
    </section>{_bagian_tanya(r)}{_bagian_terkait(r, aktif)}"""
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
    return url, _kerangka(judul, deskripsi, url, isi, aktif="game", script=SKRIP_CARI,
                          jsonld={"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Beranda", "item": situs}, {"@type": "ListItem", "position": 2, "name": "Semua game", "item": url}]})


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


def buat_halaman_game(riwayat, folder="docs", link_telegram="", event_sale=None):
    """Buat semua halaman game + halaman daftar.
    event_sale: daftar EVENT_SALE dari radar_diskon.py, untuk kalimat "harga saat event sale".
    Kalau tidak diberikan, diambil dari skrip yang sedang berjalan (radar_diskon.py).
    Kembalikan daftar (url, lastmod) halaman yang boleh diindeks, untuk sitemap."""
    if event_sale is None:
        event_sale = getattr(sys.modules.get("__main__"), "EVENT_SALE", None) or ()
    situs = url_situs()
    if not situs:
        return []
    tulis_css(folder)
    hari_ini = datetime.now(WIB).date()
    semua, untuk_sitemap, jumlah_berubah = [], [], 0
    for appid, g in riwayat.items():
        r = ringkas(appid, g)
        if r:
            semua.append(r)
    # Game yang sedang diskon dan masih dicek harian, untuk bagian "Game lain yang sedang diskon"
    aktif = [r for r in semua if r["diskon_kini"] > 0 and _hari_sejak(r["cek"], hari_ini) <= BATAS_TIDAK_DIPANTAU]
    # Harga hari ini semua game per genre, untuk kalimat perbandingan segenre
    harga_genre = {}
    for r in semua:
        for genre in r["info"].get("genre") or []:
            harga_genre.setdefault(genre, []).append(r["harga_kini"])
    konteks = {"event_sale": event_sale, "harga_genre": harga_genre}
    for r in semua:
        appid = r["appid"]
        url, html, noindex = _html_game(r, situs, link_telegram, hari_ini, aktif, konteks)
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
