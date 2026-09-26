<?php
/*
 * Inti bot alarm harga GameDiskon (dipakai webhook.php, periksa.php, pasang.php).
 *
 * Rahasia TIDAK disimpan di sini, karena repo ini publik. Semuanya ada di luar folder situs,
 * di folder /home/<akun-cpanel>/gamediskon-bot/ :
 *   config.php  -> dibuat manual, hanya berisi token bot
 *   kunci.json  -> dibuat otomatis oleh pasang.php (kunci webhook & kunci periksa)
 *   alarm.json  -> data alarm pengguna, dibuat otomatis
 */

if (!defined('GAMEDISKON_BOT')) { http_response_code(404); exit; }

define('FOLDER_RAHASIA', getenv('GAMEDISKON_BOT_DIR') ?: dirname(__DIR__, 2) . '/gamediskon-bot');
define('FILE_HARGA', dirname(__DIR__) . '/data/harga.json');
define('SITUS', 'https://gamediskon.my.id/');
define('MAKS_ALARM_PER_ORANG', 10);
define('MAKS_HASIL_CARI', 6);

// Tautan voucher Steam Wallet (afiliasi Lapakgaming), sama dengan afiliasi.py
define('LINK_VOUCHER', 'https://www.lapakgaming.com/id-id/voucher-steam-wallet?utm_campaign=Sarathiel&utm_source=Affiliate&utm_medium=LGA');
define('KODE_BARU', 'LGCSNEW');

function konfigurasi($muat_ulang = false) {
    static $k = null;
    if ($k === null || $muat_ulang) {
        $path = FOLDER_RAHASIA . '/config.php';
        if (!is_file($path)) { http_response_code(500); exit("config.php belum dibuat di " . FOLDER_RAHASIA); }
        $k = require $path;
        $file_kunci = FOLDER_RAHASIA . '/kunci.json';
        if (is_file($file_kunci)) { $k += (json_decode(file_get_contents($file_kunci), true) ?: []); }
        $k += ['webhook_rahasia' => '', 'kunci_periksa' => ''];
    }
    return $k;
}

// Cocokkan kunci kiriman dengan kunci tersimpan. Kunci kosong selalu ditolak.
function kunci_cocok($tersimpan, $kiriman) {
    return (string)$tersimpan !== '' && hash_equals((string)$tersimpan, (string)$kiriman);
}

// ---------- Telegram ----------
function tg($metode, $data) {
    $api = getenv('GAMEDISKON_API') ?: 'https://api.telegram.org';
    $url = $api . '/bot' . konfigurasi()['token'] . '/' . $metode;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 20,
    ]);
    $hasil = curl_exec($ch);
    curl_close($ch);
    $json = json_decode((string)$hasil, true);
    return is_array($json) ? $json : ['ok' => false, 'description' => 'tidak ada jawaban'];
}

function kirim($chat, $teks, $tombol = null) {
    $data = ['chat_id' => $chat, 'text' => $teks, 'parse_mode' => 'HTML', 'disable_web_page_preview' => true];
    if ($tombol) { $data['reply_markup'] = ['inline_keyboard' => $tombol]; }
    return tg('sendMessage', $data);
}

function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

function rupiah($sen) { return 'Rp ' . number_format(intdiv((int)$sen, 100), 0, ',', '.'); }

// ---------- Data harga (dibuat bot harian: docs/data/harga.json) ----------
function data_harga() {
    static $d = null;
    if ($d === null) {
        $d = is_file(FILE_HARGA) ? json_decode(file_get_contents(FILE_HARGA), true) : null;
        if (!is_array($d) || !isset($d['game'])) { $d = ['game' => [], 'diperbarui' => '']; }
    }
    return $d;
}

function game($appid) {
    $g = data_harga()['game'][(string)$appid] ?? null;
    if (!$g) { return null; }
    // Urutan kolom: nama, slug, harga sekarang, harga normal, diskon, termurah tercatat (semua dalam sen)
    return ['appid' => (string)$appid, 'nama' => $g[0], 'slug' => $g[1], 'harga' => (int)$g[2],
            'normal' => (int)$g[3], 'diskon' => (int)$g[4], 'termurah' => (int)$g[5]];
}

function url_halaman($g) {
    return SITUS . 'game/' . $g['appid'] . ($g['slug'] ? '-' . $g['slug'] : '') . '/';
}

function sederhanakan($s) {
    return trim(preg_replace('/[^a-z0-9]+/', ' ', strtolower($s)));
}

function cari_game($kata) {
    $q = sederhanakan($kata);
    if ($q === '') { return []; }
    $bagian = explode(' ', $q);
    $hasil = [];
    foreach (data_harga()['game'] as $appid => $g) {
        $nama = sederhanakan($g[0]);
        $cocok = true;
        foreach ($bagian as $b) { if (strpos($nama, $b) === false) { $cocok = false; break; } }
        if (!$cocok) { continue; }
        // Nama yang diawali kata kunci dan lebih pendek ditaruh di atas
        $skor = (strpos($nama, $q) === 0 ? 0 : 1) * 1000 + strlen($nama);
        $hasil[] = [$skor, (string)$appid];
    }
    usort($hasil, function ($a, $b) { return $a[0] <=> $b[0]; });
    return array_slice(array_map(function ($x) { return $x[1]; }, $hasil), 0, MAKS_HASIL_CARI);
}

// ---------- Penyimpanan alarm (file JSON di luar folder situs, dikunci saat ditulis) ----------
function ubah_data($fungsi) {
    if (!is_dir(FOLDER_RAHASIA)) { mkdir(FOLDER_RAHASIA, 0700, true); }
    $fp = fopen(FOLDER_RAHASIA . '/alarm.json', 'c+');
    flock($fp, LOCK_EX);
    $isi = stream_get_contents($fp);
    $data = json_decode($isi ?: '{}', true);
    if (!is_array($data)) { $data = []; }
    $data += ['alarm' => [], 'menunggu' => []];
    $hasil = $fungsi($data);
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    fflush($fp);
    flock($fp, LOCK_UN);
    fclose($fp);
    return $hasil;
}

function baca_data() { return ubah_data(function ($d) { return $d; }); }

function baris_voucher() {
    return '💳 <a href="' . h(LINK_VOUCHER) . '">Isi saldo Steam Wallet di Lapakgaming</a> (kode <b>' . KODE_BARU . '</b> untuk pengguna baru)';
}
