<?php
session_start();
if (!isset($_SESSION['logged_in']) || $_SESSION['logged_in'] !== true) {
    header("Location: login.php");
    exit;
}

$host = "localhost";
$user = "root";
$password = "";
$database = "absensi_db";

$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Koneksi gagal: " . $conn->connect_error);
}

// --- PROSES CRUD ---

// Create atau Update data
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $old_id = isset($_POST['old_id']) ? (int)$_POST['old_id'] : 0;
    $new_id = isset($_POST['id']) ? (int)$_POST['id'] : 0;
    $nama = $conn->real_escape_string($_POST['nama'] ?? '');
    $tanggal = $conn->real_escape_string($_POST['tanggal'] ?? '');
    $waktu = $conn->real_escape_string($_POST['waktu'] ?? '');

    // Validasi sederhana
    if ($new_id > 0 && $nama && $tanggal && $waktu) {

        // Cek apakah new_id sudah ada di database (kecuali jika sama dengan old_id)
        if ($new_id !== $old_id) {
            $check = $conn->query("SELECT id FROM absensi WHERE id = $new_id");
            if ($check && $check->num_rows > 0) {
                // ID baru sudah ada, tampilkan error dan stop proses
                echo "<script>alert('ID $new_id sudah digunakan, silakan pilih ID lain.');window.history.back();</script>";
                exit;
            }
        }

        if ($old_id > 0) {
            // Update data, termasuk id jika berubah
            $sql = "UPDATE absensi SET id=$new_id, nama='$nama', tanggal='$tanggal', waktu='$waktu' WHERE id=$old_id";
            if ($conn->query($sql) === false) {
                die("Error saat update data: " . $conn->error);
            }

            // Rename foto lama jika ada dan id berubah
            if ($old_id !== $new_id) {
                $oldFotoPath = "uploads/{$old_id}.jpg";
                $newFotoPath = "uploads/{$new_id}.jpg";
                if (file_exists($oldFotoPath)) {
                    rename($oldFotoPath, $newFotoPath);
                }
            }
        } else {
            // Insert data baru dengan id manual (harus pastikan tidak auto_increment di DB)
            $sql = "INSERT INTO absensi (id, nama, tanggal, waktu) VALUES ($new_id, '$nama', '$tanggal', '$waktu')";
            if ($conn->query($sql) === false) {
                die("Error saat insert data: " . $conn->error);
            }
        }

        // Upload foto jika ada
        if (isset($_FILES['foto']) && $_FILES['foto']['error'] === UPLOAD_ERR_OK) {
            $ext = pathinfo($_FILES['foto']['name'], PATHINFO_EXTENSION);
            $allowed = ['jpg','jpeg','png'];
            if (in_array(strtolower($ext), $allowed)) {
                move_uploaded_file($_FILES['foto']['tmp_name'], "uploads/$new_id.jpg");
            }
        }

        header("Location: data_absensi.php");
        exit;
    }
}

// Delete data
if (isset($_GET['delete'])) {
    $delete_id = (int)$_GET['delete'];
    if ($delete_id > 0) {
        $conn->query("DELETE FROM absensi WHERE id=$delete_id");
        // Hapus file foto jika ada
        $fotoPath = "uploads/$delete_id.jpg";
        if (file_exists($fotoPath)) {
            unlink($fotoPath);
        }
        header("Location: data_absensi.php");
        exit;
    }
}

// Ambil data untuk edit (jika ada ?edit=ID)
$editData = null;
if (isset($_GET['edit'])) {
    $edit_id = (int)$_GET['edit'];
    $res = $conn->query("SELECT * FROM absensi WHERE id=$edit_id");
    if ($res && $res->num_rows > 0) {
        $editData = $res->fetch_assoc();
    }
}

// Ambil semua data absensi
$result = $conn->query("SELECT * FROM absensi ORDER BY tanggal DESC, waktu DESC");

?>

<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <title>Data Absensi</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet" />
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #fff;
      color: #000;
    }
    .card {
      border: 1px solid #dee2e6;
      border-radius: 0.75rem;
    }
    .btn-custom {
      border-radius: 50px;
      padding: 0.5rem 1.5rem;
      font-weight: 600;
    }
    .table thead {
      background-color: #f8f9fa;
    }
    .table-hover tbody tr:hover {
      background-color: #f2f2f2;
    }
    .logo {
      height: 40px;
    }
    .header-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem 0;
      border-bottom: 1px solid #ccc;
    }
    .profile-img {
      height: 40px;
      width: 40px;
      object-fit: cover;
      border-radius: 50%;
      display: inline-block;
    }
    svg.profile-img {
      background: #eee;
      padding: 4px;
      box-sizing: content-box;
    }
    form label {
      font-weight: 600;
    }
    .form-section {
      margin-top: 2rem;
    }
  </style>
</head>
<body>
  <div class="container py-4">
    <div class="header-bar mb-4">
      <div class="d-flex align-items-center">
        <img src="assets/log.png" alt="Logo" class="logo me-3" />
        <h4 class="mb-0">Data Absensi</h4>
      </div>
      <div>
        <a href="index.php" class="btn btn-outline-dark btn-custom me-2">Kembali</a>
        <a href="export_excel.php" target="_blank" class="btn btn-dark btn-custom me-2">Unduh Excel</a>
        <a href="export_pdf.php" target="_blank" class="btn btn-dark btn-custom">Unduh PDF</a>
      </div>
    </div>

    <!-- FORM TAMBAH / EDIT -->
    <div class="card form-section p-4">
      <h5><?= $editData ? 'Edit Data Absensi' : 'Tambah Data Absensi' ?></h5>
      <form action="data_absensi.php" method="POST" enctype="multipart/form-data" class="row g-3">
        <input type="hidden" name="old_id" value="<?= $editData ? (int)$editData['id'] : 0 ?>" />
        <div class="col-md-2">
          <label for="id" class="form-label">ID</label>
          <input
            type="number"
            name="id"
            id="id"
            class="form-control"
            required
            value="<?= $editData ? (int)$editData['id'] : '' ?>"
            min="1"
          />
        </div>
        <div class="col-md-4">
          <label for="nama" class="form-label">Nama</label>
          <input
            type="text"
            name="nama"
            id="nama"
            class="form-control"
            required
            value="<?= $editData ? htmlspecialchars($editData['nama']) : '' ?>"
          />
        </div>
        <div class="col-md-3">
          <label for="tanggal" class="form-label">Tanggal</label>
          <input
            type="date"
            name="tanggal"
            id="tanggal"
            class="form-control"
            required
            value="<?= $editData ? htmlspecialchars($editData['tanggal']) : '' ?>"
          />
        </div>
        <div class="col-md-3">
          <label for="waktu" class="form-label">Waktu</label>
          <input
            type="time"
            name="waktu"
            id="waktu"
            class="form-control"
            required
            value="<?= $editData ? htmlspecialchars($editData['waktu']) : '' ?>"
          />
        </div>
        <div class="col-md-2">
          <label for="foto" class="form-label">Foto (jpg/png)</label>
          <input type="file" name="foto" id="foto" class="form-control" accept=".jpg,.jpeg,.png" <?= $editData ? '' : 'required' ?> />
        </div>
        <div class="col-12">
          <button type="submit" class="btn btn-primary btn-custom">
            <?= $editData ? 'Update Data' : 'Tambah Data' ?>
          </button>
          <?php if($editData): ?>
            <a href="data_absensi.php" class="btn btn-secondary btn-custom ms-2">Batal</a>
          <?php endif; ?>
        </div>
      </form>
    </div>

    <!-- TABEL DATA -->
    <div class="card mt-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover mb-0">
            <caption class="caption text-muted px-3 pt-2">Data absensi terbaru berdasarkan tanggal dan waktu</caption>
            <thead>
              <tr>
                <th>ID</th>
                <th>Foto</th>
                <th>Nama</th>
                <th>Tanggal</th>
                <th>Waktu</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              <?php if ($result && $result->num_rows > 0): ?>
                <?php while($row = $result->fetch_assoc()): ?>
                  <?php
                    $id      = (int)$row["id"];
                    $path    = "uploads/{$id}.jpg";
                    $fotoSrc = file_exists($path) ? $path : null;
                  ?>
                  <tr>
                    <td><?= $id ?></td>
                    <td>
                      <?php if ($fotoSrc): ?>
                        <img src="<?= $fotoSrc ?>" alt="Foto <?= htmlspecialchars($row['nama']) ?>" class="profile-img" />
                      <?php else: ?>
                        <svg
                          class="profile-img"
                          xmlns="http://www.w3.org/2000/svg"
                          viewBox="0 0 64 64"
                          fill="none"
                          stroke="#000"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <circle cx="32" cy="32" r="30" fill="#fff" />
                          <circle cx="20" cy="24" r="5" fill="#000" />
                          <circle cx="44" cy="24" r="5" fill="#000" />
                          <path d="M20 44c4 4 20 4 20 0" stroke="#000" stroke-width="3" />
                        </svg>
                      <?php endif; ?>
                    </td>
                    <td><?= htmlspecialchars($row["nama"]) ?></td>
                    <td><?= htmlspecialchars($row["tanggal"]) ?></td>
                    <td><?= htmlspecialchars($row["waktu"]) ?></td>
                    <td>
                      <a href="?edit=<?= $id ?>" class="btn btn-sm btn-warning">Edit</a>
                      <a href="?delete=<?= $id ?>" class="btn btn-sm btn-danger" onclick="return confirm('Yakin ingin menghapus data ini?')">Hapus</a>
                    </td>
                  </tr>
                <?php endwhile; ?>
              <?php else: ?>
                <tr>
                  <td colspan="6" class="text-center py-4">Belum ada data absensi.</td>
                </tr>
              <?php endif; ?>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</body>
</html>

<?php $conn->close(); ?>
