# video_hf — template animasi video harian (HyperFrames)

Dipakai otomatis oleh `video.py` → `rakit_mp4_hyperframes()`:

1. sampul diunduh ke `assets/sampul/`
2. `rakit.py` mengisi `template/*.html` dengan data hari itu → `index.html` + `compositions/`
3. `npm run render` (versi CLI HyperFrames dikunci di `package.json`)

Kalau gagal, `video.py` kembali ke video slide Pillow. Matikan jalur ini dengan `VIDEO_HYPERFRAMES=0`.

Butuh: Node.js 22+, `ffmpeg` dan `ffprobe` di PATH (di GitHub Actions dipasang oleh workflow).

Suara TTS (opsional): set secret `ELEVENLABS_API_KEY`. `video.py` → `buat_suara()` membuat satu klip
per adegan ke `assets/suara/`, dan lama tiap adegan mengikuti panjang suara asli. Suara bawaan Iwan
(`1kNciG1jHVSuFBPoxdRZ`); ganti dengan variabel repo `ELEVENLABS_VOICE_ID`. Kalau TTS gagal, video
tetap dibuat tanpa suara.

Ubah tampilan di `template/`, bukan di `compositions/` (dibuat ulang setiap hari).
Rencana dan keputusan desain lengkap ada di proyek pengembangan `hyperframes-harian/`
(BRIEF.md, STORYBOARD.md, storyboard.html).
