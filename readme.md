🎓 Aplikasi PMB Online (Penerimaan Mahasiswa Baru) - Arsitektur Decoupled
Tugas Project UAS - Web Development & Keamanan (Ethical Hacking) Kelompok 1 :

Nama Kelompok :
Diah 230311036
Ihsanul Amin 230311075
Muhammad Bagus Indrawan 230311002
Mahpujah 230311013
Rahmi Istiqamah 230311030

Mata Kuliah: Ethical Hacking

📌 Deskripsi Proyek

Proyek ini adalah sistem Penerimaan Mahasiswa Baru (PMB) Online yang dibangun menggunakan arsitektur modern Hybrid Decoupled. Frontend dan Backend sepenuhnya terpisah, berkomunikasi secara asinkron menggunakan format JSON melalui REST API.

Fokus utama proyek ini tidak hanya pada antarmuka UI/UX yang modern (Glassmorphism dan Interactive Walkthrough), melainkan juga pada implementasi keamanan sistem backend dalam menangani data sensitif calon mahasiswa.

🚀 Fitur Utama

Sistem Multi-Role Authentication: Terdapat pemisahan hak akses antara Calon Mahasiswa (user) dan Operator/Panitia (admin).
Interactive UI Walkthrough: Alur pendaftaran disajikan dalam bentuk animasi mockup layar interaktif layaknya video demonstrasi.
Manajemen Dokumen Digital: Pendaftar dapat mengunggah file (Foto, Ijazah, Akta, KK) yang akan dienkripsi menjadi format Base64 untuk penyimpanan yang lebih aman.
Live Status Tracking: Calon mahasiswa dapat memantau status kelulusan (Menunggu/Diterima/Ditolak) secara real-time.
Dashboard Admin: Panel khusus bagi admin untuk memvalidasi berkas dan mengeksekusi kelulusan pendaftar.

🛡️ Implementasi Keamanan (Security Features)

Sesuai dengan standar keamanan web (Ethical Hacking / Cyber Security), sistem ini menerapkan mitigasi kerentanan sebagai berikut:

Pencegahan SQL Injection: Semua aktivitas query ke database MySQL menggunakan metode Parameterized Queries (%s), mencegah peretas menyisipkan perintah SQL berbahaya.
Kriptografi Password: Kata sandi pengguna tidak disimpan dalam bentuk plaintext, melainkan di-hash menggunakan algoritma modern dari werkzeug.security (setara bcrypt).
Session Management: Autentikasi menggunakan sistem sesi lokal Flask (Server-side session) dengan konfigurasi CORS kredensial terisolasi.
Enkripsi File (Base64): Mencegah celah Remote Code Execution (RCE) via File Upload, karena dokumen dikonversi menjadi teks terenkripsi (Base64 String) dan disimpan dalam tabel database, bukan sebagai executable file di folder direktori publik server.

🛠️ Teknologi yang Digunakan

Frontend: HTML5, Tailwind CSS (CDN), Vanilla JavaScript, AOS Animation Library.
Backend: Python 3, Flask Web Framework.
Database: MySQL (Relational Database).
Integrasi: Fetch API (CORS Enabled).

⚙️ Panduan Instalasi & Konfigurasi

1. Persiapan Database (MySQL)
Proyek ini dilengkapi dengan fitur Auto-Migration. Anda tidak perlu repot mengimpor file .sql.
Nyalakan aplikasi XAMPP.
Klik tombol Start pada modul MySQL.

2. Instalasi Backend (Python)

Pastikan Python 3 sudah terinstal di komputer. Buka Terminal/Command Prompt, lalu jalankan perintah berikut:

# Instalasi library yang dibutuhkan
pip install flask flask-cors mysql-connector-python

# Jalankan server backend (Server akan berjalan di http://127.0.0.1:5000)
python app.py

Catatan: Saat app.py pertama kali dijalankan, ia akan otomatis membuat database pmb_online beserta tabel-tabel yang dibutuhkan di dalam MySQL Anda.

3. Menjalankan Frontend

Pastikan Server Python tetap menyala di latar belakang.
Buka aplikasi Visual Studio Code.
Buka file index.html.
Jalankan menggunakan ekstensi Live Server (Klik kanan -> Open with Live Server). Biasanya akan berjalan di port 5500.
Aplikasi siap digunakan di browser.

📝 Catatan Pengujian

Akun Default Admin: Anda dapat membuat akun Admin baru langsung dari halaman Registrasi dengan mencentang kotak opsi Otoritas Admin (Uji Coba Panel Seleksi).
Akun Calon Mahasiswa: Lakukan registrasi biasa tanpa mencentang kotak tersebut.

🛡️ Implementasi 9 Kontrol Keamanan Wajib (OWASP Standards)

Aplikasi ini telah mematuhi instruksi keamanan tugas Ethical Hacking, meliputi:

1. Autentikasi Kuat: Kata sandi di-hash menggunakan algoritma Bcrypt dari werkzeug.security. Telah diterapkan Sistem Lockout, di mana akun akan dibekukan selama 15 menit jika salah memasukkan sandi 3 kali berturut-turut.

2. Otorisasi (RBAC): Pemisahan rute ketat antara user dan admin. Calon mahasiswa terikat ke User ID masing-masing melalui parameter Session backend, sehingga Insecure Direct Object Reference (IDOR) / perubahan URL tidak dimungkinkan.

3. Manajemen Session & Cookie: Menggunakan kombinasi konfigurasi Flask SESSION_COOKIE_SECURE = True, SESSION_COOKIE_SAMESITE = 'None', dan SESSION_COOKIE_HTTPONLY = True agar cookie sesi kebal terhadap pencurian via XSS.

4. Validasi & Sanitasi Input:

SQL Injection: Dinetralisir menggunakan metode Parameterized Queries (?) pada SQLite.
XSS Attack: Seluruh input form disanitasi di backend menggunakan metode html.escape() sebelum masuk database.

5. Proteksi Upload File: Ukuran file dibatasi maksimal 2MB, menggunakan Strict MIME-Type Validation (hanya memproses header asli tipe image/jpeg, image/png, dan application/pdf). Sistem mengubah nama file dengan cara merombaknya menjadi kumpulan kode Base64 acak agar mustahil dieksekusi sebagai virus (RCE).

6. Error Handling: Blok try-except menyeluruh menangkap error teknis. Jika database down, pengguna hanya melihat pesan kesalahan generik "Sistem sedang mengalami gangguan", sedangkan detail stack trace dicatat secara tersembunyi.

7. Proteksi Data Sensitif: Data identitas (NIK) tidak pernah dikirimkan secara utuh dari server ke browser. NIK disensor di backend menggunakan metode Masking (contoh: 3201********0001).

8. Logging & Monitoring: Modul logging bawaan Python aktif mencatat (merekam) aktivitas mencurigakan seperti Brute-Force, Unauthorized Access, dan status Login ke dalam sebuah file audit bernama security.log.

9. Dependency Management: Menyertakan file requirements.txt dengan version pinning (penguncian versi spesifik) pada Flask dan Werkzeug untuk memastikan tidak ada pembaruan library usang yang berpotensi memiliki zero-day exploit.

Dikembangkan pada Juli 2026 untuk keperluan Ujian Akhir Semester.