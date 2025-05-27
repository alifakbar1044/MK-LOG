<?php
// koneksi database
$host = "localhost";
$user = "root";
$password = "";
$database = "absensi_db";

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Koneksi gagal: " . $conn->connect_error);
}

// header untuk download Excel
header("Content-Type: application/vnd.ms-excel; charset=utf-8");
header("Content-Disposition: attachment; filename=data_absensi.xls");
header("Pragma: no-cache");
header("Expires: 0");

// judul kolom
echo "ID\tNama\tTanggal\tWaktu\n";

// query data
$sql = "SELECT * FROM absensi ORDER BY tanggal DESC, waktu DESC";
$result = $conn->query($sql);

// cetak baris data
if ($result && $result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        echo $row["id"] . "\t"
           . $row["nama"] . "\t"
           . $row["tanggal"] . "\t"
           . $row["waktu"] . "\n";
    }
} else {
    echo "Tidak ada data\n";
}

$conn->close();
