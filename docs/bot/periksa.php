<?php
/*
 * Dijalankan Cron Job cPanel tiap 2 jam (cara utama), atau dipanggil lewat web dengan header X-Kunci.
 * Mencocokkan semua alarm dengan harga terbaru, mengirim kabar, lalu menghapus alarm yang sudah terpenuhi.
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

$kunci = $_SERVER['HTTP_X_KUNCI'] ?? '';
if (!dari_cron() && ($_SERVER['REQUEST_METHOD'] !== 'POST' || !kunci_cocok(konfigurasi()['kunci_periksa'], $kunci))) {
    http_response_code(403); exit;
}
if (!dari_cron()) { header('Content-Type: application/json'); }

$terpenuhi = [];   // [chat, appid, target]
$semua = baca_data()['alarm'];
foreach ($semua as $chat => $daftar) {
    foreach ($daftar as $a) {
        $g = game($a['appid']);
        if ($g && $g['harga'] <= $a['target']) { $terpenuhi[] = [(string)$chat, $a['appid'], $a['target'], $g]; }
    }
}

$terkirim = 0; $diblokir = [];
foreach ($terpenuhi as list($chat, $appid, $target, $g)) {
    if (isset($diblokir[$chat])) { continue; }
    $teks = '🔔 <b>Alarm harga!</b> ' . h($g['nama']) . ' sekarang <b>' . rupiah($g['harga']) . '</b>'
        . ($g['diskon'] > 0 ? ' (diskon ' . $g['diskon'] . '%)' : '') . ', sudah mencapai targetmu (' . rupiah($target) . ").\n\n"
        . '🛒 <a href="https://store.steampowered.com/app/' . h($appid) . '/">Beli di Steam</a>' . "\n"
        . '📈 <a href="' . h(url_halaman($g)) . '">Riwayat harganya</a>' . "\n"
        . baris_voucher() . "\n\n"
        . 'Alarm ini sudah dihapus. Kirim nama game-nya lagi kalau ingin memasang alarm baru.';
    $jawab = kirim($chat, $teks);
    if (!empty($jawab['ok'])) { $terkirim++; }
    elseif (($jawab['error_code'] ?? 0) == 403) { $diblokir[$chat] = true; }   // pengguna memblokir bot
    usleep(60000);   // jangan melebihi batas kirim Telegram
}

// Hapus alarm yang sudah dikabarkan, dan semua data pengguna yang memblokir bot
ubah_data(function (&$d) use ($terpenuhi, $diblokir) {
    foreach ($terpenuhi as list($chat, $appid)) {
        $d['alarm'][$chat] = array_values(array_filter($d['alarm'][$chat] ?? [], function ($a) use ($appid) { return $a['appid'] !== $appid; }));
        if (!$d['alarm'][$chat]) { unset($d['alarm'][$chat]); }
    }
    foreach (array_keys($diblokir) as $chat) { unset($d['alarm'][$chat], $d['menunggu'][$chat]); }
});

$jumlah = 0;
foreach ($semua as $daftar) { $jumlah += count($daftar); }
echo json_encode(['alarm_aktif' => $jumlah, 'terpenuhi' => count($terpenuhi), 'terkirim' => $terkirim,
                  'pengguna_memblokir' => count($diblokir), 'data_harga' => data_harga()['diperbarui']]);
