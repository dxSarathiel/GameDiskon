# GameDiskon

Radar diskon game Steam dengan harga Rupiah asli, plus game gratis dari Epic Games Store. Semuanya jalan otomatis tiap sore lewat GitHub Actions.

- Situs: https://gamediskon.my.id
- Channel Telegram: https://t.me/diskongame
- Bot alarm harga: [@DiskonGame_bot](https://t.me/DiskonGame_bot)
- TikTok: [@game.diskon](https://www.tiktok.com/@game.diskon)

## Kenapa bikin ini

Kebanyakan situs diskon yang aku temukan nampilin harga dalam dolar. Masalahnya, Steam pakai harga regional, jadi harga di Indonesia sering beda jauh, dan diskon yang kelihatan heboh di luar negeri belum tentu semenarik itu di sini. Aku cuma pengin satu tempat yang langsung ngasih tahu: hari ini game apa yang beneran murah, dalam Rupiah, dicek langsung ke Steam Indonesia.

Awalnya cuma bot kecil yang posting ke Telegram. Lama-lama nambah situs, halaman riwayat harga, alarm harga, sampai video harian. Ini proyek sampingan, dikerjain di sela kerja kantor, jadi wajar kalau masih ada bagian yang kasar.

## Apa yang terjadi tiap sore

Workflow jalan tiap hari sekitar jam 17.17 WIB (jadwal GitHub kadang telat sedikit). Urutannya kira-kira begini:

1. Ambil kandidat diskon dari CheapShark, lalu cek harga Rupiah-nya satu per satu ke Steam Indonesia.
2. Ambil daftar game gratis (dan yang akan gratis) dari Epic.
3. Catat harga semua game yang dipantau ke `harga_idr.json`. Dari sini halaman riwayat harga dibuat.
4. Posting deal baru ke channel Telegram. Kalau hari itu nggak ada yang baru, bot tetap kirim pesan singkat.
5. Bangun ulang situs ke folder `docs/`, lalu hosting menarik isinya lewat `docs/bot/tarik.php`. Upload FTP cuma dipakai kalau cara itu gagal.
6. Cek alarm harga pengguna, kirim kabar ke yang targetnya tercapai.
7. Bikin video vertikal harian plus naskahnya, dikirim ke chat pribadiku buat diunggah ke TikTok.

Kalau ada yang rusak di tengah jalan, bot ngirim peringatan ke chat pribadiku, jadi aku nggak perlu buka tab Actions tiap hari.

Syarat diskon yang tampil di rak (bisa diubah di bagian atas `radar_diskon.py`): potongan minimal 50% di harga Indonesia, ulasan positif minimal 85%, dan minimal 500 ulasan. Game murah yang ulasannya jelek nggak bakal lolos.

## Isi repo

| File / folder | Isinya |
|---|---|
| `radar_diskon.py` | Otak bot. Ambil data, posting ke Telegram, dan manggil semua modul lain. |
| `halaman.py` | Beranda, sitemap, `robots.txt`, `.htaccess`. |
| `halaman_game.py` | Halaman per game (riwayat harga) dan daftar semua game. |
| `halaman_artikel.py` | Artikel panduan dari folder `artikel/`. |
| `info_game.py` | Rubrik Info Game: laporan harga mingguan, game gratis Epic mendatang, dan kabar mingguan. |
| `halaman_info.py` | Halaman Tentang, Kebijakan Privasi, Kontak. |
| `gaya.py` | Semua tampilan situs (CSS, menu, kaki halaman, favicon). Ubah warna atau huruf di sini. |
| `afiliasi.py` | Link afiliasi voucher Steam Wallet dan saran nominal voucher. |
| `gambar.py`, `video.py` | Gambar untuk postingan Telegram dan video vertikal harian. |
| `artikel/` | Artikel panduan, ditulis tangan dalam Markdown. |
| `info-game/` | Kabar mingguan untuk rubrik Info Game, juga Markdown. |
| `docs/` | Hasil situs yang sudah jadi. Jangan diedit manual, bakal ketimpa di run berikutnya. |
| `docs/bot/` | Skrip PHP yang jalan di hosting: bot alarm harga, penarik situs, pemeriksa alarm. |
| `harga_idr.json`, `sent.json` | Riwayat harga dan catatan deal yang sudah diposting. Diisi otomatis. |

## Nulis artikel atau kabar mingguan

Tinggal bikin file Markdown baru di `artikel/` (untuk panduan) atau `info-game/` (untuk kabar mingguan), terus commit. Bagian atasnya begini:

```markdown
---
judul: Judul yang tampil di halaman dan di Google
deskripsi: Satu-dua kalimat ringkasan
tanggal: 2026-10-04
---

Isi tulisannya di sini, pakai Markdown biasa.
```

Nama file jadi alamat halamannya. Kalau tulisannya belum siap terbit, tambahkan `draf: ya` di bagian atas. Untuk kabar mingguan, bot ngirim daftar bahan ke chat pribadiku tiap Sabtu, lengkap dengan templat nama file.

Di artikel panduan, baris `[[gratis-epic]]` otomatis diganti daftar game gratis Epic yang lagi berlaku hari itu.

## Kalau mau jalanin sendiri

Aku pakai Python 3.12, sama dengan versi di GitHub Actions.

```bash
pip install -r requirements.txt
python radar_diskon.py
```

Tanpa token Telegram, bot jalan dalam mode uji: data tetap diambil dan situs tetap dibangun ke `docs/`, tapi nggak ada yang dikirim ke mana-mana.

Untuk jalan penuh di GitHub Actions, secret yang dipakai:

| Secret | Buat apa |
|---|---|
| `TELEGRAM_TOKEN` | Token bot dari BotFather |
| `TELEGRAM_CHAT_ID` | Channel tujuan postingan |
| `TELEGRAM_OWNER_ID` | Chat pribadi pemilik, buat video harian dan peringatan |
| `ALARM_KUNCI` | Kunci buat manggil `tarik.php` dan `periksa.php` di hosting |
| `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD` | Cadangan upload kalau `tarik.php` gagal |

Token bot dan kunci-kunci di hosting disimpan di file `config.php` di luar folder situs, jadi nggak pernah masuk ke repo ini.

## Sumber data

Harga dari toko Steam region Indonesia dan CheapShark, game gratis dari Epic Games Store, dan daftar bahan kabar mingguan dari feed Steam, PC Gamer, dan GameSpot. GameDiskon nggak ada hubungannya dengan Valve, Epic Games, atau CheapShark. Harga bisa berubah sewaktu-waktu, jadi tetap cek di tokonya sebelum bayar.

Tombol voucher Steam Wallet di situs pakai link afiliasi Lapakgaming. Kalau ada yang beli lewat situ, aku dapat komisi kecil, dan harga buat pembelinya nggak nambah.

## Yang masih di daftar tunggu

- Statistik pengunjung (tanpa cookie).
- Game yang dicari lewat bot alarm otomatis ikut dipantau.
- Halaman khusus waktu Steam Autumn Sale.

Ada saran, nemu harga yang salah, atau mau ngobrol soal kerja sama? Kirim email ke kontak@gamediskon.my.id.
