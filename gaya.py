"""
Tautan afiliasi Lapakgaming untuk GameDiskon.

Semua pengaturan afiliasi ada di sini. Kalau suatu saat ingin mematikan semua
tautan afiliasi, ubah AKTIF menjadi False: situs dan Telegram kembali seperti biasa.

Komisi dicatat lewat parameter utm di tautan (bukan lewat kode promo).
Kode promo hanya memberi potongan untuk pembeli.
"""

from html import escape
from itertools import combinations_with_replacement

AKTIF = True

# Parameter pelacak dari dashboard affiliate Lapakgaming (jangan diubah)
UTM = "utm_campaign=Sarathiel&utm_source=Affiliate&utm_medium=LGA"
HALAMAN_STEAM_WALLET = "https://www.lapakgaming.com/id-id/voucher-steam-wallet"

KODE_PENGGUNA_BARU = "LGCSNEW"
KODE_SEMUA_PENGGUNA = "CREATORSID"

# Nominal voucher Steam Wallet IDR yang dijual (dalam Rupiah). Perbarui kalau daftarnya berubah.
NOMINAL_VOUCHER = [6000, 8000, 12000, 45000, 60000, 90000, 120000, 250000, 400000, 600000]
MAKS_LEMBAR = 3   # saran paling banyak 3 voucher sekaligus


def link_steam_wallet():
    return f"{HALAMAN_STEAM_WALLET}?{UTM}"


def _rp(rupiah):
    return "Rp " + f"{rupiah:,}".replace(",", ".")


def voucher_cocok(harga_sen):
    """Kombinasi voucher paling hemat yang totalnya cukup untuk membeli game.
    Kembalikan daftar nominal (Rupiah), misalnya [8000, 6000] untuk game Rp 13.999.
    Kalau harganya melebihi batas kombinasi, kembalikan None."""
    harga = -(-harga_sen // 100)  # sen -> Rupiah, dibulatkan ke atas
    if harga <= 0:
        return None
    terbaik = None
    for n in range(1, MAKS_LEMBAR + 1):
        for kombinasi in combinations_with_replacement(NOMINAL_VOUCHER, n):
            total = sum(kombinasi)
            if total < harga:
                continue
            kunci = (total, n)   # utamakan total paling kecil, lalu lembar paling sedikit
            if terbaik is None or kunci < terbaik[0]:
                terbaik = (kunci, sorted(kombinasi, reverse=True))
    return terbaik[1] if terbaik else None


def teks_voucher(nominal):
    bagian = [f"IDR {_rp(v)[3:]}" for v in nominal]
    return " + ".join(bagian)


# ---------- Tampilan di situs ----------
def blok_halaman_game(harga_sen):
    """Kotak saran voucher di halaman game. Kosong kalau afiliasi dimatikan."""
    if not AKTIF:
        return ""
    nominal = voucher_cocok(harga_sen)
    if nominal:
        total = sum(nominal)
        saran = (f'<p>Voucher Steam Wallet yang cukup untuk harga ini: <strong>{escape(teks_voucher(nominal))}</strong>'
                 + (f" (total {_rp(total)})" if len(nominal) > 1 else "") + ".</p>")
    else:
        saran = "<p>Isi saldo Steam Wallet dengan beberapa voucher sekaligus.</p>"
    return f"""
    <aside class="voucher" aria-labelledby="h-voucher">
      <h2 id="h-voucher">Tidak punya kartu kredit?</h2>
      <p>Isi saldo Steam Wallet dulu dengan voucher, bayar pakai QRIS atau e-wallet, lalu beli game-nya di Steam.</p>
      {saran}
      <p class="kode">Kode promo: <b>{KODE_PENGGUNA_BARU}</b> untuk pengguna baru, <b>{KODE_SEMUA_PENGGUNA}</b> untuk semua pengguna.</p>
      <a class="tombol" href="{escape(link_steam_wallet())}" rel="sponsored noopener">Beli voucher di Lapakgaming</a>
      <p class="ungkap">Tautan afiliasi: GameDiskon mendapat komisi kecil dari pembelianmu, tanpa biaya tambahan. <a href="/tentang/#afiliasi">Selengkapnya</a>.</p>
    </aside>"""


def blok_beranda():
    """Satu pita ajakan di beranda, di bawah rak diskon."""
    if not AKTIF:
        return ""
    return f"""
    <aside class="voucher lebar" aria-labelledby="h-voucher">
      <div>
        <h2 id="h-voucher">Bayar game Steam tanpa kartu kredit</h2>
        <p>Isi saldo Steam Wallet dengan voucher IDR, bayar pakai QRIS atau e-wallet. Kode promo <b>{KODE_PENGGUNA_BARU}</b> untuk pengguna baru, <b>{KODE_SEMUA_PENGGUNA}</b> untuk semua pengguna.</p>
        <p class="ungkap">Tautan afiliasi: GameDiskon mendapat komisi kecil tanpa biaya tambahan untukmu. <a href="/tentang/#afiliasi">Selengkapnya</a>.</p>
      </div>
      <a class="tombol" href="{escape(link_steam_wallet())}" rel="sponsored noopener">Beli voucher Steam Wallet</a>
    </aside>"""


# ---------- Telegram ----------
def baris_telegram():
    """Satu baris di akhir postingan Telegram. Kosong kalau afiliasi dimatikan."""
    if not AKTIF:
        return ""
    # Mode HTML Telegram mewajibkan & ditulis sebagai &amp; (termasuk di dalam alamat tautan)
    return (f'💳 <a href="{escape(link_steam_wallet())}">Isi saldo Steam Wallet di Lapakgaming</a> '
            f'(kode <b>{KODE_PENGGUNA_BARU}</b> untuk pengguna baru)')
