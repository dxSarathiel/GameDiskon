<?php
/*
 * Jalankan SEKALI setelah config.php dibuat:  https://gamediskon.my.id/bot/pasang.php?kunci=KUNCI_PERIKSA
 * Menyambungkan bot Telegram ke webhook.php dan mengisi daftar perintah bot.
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

if (!hash_equals((string)konfigurasi()['kunci_periksa'], (string)($_GET['kunci'] ?? ''))) { http_response_code(403); exit; }
header('Content-Type: text/plain; charset=utf-8');

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

$info = tg('getWebhookInfo', []);
echo "4. Status webhook: " . json_encode($info['result'] ?? $info, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT) . "\n";
echo "\nData harga: " . (is_file(FILE_HARGA) ? 'ada, ' . count(data_harga()['game']) . ' game' : 'BELUM ADA (jalankan workflow dulu)') . "\n";
