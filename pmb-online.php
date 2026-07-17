<?php
// 1. KONFIGURASI DATABASE & AUTO-SETUP
$host = "localhost";
$username = "root";
$password = "";
$dbname = "pmb_online";

try {
    // Koneksi awal tanpa nama database untuk mengecek/membuat database
    $pdo = new PDO("mysql:host=$host", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    // Buat database jika belum ada
    $pdo->exec("CREATE DATABASE IF NOT EXISTS `$dbname` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci");
    
    // Masuk ke database pmb_online
    $pdo->exec("USE `$dbname`");
    
    // Buat tabel users jika belum ada
    $pdo->exec("CREATE TABLE IF NOT EXISTS `users` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `name` VARCHAR(100) NOT NULL,
        `email` VARCHAR(100) NOT NULL UNIQUE,
        `password` VARCHAR(255) NOT NULL,
        `role` ENUM('user', 'admin') DEFAULT 'user',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB");

    // Buat tabel applications jika belum ada
    $pdo->exec("CREATE TABLE IF NOT EXISTS `applications` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `nik` VARCHAR(20) NOT NULL,
        `phone` VARCHAR(20) NOT NULL,
        `prodi` VARCHAR(100) NOT NULL,
        `photo` LONGTEXT NOT NULL,
        `status` ENUM('Menunggu', 'Diterima', 'Ditolak') DEFAULT 'Menunggu',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB");

} catch (PDOException $e) {
    die("Koneksi atau Setup Database Gagal: " . $e->getMessage());
}

// 2. MANAJEMEN SESSION & AUTHENTICATION LOGIC
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$error_msg = "";
$success_msg = "";

// Aksi Logout
if (isset($_GET['action']) && $_GET['action'] == 'logout') {
    session_unset();
    session_destroy();
    header("Location: pmb-online.php");
    exit;
}

// Proses Registrasi & Login
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['auth_type'])) {
    if ($_POST['auth_type'] == 'register') {
        $name = htmlspecialchars($_POST['name']);
        $email = htmlspecialchars($_POST['email']);
        $pass = password_hash($_POST['password'], PASSWORD_BCRYPT);
        $role = isset($_POST['is_admin']) ? 'admin' : 'user';

        try {
            $stmt = $pdo->prepare("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)");
            $stmt->execute([$name, $email, $pass, $role]);
            $success_msg = "Registrasi berhasil! Silakan login.";
        } catch (PDOException $e) {
            $error_msg = "Email sudah terdaftar atau terjadi kesalahan.";
        }
    } elseif ($_POST['auth_type'] == 'login') {
        $email = htmlspecialchars($_POST['email']);
        $password = $_POST['password'];

        $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$email]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['name'] = $user['name'];
            $_SESSION['role'] = $user['role'];
            header("Location: pmb-online.php");
            exit;
        } else {
            $error_msg = "Email atau Password salah!";
        }
    }
}

// Proses Submit Formulir Pendaftaran (User)
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['action']) && $_POST['action'] == 'submit_pmb') {
    if (!isset($_SESSION['user_id']) || $_SESSION['role'] !== 'user') {
        die("Akses ditolak.");
    }
    
    $nik = htmlspecialchars($_POST['nik']);
    $phone = htmlspecialchars($_POST['phone']);
    $prodi = htmlspecialchars($_POST['prodi']);
    
    // Pengolahan upload file ke Base64 string
    if (isset($_FILES['photo']) && $_FILES['photo']['error'] == 0) {
        $allowed = ['image/jpeg', 'image/png', 'image/jpg'];
        if (in_array($_FILES['photo']['type'], $allowed) && $_FILES['photo']['size'] < 2000000) {
            $imgData = base64_encode(file_get_contents($_FILES['photo']['tmp_name']));
            $src = 'data:' . $_FILES['photo']['type'] . ';base64,' . $imgData;
            
            // Simpan ke database
            $stmt = $pdo->prepare("INSERT INTO applications (user_id, nik, phone, prodi, photo) VALUES (?, ?, ?, ?, ?)");
            $stmt->execute([$_SESSION['user_id'], $nik, $phone, $prodi, $src]);
            $success_msg = "Pendaftaran Anda berhasil dikirim!";
        } else {
            $error_msg = "Format file tidak valid atau ukuran terlalu besar (Maks 2MB).";
        }
    } else {
        $error_msg = "Wajib mengunggah Pas Foto.";
    }
}

// Proses Update Status Pendaftaran (Admin)
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['action']) && $_POST['action'] == 'update_status') {
    if (!isset($_SESSION['user_id']) || $_SESSION['role'] !== 'admin') {
        die("Akses ditolak.");
    }
    $app_id = intval($_POST['app_id']);
    $status = htmlspecialchars($_POST['status']);
    
    $stmt = $pdo->prepare("UPDATE applications SET status = ? WHERE id = ?");
    $stmt->execute([$status, $app_id]);
    $success_msg = "Status pendaftar berhasil diperbarui.";
}
?>

<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PMB Online - Universitas Terbuka</title>
    <!-- Tailwind CSS untuk Styling Modern -->
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="bg-gray-50 font-sans text-gray-800 flex flex-col min-h-screen">

    <!-- HEADER / NAVIGATION -->
    <header class="bg-blue-600 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <a href="pmb-online.php" class="flex items-center space-x-2 text-xl font-bold tracking-wide">
                <span>🎓</span> <span>Univ. PHP</span>
            </a>
            <nav class="hidden md:flex space-x-6 font-medium">
                <a href="#home" class="hover:text-blue-200 transition">Beranda</a>
                <a href="#prodi" class="hover:text-blue-200 transition">Program Studi</a>
                <a href="#alur" class="hover:text-blue-200 transition">Alur Pendaftaran</a>
                <?php if(isset($_SESSION['user_id'])): ?>
                    <a href="#dashboard" class="hover:text-blue-200 transition text-yellow-300 font-bold">Dashboard (<?= ucfirst($_SESSION['role']); ?>)</a>
                <?php else: ?>
                    <a href="#auth-section" class="hover:text-blue-200 transition">Daftar/Login</a>
                <?php endif; ?>
            </nav>
            <div>
                <?php if(isset($_SESSION['user_id'])): ?>
                    <div class="flex items-center space-x-4">
                        <span class="text-sm bg-blue-700 px-3 py-1 rounded-full">Halo, <?= $_SESSION['name']; ?></span>
                        <a href="pmb-online.php?action=logout" class="bg-red-500 hover:bg-red-600 px-4 py-2 rounded text-sm font-semibold transition shadow text-white">Logout</a>
                    </div>
                <?php else: ?>
                    <a href="#auth-section" class="bg-yellow-500 hover:bg-yellow-600 text-blue-900 px-5 py-2 rounded font-bold transition shadow">Mulai Daftar</a>
                <?php endif; ?>
            </div>
        </div>
    </header>

    <!-- NOTIFIKASI ERROR / SUKSES -->
    <?php if($error_msg): ?>
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 text-center" role="alert"><?= $error_msg; ?></div>
    <?php endif; ?>
    <?php if($success_msg): ?>
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 text-center" role="alert"><?= $success_msg; ?></div>
    <?php endif; ?>

    <!-- MAIN CONTENT -->
    <main class="flex-grow">
        
        <!-- HERO SECTION -->
        <section id="home" class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-20 px-4 text-center">
            <div class="max-w-4xl mx-auto">
                <h1 class="text-4xl md:text-5xl font-extrabold mb-4 leading-tight">Raih Masa Depan Gemilang Bersama Universitas PHP</h1>
                <p class="text-lg md:text-xl text-blue-100 mb-8">Pendaftaran Mahasiswa Baru Tahun Akademik 2026/2027 telah dibuka secara Online. Proses cepat, mudah, dan transparan.</p>
                <?php if(!isset($_SESSION['user_id'])): ?>
                    <a href="#auth-section" class="bg-yellow-500 hover:bg-yellow-600 text-blue-950 font-extrabold px-8 py-4 rounded-lg text-lg transition transform hover:scale-105 inline-block shadow-lg">Daftar Akun Sekarang</a>
                <?php else: ?>
                    <a href="#dashboard" class="bg-green-500 hover:bg-green-600 text-white font-extrabold px-8 py-4 rounded-lg text-lg transition transform hover:scale-105 inline-block shadow-lg">Buka Dashboard Anda</a>
                <?php endif; ?>
            </div>
        </section>

        <!-- INFORMASI PROGRAM STUDI -->
        <section id="prodi" class="py-16 max-w-7xl mx-auto px-4">
            <h2 class="text-3xl font-bold text-center mb-12 text-blue-900">Program Studi Unggulan</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="bg-white p-6 rounded-xl shadow hover:shadow-xl transition border-t-4 border-blue-500">
                    <div class="text-3xl mb-3">💻</div>
                    <h3 class="text-xl font-bold mb-2 text-gray-900">Teknik Informatika</h3>
                    <p class="text-gray-600">Fokus pada rekayasa perangkat lunak, keamanan siber, data science, dan pengembangan teknologi web/mobile terkini.</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow hover:shadow-xl transition border-t-4 border-indigo-500">
                    <div class="text-3xl mb-3">📊</div>
                    <h3 class="text-xl font-bold mb-2 text-gray-900">Sistem Informasi</h3>
                    <p class="text-gray-600">Menjembatani bisnis dan teknologi. Mempelajari analisis sistem, manajemen data, dan tata kelola teknologi informasi perusahaan.</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow hover:shadow-xl transition border-t-4 border-purple-500">
                    <div class="text-3xl mb-3">🎨</div>
                    <h3 class="text-xl font-bold mb-2 text-gray-900">Desain Komunikasi Visual</h3>
                    <p class="text-gray-600">Mengembangkan kreativitas multimedia, desain grafis, animasi, UI/UX, dan komunikasi visual berbasis industri kreatif.</p>
                </div>
            </div>
        </section>

        <!-- ALUR PENDAFTARAN -->
        <section id="alur" class="bg-gray-100 py-16 px-4">
            <div class="max-w-6xl mx-auto">
                <h2 class="text-3xl font-bold text-center mb-12 text-blue-900">Alur Pendaftaran Mudah</h2>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
                    <div class="bg-white p-6 rounded-lg shadow relative">
                        <div class="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold mx-auto mb-3">1</div>
                        <h4 class="font-bold mb-1">Buat Akun</h4>
                        <p class="text-sm text-gray-600">Registrasi akun baru dengan email aktif Anda.</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow relative">
                        <div class="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold mx-auto mb-3">2</div>
                        <h4 class="font-bold mb-1">Isi Formulir</h4>
                        <p class="text-sm text-gray-600">Lengkapi NIK, nomor HP, dan pilih program studi impian.</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow relative">
                        <div class="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold mx-auto mb-3">3</div>
                        <h4 class="font-bold mb-1">Upload Foto</h4>
                        <p class="text-sm text-gray-600">Unggah pas foto formal terbaru ukuran maksimal 2MB.</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow relative">
                        <div class="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold mx-auto mb-3">4</div>
                        <h4 class="font-bold mb-1">Pantau Hasil</h4>
                        <p class="text-sm text-gray-600">Cek dashboard berkala untuk melihat pengumuman kelulusan.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- CONDITIONAL PORTAL AREA (DASHBOARD ATAU LOGIN/REGISTER) -->
        <section id="portal-area" class="py-16 max-w-6xl mx-auto px-4">
            
            <?php if(isset($_SESSION['user_id'])): ?>
                <!-- DYNAMIC DASHBOARD -->
                <div id="dashboard" class="bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
                    <h2 class="text-2xl font-bold text-blue-900 border-b pb-4 mb-6 flex items-center justify-between">
                        <span>Halaman Dashboard Portal PMB</span>
                        <span class="text-xs tracking-widest uppercase bg-indigo-100 text-indigo-800 px-3 py-1 rounded">Login Sebagai: <?= strtoupper($_SESSION['role']); ?></span>
                    </h2>

                    <?php if($_SESSION['role'] === 'user'): ?>
                        <!-- INTERFACE USER (CALON MAHASISWA) -->
                        <?php
                        // Cek status pendaftaran user saat ini
                        $stmt = $pdo->prepare("SELECT * FROM applications WHERE user_id = ?");
                        $stmt->execute([$_SESSION['user_id']]);
                        $application = $stmt->fetch(PDO::FETCH_ASSOC);
                        ?>

                        <?php if(!$application): ?>
                            <!-- FORMULIR INPUT PENDAFTARAN -->
                            <div class="max-w-2xl mx-auto">
                                <h3 class="text-xl font-bold mb-6 text-gray-800">Formulir Pendaftaran Mahasiswa Baru</h3>
                                <form action="pmb-online.php#dashboard" method="POST" enctype="multipart/form-data" class="space-y-4">
                                    <input type="hidden" name="action" value="submit_pmb">
                                    <div>
                                        <label class="block text-sm font-semibold mb-1">Nomor Induk Kependudukan (NIK)</label>
                                        <input type="text" name="nik" required placeholder="Masukkan 16 digit NIK" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-semibold mb-1">Nomor Telepon / WhatsApp</label>
                                        <input type="tel" name="phone" required placeholder="Contoh: 08123456789" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-semibold mb-1">Pilihan Program Studi</label>
                                        <select name="prodi" required class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                                            <option value="">-- Pilih Program Studi --</option>
                                            <option value="Teknik Informatika">Teknik Informatika</option>
                                            <option value="Sistem Informasi">Sistem Informasi</option>
                                            <option value="Desain Komunikasi Visual">Desain Komunikasi Visual</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-sm font-semibold mb-1">Upload Pas Foto Formal (JPG/PNG, Maks 2MB)</label>
                                        <input type="file" name="photo" accept="image/*" required class="w-full border border-gray-300 rounded p-1 text-sm bg-gray-50 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                                    </div>
                                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded shadow transition">Kirim Formulir Pendaftaran</button>
                                </form>
                            </div>
                        <?php else: ?>
                            <!-- STATUS DATA PENDAFTARAN USER -->
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
                                <div class="text-center bg-gray-50 p-6 rounded-xl border border-dashed border-gray-200">
                                    <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Pas Foto</p>
                                    <img src="<?= $application['photo']; ?>" alt="Foto Pendaftar" class="w-40 h-52 object-cover mx-auto rounded shadow-md border-4 border-white">
                                </div>
                                <div class="md:col-span-2 space-y-4">
                                    <h3 class="text-xl font-bold text-gray-900">Biodata Pendaftaran Anda</h3>
                                    <div class="grid grid-cols-2 gap-4 border-b pb-4 text-sm">
                                        <div><p class="font-semibold text-gray-500">Nama Lengkap</p><p class="text-base font-bold text-gray-900"><?= $_SESSION['name']; ?></p></div>
                                        <div><p class="font-semibold text-gray-500">Pilihan Program Studi</p><p class="text-base font-bold text-blue-600"><?= $application['prodi']; ?></p></div>
                                        <div><p class="font-semibold text-gray-500">Nomor NIK</p><p class="text-base font-medium"><?= $application['nik']; ?></p></div>
                                        <div><p class="font-semibold text-gray-500">Nomor Telepon</p><p class="text-base font-medium"><?= $application['phone']; ?></p></div>
                                    </div>
                                    <div>
                                        <p class="font-semibold text-gray-500 mb-2">Status Seleksi Administrasi:</p>
                                        <?php if($application['status'] === 'Menunggu'): ?>
                                            <span class="inline-block bg-yellow-100 text-yellow-800 text-sm font-bold px-4 py-2 rounded-full shadow-sm">⏳ Sedang Diproses (Menunggu Konfirmasi Admin)</span>
                                        <?php elseif($application['status'] === 'Diterima'): ?>
                                            <span class="inline-block bg-green-100 text-green-800 text-sm font-bold px-4 py-2 rounded-full shadow-sm">🎉 Selamat! Anda Dinyatakan DITERIMA</span>
                                        <?php else: ?>
                                            <span class="inline-block bg-red-100 text-red-800 text-sm font-bold px-4 py-2 rounded-full shadow-sm">❌ Maaf, Anda Dinyatakan DITOLAK</span>
                                        <?php endif; ?>
                                    </div>
                                </div>
                            </div>
                        <?php endif; ?>

                    <?php else: ?>
                        <!-- INTERFACE ADMIN (MANAJEMEN DATA PENDAFTAR) -->
                        <h3 class="text-xl font-bold mb-4 text-gray-800">Daftar Seluruh Calon Mahasiswa Terdaftar</h3>
                        <?php
                        // Ambil semua aplikasi pendaftar beserta nama user
                        $stmt = $pdo->query("SELECT a.*, u.name, u.email FROM applications a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC");
                        $all_apps = $stmt->fetchAll(PDO::FETCH_ASSOC);
                        ?>

                        <?php if(count($all_apps) == 0): ?>
                            <p class="text-gray-500 text-center py-6">Belum ada calon mahasiswa yang mengirimkan formulir pendaftaran.</p>
                        <?php else: ?>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse text-sm">
                                    <thead>
                                        <tr class="bg-gray-100 text-gray-700 uppercase font-semibold border-b">
                                            <th class="py-3 px-4">Foto</th>
                                            <th class="py-3 px-4">Nama / Kontak</th>
                                            <th class="py-3 px-4">Prodi / NIK</th>
                                            <th class="py-3 px-4">Status Sekarang</th>
                                            <th class="py-3 px-4 text-center">Aksi Otorisasi</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-gray-200">
                                        <?php foreach($all_apps as $app): ?>
                                            <tr>
                                                <td class="py-3 px-4">
                                                    <img src="<?= $app['photo']; ?>" class="w-12 h-16 object-cover rounded border bg-gray-100">
                                                </td>
                                                <td class="py-3 px-4">
                                                    <div class="font-bold text-gray-900"><?= $app['name']; ?></div>
                                                    <div class="text-xs text-gray-500"><?= $app['email']; ?></div>
                                                    <div class="text-xs text-gray-500"><?= $app['phone']; ?></div>
                                                </td>
                                                <td class="py-3 px-4">
                                                    <div class="font-semibold text-blue-700"><?= $app['prodi']; ?></div>
                                                    <div class="text-xs text-gray-400">NIK: <?= $app['nik']; ?></div>
                                                </td>
                                                <td class="py-3 px-4">
                                                    <?php if($app['status'] == 'Menunggu'): ?>
                                                        <span class="bg-yellow-100 text-yellow-800 text-xs font-bold px-2.5 py-1 rounded">Menunggu</span>
                                                    <?php elseif($app['status'] == 'Diterima'): ?>
                                                        <span class="bg-green-100 text-green-800 text-xs font-bold px-2.5 py-1 rounded">Diterima</span>
                                                    <?php else: ?>
                                                        <span class="bg-red-100 text-red-800 text-xs font-bold px-2.5 py-1 rounded">Ditolak</span>
                                                    <?php endif; ?>
                                                </td>
                                                <td class="py-3 px-4">
                                                    <form action="pmb-online.php#dashboard" method="POST" class="flex items-center justify-center space-x-2">
                                                        <input type="hidden" name="action" value="update_status">
                                                        <input type="hidden" name="app_id" value="<?= $app['id']; ?>">
                                                        <select name="status" class="border border-gray-300 rounded text-xs px-2 py-1 outline-none bg-white">
                                                            <option value="Menunggu" <?= $app['status']=='Menunggu'?'selected':''; ?>>Menunggu</option>
                                                            <option value="Diterima" <?= $app['status']=='Diterima'?'selected':''; ?>>Terima</option>
                                                            <option value="Ditolak" <?= $app['status']=='Ditolak'?'selected':''; ?>>Tolak</option>
                                                        </select>
                                                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded shadow transition">Update</button>
                                                    </form>
                                                </td>
                                            </tr>
                                        <?php endforeach; ?>
                                    </tbody>
                                </table>
                            </div>
                        <?php endif; ?>
                    <?php endif; ?>
                </div>

            <?php else: ?>
                <!-- INTERFACE REGISTER / LOGIN TAB (JIKA BELUM LOGIN) -->
                <div id="auth-section" class="max-w-md mx-auto bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
                    <!-- Navigasi Tab Sederhana Menggunakan JS Toggle -->
                    <div class="flex border-b text-center font-medium bg-gray-50">
                        <button id="tab-login-btn" onclick="switchAuthTab('login')" class="w-1/2 py-3 text-blue-600 border-b-2 border-blue-600 outline-none transition font-bold">Login</button>
                        <button id="tab-register-btn" onclick="switchAuthTab('register')" class="w-1/2 py-3 text-gray-500 hover:text-blue-600 transition outline-none font-bold">Registrasi</button>
                    </div>

                    <div class="p-6">
                        <!-- FORM LOGIN -->
                        <form id="form-login" action="pmb-online.php#auth-section" method="POST" class="space-y-4">
                            <input type="hidden" name="auth_type" value="login">
                            <div>
                                <label class="block text-sm font-semibold mb-1">Email</label>
                                <input type="email" name="email" required placeholder="nama@email.com" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold mb-1">Password</label>
                                <input type="password" name="password" required placeholder="Masukkan password" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded shadow transition">Login</button>
                        </form>

                        <!-- FORM REGISTRASI -->
                        <form id="form-register" action="pmb-online.php#auth-section" method="POST" class="space-y-4 hidden">
                            <input type="hidden" name="auth_type" value="register">
                            <div>
                                <label class="block text-sm font-semibold mb-1">Nama Lengkap</label>
                                <input type="text" name="name" required placeholder="Masukkan nama lengkap" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold mb-1">Email Aktif</label>
                                <input type="email" name="email" required placeholder="contoh@email.com" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <div>
                                <label class="block text-sm font-semibold mb-1">Password</label>
                                <input type="password" name="password" required placeholder="Minimal 6 karakter" class="w-full border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none">
                            </div>
                            <div class="flex items-center space-x-2 bg-gray-50 p-2.5 rounded border border-gray-200">
                                <input type="checkbox" name="is_admin" id="is_admin" class="w-4 h-4 text-blue-600 border-gray-300 rounded">
                                <label for="is_admin" class="text-xs text-gray-700 font-semibold cursor-pointer select-none">Daftar Sebagai Admin (Untuk Pengujian Otorisasi)</label>
                            </div>
                            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 rounded shadow transition">Daftar Akun</button>
                        </form>
                    </div>
                </div>

                <!-- JavaScript Sederhana untuk Toggle Tab Login/Register -->
                <script>
                    function switchAuthTab(type) {
                        const formLogin = document.getElementById('form-login');
                        const formRegister = document.getElementById('form-register');
                        const tabLoginBtn = document.getElementById('tab-login-btn');
                        const tabRegisterBtn = document.getElementById('tab-register-btn');

                        if (type === 'login') {
                            formLogin.classList.remove('hidden');
                            formRegister.classList.add('hidden');
                            tabLoginBtn.className = "w-1/2 py-3 text-blue-600 border-b-2 border-blue-600 outline-none font-bold transition";
                            tabRegisterBtn.className = "w-1/2 py-3 text-gray-500 hover:text-blue-600 outline-none font-bold transition";
                        } else {
                            formLogin.classList.add('hidden');
                            formRegister.classList.remove('hidden');
                            tabLoginBtn.className = "w-1/2 py-3 text-gray-500 hover:text-blue-600 outline-none font-bold transition";
                            tabRegisterBtn.className = "w-1/2 py-3 text-blue-600 border-b-2 border-blue-600 outline-none font-bold transition";
                        }
                    }
                </script>
            <?php endif; ?>
        </section>

    </main>

    <!-- FOOTER -->
    <footer class="bg-gray-900 text-gray-400 py-8 px-4 border-t border-gray-800 text-center text-sm">
        <p class="mb-2">&copy; 2026 Universitas PHP. Seluruh Hak Cipta Dilindungi Undang-Undang.</p>
        <p class="text-xs text-gray-600">Sistem Aplikasi Informasi Penerimaan Mahasiswa Baru Berbasis Sisi Server.</p>
    </footer>

</body>
</html>