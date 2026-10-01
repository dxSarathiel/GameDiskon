"""
Detail game dari toko Steam (genre, developer, publisher, tanggal rilis, fitur, deskripsi singkat).

Dipakai halaman_game.py supaya setiap halaman game punya isi yang khas, bukan hanya harga.
Detail disimpan di harga_idr.json (kunci "info") dan hanya diambil ulang setiap 30 hari,
dengan batas sekian game per run supaya tidak terkena pembatasan Steam.
"""

import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape

MAKS_PER_RUN = 50          # Steam membatasi sekitar 200 permintaan per 5 menit
JEDA_DETIK = 1.2
SEGARKAN_SETELAH_HARI = 30


def _bersihkan(teks):
    teks = unescape(re.sub(r"<[^>]+>", " ", teks or ""))
    return re.sub(r"\s+", " ", teks).strip()


def ambil_detail(appid, session):
    """Detail satu game, atau None kalau Steam tidak punya datanya."""
    r = session.get("https://store.steampowered.com/api/appdetails",
                    params={"appids": appid, "cc": "id", "l": "indonesian"}, timeout=30)
    if r.status_code == 429:
        raise RuntimeError("dibatasi Steam (429)")
    r.raise_for_status()
    isi = (r.json() or {}).get(str(appid)) or {}
    if not isi.get("success"):
        return None
    d = isi.get("data") or {}
    rilis = (d.get("release_date") or {}).get("date", "")
    return {
        "deskripsi": _bersihkan(d.get("short_description"))[:400],
        "genre": [g["description"] for g in d.get("genres", [])][:4],
        "developer": (d.get("developers") or [])[:2],
        "publisher": (d.get("publishers") or [])[:2],
        "rilis": rilis,
        "fitur": [c["description"] for c in d.get("categories", [])][:6],
        "diambil": datetime.now(timezone.utc).date().isoformat(),
    }


def lengkapi_detail(riwayat, session, utamakan=(), catat_masalah=print):
    """Isi detail untuk game yang belum punya (atau sudah lama). Kembalikan jumlah yang diperbarui.
    utamakan: appid yang didahulukan, misalnya game yang sedang tampil di rak diskon."""
    batas = (datetime.now(timezone.utc) - timedelta(days=SEGARKAN_SETELAH_HARI)).date().isoformat()
    perlu = [a for a, g in riwayat.items() if (g.get("info") or {}).get("diambil", "") < batas]
    prioritas = set(map(str, utamakan))
    # Didahulukan: yang sedang tampil di rak, lalu yang paling lama dipantau (paling dekat masuk Google)
    perlu.sort(key=lambda a: (a not in prioritas, riwayat[a].get("mulai") or "9999"))
    jumlah = 0
    for appid in perlu[:MAKS_PER_RUN]:
        try:
            detail = ambil_detail(appid, session)
        except Exception as err:
            if "429" in str(err):
                print("Steam membatasi permintaan detail, dilanjutkan di run berikutnya.")
                break
            print(f"Detail {appid} gagal: {err}")
            continue
        if detail:
            riwayat[appid]["info"] = detail
            jumlah += 1
        else:
            # Tetap dicatat supaya tidak diambil ulang setiap hari
            riwayat[appid]["info"] = {"diambil": datetime.now(timezone.utc).date().isoformat()}
        time.sleep(JEDA_DETIK)
    sisa = len(perlu) - min(len(perlu), MAKS_PER_RUN)
    print(f"Detail Steam: {jumlah} game diperbarui, {sisa} menunggu run berikutnya.")
    return jumlah
