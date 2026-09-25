"""
Radar Diskon Game — MVP
Sumber data (semua gratis, tanpa API key):
  1. CheapShark  -> daftar kandidat diskon Steam yang ratingnya bagus
  2. Steam       -> cek harga ASLI di region Indonesia (Rupiah)
  3. Epic Games  -> game yang sedang gratis
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

USER_AGENT = "RadarDiskonGameID/0.1 (github.com/USERNAME/radar-diskon)"  # ganti USERNAME
STATE_FILE = "sent.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT  # CheapShark menolak request tanpa User-Agent jelas


# ---------- State: mencatat apa yang sudah dikirim ----------
def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state):
    batas = datetime.now(timezone.utc) - timedelta(days=LUPAKAN_SETELAH_HARI)
    state = {k: v for k, v in state.items() if datetime.fromisoformat(v) > batas}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def rupiah(nilai_sen):
    # Steam memberi harga dalam "sen": 26950000 -> Rp 269.500
    return "Rp " + f"{nilai_sen // 100:,}".replace(",", ".")


# ---------- Sumber 1 + 2: Steam ----------
def ambil_diskon_steam(state):
    r = session.get(
        "https://www.cheapshark.com/api/1.0/deals",
        params={"storeID": 1, "onSale": 1, "sortBy": "Deal Rating", "pageSize": 60},
        timeout=30,
    )
    r.raise_for_status()

    kandidat = {}
    for d in r.json():
        if not d.get("steamAppID"):
            continue
        if int(d.get("steamRatingPercent") or 0) < MIN_RATING_STEAM:
            continue
        if int(d.get("steamRatingCount") or 0) < MIN_JUMLAH_ULASAN:
            continue
        kandidat[d["steamAppID"]] = d

    if not kandidat:
        return []

    # Cek harga Indonesia. Diskon di AS belum tentu berlaku di region ID.
    hasil = []
    ids = list(kandidat)
    for i in range(0, len(ids), 20):
        potong = ids[i:i + 20]
        r = session.get(
            "https://store.steampowered.com/api/appdetails",
            params={"appids": ",".join(potong), "cc": "id", "filters": "price_overview"},
            timeout=30,
        )
        r.raise_for_status()
        for appid, isi in r.json().items():
            harga = (isi.get("data") or {}).get("price_overview") if isi.get("success") else None
            if not harga or harga.get("currency") != "IDR":
                continue
            if harga["discount_percent"] < MIN_DISKON_PERSEN:
                continue
            kunci = f"steam:{appid}:{harga['final']}"
            if kunci in state:
                continue
            d = kandidat[appid]
            hasil.append({
                "kunci": kunci,
                "judul": d["title"],
                "diskon": harga["discount_percent"],
                "harga_awal": harga["initial"],
                "harga_akhir": harga["final"],
                "rating": d["steamRatingText"],
                "url": f"https://store.steampowered.com/app/{appid}/",
            })
        time.sleep(1.5)  # sopan ke server Steam

    hasil.sort(key=lambda x: x["diskon"], reverse=True)
    return hasil[:MAKS_ITEM_STEAM]


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
        berakhir = datetime.fromisoformat(tawaran["endDate"].replace("Z", "+00:00"))
        berakhir_wib = berakhir.astimezone(timezone(timedelta(hours=7)))
        hasil.append({
            "kunci": kunci,
            "judul": e["title"],
            "berakhir": berakhir_wib.strftime("%d/%m %H:%M WIB"),
            "url": f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games",
        })
    return hasil


# ---------- Susun pesan ----------
def susun_pesan(epic, steam):
    baris = [f"🎮 <b>Radar Diskon Game</b> — {datetime.now(timezone(timedelta(hours=7))):%d/%m/%Y}", ""]
    if epic:
        baris.append("🆓 <b>GRATIS di Epic</b>")
        for g in epic:
            baris.append(f'• <a href="{g["url"]}">{escape(g["judul"])}</a> — klaim sebelum {g["berakhir"]}')
        baris.append("")
    if steam:
        baris.append("🔥 <b>Diskon Steam (harga Indonesia)</b>")
        for g in steam:
            baris.append(
                f'• <a href="{g["url"]}">{escape(g["judul"])}</a> — <b>-{g["diskon"]}%</b> '
                f'{rupiah(g["harga_akhir"])} <s>{rupiah(g["harga_awal"])}</s> · {escape(g["rating"])}'
            )
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
    state = load_state()

    # Satu sumber gagal tidak boleh menggagalkan semuanya
    try:
        epic = ambil_gratis_epic(state)
    except Exception as err:
        print("Epic gagal:", err)
        epic = []
    try:
        steam = ambil_diskon_steam(state)
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
        save_state(state)


if __name__ == "__main__":
    main()
