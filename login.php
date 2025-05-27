<?php
session_start();

$host = "localhost";
$user = "root";
$password = "";
$database = "absensi_db";
$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die("Koneksi gagal: " . $conn->connect_error);
}

$error = '';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if ($username === 'admin' && $password === '123') {
        $_SESSION['logged_in'] = true;
        $_SESSION['username'] = $username;
        header("Location: index.php");
        exit;
    } else {
        $error = "Username atau password salah!";
    }
}
?>

<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Login Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            height: 100vh;
            display: flex;
            background-color: #fff;
            font-family: 'Roboto Mono', monospace;
            color: #222;
        }

        .left-side {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #fff;
        }

        .left-side img {
            max-width: 320px; /* Ukuran gambar diperbesar */
            height: auto;
        }

        .right-side {
            flex: 1;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            padding-left: 80px; /* Login digeser ke kanan */
        }

        .login-form {
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 6.5rem 2rem;
    width: 390px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    text-align: center;
    border: 1px solid #ddd;
}

        .login-logo {
            width: 145px;
            margin-bottom: 1.5rem;
        }

        h3 {
            margin-bottom: 1.5rem;
            font-weight: 600;
            font-size: 1.4rem;
            letter-spacing: 1.5px;
            color: #222;
        }

        label {
            display: block;
            text-align: left;
            margin-bottom: 0.4rem;
            font-size: 0.9rem;
            color: #444;
        }

        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 0.6rem 0.8rem;
            margin-bottom: 1.2rem;
            border: 1px solid #aaa;
            border-radius: 3px;
            background-color: #fff;
            color: #222;
            font-size: 0.95rem;
            transition: border-color 0.3s ease;
            outline: none;
        }

        input[type="text"]:focus,
        input[type="password"]:focus {
            border-color: #000;
        }

        .btn-primary {
            width: 100%;
            padding: 0.7rem 0;
            font-size: 1rem;
            background-color: #222;
            color: #fff;
            border: none;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .btn-primary:hover {
            background-color: #555;
        }

        .alert {
            background-color: #f8d7da;
            color: #842029;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-weight: 600;
            font-size: 0.9rem;
            border: 1px solid #f5c2c7;
        }

        @media (max-width: 768px) {
            body {
                flex-direction: column;
            }

            .left-side img {
                max-width: 180px;
            }

            .right-side {
                justify-content: center;
                padding: 1.5rem;
            }

            .login-form {
                width: 90%;
            }
        }
    </style>
</head>
<body>
    <div class="left-side">
        <img src="assets/base.png" alt="Gambar Samping" />
    </div>
    <div class="right-side">
        <form method="POST" action="" class="login-form" autocomplete="off" spellcheck="false">
            <img src="assets/log.png" alt="Logo MK LOG" class="login-logo" />
            <h3></h3>

            <?php if ($error): ?>
                <div class="alert"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <label for="username">Username</label>
            <input type="text" id="username" name="username" required autofocus autocomplete="username" />

            <label for="password">Password</label>
            <input type="password" id="password" name="password" required autocomplete="current-password" />

            <button type="submit" class="btn-primary">Login</button>
        </form>
    </div>
</body>
</html>
