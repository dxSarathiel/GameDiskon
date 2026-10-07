"""
Rakit komposisi HyperFrames untuk video harian Game Diskon dari satu file data JSON.

Menulis index.html + compositions/<adegan>.html dari template/ (satu file per adegan,
satu file per kartu game supaya id di halaman rakitan tetap unik), lalu siap dirender:
    python rakit.py data-contoh.json
    npx hyperframes render

Durasi root komposisi dibaca statis saat kompilasi, jadi durasi harian harus ditulis di
sini, bukan lewat --variables.
"""

import glob
import html
import json
import math
import os
import re
import sys
from datetime import date

AKAR = os.path.dirname(os.path.abspath(__file__))
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

KATA_PER_DETIK = 2.6          # sama dengan video.py
MIN_PENUTUP = 5.8             # CTA ditahan >= 3 detik setelah semua elemen masuk
JEDA_SUARA = 0.15             # suara mulai sesaat setelah transisi masuk mendarat
EKOR_SUARA = 0.35             # napas setelah kalimat sebelum adegan berganti
EKOR_PENUTUP = 1.2            # penutup tetap tertahan sebentar setelah kalimat terakhir
# Lama tumpang-tindih tiap jenis transisi (detik)
TRANSISI = {"zoom": 0.55, "push": 0.45, "grid": 0.6, "fade": 0.6}
PALET_GRID = ["#1b1e2b", "#f6e146", "#12141e", "#262a3a", "#0a0b12"]   # tinta gelap dominan + satu aksen kuning (tema "Shonen Sale")


def lama(teks, minimal, maksimal):
    """Sama dengan _lama() di video.py: waktu membaca kalimat + jeda napas, dibatasi."""
    return max(minimal, min(maksimal, len((teks or "").split()) / KATA_PER_DETIK + 0.6))


def rupiah(sen):
    return "Rp " + f"{int(sen) // 100:,}".replace(",", ".")


def angka_rating(r):
    return int(str(r).rstrip("%") or 0)


def _template(nama):
    with open(os.path.join(AKAR, "template", nama), encoding="utf-8") as f:
        return f.read()


def _isi(teks, nilai):
    for k, v in nilai.items():
        teks = teks.replace("{{" + k + "}}", str(v))
    sisa = re.findall(r"\{\{[A-Z_]+\}\}", teks)
    if sisa:
        raise ValueError(f"Placeholder belum terisi: {sorted(set(sisa))}")
    return teks


def _e(teks):
    return html.escape(str(teks), quote=True)


def _r(x):
    return round(x, 3)


# ---------- Adegan ----------
def _pembuka(id_, data, steam, epic, tgl, dur, mulai):
    g0 = steam[0]
    pill = f'<div class="abs" id="{id_}-pill">+ GAME GRATIS<span class="jp">無料</span></div>' if epic else ""
    return _isi(_template("pembuka.html"), {
        "ID": id_, "SAMPUL": _e(g0["sampul"]), "DISKON": int(g0["diskon"]),
        "TGL_PENDEK": f"{tgl.day} {BULAN[tgl.month - 1]}",
        "TGL_PANJANG": f"{HARI[tgl.weekday()]}, {tgl.day} {BULAN[tgl.month - 1]} {tgl.year}",
        "JUMLAH": len(steam), "PILL": pill,
        "DATA": json.dumps({"mulai": _r(mulai), "durasi": _r(dur)}),
    })


def _game(id_, g, nomor, total, dur, mulai):
    seg = []
    for i in range(1, total + 1):
        if i < nomor:
            seg.append('<i class="seg"><b></b></i>')
        elif i == nomor:
            seg.append(f'<i class="seg"><b id="{id_}-seg"></b></i>')
        else:
            seg.append('<i class="seg kosong"><b></b></i>')
    badge = f'<div id="{id_}-badge">Termurah sejak dipantau</div>' if g.get("terendah_sejak") else ""
    rating = angka_rating(g["rating"])
    return _isi(_template("game.html"), {
        "ID": id_, "SEGMEN": "".join(seg), "NOMOR": nomor, "TOTAL": total,
        "SAMPUL": _e(g["sampul"]), "BADGE": badge, "JUDUL": _e(g["judul"]),
        "RATING": rating, "DISKON": int(g["diskon"]),
        "HARGA_AKHIR": rupiah(g["harga_akhir"]), "HARGA_AWAL": rupiah(g["harga_awal"]),
        "DATA": json.dumps({"mulai": _r(mulai), "durasi": _r(dur), "nomor": nomor, "rating": rating,
                            "awal": int(g["harga_awal"]) // 100, "akhir": int(g["harga_akhir"]) // 100}),
    })


def _gratis(id_, g, dur, mulai):
    return _isi(_template("gratis.html"), {
        "ID": id_, "GAMBAR": _e(g["gambar"]), "JUDUL": _e(g["judul"]), "BERAKHIR": _e(g["berakhir"]),
        "DATA": json.dumps({"mulai": _r(mulai), "durasi": _r(dur)}),
    })


def _penutup(id_, username_bot, link_channel, dur, mulai):
    baris, top = [], 1190
    for ket, isi in (("Alarm harga di Telegram", f"@{username_bot}" if username_bot else ""),
                     ("Info diskon harian", link_channel or "")):
        if isi:
            baris.append(f'<div class="abs tg" style="top: {top}px"><div class="ket">{_e(ket)}</div><div class="isi">{_e(isi)}</div></div>')
            top += 170
    return _isi(_template("penutup.html"), {
        "ID": id_, "TELEGRAM": "\n        ".join(baris),
        "DATA": json.dumps({"mulai": _r(mulai), "durasi": _r(dur)}),
    })


# ---------- Transisi (dijalankan di timeline utama, pada slot host) ----------
def _js_transisi(jenis, a, b, t, idx):
    A, B = f'"#el-{a}"', f'"#el-{b}"'
    if jenis == "zoom":
        return (f'      tl.to({A}, {{ scale: 2.2, opacity: 0, duration: 0.4, ease: "power3.in" }}, {t});\n'
                f'      tl.fromTo({B}, {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "power3.out" }}, {_r(t + 0.15)});\n')
    if jenis == "push":
        return (f'      tl.to({A}, {{ y: -1920, duration: 0.45, ease: "power3.inOut" }}, {t});\n'
                f'      tl.fromTo({B}, {{ y: 1920, opacity: 1 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power3.inOut" }}, {t});\n')
    if jenis == "fade":
        return (f'      tl.to({A}, {{ opacity: 0, duration: 0.6, ease: "power2.inOut" }}, {t});\n'
                f'      tl.fromTo({B}, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.inOut" }}, {t});\n')
    if jenis == "grid":
        return (f'      gsap.utils.toArray("#gd-{idx} i").forEach((c, k, s) => {{\n'
                f'        tl.fromTo(c, {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.18, ease: "power2.out" }}, {t} + k * (0.12 / s.length));\n'
                f'        tl.to(c, {{ opacity: 0, scale: 0.9, duration: 0.18, ease: "power2.in" }}, {_r(t + 0.32)} + k * (0.1 / s.length));\n'
                f'      }});\n'
                f'      tl.to({A}, {{ opacity: 0, duration: 0.02 }}, {_r(t + 0.3)});\n'
                f'      tl.fromTo({B}, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.02 }}, {_r(t + 0.3)});\n')
    raise ValueError(jenis)


def _sel_grid(idx, t):
    """Grid dissolve: 4x6 sel menutup layar beriak dari tengah, warna palet bergantian."""
    sel = []
    for r in range(6):
        for c in range(4):
            x, y = c * 270, r * 320
            jarak = math.hypot(x + 135 - 540, y + 160 - 960)
            sel.append((jarak, x, y))
    sel.sort()
    isi = "".join(f'<i style="left: {x}px; top: {y}px; background: {PALET_GRID[k % 5]}"></i>' for k, (_, x, y) in enumerate(sel))
    return (f'      <div id="gd-{idx}" class="clip grid-cells" data-start="{_r(t)}" data-duration="{TRANSISI["grid"]}" '
            f'data-track-index="5">{isi}</div>')


# ---------- Rakit ----------
def rakit(data, keluar=AKAR):
    steam = data["steam"][:5]
    if len(steam) < 2:
        raise ValueError("Perlu minimal 2 diskon Steam.")
    epic = (data.get("epic") or [])[:1]
    naskah = data.get("naskah", {})
    tgl = date.fromisoformat(data["tanggal"])

    # Suara TTS (opsional): {"pembuka": {"file", "durasi"}, "game": [...], "gratis": {...}, "penutup": {...}}
    # Ada suara → lama adegan mengikuti panjang suara asli; tanpa suara → perkiraan dari jumlah kata.
    suara = data.get("suara") or {}
    game_suara = suara.get("game") or [None] * len(steam)

    def lama_adegan(teks, minimal, maksimal, masuk, klip, ekor=EKOR_SUARA):
        if klip:
            mulai = TRANSISI[masuk] * 0.75 if masuk else 0.0
            return max(minimal, mulai + JEDA_SUARA + klip["durasi"] + ekor)
        return lama(teks, minimal, maksimal)

    adegan = [("pembuka", lama_adegan(naskah.get("pembuka"), 2.4, 4.5, None, suara.get("pembuka")), None, suara.get("pembuka"))]
    for i, g in enumerate(steam, 1):
        teks = (naskah.get("game") or [""] * len(steam))[i - 1]
        masuk = "zoom" if i == 1 else "push"
        adegan.append((f"game-{i}", lama_adegan(teks, 2.6, 6.0, masuk, game_suara[i - 1]), masuk, game_suara[i - 1]))
    if epic:
        adegan.append(("gratis", lama_adegan(naskah.get("gratis"), 3.0, 6.5, "grid", suara.get("gratis")), "grid", suara.get("gratis")))
    dur_penutup = max(MIN_PENUTUP, lama_adegan(naskah.get("penutup"), 3.4, 7.0, "fade", suara.get("penutup"), EKOR_PENUTUP))
    adegan.append(("penutup", dur_penutup, "fade", suara.get("penutup")))

    # Waktu: adegan berikut mulai sebelum yang sebelumnya selesai (tumpang tindih = lama transisi)
    rencana, t = [], 0.0
    for idx, (id_, dur, masuk, klip) in enumerate(adegan):
        if masuk:
            t -= TRANSISI[masuk]
        mulai = TRANSISI[masuk] * 0.75 if masuk else 0.0
        rencana.append({"id": id_, "mulai_global": _r(t), "durasi": _r(dur), "masuk": masuk, "mulai_lokal": _r(mulai), "idx": idx, "suara": klip})
        t += dur
    total = _r(t)

    os.makedirs(os.path.join(keluar, "compositions"), exist_ok=True)
    for lama_file in glob.glob(os.path.join(keluar, "compositions", "*.html")):
        os.remove(lama_file)

    with open(os.path.join(keluar, "compositions", "latar.html"), "w", encoding="utf-8") as f:
        f.write(_isi(_template("latar.html"), {"DATA": json.dumps({"durasi": total})}))
    slots = [f'      <div id="el-latar" data-composition-id="latar" data-composition-src="compositions/latar.html" '
             f'data-start="0" data-duration="{total}" data-track-index="0" data-width="1080" data-height="1920"></div>']
    trans = []
    for p in rencana:
        id_, dur, mulai = p["id"], p["durasi"], p["mulai_lokal"]
        if id_ == "pembuka":
            isi = _pembuka(id_, data, steam, epic, tgl, dur, mulai)
        elif id_.startswith("game-"):
            n = int(id_.split("-")[1])
            isi = _game(id_, steam[n - 1], n, len(steam), dur, mulai)
        elif id_ == "gratis":
            isi = _gratis(id_, epic[0], dur, mulai)
        else:
            isi = _penutup(id_, data.get("username_bot", ""), data.get("link_channel", ""), dur, mulai)
        with open(os.path.join(keluar, "compositions", f"{id_}.html"), "w", encoding="utf-8") as f:
            f.write(isi)
        slots.append(f'      <div id="el-{id_}" data-composition-id="{id_}" data-composition-src="compositions/{id_}.html" '
                     f'data-start="{p["mulai_global"]}" data-duration="{dur}" data-track-index="{1 + p["idx"] % 2}" '
                     f'data-width="1080" data-height="1920"></div>')
        if p["masuk"]:
            sebelum = rencana[p["idx"] - 1]["id"]
            trans.append(_js_transisi(p["masuk"], sebelum, id_, p["mulai_global"], p["idx"]))
            if p["masuk"] == "grid":
                slots.append(_sel_grid(p["idx"], p["mulai_global"]))
        if p["suara"]:
            # Satu <audio> per adegan (id wajib, kalau tidak mixer melewatkannya); trek bergantian supaya tidak bertumpuk
            slots.append(f'      <audio id="vo-{id_}" src="{_e(p["suara"]["file"])}" data-start="{_r(p["mulai_global"] + mulai + JEDA_SUARA)}" '
                         f'data-duration="{_r(p["suara"]["durasi"])}" data-track-index="{10 + p["idx"] % 2}" data-volume="1"></audio>')

    index = _isi(_template("index.html"), {"DURASI": total, "SLOTS": "\n".join(slots), "TRANSISI": "".join(trans)})
    with open(os.path.join(keluar, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)
    return {"durasi": total, "adegan": rencana, "dengan_suara": any(p["suara"] for p in rencana)}


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(AKAR, "data-contoh.json"), encoding="utf-8") as f:
        hasil = rakit(json.load(f))
    for p in hasil["adegan"]:
        print(f'{p["id"]:<9} {p["mulai_global"]:>6.2f}s  +{p["durasi"]:.2f}s  masuk: {p["masuk"] or "-":<5}  suara: {p["suara"]["durasi"] if p["suara"] else "-"}')
    print(f'total {hasil["durasi"]:.2f}s')
