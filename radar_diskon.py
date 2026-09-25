"""
Radar Diskon Game — v2 (dengan pencatatan riwayat harga Rupiah)
Sumber data (semua gratis, tanpa API key):
  1. CheapShark  -> daftar kandidat diskon Steam yang ratingnya bagus
  2. Steam       -> cek harga ASLI di region Indonesia (Rupiah)
  3. Epic Games  -> game yang sedang gratis
Setiap hari, harga Rupiah semua game yang dipantau dicatat ke harga_idr.json.
Hasil dikirim ke channel Telegram. Kalau token belum diisi, hanya dicetak (dry run).
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from html import escape

import requests

# ---------- Pengaturan (ubah sesuai selera) ----------
MIN_DISKON_PERSEN = 50      # diskon minimal di harga Indonesia
MIN_RATING_STEAM = 85       # % ulasan positif minimal
MIN_JUMLAH_ULASAN = 500     # supaya game obscure tidak lolos
MAKS_ITEM_STEAM = 8         # jumlah game Steam per posting
LUPAKAN_SETELAH_HARI = 30   # deal yang sama boleh diposting ulang setelah ini

HALAMAN_CHEAPSHARK = 2      # 2 halaman x 60 = sampai 120 kandidat per hari
MAKS_GAME_DIPANTAU = 2000   # batas jumlah game yang harganya dicatat tiap hari
MIN_HARI_DATA = 30          # label "terendah" baru muncul setelah data game >= sekian hari

USER_AGENT = "RadarDiskonGameID/0.2 (github.com/dxSarathiel/GameDiskon)"  # ganti USERNAME
STATE_FILE = "sent.json"
RIWAYAT_FILE = "harga_idr.json"
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

    # Pilih yang layak diposting
    hasil = []
    for appid, d in kandidat.items():
        harga = harga_idr.get(appid)
        if not harga or harga["discount_percent"] < MIN_DISKON_PERSEN:
            continue
        if int(d.get("steamRatingPercent") or 0) < MIN_RATING_STEAM:
            continue
        if int(d.get("steamRatingCount") or 0) < MIN_JUMLAH_ULASAN:
            continue
        kunci = f"steam:{appid}:{harga['final']}"
        if kunci in state:
            continue
        hasil.append({
            "kunci": kunci,
            "judul": " ".join(d["title"].split()),
            "diskon": harga["discount_percent"],
            "harga_awal": harga["initial"],
            "harga_akhir": harga["final"],
            "rating": f"{int(d['steamRatingPercent'])}%",
            "terendah_sejak": label.get(appid),
            "url": f"https://store.steampowered.com/app/{appid}/",
        })

    # Yang harganya terendah tercatat didahulukan, lalu yang diskonnya terbesar
    hasil.sort(key=lambda x: (x["terendah_sejak"] is not None, x["diskon"]), reverse=True)
    return hasil[:MAKS_ITEM_STEAM], len(harga_idr)


# ---------- Sumber 3: Epic gratis ----------
def ambil_gratis_epic(state):
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
        if kunci in state:
            continue
        slug = next((m["pageSlug"] for m in (e.get("offerMappings") or []) if m.get("pageSlug")),
                    e.get("productSlug"))
        berakhir = datetime.fromisoformat(tawaran["endDate"].replace("Z", "+00:00")).astimezone(WIB)
        hasil.append({
            "kunci": kunci,
            "judul": e["title"],
            "berakhir": berakhir.strftime("%d/%m %H:%M WIB"),
            "url": f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games",
        })
    return hasil


# ---------- Susun pesan ----------
def tanggal_pendek(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")


def susun_pesan(epic, steam):
    baris = [f"🎮 <b>Radar Diskon Game</b> — {datetime.now(WIB):%d/%m/%Y}", ""]
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
    return "\n".join(baris).strip()


def kirim_telegram(teks):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("[DRY RUN] Token/chat ID belum diisi. Pesan yang akan dikirim:\n")
        print(teks)
        return True
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": teks, "parse_mode": "HTML",
              "disable_web_page_preview": "true"},
        timeout=30,
    )
    if not r.ok:
        print("Gagal kirim:", r.text)
    return r.ok


def main():
    state = baca_json(STATE_FILE)
    riwayat = baca_json(RIWAYAT_FILE)

    # Satu sumber gagal tidak boleh menggagalkan semuanya
    try:
        epic = ambil_gratis_epic(state)
    except Exception as err:
        print("Epic gagal:", err)
        epic = []
    try:
        steam, jumlah_dicek = proses_steam(state, riwayat)
        # Riwayat disimpan SETIAP hari, walaupun tidak ada yang diposting
        tulis_json(RIWAYAT_FILE, riwayat, rapi=False)
        print(f"Harga dicatat: {jumlah_dicek} game dicek, total {len(riwayat)} game dipantau.")
    except Exception as err:
        print("Steam/CheapShark gagal:", err)
        steam = []

    if not epic and not steam:
        print("Tidak ada deal baru hari ini.")
        return

    if kirim_telegram(susun_pesan(epic, steam)):
        sekarang = datetime.now(timezone.utc).isoformat()
        for g in epic + steam:
            state[g["kunci"]] = sekarang
        simpan_state(state)


if __name__ == "__main__":
    main()
