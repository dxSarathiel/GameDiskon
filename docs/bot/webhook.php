<?php
/*
 * Webhook bot alarm harga GameDiskon. Telegram mengirim setiap pesan ke sini.
 * Perintah: /start, /daftar, /hapussemua, /bantuan, atau cukup ketik nama game.
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

// Hanya terima kiriman yang membawa kunci rahasia webhook (diatur lewat pasang.php)
$kunci = $_SERVER['HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN'] ?? '';
if (!kunci_cocok(konfigurasi()['webhook_rahasia'], $kunci)) { http_response_code(403); exit; }

$update = json_decode(file_get_contents('php://input'), true);
if (!is_array($update)) { exit; }

if (isset($update['callback_query'])) {
    $q = $update['callback_query'];
    tg('answerCallbackQuery', ['callback_query_id' => $q['id']]);
    tangani_tombol((string)$q['message']['chat']['id'], (string)($q['data'] ?? ''));
} elseif (isset($update['message']['text'])) {
    $m = $update['message'];
    if (($m['chat']['type'] ?? '') === 'private') {       // abaikan grup dan channel
        tangani_pesan((string)$m['chat']['id'], trim($m['text']));
    }
}
echo 'ok';

// ---------------------------------------------------------------------------

function tangani_pesan($chat, $teks) {
    if (preg_match('/^\/start(?:\s+(\d+))?/', $teks, $m)) {
        if (!empty($m[1]) && game($m[1])) { tawarkan_target($chat, $m[1]); return; }
        kirim($chat, sambutan());
        return;
    }
    if (preg_match('/^\/(daftar|alarm)\b/', $teks)) { tampilkan_daftar($chat); return; }
    if (preg_match('/^\/hapussemua\b/', $teks)) {
        ubah_data(function (&$d) use ($chat) { unset($d['alarm'][$chat], $d['menunggu'][$chat]); });
        kirim($chat, 'Semua alarm-mu sudah dihapus, dan data chat-mu tidak lagi kami simpan.');
        return;
    }
    if (preg_match('/^\/(bantuan|help)\b/', $teks)) { kirim($chat, sambutan()); return; }
    if (preg_match('/^\/idsaya\b/', $teks)) {
        kirim($chat, 'ID chat kamu: <code>' . h($chat) . "</code>\n\nPemilik GameDiskon memakai ID ini untuk menerima video harian dari bot.");
        return;
    }
    if ($teks !== '' && $teks[0] === '/') { kirim($chat, 'Perintah itu tidak dikenal. Ketik /bantuan untuk melihat caranya.'); return; }

    // Sedang menunggu angka target untuk game yang baru dipilih?
    $menunggu = baca_data()['menunggu'][$chat] ?? null;
    $angka = baca_angka($teks);
    if ($menunggu && $angka !== null) { simpan_alarm($chat, $menunggu, $angka * 100); return; }

    // Selain itu, anggap sebagai pencarian nama game
    $hasil = cari_game($teks);
    if (!$hasil) {
        kirim($chat, 'Game dengan nama "<b>' . h($teks) . '</b>" belum ada di daftar yang kami pantau. '
            . 'Coba ketik sebagian namanya saja, misalnya <i>witcher</i>, atau lihat daftarnya di ' . SITUS . 'game/');
        return;
    }
    $tombol = [];
    foreach ($hasil as $appid) {
        $g = game($appid);
        $tombol[] = [['text' => $g['nama'] . ' (' . rupiah($g['harga']) . ')', 'callback_data' => 'pilih:' . $appid]];
    }
    kirim($chat, 'Pilih game yang kamu maksud:', $tombol);
}

function tangani_tombol($chat, $data) {
    $b = explode(':', $data);
    if ($b[0] === 'pilih' && isset($b[1])) { tawarkan_target($chat, $b[1]); }
    elseif ($b[0] === 'target' && isset($b[1], $b[2])) { simpan_alarm($chat, $b[1], (int)$b[2]); }
    elseif ($b[0] === 'hapus' && isset($b[1])) {
        ubah_data(function (&$d) use ($chat, $b) {
            $d['alarm'][$chat] = array_values(array_filter($d['alarm'][$chat] ?? [], function ($a) use ($b) { return $a['appid'] !== $b[1]; }));
            if (!$d['alarm'][$chat]) { unset($d['alarm'][$chat]); }
        });
        $g = game($b[1]);
        kirim($chat, 'Alarm untuk <b>' . h($g ? $g['nama'] : $b[1]) . '</b> sudah dihapus.');
    }
}

function tawarkan_target($chat, $appid) {
    $g = game($appid);
    if (!$g) { kirim($chat, 'Game itu tidak ditemukan.'); return; }
    $kini = $g['harga'];
    $normal = $g['normal'] ?: $kini;
    $pilihan = [];
    $tambah = function ($label, $target) use (&$pilihan, $kini) {
        $target = intdiv($target, 100) * 100;                      // bulatkan ke Rupiah penuh
        if ($target > 0 && $target < $kini && !isset($pilihan[$target])) { $pilihan[$target] = $label . ' (' . rupiah($target) . ')'; }
    };
    if ($kini >= $normal) {
        // Belum diskon: target dihitung dari harga normal
        $tambah('Diskon berapa pun', $normal - 100);
        $tambah('Setengah harga', intdiv($normal, 2));
        $tambah('Diskon 75%', intdiv($normal, 4));
    } else {
        // Sudah diskon: target dihitung dari harga sekarang
        $tambah('Lebih murah dari sekarang', $kini - 100);
        $tambah('Turun 25% lagi', intdiv($kini * 3, 4));
        $tambah('Turun 50% lagi', intdiv($kini, 2));
    }
    if ($g['termurah'] && $g['termurah'] < $kini) { $tambah('Setara termurah tercatat', $g['termurah']); }
    krsort($pilihan);
    $tombol = [];
    foreach ($pilihan as $target => $label) { $tombol[] = [['text' => $label, 'callback_data' => 'target:' . $appid . ':' . $target]]; }

    ubah_data(function (&$d) use ($chat, $appid) { $d['menunggu'][$chat] = $appid; });
    $status = $g['diskon'] > 0 ? 'sedang diskon ' . $g['diskon'] . '% menjadi <b>' . rupiah($kini) . '</b>' : 'sekarang <b>' . rupiah($kini) . '</b>';
    kirim($chat, '<b>' . h($g['nama']) . '</b> ' . $status . ' (harga normal ' . rupiah($normal) . ").\n\n"
        . 'Kabari kamu kalau harganya turun sampai berapa? Pilih di bawah, atau ketik angkanya, misalnya <i>50000</i> atau <i>50rb</i>.', $tombol);
}

function simpan_alarm($chat, $appid, $target) {
    $g = game($appid);
    if (!$g || $target <= 0) { kirim($chat, 'Target harga tidak valid.'); return; }
    if ($g['harga'] <= $target) {
        ubah_data(function (&$d) use ($chat) { unset($d['menunggu'][$chat]); });
        kirim($chat, 'Harga <b>' . h($g['nama']) . '</b> sekarang ' . rupiah($g['harga']) . ', sudah di bawah targetmu. '
            . 'Tidak perlu alarm, bisa langsung dibeli: <a href="https://store.steampowered.com/app/' . h($appid) . '/">buka di Steam</a>.');
        return;
    }
    $hasil = ubah_data(function (&$d) use ($chat, $appid, $target) {
        $daftar = array_values(array_filter($d['alarm'][$chat] ?? [], function ($a) use ($appid) { return $a['appid'] !== $appid; }));
        if (count($daftar) >= MAKS_ALARM_PER_ORANG) { return 'penuh'; }
        $daftar[] = ['appid' => $appid, 'target' => $target, 'dibuat' => date('Y-m-d')];
        $d['alarm'][$chat] = $daftar;
        unset($d['menunggu'][$chat]);
        return 'ok';
    });
    if ($hasil === 'penuh') {
        kirim($chat, 'Kamu sudah punya ' . MAKS_ALARM_PER_ORANG . ' alarm, batas maksimalnya. Hapus salah satu lewat /daftar dulu.');
        return;
    }
    kirim($chat, '🔔 Siap! Kamu akan dikabari kalau <b>' . h($g['nama']) . '</b> turun ke <b>' . rupiah($target) . "</b> atau lebih murah.\n\n"
        . 'Harga dicek sekali sehari setiap sore. Lihat semua alarm-mu dengan /daftar.');
}

function tampilkan_daftar($chat) {
    $daftar = baca_data()['alarm'][$chat] ?? [];
    if (!$daftar) { kirim($chat, 'Kamu belum punya alarm. Ketik nama game untuk memasang alarm pertama.'); return; }
    $baris = ['<b>Alarm harga kamu</b>'];
    $tombol = [];
    foreach ($daftar as $a) {
        $g = game($a['appid']);
        $nama = $g ? $g['nama'] : 'App ' . $a['appid'];
        $baris[] = '• ' . h($nama) . ': target ' . rupiah($a['target']) . ($g ? ', sekarang ' . rupiah($g['harga']) : '');
        $tombol[] = [['text' => '❌ Hapus ' . $nama, 'callback_data' => 'hapus:' . $a['appid']]];
    }
    kirim($chat, implode("\n", $baris), $tombol);
}

function baca_angka($teks) {
    $t = strtolower(str_replace(['rp', ' '], '', $teks));
    if (preg_match('/^(\d+(?:[.,]\d+)?)(rb|ribu|k)$/', $t, $m)) { return (int)round((float)str_replace(',', '.', $m[1]) * 1000); }
    $t = str_replace(['.', ','], '', $t);
    return ctype_digit($t) && strlen($t) <= 9 ? (int)$t : null;
}

function sambutan() {
    return "👋 Halo! Ini <b>alarm harga GameDiskon</b>.\n\n"
        . "Ketik nama game Steam, pilih target harganya, dan kamu akan dikabari di sini saat harganya di Steam Indonesia turun sampai target itu.\n\n"
        . "• Ketik nama game, misalnya <i>hades</i>\n"
        . "• /daftar untuk melihat dan menghapus alarm\n"
        . "• /hapussemua untuk menghapus semua alarm dan data chat-mu\n\n"
        . "Harga dicek sekali sehari setiap sore. Maksimal " . MAKS_ALARM_PER_ORANG . " alarm per orang.";
}
