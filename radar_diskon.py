"""
Radar Diskon Game — v5 (riwayat harga + gambar + halaman web + penanda event sale)
Sumber data (semua gratis, tanpa API key):
  1. CheapShark  -> daftar kandidat diskon Steam yang ratingnya bagus
  2. Steam       -> cek harga ASLI di region Indonesia (Rupiah)
  3. Epic Games  -> game yang sedang gratis
Setiap hari, harga Rupiah semua game yang dipantau dicatat ke harga_idr.json.
Setiap posting disertai gambar ringkasan (dibuat oleh gambar.py).
Setiap hari halaman web docs/index.html diperbarui dan di-upload ke gamediskon.my.id (halaman.py).
Di hari tanpa deal baru, dikirim pesan singkat berisi yang masih berlaku (maksimal sekali sehari).
Hasil dikirim ke channel Telegram. Kalau token belum diisi, hanya dicetak (dry run).
"""

import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from html import escape, unescape

import requests

from gambar import buat_gambar
try:
    from halaman import buat_halaman, url_situs
except Exception as err:
    # Kesalahan di halaman.py tidak boleh menghentikan posting Telegram
    print("halaman.py bermasalah, halaman web dilewati:", err)
    buat_halaman = None

    def url_situs():
        return ""

# ---------- Pengaturan (ubah sesuai selera) ----------
MIN_DISKON_PERSEN = 50      # diskon minimal di harga Indonesia
MIN_RATING_STEAM = 85       # % ulasan positif minimal
MIN_JUMLAH_ULASAN = 500     # supaya game obscure tidak lolos
MAKS_ITEM_STEAM = 8         # jumlah game Steam per posting
LUPAKAN_SETELAH_HARI = 30   # deal yang sama boleh diposting ulang setelah ini

HALAMAN_CHEAPSHARK = 2      # 2 halaman x 60 = sampai 120 kandidat per hari
MAKS_GAME_DIPANTAU = 2000   # batas jumlah game yang harganya dicatat tiap hari
MIN_HARI_DATA = 30          # label "terendah" baru muncul setelah data game >= sekian hari

NAMA_CHANNEL = "Kumpulan Game Diskon"  # tampil di bagian atas gambar
KIRIM_GAMBAR = True                     # ubah ke False untuk kembali ke teks saja
KIRIM_PESAN_KOSONG = True               # tetap kirim pesan singkat di hari tanpa deal baru
MAKS_PENGINGAT_EPIC = 3                 # jumlah game gratis Epic yang diingatkan di pesan itu
BUAT_HALAMAN = True                     # halaman web harian untuk GitHub Pages (folder docs)
TAMPILKAN_LINK_WEB = True              # ubah ke True SETELAH GitHub Pages aktif
GOOGLE_VERIFIKASI = "NeGuLjS_j7yta3znaeJWo-JRiksuR9yDI_F7atB-RqU" # isi kode dari Google Search Console (opsional)

# ---------- Event sale besar ----------
# Tanggal dari jadwal resmi Steamworks. Tambahkan event baru dengan format yang sama.
EVENT_SALE = [
    {"nama": "Steam Autumn Sale 2026", "mulai": "2026-10-01", "selesai": "2026-10-08", "emoji": "🍂"},
    {"nama": "Steam Winter Sale 2026", "mulai": "2026-12-17", "selesai": "2027-01-04", "emoji": "❄️"},
]
HARI_PENGUMUMAN_EVENT = 3   # mulai diumumkan sekian hari sebelum event
MAKS_ITEM_STEAM_EVENT = 12  # jumlah game Steam per posting selama event berlangsung

USER_AGENT = "RadarDiskonGameID/0.5 (github.com/dxSarathiel/GameDiskon)"  # ganti USERNAME
STATE_FILE = "sent.json"
RIWAYAT_FILE = "harga_idr.json"
GAMBAR_FILE = "radar.jpg"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

WIB = timezone(timedelta(hours=7))
HARI_INI = datetime.now(WIB).strftime("%Y-%m-%d")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT  # CheapShark menolak request tanpa User-Agent jelas


# ---------- File JSON ----------
def baca_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def tulis_json(path, data, rapi=True):
    with open(path, "w", encoding="utf-8") as f:
        if rapi:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # satu game per baris: ukuran kecil, perubahan di GitHub tetap mudah dibaca
            f.write("{\n")
            baris = [f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in data.items()]
            f.write(",\n".join(baris))
            f.write("\n}\n")


def simpan_state(state):
    batas = datetime.now(timezone.utc) - timedelta(days=LUPAKAN_SETELAH_HARI)
    state = {k: v for k, v in state.items() if datetime.fromisoformat(v) > batas}
    tulis_json(STATE_FILE, state)


def rupiah(nilai_sen):
    # Steam memberi harga dalam "sen": 26950000 -> Rp 269.500
    return "Rp " + f"{nilai_sen // 100:,}".replace(",", ".")


# ---------- Event sale ----------
BULAN_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
            "Agustus", "September", "Oktober", "November", "Desember"]


def _tgl(iso):
    return datetime.strptime(iso, "%Y-%m-%d")


def _periode(mulai, selesai):
    """1–8 Oktober 2026  /  17 Desember 2026 – 4 Januari 2027"""
    if mulai.year != selesai.year:
        return (f"{mulai.day} {BULAN_ID[mulai.month - 1]} {mulai.year} – "
                f"{selesai.day} {BULAN_ID[selesai.month - 1]} {selesai.year}")
    if mulai.month != selesai.month:
        return (f"{mulai.day} {BULAN_ID[mulai.month - 1]} – "
                f"{selesai.day} {BULAN_ID[selesai.month - 1]} {selesai.year}")
    return f"{mulai.day}–{selesai.day} {BULAN_ID[mulai.month - 1]} {mulai.year}"


def event_hari_ini():
    """Event yang sedang berlangsung, atau yang akan dimulai dalam HARI_PENGUMUMAN_EVENT hari.
    Kembalikan dict berisi status "berlangsung"/"segera", atau None."""
    hari_ini = _tgl(HARI_INI)
    for ev in EVENT_SALE:
        mulai, selesai = _tgl(ev["mulai"]), _tgl(ev["selesai"])
        # Sale Steam biasanya dimulai pagi waktu Pasifik = sekitar tengah malam WIB,
        # jadi saat bot posting pukul 18.00 WIB di tanggal mulai, sale kemungkinan belum aktif.
        # Karena itu status "berlangsung" baru dipakai sejak hari berikutnya.
        if mulai < hari_ini <= selesai:
            status = "berlangsung"
        elif timedelta(0) <= mulai - hari_ini <= timedelta(days=HARI_PENGUMUMAN_EVENT):
            status = "segera"
        else:
            continue
        return {
            "nama": ev["nama"],
            "emoji": ev.get("emoji", "🔥"),
            "status": status,
            "periode": _periode(mulai, selesai),
            "mulai_teks": f"{mulai.day} {BULAN_ID[mulai.month - 1]} {mulai.year}",
        }
    return None


# ---------- Riwayat harga ----------
# Format per game:
#   "1057090": {"nama": "...", "mulai": "2026-09-26", "cek": "2026-09-27", "kandidat": "2026-09-27",
#               "riwayat": [["2026-09-26", 1399900, 90], ...]}
# Satu entri riwayat = [tanggal, harga_akhir_dalam_sen, persen_diskon].
# Entri baru hanya ditambahkan kalau harga BERUBAH, supaya file tetap kecil.
def catat_harga(riwayat, appid, nama, harga):
    g = riwayat.setdefault(appid, {"nama": nama, "mulai": HARI_INI, "riwayat": []})
    g["nama"] = nama or g.get("nama", "")
    g["cek"] = HARI_INI
    entri = [HARI_INI, harga["final"], harga["discount_percent"]]
    if not g["riwayat"] or g["riwayat"][-1][1] != harga["final"]:
        g["riwayat"].append(entri)


def status_terendah(riwayat, appid, harga_sekarang):
    """Kembalikan tanggal mulai pencatatan kalau harga sekarang adalah yang terendah
    sepanjang data, dan data game itu sudah cukup lama. Selain itu None."""
    g = riwayat.get(appid)
    if not g:
        return None
    hari_data = (datetime.strptime(HARI_INI, "%Y-%m-%d") - datetime.strptime(g["mulai"], "%Y-%m-%d")).days
    if hari_data < MIN_HARI_DATA:
        return None
    if harga_sekarang <= min(e[1] for e in g["riwayat"]):
        return g["mulai"]
    return None


def ambil_harga_idr(appids):
    """Harga Steam region Indonesia, 100 game per request."""
    hasil = {}
    for i in range(0, len(appids), 100):
        potong = appids[i:i + 100]
        r = session.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": ",".join(potong), "cc": "id", "filters": "price_overview"},
            timeout=60,
        )
        r.raise_for_status()
        for appid, isi in r.json().items():
            data = isi.get("data") if isi.get("success") else None
            harga = data.get("price_overview") if isinstance(data, dict) else None
            if harga and harga.get("currency") == "IDR":
                hasil[appid] = harga
        time.sleep(2)  # sopan ke server Steam
    return hasil


# ---------- Sumber 1 + 2: Steam ----------
def ambil_kandidat_cheapshark():
    kandidat = {}
    for halaman in range(HALAMAN_CHEAPSHARK):
        r = session.get(
            "https://www.cheapshark.com/api/1.0/deals",
            params={"storeID": 1, "onSale": 1, "sortBy": "Deal Rating",
                    "pageSize": 60, "pageNumber": halaman},
            timeout=30,
        )
        r.raise_for_status()
        for d in r.json():
            if d.get("steamAppID"):
                kandidat[d["steamAppID"]] = d
        time.sleep(1)
    return kandidat


def proses_steam(state, riwayat):
    kandidat = ambil_kandidat_cheapshark()

    # Semua kandidat hari ini ikut dipantau, lalu digabung dengan yang sudah dipantau.
    # Kalau melebihi batas, game yang paling lama tidak muncul sebagai kandidat
    # berhenti dicek harian (datanya tetap tersimpan, tidak dihapus).
    lama = sorted((a for a in riwayat if a not in kandidat),
                  key=lambda a: riwayat[a].get("kandidat", ""), reverse=True)
    semua = (list(kandidat) + lama)[:MAKS_GAME_DIPANTAU]
    harga_idr = ambil_harga_idr(semua)

    # Hitung status "terendah" SEBELUM harga hari ini dicatat,
    # supaya harga hari ini dibandingkan dengan data lama, bukan dengan dirinya sendiri.
    label = {a: status_terendah(riwayat, a, h["final"]) for a, h in harga_idr.items()}

    for appid, harga in harga_idr.items():
        nama = " ".join(kandidat[appid]["title"].split()) if appid in kandidat else None
        catat_harga(riwayat, appid, nama, harga)
        if appid in kandidat:
            riwayat[appid]["kandidat"] = HARI_INI  # terakhir kali muncul sebagai kandidat

    # Semua yang lolos saringan (untuk halaman web), lalu yang belum pernah diposting (untuk Telegram)
    layak = []
    for appid, d in kandidat.items():
        harga = harga_idr.get(appid)
        if not harga or harga["discount_percent"] < MIN_DISKON_PERSEN:
            continue
        if int(d.get("steamRatingPercent") or 0) < MIN_RATING_STEAM:
            continue
        if int(d.get("steamRatingCount") or 0) < MIN_JUMLAH_ULASAN:
            continue
        kunci = f"steam:{appid}:{harga['final']}"
        layak.append({
            "kunci": kunci,
            "judul": " ".join(d["title"].split()),
            "diskon": harga["discount_percent"],
            "harga_awal": harga["initial"],
            "harga_akhir": harga["final"],
            "rating": f"{int(d['steamRatingPercent'])}%",
            "terendah_sejak": label.get(appid),
            "url": f"https://store.steampowered.com/app/{appid}/",
            "gambar": f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg",
        })

    # Yang harganya terendah tercatat didahulukan, lalu yang diskonnya terbesar
    layak.sort(key=lambda x: (x["terendah_sejak"] is not None, x["diskon"]), reverse=True)
    baru = [g for g in layak if g["kunci"] not in state]
    ev = event_hari_ini()
    batas = MAKS_ITEM_STEAM_EVENT if ev and ev["status"] == "berlangsung" else MAKS_ITEM_STEAM
    return baru[:batas], layak, len(harga_idr)


# ---------- Sumber 3: Epic gratis ----------
def ambil_gratis_epic():
    r = session.get(
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
        params={"locale": "en-US", "country": "ID", "allowCountries": "ID"},
        timeout=30,
    )
    r.raise_for_status()
    hasil = []
    for e in r.json()["data"]["Catalog"]["searchStore"]["elements"]:
        promo = (e.get("promotions") or {}).get("promotionalOffers") or []
        if not promo or e["price"]["totalPrice"]["discountPrice"] != 0:
            continue
        tawaran = promo[0]["promotionalOffers"][0]
        kunci = f"epic:{e['id']}:{tawaran['startDate']}"
        slug = next((m["pageSlug"] for m in (e.get("offerMappings") or []) if m.get("pageSlug")),
                    e.get("productSlug"))
        berakhir = datetime.fromisoformat(tawaran["endDate"].replace("Z", "+00:00")).astimezone(WIB)
        gambar = {k["type"]: k["url"] for k in (e.get("keyImages") or [])}
        hasil.append({
            "kunci": kunci,
            "judul": e["title"],
            "berakhir": berakhir.strftime("%d/%m %H:%M WIB"),
            "url": f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games",
            "gambar": gambar.get("OfferImageWide") or gambar.get("Thumbnail") or next(iter(gambar.values()), ""),
        })
    return hasil


# ---------- Susun pesan ----------
def tanggal_pendek(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def susun_pesan(epic, steam):
    baris = [f"🎮 <b>Radar Diskon Game</b> — {datetime.now(WIB):%d/%m/%Y}"]
    ev = event_hari_ini()
    if ev and ev["status"] == "berlangsung":
        baris.append(f'{ev["emoji"]} <b>{escape(ev["nama"])}</b> sedang berlangsung ({ev["periode"]})')
    elif ev:
        baris.append(f'⏳ {escape(ev["nama"])} dimulai {ev["mulai_teks"]}')
    baris.append("")
    if epic:
        baris.append("🆓 <b>GRATIS di Epic</b>")
        for g in epic:
            baris.append(f'• <a href="{g["url"]}">{escape(g["judul"])}</a> — klaim sebelum {g["berakhir"]}')
        baris.append("")
    if steam:
        baris.append("🔥 <b>Diskon Steam (harga Indonesia)</b>")
        for g in steam:
            teks = (
                f'• <a href="{g["url"]}">{escape(g["judul"])}</a> — <b>-{g["diskon"]}%</b> '
                f'{rupiah(g["harga_akhir"])} <s>{rupiah(g["harga_awal"])}</s> · 👍 {g["rating"]}'
            )
            if g["terendah_sejak"]:
                teks += f'\n   📉 <i>Terendah sejak dicatat ({tanggal_pendek(g["terendah_sejak"])})</i>'
            baris.append(teks)
    situs = url_situs()
    if TAMPILKAN_LINK_WEB and situs:
        baris += ["", f'🌐 <a href="{situs}">Lihat semua diskon hari ini di web</a>']
    return "\n".join(baris).strip()


def susun_pesan_kosong(epic_semua, steam_layak):
    """Pesan singkat untuk hari tanpa deal BARU: rangkuman yang masih berlaku + link web."""
    baris = [f"🎮 <b>Radar Diskon Game</b> — {datetime.now(WIB):%d/%m/%Y}"]
    ev = event_hari_ini()
    if ev and ev["status"] == "berlangsung":
        baris.append(f'{ev["emoji"]} <b>{escape(ev["nama"])}</b> sedang berlangsung ({ev["periode"]})')
    elif ev:
        baris.append(f'⏳ {escape(ev["nama"])} dimulai {ev["mulai_teks"]}')
    baris += ["", "📭 Belum ada diskon atau game gratis <b>baru</b> hari ini."]

    masih = []
    if steam_layak:
        masih.append(f"{len(steam_layak)} diskon Steam (harga Indonesia)")
    if epic_semua:
        masih.append(f"{len(epic_semua)} game gratis Epic")
    if masih:
        baris.append("Yang masih berlaku: " + " dan ".join(masih) + ".")

    if epic_semua:
        baris += ["", "🆓 <b>Masih bisa diklaim gratis:</b>"]
        for g in epic_semua[:MAKS_PENGINGAT_EPIC]:
            baris.append(f'• <a href="{g["url"]}">{escape(g["judul"])}</a> — sampai {g["berakhir"]}')

    situs = url_situs()
    if TAMPILKAN_LINK_WEB and situs:
        baris += ["", f'🌐 <a href="{situs}">Lihat daftar lengkapnya di web</a>']
    baris += ["", "Radar berikutnya: besok sore. 👋"]
    return "\n".join(baris).strip()


def kirim_pesan_kosong(state, epic_semua, steam_layak, semua_sumber_gagal):
    """Kirim paling banyak SEKALI per hari, walaupun workflow dijalankan berkali-kali."""
    if not KIRIM_PESAN_KOSONG:
        return
    if semua_sumber_gagal:
        # Jangan bilang "tidak ada diskon" kalau sebenarnya datanya gagal diambil
        print("Semua sumber gagal, pesan hari kosong tidak dikirim.")
        return
    kunci = f"pesan-kosong:{HARI_INI}"
    if kunci in state:
        print("Pesan hari kosong sudah dikirim hari ini, dilewati.")
        return
    if kirim_telegram(susun_pesan_kosong(epic_semua, steam_layak)):
        state[kunci] = datetime.now(timezone.utc).isoformat()
        simpan_state(state)


def panjang_terlihat(teks_html):
    # Batas caption Telegram dihitung dari teks yang terlihat, bukan tag HTML-nya
    return len(unescape(re.sub(r"<[^>]+>", "", teks_html)))


def link_channel():
    return f"t.me/{TELEGRAM_CHAT_ID[1:]}" if TELEGRAM_CHAT_ID.startswith("@") else ""


def _telegram(metode, data, files=None):
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{metode}",
                      data=data, files=files, timeout=60)
    if not r.ok:
        print(f"{metode} gagal:", r.text)
    return r.ok


def kirim_telegram(teks, path_gambar=None):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("[DRY RUN] Token/chat ID belum diisi. Pesan yang akan dikirim:\n")
        print(teks)
        if path_gambar:
            print(f"\n[DRY RUN] Gambar disimpan di {path_gambar} "
                  f"(panjang caption {panjang_terlihat(teks)} karakter)")
        return True

    dasar = {"chat_id": TELEGRAM_CHAT_ID, "parse_mode": "HTML"}

    if path_gambar:
        with open(path_gambar, "rb") as foto:
            if panjang_terlihat(teks) <= 1024:
                # Muat dalam satu posting: gambar + teks sebagai caption
                if _telegram("sendPhoto", dict(dasar, caption=teks), {"photo": foto}):
                    return True
            else:
                # Terlalu panjang untuk caption: kirim gambar dulu, teks menyusul
                _telegram("sendPhoto", dict(dasar, caption="🔥 Sorotan hari ini — detail di bawah 👇"),
                          {"photo": foto})
        print("Lanjut kirim teks.")

    # Teks selalu dikirim kalau gambar tidak ada, gagal, atau caption kepanjangan
    return _telegram("sendMessage", dict(dasar, text=teks, disable_web_page_preview="true"))


def main():
    state = baca_json(STATE_FILE)
    riwayat = baca_json(RIWAYAT_FILE)

    # Satu sumber gagal tidak boleh menggagalkan semuanya
    try:
        epic_semua = ambil_gratis_epic()
    except Exception as err:
        print("Epic gagal:", err)
        epic_semua = []
        epic_gagal = True
    else:
        epic_gagal = False
    epic = [g for g in epic_semua if g["kunci"] not in state]

    steam, steam_layak = [], []
    steam_gagal = False
    try:
        steam, steam_layak, jumlah_dicek = proses_steam(state, riwayat)
        # Riwayat disimpan SETIAP hari, walaupun tidak ada yang diposting
        tulis_json(RIWAYAT_FILE, riwayat, rapi=False)
        print(f"Harga dicatat: {jumlah_dicek} game dicek, total {len(riwayat)} game dipantau.")
    except Exception as err:
        print("Steam/CheapShark gagal:", err)
        steam_gagal = True

    # Halaman web juga diperbarui setiap hari, termasuk hari tanpa posting baru
    if BUAT_HALAMAN and buat_halaman and (epic_semua or steam_layak):
        try:
            path = buat_halaman(epic_semua, steam_layak, link_telegram=link_channel(),
                                nama_channel=NAMA_CHANNEL, google_verifikasi=GOOGLE_VERIFIKASI,
                                event=event_hari_ini())
            print(f"Halaman web diperbarui: {path} ({len(steam_layak)} diskon Steam, {len(epic_semua)} gratis Epic)")
        except Exception as err:
            print("Halaman web gagal dibuat:", err)

    if not epic and not steam:
        print("Tidak ada deal baru hari ini.")
        kirim_pesan_kosong(state, epic_semua, steam_layak, epic_gagal and steam_gagal)
        return

    path_gambar = None
    if KIRIM_GAMBAR:
        try:
            ev = event_hari_ini()
            label_event = ev["nama"] if ev and ev["status"] == "berlangsung" else ""
            path_gambar = buat_gambar(epic, steam, GAMBAR_FILE, session,
                                      NAMA_CHANNEL, link_channel(), label_event)
        except Exception as err:
            print("Gambar gagal dibuat, kirim teks saja:", err)

    if kirim_telegram(susun_pesan(epic, steam), path_gambar):
        sekarang = datetime.now(timezone.utc).isoformat()
        for g in epic + steam:
            state[g["kunci"]] = sekarang
        simpan_state(state)


if __name__ == "__main__":
    main()
