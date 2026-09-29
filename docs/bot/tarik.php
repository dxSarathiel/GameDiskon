<?php
/*
 * Menerbitkan situs dengan cara MENARIK isi folder docs/ langsung dari GitHub (lewat HTTPS),
 * sebagai pengganti upload FTP yang sering timeout.
 *
 * Cara utama: Cron Job cPanel menjalankannya tiap 30 menit (tidak lewat web, jadi tidak kena anti-bot):
 *   /usr/local/bin/php /home/<akun>/public_html/bot/tarik.php
 * Cara lama (masih bisa): POST https://gamediskon.my.id/bot/tarik.php?sha=<commit> dengan header X-Kunci.
 * Hanya file di dalam docs/ yang disalin, dan hanya file yang isinya berubah yang ditulis ulang.
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

define('REPO', 'dxsarathiel/GameDiskon');

function selesai($data, $kode = 200) {
    if (dari_cron()) {
        echo json_encode($data) . "\n";
        if (empty($data['ok'])) {
            kabari_pemilik("⚠️ tarik.php gagal menerbitkan situs: " . ($data['pesan'] ?? 'tanpa keterangan'));
        }
        exit(empty($data['ok']) ? 1 : 0);
    }
    http_response_code($kode); echo json_encode($data); exit;
}
if (!dari_cron()) { header('Content-Type: application/json'); }

if (!dari_cron() && ($_SERVER['REQUEST_METHOD'] !== 'POST' || !kunci_cocok(konfigurasi()['kunci_periksa'], $_SERVER['HTTP_X_KUNCI'] ?? ''))) {
    selesai(['ok' => false, 'pesan' => 'ditolak'], 403);
}
if (!class_exists('ZipArchive')) { selesai(['ok' => false, 'pesan' => 'PHP di hosting tidak punya modul zip'], 500); }
@set_time_limit(240);
$mulai_waktu = microtime(true);

$sha = $_GET['sha'] ?? '';
$ref = preg_match('/^[0-9a-f]{40}$/', $sha) ? $sha : 'refs/heads/main';
$url = (getenv('GAMEDISKON_ZIP_BASE') ?: 'https://codeload.github.com/' . REPO . '/zip/') . $ref;

// 1. Unduh arsip repo ke folder rahasia (di luar folder situs)
$file_zip = FOLDER_RAHASIA . '/terbit.zip';
$fp = fopen($file_zip, 'w');
$ch = curl_init($url);
curl_setopt_array($ch, [CURLOPT_FILE => $fp, CURLOPT_FOLLOWLOCATION => true, CURLOPT_TIMEOUT => 120,
                        CURLOPT_USERAGENT => 'GameDiskon-terbit']);
$berhasil = curl_exec($ch);
$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);
fclose($fp);
if (!$berhasil || $status !== 200) { @unlink($file_zip); selesai(['ok' => false, 'pesan' => "unduh arsip gagal (HTTP $status)"], 502); }

// 2. Salin isi docs/ ke folder situs, hanya yang berubah
$zip = new ZipArchive();
if ($zip->open($file_zip) !== true) { @unlink($file_zip); selesai(['ok' => false, 'pesan' => 'arsip tidak bisa dibuka'], 500); }
$tujuan = dirname(__DIR__);          // folder situs (public_html)
$ditulis = 0; $sama = 0; $dilewati = 0;
for ($i = 0; $i < $zip->numFiles; $i++) {
    $nama = $zip->getNameIndex($i);
    // Nama di arsip: GameDiskon-<ref>/docs/...
    $bagian = explode('/', $nama, 3);
    if (count($bagian) < 3 || $bagian[1] !== 'docs' || $bagian[2] === '' || substr($nama, -1) === '/') { continue; }
    $relatif = $bagian[2];
    if (strpos($relatif, '..') !== false || $relatif[0] === '/' || basename($relatif) === '.nojekyll') { $dilewati++; continue; }
    $isi = $zip->getFromIndex($i);
    $path = $tujuan . '/' . $relatif;
    if (is_file($path) && md5_file($path) === md5($isi)) { $sama++; continue; }
    if (!is_dir(dirname($path))) { mkdir(dirname($path), 0755, true); }
    file_put_contents($path . '.baru', $isi);
    rename($path . '.baru', $path);   // ganti sekaligus, supaya pengunjung tidak melihat file setengah jadi
    $ditulis++;
}
$zip->close();
@unlink($file_zip);

selesai(['ok' => true, 'ref' => $ref, 'ditulis' => $ditulis, 'tidak_berubah' => $sama,
         'dilewati' => $dilewati, 'detik' => round(microtime(true) - $mulai_waktu, 1)]);
