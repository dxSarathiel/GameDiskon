<?php
/*
 * Pemasangan bot alarm harga. Buka di browser:  https://gamediskon.my.id/bot/pasang.php
 *
 * Pertama kali dibuka: kunci webhook dan kunci periksa dibuat otomatis, disimpan di luar
 * folder situs (kunci.json), dan KUNCI PERIKSA ditampilkan SEKALI untuk disalin ke GitHub.
 * Setelah itu halaman ini hanya bisa dibuka lagi dengan ?kunci=KUNCI_PERIKSA.
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

header('Content-Type: text/plain; charset=utf-8');
$kunci_baru = '';
if (konfigurasi()['kunci_periksa'] === '') {
    $kunci = ['webhook_rahasia' => bin2hex(random_bytes(24)), 'kunci_periksa' => bin2hex(random_bytes(24))];
    $file = FOLDER_RAHASIA . '/kunci.json';
    if (file_put_contents($file, json_encode($kunci)) === false) { exit("GAGAL menyimpan $file. Cek izin folder gamediskon-bot."); }
    chmod($file, 0600);
    konfigurasi(true);
    $kunci_baru = $kunci['kunci_periksa'];
} elseif (!kunci_cocok(konfigurasi()['kunci_periksa'], $_GET['kunci'] ?? '')) {
    http_response_code(403);
    exit("Bot sudah pernah dipasang. Untuk menjalankan ulang, buka halaman ini dengan ?kunci=KUNCI_PERIKSA");
}

$saya = tg('getMe', []);
echo "1. Cek token bot: " . (!empty($saya['ok']) ? "OK, bot @" . $saya['result']['username'] : "GAGAL: " . ($saya['description'] ?? '')) . "\n";

$w = tg('setWebhook', [
    'url' => SITUS . 'bot/webhook.php',
    'secret_token' => konfigurasi()['webhook_rahasia'],
    'allowed_updates' => ['message', 'callback_query'],
]);
echo "2. Pasang webhook: " . (!empty($w['ok']) ? 'OK' : 'GAGAL: ' . ($w['description'] ?? '')) . "\n";

$c = tg('setMyCommands', ['commands' => [
    ['command' => 'daftar', 'description' => 'Lihat dan hapus alarm harga'],
    ['command' => 'hapussemua', 'description' => 'Hapus semua alarm dan data chat'],
    ['command' => 'bantuan', 'description' => 'Cara memakai bot'],
]]);
echo "3. Daftar perintah: " . (!empty($c['ok']) ? 'OK' : 'GAGAL: ' . ($c['description'] ?? '')) . "\n";
echo "4. Data harga: " . (is_file(FILE_HARGA) ? 'OK, ' . count(data_harga()['game']) . ' game' : 'BELUM ADA (jalankan workflow dulu)') . "\n";

if ($kunci_baru) {
    echo "\n==========================================================\n";
    echo "KUNCI PERIKSA (hanya ditampilkan sekali ini):\n\n$kunci_baru\n\n";
    echo "Salin ke GitHub: Settings > Secrets and variables > Actions >\n";
    echo "New repository secret, nama ALARM_KUNCI, nilai = kunci di atas.\n";
    echo "==========================================================\n";
}
