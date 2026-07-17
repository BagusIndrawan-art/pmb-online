from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import base64
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Secret key diperlukan untuk manajemen sesi (session)
app.secret_key = 'super_secret_pmb_key_2026'

# Mengizinkan akses lintas asal (CORS) dari Live Server atau browser lokal dengan dukungan kredensial (cookie)
CORS(app, supports_credentials=True)

def get_db_connection():
    try:
        # Koneksi awal ke server MySQL (Pastikan XAMPP MySQL menyala)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor(dictionary=True)
        
        # Membuat database jika belum ada
        cursor.execute("CREATE DATABASE IF NOT EXISTS pmb_online CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        cursor.execute("USE pmb_online")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                nik VARCHAR(20) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                prodi VARCHAR(100) NOT NULL,
                tempat_lahir VARCHAR(100),
                tanggal_lahir DATE,
                jenis_kelamin ENUM('Laki-laki', 'Perempuan'),
                agama VARCHAR(50),
                alamat TEXT,
                asal_sekolah VARCHAR(150),
                nama_ayah VARCHAR(100),
                pekerjaan_ayah VARCHAR(100),
                gaji_ayah VARCHAR(50),
                nama_ibu VARCHAR(100),
                pekerjaan_ibu VARCHAR(100),
                gaji_ibu VARCHAR(50),
                nama_wali VARCHAR(100),
                pekerjaan_wali VARCHAR(100),
                gaji_wali VARCHAR(50),
                photo LONGTEXT NOT NULL,
                ijazah LONGTEXT,
                akta LONGTEXT,
                kk LONGTEXT,
                status ENUM('Menunggu', 'Diterima', 'Ditolak') DEFAULT 'Menunggu',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Ini mencegah error dan otomatis menambahkan kolom-kolom baru
        columns_to_add = [
            "tempat_lahir VARCHAR(100) AFTER prodi",
            "tanggal_lahir DATE AFTER tempat_lahir",
            "jenis_kelamin ENUM('Laki-laki', 'Perempuan') AFTER tanggal_lahir",
            "agama VARCHAR(50) AFTER jenis_kelamin",
            "alamat TEXT AFTER agama",
            "asal_sekolah VARCHAR(150) AFTER alamat",
            "nama_ayah VARCHAR(100) AFTER asal_sekolah",
            "pekerjaan_ayah VARCHAR(100) AFTER nama_ayah",
            "gaji_ayah VARCHAR(50) AFTER pekerjaan_ayah",
            "nama_ibu VARCHAR(100) AFTER gaji_ayah",
            "pekerjaan_ibu VARCHAR(100) AFTER nama_ibu",
            "gaji_ibu VARCHAR(50) AFTER pekerjaan_ibu",
            "nama_wali VARCHAR(100) AFTER gaji_ibu",
            "pekerjaan_wali VARCHAR(100) AFTER nama_wali",
            "gaji_wali VARCHAR(50) AFTER pekerjaan_wali",
            "ijazah LONGTEXT AFTER photo",
            "akta LONGTEXT AFTER ijazah",
            "kk LONGTEXT AFTER akta"
        ]
        
        for col in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {col}")
            except mysql.connector.Error:
                pass # Abaikan jika kolom sudah eksis

        conn.commit()
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error Database: {err}")
        return None, None

@app.route('/api', methods=['GET', 'POST'])
def api_handler():
    # Mendapatkan jenis aksi dari parameter URL (GET) atau form data (POST)
    action = request.args.get('action') if request.method == 'GET' else request.form.get('action')
    
    conn, cursor = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Gagal terhubung ke database MySQL."}), 500

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
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)", 
                              (name, email, hashed_pw, role))
                conn.commit()
                return jsonify({"success": True, "message": "Registrasi berhasil! Silakan login."})
            except mysql.connector.IntegrityError:
                return jsonify({"success": False, "message": "Email sudah terdaftar."})

        elif action == 'login':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['role'] = user['role']
                return jsonify({"success": True, "message": "Login berhasil!", "data": {"name": user['name'], "role": user['role']}})
            return jsonify({"success": False, "message": "Email atau Password salah."})

        elif action == 'get_user_application':
            if session.get('role') != 'user':
                return jsonify({"success": False, "message": "Akses ditolak."})
                
            cursor.execute("SELECT * FROM applications WHERE user_id = %s", (session['user_id'],))
            app_data = cursor.fetchone()
            
            if app_data:
                # Format tanggal agar aman dikirim ke frontend JSON
                if app_data.get('tanggal_lahir'):
                    app_data['tanggal_lahir'] = app_data['tanggal_lahir'].strftime('%Y-%m-%d')
                return jsonify({"success": True, "data": app_data})
            return jsonify({"success": False, "message": "Belum ada pendaftaran."})

        elif action == 'submit_pmb':
            if session.get('role') != 'user':
                return jsonify({"success": False, "message": "Sesi kedaluwarsa."})
                
            # Cek apakah sudah pernah mendaftar
            cursor.execute("SELECT id FROM applications WHERE user_id = %s", (session['user_id'],))
            if cursor.fetchone():
                return jsonify({"success": False, "message": "Anda sudah mendaftar sebelumnya."})
                
            # Mengambil data form text (A. Pribadi & B. Pendidikan)
            nik = request.form.get('nik', '').strip()
            phone = request.form.get('phone', '').strip()
            prodi = request.form.get('prodi', '').strip()
            tempat_lahir = request.form.get('tempat_lahir', '').strip()
            tanggal_lahir = request.form.get('tanggal_lahir', '').strip()
            jk = request.form.get('jk', '').strip()
            agama = request.form.get('agama', '').strip()
            alamat = request.form.get('alamat', '').strip()
            asal_sekolah = request.form.get('asal_sekolah', '').strip()
            
            nama_ayah = request.form.get('nama_ayah', '').strip()
            pek_ayah = request.form.get('pekerjaan_ayah', '').strip()
            gaji_ayah = request.form.get('gaji_ayah', '').strip()
            nama_ibu = request.form.get('nama_ibu', '').strip()
            pek_ibu = request.form.get('pekerjaan_ibu', '').strip()
            gaji_ibu = request.form.get('gaji_ibu', '').strip()
            nama_wali = request.form.get('nama_wali', '').strip()
            pek_wali = request.form.get('pekerjaan_wali', '').strip()
            gaji_wali = request.form.get('gaji_wali', '').strip()
            
            def process_file(f):
                if f and f.filename:
                    file_bytes = f.read()
                    if len(file_bytes) > 2097152: # Batas Maksimal 2MB
                        return "too_large"
                    mime_type = f.mimetype
                    b64 = base64.b64encode(file_bytes).decode('utf-8')
                    return f"data:{mime_type};base64,{b64}"
                return None

            # Memproses semua file yang dikirim
            photo_b64 = process_file(request.files.get('photo'))
            ijazah_b64 = process_file(request.files.get('ijazah'))
            akta_b64 = process_file(request.files.get('akta'))
            kk_b64 = process_file(request.files.get('kk'))

            if not photo_b64 or not ijazah_b64 or not akta_b64 or not kk_b64:
                return jsonify({"success": False, "message": "Semua berkas (Foto, Ijazah, Akta, KK) wajib diunggah."})

            if "too_large" in [photo_b64, ijazah_b64, akta_b64, kk_b64]:
                return jsonify({"success": False, "message": "Maksimal ukuran per file adalah 2MB."})
                
            cursor.execute("""
                INSERT INTO applications 
                (user_id, nik, phone, prodi, tempat_lahir, tanggal_lahir, jenis_kelamin, agama, alamat, asal_sekolah, 
                 nama_ayah, pekerjaan_ayah, gaji_ayah, nama_ibu, pekerjaan_ibu, gaji_ibu, nama_wali, pekerjaan_wali, gaji_wali, 
                 photo, ijazah, akta, kk) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], nik, phone, prodi, tempat_lahir, tanggal_lahir, jk, agama, alamat, asal_sekolah, 
                  nama_ayah, pek_ayah, gaji_ayah, nama_ibu, pek_ibu, gaji_ibu, nama_wali, pek_wali, gaji_wali, 
                  photo_b64, ijazah_b64, akta_b64, kk_b64))
            
            conn.commit()
            return jsonify({"success": True, "message": "Formulir pendaftaran beserta berkas berhasil disimpan!"})

        elif action == 'get_all_applications':
            if session.get('role') != 'admin':
                return jsonify({"success": False, "message": "Akses khusus admin."})
                
            cursor.execute("""
                SELECT a.id, a.nik, a.phone, a.prodi, a.photo, a.status, u.name, u.email 
                FROM applications a JOIN users u ON a.user_id = u.id 
                ORDER BY a.created_at DESC
            """)
            return jsonify({"success": True, "data": cursor.fetchall()})

        elif action == 'update_status':
            if session.get('role') != 'admin':
                return jsonify({"success": False, "message": "Akses khusus admin."})
                
            app_id = request.form.get('app_id')
            status = request.form.get('status')
            
            if status not in ['Menunggu', 'Diterima', 'Ditolak']:
                return jsonify({"success": False, "message": "Status tidak valid."})
                
            cursor.execute("UPDATE applications SET status = %s WHERE id = %s", (status, app_id))
            conn.commit()
            return jsonify({"success": True, "message": f"Status berhasil diubah menjadi {status}."})

        # Endpoint default jika tidak ada action yang cocok
        return jsonify({"success": False, "message": "Action tidak dikenali."})
        
    except Exception as e:
        print(f"Error pada server: {e}")
        return jsonify({"success": False, "message": f"Terjadi kesalahan di server."}), 500
    finally:
        # Selalu pastikan koneksi database ditutup untuk mencegah kebocoran memori
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)