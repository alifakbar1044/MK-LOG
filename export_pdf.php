<?php
require 'vendor/autoload.php';  // pastikan path Dompdf benar

use Dompdf\Dompdf;

// Koneksi database
$host = "localhost";
$user = "root";
$password = "";
$database = "absensi_db";

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Koneksi gagal: " . $conn->connect_error);
}

// Ambil data absensi
$sql = "SELECT * FROM absensi ORDER BY tanggal DESC, waktu DESC";
$result = $conn->query($sql);

// Path logo
$logoPath = 'assets/log.png';
$logoBase64 = '';
if (file_exists($logoPath)) {
    $logoData = file_get_contents($logoPath);
    $logoBase64 = 'data:image/png;base64,' . base64_encode($logoData);
}

// Load gambar m.png untuk foto user default
$mPath = 'assets/m.png';
$mBase64 = '';
if (file_exists($mPath)) {
    $mData = file_get_contents($mPath);
    $mBase64 = 'data:image/png;base64,' . base64_encode($mData);
}

// Mulai bangun HTML PDF
$html = '
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: sans-serif; margin: 0; padding: 0; }
    .header {
      text-align: center;
      margin-bottom: 20px;
    }
    .header img {
      height: 60px;
      margin-bottom: 10px;
    }
    h2 {
      margin: 0;
      font-weight: 700;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }
    th, td {
      border: 1px solid #333;
      padding: 8px;
      vertical-align: middle;
      text-align: left;
    }
    th {
      background: #f2f2f2;
    }
    .foto {
      width: 50px;
      height: 50px;
      object-fit: cover;
      border-radius: 50%;
      border: 1px solid #ccc;
    }
  </style>
</head>
<body>
  <div class="header">';

if ($logoBase64 !== '') {
    $html .= '<img src="' . $logoBase64 . '" alt="Logo MK LOG">';
}

$html .= '<h2>Laporan Data Absensi</h2>
  </div>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Foto</th>
        <th>Nama</th>
        <th>Tanggal</th>
        <th>Waktu</th>
      </tr>
    </thead>
    <tbody>';

// Ambil data baris
if ($result && $result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $id = (int)$row['id'];

        // Pakai foto m.png dari assets sebagai gambar user
        $fotoBase64 = $mBase64;

        $html .= '<tr>
          <td>' . $id . '</td>
          <td><img src="' . $fotoBase64 . '" alt="Foto ' . htmlspecialchars($row['nama']) . '" class="foto"></td>
          <td>' . htmlspecialchars($row['nama']) . '</td>
          <td>' . htmlspecialchars($row['tanggal']) . '</td>
          <td>' . htmlspecialchars($row['waktu']) . '</td>
        </tr>';
    }
} else {
    $html .= '<tr><td colspan="5" style="text-align:center">Tidak ada data</td></tr>';
}

$html .= '
    </tbody>
  </table>
</body>
</html>';

// Inisialisasi Dompdf dan render PDF
$dompdf = new Dompdf();
$dompdf->loadHtml($html);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();

// Output PDF ke browser
$dompdf->stream("data_absensi.pdf", ["Attachment" => true]);

$conn->close();
?>
