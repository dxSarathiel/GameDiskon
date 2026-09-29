<?php
/*
 * Pemicu harian bot GameDiskon. Dijalankan Cron Job cPanel SETIAP JAM:
 *   /usr/local/bin/php /home/<akun>/public_html/bot/picu.php > /dev/null 2>&1
 *
 * Antara pukul 17.00 dan 20.59 WIB, skrip ini meminta GitHub menjalankan workflow
 * "Radar Diskon Game" sekarang juga (sekali sehari). Jadwal otomatis GitHub sering
 * terlambat berjam-jam; pemicu ini membuat bot selalu jalan sekitar jam 5 sore.
 * Butuh 'github_token' di config.php (token dengan izin Actions: Read and write).
 *
 * Tes manual (langsung memicu, abaikan jam):  php picu.php sekarang
 */
define('GAMEDISKON_BOT', true);
require __DIR__ . '/inti.php';

if (!dari_cron()) { http_response_code(404); exit; }

define('JAM_MULAI', 17);          // mulai coba jam 17.00 WIB
define('JAM_AKHIR', 20);          // coba ulang tiap jam sampai 20.59 WIB kalau gagal
define('WORKFLOW', 'radar-diskon.yml');

$paksa = in_array('sekarang', $argv ?? [], true);
$sekarang = new DateTime('now', new DateTimeZone('Asia/Jakarta'));
$jam = (int)$sekarang->format('G');
$hari_ini = $sekarang->format('Y-m-d');
$file_catatan = FOLDER_RAHASIA . '/picu-terakhir.txt';

if (!$paksa) {
    if ($jam < JAM_MULAI || $jam > JAM_AKHIR) { exit(0); }                      // belum/sudah lewat waktunya
    if (@trim(file_get_contents($file_catatan)) === $hari_ini) { exit(0); }      // hari ini sudah dipicu
}

$token = konfigurasi()['github_token'] ?? '';
if ($token === '') {
    echo "github_token belum diisi di config.php\n";
    kabari_pemilik("⚠️ picu.php: github_token belum diisi di config.php, bot tidak bisa dipicu dari hosting.");
    exit(1);
}

$ch = curl_init((getenv('GAMEDISKON_GITHUB_API') ?: 'https://api.github.com') . '/repos/' . REPO_GITHUB . '/actions/workflows/' . WORKFLOW . '/dispatches');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode(['ref' => 'main']),
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $token,
        'Accept: application/vnd.github+json',
        'X-GitHub-Api-Version: 2022-11-28',
        'User-Agent: GameDiskon-picu',
        'Content-Type: application/json',
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
]);
$jawab = curl_exec($ch);
$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($status === 204) {
    file_put_contents($file_catatan, $hari_ini);
    echo "Workflow dipicu ($hari_ini " . $sekarang->format('H:i') . " WIB)\n";
    exit(0);
}

$pesan = "HTTP $status " . substr((string)$jawab, 0, 200);
echo "Gagal memicu workflow: $pesan\n";
// Kabari pemilik hanya sekali per hari supaya tidak berulang tiap jam
$file_gagal = FOLDER_RAHASIA . '/picu-gagal.txt';
if (@trim(file_get_contents($file_gagal)) !== $hari_ini) {
    file_put_contents($file_gagal, $hari_ini);
    $saran = $status === 401 ? " Token salah atau kedaluwarsa, buat token baru." :
             ($status === 403 || $status === 404 ? " Periksa izin token (Actions: Read and write) dan repo yang dipilih." : "");
    kabari_pemilik("⚠️ picu.php gagal menjalankan bot di GitHub: $pesan.$saran Jadwal otomatis GitHub tetap jadi cadangan.");
}
exit(1);
