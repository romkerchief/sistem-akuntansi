# Sistem Akuntansi — Panduan Instalasi & Setup

README ini dibuat untuk memudahkan kamu (atau siapa pun) dalam melakukan instalasi dan menjalankan project Django **Sistem Akuntansi** dengan lancar. Ikuti langkah-langkah berikut dari awal sampai akhir.

---

## 📦 1. Instal Python 3.13.x

Download dan instal Python versi 3.13.x.
Saat instalasi, **wajib centang**:

* ✔️ *Add Python to PATH*

---

## 🖥️ 2. Buka Terminal / CMD / PowerShell

Gunakan salah satu terminal berikut:

* Command Prompt
* PowerShell
* Windows Terminal
* Git Bash

---

## 📥 3. Clone Repository

Jalankan perintah berikut:

```bash
git clone https://github.com/romkerchief/sistem-akuntansi.git
```

---

## 📂 4. Masuk ke Folder Project

```bash
cd sistem-akuntansi
```

---

## 🧪 5. (Opsional Tapi Direkomendasikan) Buat Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Jika environment aktif, kamu akan melihat `(venv)` di awal baris terminal.

---

## 📚 6. Install Dependencies

Pastikan file `requirements.txt` sudah ada.

```bash
pip install -r requirements.txt
```

---

## 🗄️ 7. Setting Database (MySQL)

1. Jalankan **XAMPP** dan nyalakan **MySQL**.
2. Buka **phpMyAdmin**.
3. Buat database baru, misalnya:

   * `sistem_akuntansi`
4. Sesuaikan konfigurasi database di `settings.py`:

Contoh:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sistem_akuntansi',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

Pastikan:

* Nama database sama dengan yang kamu buat
* Username/password sesuai dengan setting MySQL kamu

---

## 🏗️ 8. Jalankan Migrasi Django

```bash
python manage.py migrate
```

Ini akan membuat semua tabel yang dibutuhkan di database.

---

## 🚀 9. Jalankan Server Django

```bash
python manage.py runserver
```

Setelah itu buka browser dan akses:

```
http://127.0.0.1:8000/
```

---

## 🎉 Selesai!

Project sudah berjalan. Kamu bisa mulai ngembangin fitur atau menjalankan aplikasinya.

Jika ada error, cek hal-hal berikut:

* Python benar-benar sudah masuk PATH
* Virtual environment aktif
* Nama database dan user/password MySQL sudah benar
* MySQL server aktif

---

## 🤝 Kontribusi

Pull request dan issue dipersilakan bila ingin bantu improve project.

---

## 📄 Lisensi

Project ini mengikuti lisensi yang tertera di repository (jika ada).

---

Kalau kamu mau, aku bisa buatin versi README bahasa Inggris atau versi dengan gambar (screenshot step by step).
