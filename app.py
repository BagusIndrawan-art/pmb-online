from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import base64
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import datetime
import html

app = Flask(__name__)
app.secret_key = 'super_secret_pmb_key_2026'

# --- KONFIGURASI KEAMANAN KHUSUS UNTUK ONLINE (GITHub Pages) ---
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True  # KONTROL 3: Manajemen Session & Cookie (Mencegah pencurian XSS)

# KONTROL 8: Logging & Monitoring
logging.basicConfig(filename='security.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURASI CORS ---
# Izinkan akses HANYA dari URL GitHub Pages kamu
CORS(app, supports_credentials=True, origins=["https://bagusindrawan-art.github.io"])

def get_db_connection():
    try:
        # Menggunakan SQLite (Database berbentuk file yang tersimpan otomatis di folder yang sama)
        db_path = os.path.join(os.path.dirname(__file__), 'pmb_online.db')
        conn = sqlite3.connect(db_path)
        
        # Agar hasil fetch berupa dictionary (seperti MySQL)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # Pembuatan tabel otomatis
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
        
        conn.commit()
        return conn, cursor
    except sqlite3.Error as err:
        print(f"Error Database: {err}")
        return None, None

@app.route('/api', methods=['GET', 'POST'])
def api_handler():
    action = request.args.get('action') if request.method == 'GET' else request.form.get('action')
    
    conn, cursor = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Gagal membaca database SQLite."}), 500

    try:
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

        elif action == 'logout':
            session.clear()
            return jsonify({"success": True, "message": "Anda telah keluar sistem."})

        elif action == 'register':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            is_admin = request.form.get('is_admin')
            
            if not name or not email or not password:
                return jsonify({"success": False, "message": "Data tidak lengkap."})
                
            role = 'admin' if is_admin else 'user'
            hashed_pw = generate_password_hash(password)
            
            try:
                # Perubahan syntax parameter SQLite menggunakan tanda '?' 
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                              (name, email, hashed_pw, role))
                conn.commit()
                return jsonify({"success": True, "message": "Registrasi berhasil! Silakan login."})
            except sqlite3.IntegrityError:
                return jsonify({"success": False, "message": "Email sudah terdaftar."})

        elif action == 'login':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                # KONTROL 1: Sistem Lockout & Password Hashing
                if user['locked_until'] and datetime.datetime.strptime(user['locked_until'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.now():
                    logging.warning(f"Brute-Force Terblokir: Akun {email} mencoba login saat masa lockout.")
                    return jsonify({"success": False, "message": "Akun terkunci karena terlalu banyak percobaan gagal. Silakan coba 15 menit lagi."})

                if check_password_hash(user['password'], password):
                    # Reset failed attempts jika login sukses
                    cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE email = ?", (email,))
                    conn.commit()
                    
                    session['user_id'] = user['id']
                    session['name'] = user['name']
                    session['role'] = user['role']
                    logging.info(f"Login Sukses: User {email} (Role: {user['role']})")
                    return jsonify({"success": True, "message": "Login berhasil!", "data": {"name": user['name'], "role": user['role']}})
                else:
                    # Tambah hitungan gagal
                    attempts = user['failed_attempts'] + 1
                    locked_until = None
                    if attempts >= 3: # Lockout setelah 3 kali salah
                        locked_until = (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                        logging.warning(f"Lockout Diaktifkan: Akun {email} gagal login 3x.")
                    
                    cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE email = ?", (attempts, locked_until, email))
                    conn.commit()
                    logging.warning(f"Login Gagal: {email} (Percobaan ke-{attempts})")
                    
            return jsonify({"success": False, "message": "Email atau Password salah."})

        elif action == 'get_user_application':
            if session.get('role') != 'user':
                logging.warning(f"Unauthorized Access: Seseorang mencoba bypass ke data pendaftaran.")
                return jsonify({"success": False, "message": "Akses ditolak."})
                
            # KONTROL 2: Otorisasi (Hanya mengambil data berdasarkan ID Sesi milik sendiri)
            cursor.execute("SELECT * FROM applications WHERE user_id = ?", (session['user_id'],))
            app_data = cursor.fetchone()
            
            if app_data:
                app_dict = dict(app_data)
                
                # KONTROL 7: Proteksi Data Sensitif (Masking NIK)
                raw_nik = app_dict['nik']
                if len(raw_nik) >= 16:
                    app_dict['nik'] = f"{raw_nik[:4]}********{raw_nik[-4:]}"
                    
                return jsonify({"success": True, "data": app_dict})
            return jsonify({"success": False, "message": "Belum ada pendaftaran."})

        elif action == 'submit_pmb':
            if session.get('role') != 'user':
                return jsonify({"success": False, "message": "Sesi kedaluwarsa."})
                
            cursor.execute("SELECT id FROM applications WHERE user_id = ?", (session['user_id'],))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Anda sudah mendaftar sebelumnya."})
                
            # KONTROL 4: Validasi & Sanitasi Input (html.escape mencegah XSS Injection)
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
            
            def process_file(f):
                if f and f.filename:
                    # KONTROL 5: Proteksi Upload File (Strict MIME-Type Check)
                    allowed_mimes = ['image/jpeg', 'image/png', 'application/pdf']
                    if f.mimetype not in allowed_mimes:
                        return "invalid_type"
                        
                    file_bytes = f.read()
                    if len(file_bytes) > 2097152: 
                        return "too_large"
                        
                    mime_type = f.mimetype
                    b64 = base64.b64encode(file_bytes).decode('utf-8')
                    return f"data:{mime_type};base64,{b64}"
                return None

            photo_b64 = process_file(request.files.get('photo'))
            ijazah_b64 = process_file(request.files.get('ijazah'))
            akta_b64 = process_file(request.files.get('akta'))
            kk_b64 = process_file(request.files.get('kk'))

            if not photo_b64 or not ijazah_b64 or not akta_b64 or not kk_b64:
                return jsonify({"success": False, "message": "Semua berkas (Foto, Ijazah, Akta, KK) wajib diunggah."})

            if "invalid_type" in [photo_b64, ijazah_b64, akta_b64, kk_b64]:
                logging.warning(f"File Rejection: Upaya upload file berbahaya oleh User ID {session['user_id']}")
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
            return jsonify({"success": True, "message": "Formulir pendaftaran beserta berkas berhasil disimpan!"})

        elif action == 'get_all_applications':
            # KONTROL 2: Otorisasi RBAC (Hanya Admin)
            if session.get('role') != 'admin':
                logging.warning(f"Privilege Escalation Attempt: {session.get('email')} mencoba akses halaman admin.")
                return jsonify({"success": False, "message": "Akses khusus admin."})
                
            cursor.execute("""
                SELECT a.id, a.nik, a.phone, a.prodi, a.photo, a.status, u.name, u.email 
                FROM applications a JOIN users u ON a.user_id = u.id 
                ORDER BY a.created_at DESC
            """)
            apps = []
            for row in cursor.fetchall():
                app_dict = dict(row)
                # KONTROL 7: Masking NIK untuk Operator juga
                raw_nik = app_dict['nik']
                if len(raw_nik) >= 16:
                    app_dict['nik'] = f"{raw_nik[:4]}********{raw_nik[-4:]}"
                apps.append(app_dict)
                
            logging.info(f"Admin Access: {session.get('email')} memuat seluruh data pendaftaran.")
            return jsonify({"success": True, "data": apps})

        elif action == 'update_status':
            if session.get('role') != 'admin':
                return jsonify({"success": False, "message": "Akses khusus admin."})
                
            app_id = request.form.get('app_id')
            status = request.form.get('status')
            
            if status not in ['Menunggu', 'Diterima', 'Ditolak']:
                return jsonify({"success": False, "message": "Status tidak valid."})
                
            cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
            conn.commit()
            return jsonify({"success": True, "message": f"Status berhasil diubah menjadi {status}."})

        return jsonify({"success": False, "message": "Action tidak dikenali."})
        
    except Exception as e:
        # KONTROL 6: Error Handling (Jangan pernah tampilkan query database ke user)
        logging.error(f"Internal Server Error: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Sistem sedang mengalami gangguan. Silakan coba beberapa saat lagi."}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)