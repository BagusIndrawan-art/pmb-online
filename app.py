from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import base64
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import datetime
import html
import re
import random

app = Flask(__name__)
app.secret_key = 'super_secret_pmb_key_2026'

# --- KONFIGURASI KEAMANAN KHUSUS UNTUK ONLINE (GitHub Pages) ---
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Mencegah pencurian XSS

# KONTROL 8: Logging & Monitoring
logging.basicConfig(filename='security.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURASI CORS ---
CORS(app, supports_credentials=True, origins=[
    "https://bagusindrawan-art.github.io", 
    "http://127.0.0.1:5500", 
    "http://localhost:5500"
])

def get_db_connection():
    try:
        # Menggunakan SQLite. Penyesuaian parameter URI untuk kompatibilitas x86 (driver 32-bit).
        db_path = os.path.join(os.path.dirname(__file__), 'pmb_online.db')
        conn = sqlite3.connect(f"file:{db_path}?mode=rwc", uri=True)
        
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Pembuatan tabel users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Pembuatan tabel applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nik TEXT NOT NULL,
                phone TEXT NOT NULL,
                prodi TEXT NOT NULL,
                tempat_lahir TEXT,
                tanggal_lahir DATE,
                jenis_kelamin TEXT,
                agama TEXT,
                alamat TEXT,
                asal_sekolah TEXT,
                nama_ayah TEXT,
                pekerjaan_ayah TEXT,
                gaji_ayah TEXT,
                nama_ibu TEXT,
                pekerjaan_ibu TEXT,
                gaji_ibu TEXT,
                nama_wali TEXT,
                pekerjaan_wali TEXT,
                gaji_wali TEXT,
                photo TEXT NOT NULL,
                ijazah TEXT,
                akta TEXT,
                kk TEXT,
                status TEXT DEFAULT 'Menunggu',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Buat akun IT Support (Super Operator) otomatis jika belum ada di dalam database
        cursor.execute("SELECT id FROM users WHERE email = 'operator@univ.ac.id'")
        if not cursor.fetchone():
            hashed_pw = generate_password_hash('operator123')
            cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                           ('Super Operator (IT Support)', 'operator@univ.ac.id', hashed_pw, 'operator'))
            
        conn.commit()
        return conn, cursor
    except sqlite3.Error as err:
        print(f"Error Database: {err}")
        return None, None

# --- RUTE HALAMAN UTAMA (Agar tidak Error 404 saat dibuka) ---
@app.route('/', methods=['GET'])
def index_route():
    return jsonify({
        "status": "Online",
        "message": "Server API PMB Universitas Modern Berjalan Normal.",
        "endpoints": "/api"
    })

# --- RUTE UTAMA HANDLER API ---
@app.route('/api', methods=['GET', 'POST'])
def api_handler():
    action = request.args.get('action') if request.method == 'GET' else request.form.get('action')
    
    conn, cursor = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Gagal membaca database SQLite."}), 500

    try:
        # 1. Cek Sesi
        if action == 'check_session':
            if 'user_id' in session:
                return jsonify({
                    "success": True, 
                    "data": {
                        "user_id": session['user_id'], 
                        "name": session['name'], 
                        "role": session['role']
                    }
                })
            return jsonify({"success": False, "message": "Belum ada sesi aktif."})

        # 2. Logout
        elif action == 'logout':
            session.clear()
            return jsonify({"success": True, "message": "Anda telah keluar sistem."})

        # 3. Registrasi
        elif action == 'register':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            is_admin = request.form.get('is_admin')
            
            if not name or not email or not password:
                return jsonify({"success": False, "message": "Data tidak lengkap."})
                
            # Validasi Password Kuat (Backend Regex)
            if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password) or not re.search(r'[@$!%*?&#]', password):
                logging.warning(f"Registration Failed: {email} mencoba mendaftar dengan password lemah.")
                return jsonify({"success": False, "message": "Password tidak memenuhi standar keamanan (Harus Kombinasi Huruf Besar, Kecil, Angka, dan Simbol)."})
            
            # Map checkbox form ke Role 'Admin Area' (disimpan sebagai 'admin') atau 'user'
            role = 'admin' if is_admin else 'user'
            hashed_pw = generate_password_hash(password)
            
            try:
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                              (name, email, hashed_pw, role))
                conn.commit()
                return jsonify({"success": True, "message": "Registrasi berhasil! Silakan login."})
            except sqlite3.IntegrityError:
                return jsonify({"success": False, "message": "Email sudah terdaftar."})

        # 4. Login (Brute-Force Protection + MFA/OTP)
        elif action == 'login':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                # Cek masa Lockout
                if user['locked_until'] and datetime.datetime.strptime(user['locked_until'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.now():
                    logging.warning(f"Brute-Force Terblokir: Akun {email} mencoba login saat masa lockout.")
                    return jsonify({"success": False, "message": "Akun terkunci karena terlalu banyak percobaan gagal. Silakan coba 15 menit lagi."})

                if check_password_hash(user['password'], password):
                    # Reset failed attempts jika password benar
                    cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE email = ?", (email,))
                    conn.commit()
                    
                    # Buat Kode OTP 6-Digit (Multi-Factor Authentication)
                    otp_code = str(random.randint(100000, 999999))
                    session['pending_user'] = {'id': user['id'], 'name': user['name'], 'role': user['role']}
                    session['pending_otp'] = otp_code
                    
                    print(f"\n{'='*50}\n[MFA OTP] Kode Verifikasi untuk {email} adalah: {otp_code}\n{'='*50}\n")
                    logging.info(f"MFA OTP dikirimkan untuk {email} adalah: {otp_code}")
                    
                    return jsonify({
                        "success": True, 
                        "mfa_required": True, 
                        "message": "Kode OTP 6 Digit telah dikirimkan. (Cek Terminal Python/Log)"
                    })
                else:
                    # Increment failed attempts jika password salah
                    attempts = user['failed_attempts'] + 1
                    locked_until = None
                    if attempts >= 3: 
                        locked_until = (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                        logging.warning(f"Lockout Diaktifkan: Akun {email} gagal login 3x.")
                    
                    cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE email = ?", (attempts, locked_until, email))
                    conn.commit()
                    logging.warning(f"Login Gagal: {email} (Percobaan ke-{attempts})")
                    
            return jsonify({"success": False, "message": "Email atau Password salah."})

        # 5. Verifikasi MFA (OTP Checker)
        elif action == 'verify_mfa':
            user_otp = request.form.get('otp', '').strip()
            
            if 'pending_otp' in session and session['pending_otp'] == user_otp:
                # OTP Valid, berikan session sesungguhnya
                session['user_id'] = session['pending_user']['id']
                session['name'] = session['pending_user']['name']
                session['role'] = session['pending_user']['role']
                
                # Buang sesi temporary
                session.pop('pending_otp', None)
                session.pop('pending_user', None)
                
                logging.info(f"MFA Sukses & Login Selesai: User ID {session['user_id']}")
                return jsonify({"success": True, "message": "Autentikasi berhasil!"})
            else:
                logging.warning("MFA Gagal: Kode OTP salah dimasukkan.")
                return jsonify({"success": False, "message": "Kode OTP tidak valid atau kadaluarsa."})

        # 6. Mengambil Formulir Biodata Pendaftar (Regular User)
        elif action == 'get_user_application':
            if session.get('role') != 'user':
                return jsonify({"success": False, "message": "Akses ditolak."})
                
            cursor.execute("SELECT * FROM applications WHERE user_id = ?", (session['user_id'],))
            app_data = cursor.fetchone()
            
            if app_data:
                app_dict = dict(app_data)
                # Masking NIK sebagai bentuk proteksi data
                raw_nik = app_dict['nik']
                if len(raw_nik) >= 16:
                    app_dict['nik'] = f"{raw_nik[:4]}********{raw_nik[-4:]}"
                return jsonify({"success": True, "data": app_dict})
            return jsonify({"success": False, "message": "Belum ada pendaftaran."})

        # 7. Menyimpan Formulir Pendaftaran dan Dokumen (Upload)
        elif action == 'submit_pmb':
            if session.get('role') != 'user':
                return jsonify({"success": False, "message": "Sesi kedaluwarsa."})
                
            cursor.execute("SELECT id FROM applications WHERE user_id = ?", (session['user_id'],))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Anda sudah mendaftar sebelumnya."})
                
            # Sanitasi input (XSS Protection)
            nik = html.escape(request.form.get('nik', '').strip())
            phone = html.escape(request.form.get('phone', '').strip())
            prodi = html.escape(request.form.get('prodi', '').strip())
            tempat_lahir = html.escape(request.form.get('tempat_lahir', '').strip())
            tanggal_lahir = html.escape(request.form.get('tanggal_lahir', '').strip())
            jk = html.escape(request.form.get('jk', '').strip())
            agama = html.escape(request.form.get('agama', '').strip())
            alamat = html.escape(request.form.get('alamat', '').strip())
            asal_sekolah = html.escape(request.form.get('asal_sekolah', '').strip())
            
            nama_ayah = html.escape(request.form.get('nama_ayah', '').strip())
            pek_ayah = html.escape(request.form.get('pekerjaan_ayah', '').strip())
            gaji_ayah = html.escape(request.form.get('gaji_ayah', '').strip())
            nama_ibu = html.escape(request.form.get('nama_ibu', '').strip())
            pek_ibu = html.escape(request.form.get('pekerjaan_ibu', '').strip())
            gaji_ibu = html.escape(request.form.get('gaji_ibu', '').strip())
            nama_wali = html.escape(request.form.get('nama_wali', '').strip())
            pek_wali = html.escape(request.form.get('pekerjaan_wali', '').strip())
            gaji_wali = html.escape(request.form.get('gaji_wali', '').strip())
            
            # File Upload Handler
            def process_file(f):
                if f and f.filename:
                    allowed_mimes = ['image/jpeg', 'image/png', 'application/pdf']
                    if f.mimetype not in allowed_mimes: return "invalid_type"
                    
                    file_bytes = f.read()
                    if len(file_bytes) > 2097152: return "too_large" # Max 2MB
                    
                    mime_type = f.mimetype
                    b64 = base64.b64encode(file_bytes).decode('utf-8')
                    return f"data:{mime_type};base64,{b64}"
                return None

            photo_b64 = process_file(request.files.get('photo'))
            ijazah_b64 = process_file(request.files.get('ijazah'))
            akta_b64 = process_file(request.files.get('akta'))
            kk_b64 = process_file(request.files.get('kk'))

            if not photo_b64 or not ijazah_b64 or not akta_b64 or not kk_b64:
                return jsonify({"success": False, "message": "Semua berkas wajib diunggah."})

            if "invalid_type" in [photo_b64, ijazah_b64, akta_b64, kk_b64]:
                return jsonify({"success": False, "message": "Tipe file tidak diizinkan. Hanya menerima JPG, PNG, atau PDF."})

            if "too_large" in [photo_b64, ijazah_b64, akta_b64, kk_b64]:
                return jsonify({"success": False, "message": "Maksimal ukuran per file adalah 2MB."})
                
            cursor.execute("""
                INSERT INTO applications 
                (user_id, nik, phone, prodi, tempat_lahir, tanggal_lahir, jenis_kelamin, agama, alamat, asal_sekolah, 
                 nama_ayah, pekerjaan_ayah, gaji_ayah, nama_ibu, pekerjaan_ibu, gaji_ibu, nama_wali, pekerjaan_wali, gaji_wali, 
                 photo, ijazah, akta, kk) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session['user_id'], nik, phone, prodi, tempat_lahir, tanggal_lahir, jk, agama, alamat, asal_sekolah, 
                  nama_ayah, pek_ayah, gaji_ayah, nama_ibu, pek_ibu, gaji_ibu, nama_wali, pek_wali, gaji_wali, 
                  photo_b64, ijazah_b64, akta_b64, kk_b64))
            
            conn.commit()
            return jsonify({"success": True, "message": "Formulir pendaftaran berhasil disimpan!"})

        # 8. Menarik Seluruh Data Aplikasi (Role Admin Area & IT Support)
        elif action == 'get_all_applications':
            if session.get('role') not in ['admin', 'operator']:
                return jsonify({"success": False, "message": "Akses ditolak."})
                
            cursor.execute("""
                SELECT a.id, a.nik, a.phone, a.prodi, a.photo, a.status, u.name, u.email 
                FROM applications a JOIN users u ON a.user_id = u.id 
                ORDER BY a.created_at DESC
            """)
            apps = []
            for row in cursor.fetchall():
                app_dict = dict(row)
                raw_nik = app_dict['nik']
                if len(raw_nik) >= 16:
                    app_dict['nik'] = f"{raw_nik[:4]}********{raw_nik[-4:]}"
                apps.append(app_dict)
            return jsonify({"success": True, "data": apps})

        # 9. Validasi Status (Role Admin Area & IT Support)
        elif action == 'update_status':
            if session.get('role') not in ['admin', 'operator']:
                return jsonify({"success": False, "message": "Akses ditolak."})
                
            app_id = request.form.get('app_id')
            status = request.form.get('status')
            
            if status not in ['Menunggu', 'Diterima', 'Ditolak']:
                return jsonify({"success": False, "message": "Status tidak valid."})
                
            cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
            conn.commit()
            return jsonify({"success": True, "message": f"Status berhasil diubah menjadi {status}."})

        # 10. Mengambil Daftar Seluruh User (Hanya Role IT Support/Operator)
        elif action == 'get_all_users':
            if session.get('role') != 'operator':
                return jsonify({"success": False, "message": "Akses ditolak. Fitur khusus IT Support."})
            
            cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id DESC")
            users = [dict(row) for row in cursor.fetchall()]
            return jsonify({"success": True, "data": users})

        # 11. Merubah Hak Akses User (Hanya Role IT Support/Operator)
        elif action == 'update_user_role':
            if session.get('role') != 'operator':
                return jsonify({"success": False, "message": "Akses ditolak. Fitur khusus IT Support."})
                
            user_id = request.form.get('user_id')
            new_role = request.form.get('role')
            
            if new_role not in ['user', 'admin', 'operator']:
                return jsonify({"success": False, "message": "Role tidak valid."})
                
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
            conn.commit()
            return jsonify({"success": True, "message": f"Hak akses berhasil diubah menjadi {new_role}."})

        # 12. Menghapus User dan Data Pendaftarannya (Hanya Role IT Support/Operator)
        elif action == 'delete_user':
            if session.get('role') != 'operator':
                return jsonify({"success": False, "message": "Akses ditolak. Fitur khusus IT Support."})
                
            user_id = request.form.get('user_id')
            # Proteksi agar operator tidak tidak sengaja menghapus akun dirinya sendiri
            if str(user_id) == str(session['user_id']):
                return jsonify({"success": False, "message": "Tidak dapat menghapus akun Anda sendiri."})
                
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return jsonify({"success": True, "message": "Akun berhasil dihapus."})

        return jsonify({"success": False, "message": "Action tidak dikenali."})
        
    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": "Sistem sedang mengalami gangguan."}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)