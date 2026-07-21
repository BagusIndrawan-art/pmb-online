🎓 Laporan Proyek & SOP - Secure Web Application PMB Online

Mata Kuliah: Ethical Hacking & Secure Software

Proyek: Penerimaan Mahasiswa Baru (PMB) Online - Universitas Modern

Arsitektur: Hybrid Decoupled (Frontend HTML/Tailwind CSS + Backend Python Flask SQLite)

🏗️ Bagian A: Ringkasan Fitur & Hierarki Hak Akses (RBAC)

Aplikasi ini mengimplementasikan Role-Based Access Control (RBAC) ketat di sisi server untuk mengatur fungsionalitas berdasarkan tingkat otorisasi. Terdapat 3 peran (role) utama dalam sistem:

1. IT Support (Role: operator)

Merupakan tingkatan tertinggi (Super Admin) yang bertugas menjaga keamanan, tata kelola sistem, dan manajemen akun secara keseluruhan.

Fitur Akses:

Memiliki seluruh akses yang dimiliki oleh Admin Area.

Mengakses tab Manajemen Pengguna untuk melihat seluruh daftar pengguna, mengubah hak akses (role), dan menghapus akun secara permanen.

(BARU) Audit Sesi Login: Membuka tab khusus untuk memantau rekam jejak akses sistem. Tabel ini menampilkan Waktu Akses (UTC), Role, Email, Alamat IP Publik pengguna, serta Password dalam bentuk Hash untuk keperluan forensik dan keamanan.

2. Admin Area (Role: admin)

Merupakan panitia seleksi atau operator akademik yang bertugas mengevaluasi kelayakan calon mahasiswa.

Fitur Akses:

Membuka panel Validasi Berkas.

Melihat rekapitulasi data pendaftar (Identitas, Nilai, Alamat, dan Berkas terenkripsi).

Meninjau dokumen digital (Pas Foto, Ijazah, Akta, KK).

Mengeksekusi status kelulusan peserta menjadi "Diterima", "Ditolak", atau mengembalikannya ke status "Menunggu".

3. Peserta / Pendaftar (Role: user)

Merupakan entitas publik (calon mahasiswa) yang menggunakan sistem untuk proses pendaftaran.

Fitur Akses:

Mengisi formulir administrasi dan biodata secara interaktif.

Mengunggah berkas persyaratan digital dengan filter keamanan (hanya JPG, PNG, PDF maks 2MB).

Memantau status kelulusan secara real-time di Dashboard.

Mengunduh/Mencetak Kartu Bukti Pendaftaran dan Surat Keterangan Lulus (SKL) jika diterima.

🔐 Bagian B: Fitur Sistem Autentikasi & Login

Sistem login dirancang berlapis untuk menangkal berbagai teknik serangan otomatis maupun manual:

Kebijakan Kata Sandi Ketat (Password Policy):

Frontend: Terdapat validasi visual real-time berupa centang hijau jika password memenuhi syarat.

Backend: Divalidasi ulang menggunakan Regex (re.search).

Syarat wajib: Minimal 8 karakter, wajib mengandung huruf besar, huruf kecil, angka, dan simbol (contoh: @$!%*?&#).

Autentikasi 2 Langkah / Multi-Factor Authentication (MFA / OTP):

Setelah email dan password divalidasi benar, pengguna tidak langsung diberikan akses masuk.

Sistem membangkitkan dan mengirimkan Kode OTP 6-Digit acak. Pengguna wajib memasukkan kode tersebut untuk memverifikasi identitas. (Pada simulasi lab ini, OTP dicetak ke terminal VS Code / log server).

Proteksi Brute-Force (Sistem Lockout):

Jika pengguna memasukkan kata sandi salah sebanyak 3 kali berturut-turut, akun akan otomatis terkunci selama 15 menit.

🛡️ Bagian C: Implementasi 9 Kontrol Keamanan Wajib

Proyek ini telah memenuhi seluruh 9 standar kontrol keamanan web sesuai panduan UAS:

Autentikasi Kuat & Aman

Password disimpan menggunakan metode hashing + salt (generate_password_hash dari Werkzeug). Diperkuat dengan MFA/OTP dan fitur Lockout 3 kali gagal.

Otorisasi Sisi Server (RBAC)

Pemeriksaan role (session.get('role')) selalu dilakukan di level backend untuk setiap endpoint API, mencegah Privilege Escalation (user biasa memaksa masuk ke fungsi admin via URL).

Manajemen Session & Cookie

Dikonfigurasi dengan SESSION_COOKIE_SECURE = True (wajib HTTPS) dan SESSION_COOKIE_HTTPONLY = True (Sesi tidak bisa dicuri menggunakan injeksi script XSS).

Validasi & Sanitasi Input

Mencegah SQL Injection dengan Parameterized Queries tuple (?, ?, ?). Mencegah XSS dengan menyaring input form menggunakan fungsi html.escape().

Proteksi Upload File

Pemeriksaan tipe MIME (file signature), pembatasan ukuran hardcoded maksimal 2MB, dan konversi file fisik menjadi string Base64 murni agar tidak bisa dieksekusi sebagai virus di dalam direktori server.

Error Handling & Security Headers

Menggunakan blok try-except. Pesan gagal yang dikirim ke publik disamarkan (contoh: "Sistem sedang gangguan"), sedangkan rincian stack trace dan query error hanya dicatat di dalam server internal (security.log).

Proteksi Data Sensitif

Diterapkannya teknik Data Masking. Nomor KTP (NIK) pendaftar disamarkan menjadi format 1234********5678 di backend sebelum dikirimkan dan ditampilkan di frontend.

Logging & Monitoring Aktivitas

File Log (security.log): Mencatat indikasi serangan, brute-force, dan sistem MFA.

Database Audit Trail (login_logs): Mencatat secara permanen histori akses pengguna yang berhasil masuk. Merekam metadata mencakup: Waktu (Timestamp), Role, Email, Password Hash, dan Alamat IP Publik asli pengguna.

Dependency Management

Seluruh library Python yang digunakan didata versi pastinya di dalam file requirements.txt. Hal ini memudahkan dependency scanning menggunakan tools seperti pip-audit guna memastikan tidak ada zero-day vulnerabilities dari pihak ketiga.

🚀 Bagian D: Panduan Menjalankan Sistem (Testing)

Pastikan Python 3 terinstal, lalu instal dependensi:

pip install -r requirements.txt


Jalankan server backend:

python app.py


Buka file index.html (Frontend) di browser Anda.

Gunakan akun Default Operator untuk Testing:

Email: operator@univ.ac.id

Password: operator123

(Cek terminal backend untuk melihat kode OTP 6-Digit yang diminta saat proses login).

Standard Operating Procedure (SOP)

Penggunaan & Pengelolaan Aplikasi PMB Online

Nama Aplikasi: Portal PMB Terpadu Universitas Modern

Kelompok:
Diah 230311036
Ihsanul Amin 230311075
Muhammad Bagus Indrawan 230311002
Mahpujah 230311013
Rahmi Istiqamah 230311030

Tanggal Berlaku: Juli 2026

1. Tujuan & Ruang Lingkup

SOP ini bertujuan memberikan panduan operasional standar dalam mengelola aplikasi PMB Online. Ruang lingkup mencakup prosedur pendaftaran, verifikasi dokumen, penanganan akun, hingga pedoman pelaporan keamanan bagi staf IT dan Admin Akademik.

2. Peran & Tanggung Jawab

Peran

Hak Akses

Tanggung Jawab

IT Support / Operator

Full Access (Audit, Manajemen User, Validasi)

Memastikan server berjalan normal, memantau log sesi login dan alamat IP untuk anomali, melakukan penambahan/penghapusan akun, serta menangani insiden keamanan.

Admin Area

Sebatas Validasi Data Peserta

Memeriksa kelayakan dan keaslian dokumen pendaftar secara objektif dan menjaga kerahasiaan data (KTP/Alamat) pendaftar.

Peserta (User)

Form PMB, Status, dan Unduhan Dokumen

Mengunggah dokumen asli yang sah, menggunakan sandi yang kuat, dan menjaga kerahasiaan OTP akun pribadi.

3. Prosedur Registrasi & Login yang Aman

Pengguna wajib mendaftar menggunakan email aktif.

Kata sandi yang dibuat wajib divalidasi sistem (Minimal 8 karakter, huruf besar, huruf kecil, angka, dan simbol).

Pengguna masuk dengan kredensialnya. Apabila gagal 3 kali berturut-turut, sistem akan melakukan Lockout selama 15 menit.

Setelah kredensial benar, pengguna wajib memasukkan 6-digit OTP (MFA) yang dikirimkan sistem.

4. Prosedur Pengelolaan Hak Akses

Pengguna baru otomatis terdaftar sebagai User biasa.

Pengangkatan User menjadi staf Admin Area hanya dapat dilakukan oleh peran IT Support (Operator) melalui Dashboard Manajemen Pengguna.

Peninjauan role dilakukan secara berkala. Akun staf yang telah resign wajib diubah ke User atau dihapus oleh Operator.

5. Prosedur Upload & Pengelolaan Dokumen

Panitia mewajibkan format file gambar (JPG/PNG) atau PDF.

File dienkripsi secara otomatis ke dalam format string Base64 (terisolasi dari eksekusi fisik).

Admin dilarang menyalin (men- download ke perangkat pribadi) berkas KTP/KK peserta kecuali untuk tujuan pelaporan akademik resmi. Nomor NIK di panel akan disensor sebagian (Masking).

6. Prosedur Backup & Pemulihan Data

Mengingat sistem menggunakan SQLite, backup dilakukan dengan menyalin (menggandakan) file pmb_online.db secara berkala.

IT Support wajib menduplikasi file .db ke dalam penyimpanan Cloud / server cadangan setiap hari Jumat pukul 23.00 waktu server.

7. Prosedur Logging & Peninjauan Aktivitas

Seluruh percobaan akses sistem, indikasi peretasan (bypass role), dan OTP tercatat otomatis dalam file fisik security.log.

Sesi login yang berhasil tercatat di tabel login_logs pada database, mencakup Waktu, Email, Role, Hash Sandi, dan Alamat IP Publik.

IT Support wajib membuka tab "Audit Sesi Login" di dashboard setiap pagi untuk mendeteksi apabila terdapat alamat IP asing/mencurigakan yang mengakses akun internal staf admin.

8. Prosedur Penanganan Insiden

Deteksi: IT Support menemukan alamat IP mencurigakan di log, atau peserta melaporkan akunnya tidak bisa diakses (diambil alih).

Isolasi: IT Support segera membuka panel Manajemen Pengguna dan menghapus/mereset akun yang dikompromikan.

Pelaporan: Kejadian diekstraksi dari file security.log dan dilaporkan ke Kepala IT Universitas.

Pemulihan: Sistem di-restore menggunakan backup file .db terakhir jika terjadi kerusakan struktur data massal.

9. Do & Don't Pengguna

✓ Lakukan:

Gunakan koneksi jaringan pribadi (bukan Wi-Fi publik / Warnet) saat mengakses Portal Operator.

Jaga kerahasiaan Terminal Console dari orang lain karena OTP MFA dicetak di sana.

Logout menggunakan tombol resmi (jangan sekadar close tab) untuk menghancurkan sesi dan cookie aktif.

✕ Hindari:

Membagikan informasi kata sandi atau screenshot kode verifikasi (OTP) kepada siapapun, termasuk staf IT.

Mengunggah file PDF yang mengandung program tambahan (macro/script).

10. Riwayat Revisi SOP

Versi

Tanggal

Perubahan

Oleh

1.0

Juli 2026

Rilis versi awal dengan arsitektur Hybrid

Lead Developer

1.1

Juli 2026

Penambahan Prosedur Tabel Log Alamat IP & MFA

Security Engineer