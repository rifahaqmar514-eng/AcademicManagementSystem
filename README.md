# Academic Management System (SIAKAD)

Aplikasi desktop Python dan MySQL untuk mengelola data akademik mahasiswa, KRS, nilai, transkrip, IPS, dan IPK. Antarmuka dibuat dengan Tkinter/ttk.

## Fitur

- Login admin dan dosen menggunakan username dan password.
- Mahasiswa mendaftar dan login menggunakan nama lengkap serta NIM.
- Pengelolaan data mahasiswa, dosen, jurusan, program studi, kelas, dan mata kuliah.
- Pengajuan KRS oleh mahasiswa serta persetujuan oleh dosen PA.
- Input nilai oleh dosen untuk kelas yang diajar.
- Transkrip, IPS, dan IPK disajikan melalui view database.
- Pencarian dan filter data.

## Hak akses

| Fitur             | Admin  | Dosen                           | Mahasiswa                     |
| ----------------- | ------ | ------------------------------- | ----------------------------- |
| Data mahasiswa    | Kelola | Lihat sesuai akses              | —                             |
| Data dosen        | Kelola | —                               | —                             |
| Master akademik   | Kelola | —                               | —                             |
| KRS               | —      | Setujui KRS mahasiswa bimbingan | Ajukan dan kelola KRS sendiri |
| Nilai             | Lihat  | Input nilai kelas yang diajar   | Lihat nilai sendiri           |
| Transkrip dan IPK | Lihat  | Lihat                           | Lihat milik sendiri           |

Pembatasan akses diterapkan di backend melalui <code>utils/permissions.py</code>, bukan hanya dengan menyembunyikan menu.

## Struktur aplikasi

```text
AcademicManagementSystem/
├── main.py                         # Menjalankan aplikasi
├── config.py                       # Membaca pengaturan database dari .env
├── .env.example                    # Contoh konfigurasi lokal
├── .env                            # Konfigurasi lokal; jangan di-commit
├── .gitignore                      # Mengecualikan file rahasia dan cache dari Git
├── requirements.txt                # Daftar library Python
├── assets/
│   └── colors.py                   # Warna dan tema tampilan
├── backend/
│   ├── auth.py                     # Login dan pendaftaran
│   ├── dashboard.py                # Ringkasan statistik beranda
│   ├── dosen.py                    # Data dan akun dosen
│   ├── ipk.py                      # Data transkrip, IPS, dan IPK
│   ├── jurusan.py                  # Data jurusan
│   ├── kelas.py                    # Data kelas kuliah
│   ├── krs.py                      # Pengajuan dan persetujuan KRS
│   ├── mahasiswa.py                # Data mahasiswa
│   ├── mata_kuliah.py              # Data mata kuliah
│   ├── nilai.py                    # Input dan pembacaan nilai
│   ├── prodi.py                    # Data program studi
│   ├── semester.py                 # Data semester akademik
│   └── skala_nilai.py              # Rentang nilai dan bobot mutu
├── database/
│   ├── connection.py               # Membuka koneksi dan menjalankan query MySQL
│   ├── create_admin.py             # Membuat akun admin pertama
│   ├── schema.sql                  # Skema lama; berbahaya untuk database aktif
│   ├── seed.sql                    # Data contoh dan data referensi
│   ├── seed_jurusan_prodi.sql      # Data jurusan dan program studi kampus
│   ├── triggers_views.sql          # Membuat view transkrip, IPS, dan IPK
│   ├── migrate_fakultas_to_jurusan.sql
│   │                                # Migrasi struktur fakultas lama ke jurusan
│   └── migrate_student_public_registration.sql
│                                    # Mengubah kolom untuk pendaftaran mahasiswa
├── frontend/
│   ├── main_window.py              # Jendela utama dan navigasi aplikasi
│   ├── login_page.py               # Login dan formulir pendaftaran mahasiswa
│   ├── akademik_master_page.py     # Tampilan data master akademik
│   ├── mahasiswa_page.py           # Tampilan dan pengelolaan mahasiswa
│   ├── dosen_page.py               # Tampilan dan pengelolaan dosen
│   ├── kelas_page.py               # Tampilan dan pengelolaan kelas
│   ├── krs_page.py                 # Tampilan KRS mahasiswa dan dosen
│   ├── nilai_page.py               # Tampilan input nilai
│   └── transkrip_page.py           # Tampilan transkrip dan IPK
├── utils/
│   ├── permissions.py              # Mengatur hak akses berdasarkan role
│   ├── security.py                 # Hash dan pemeriksaan password
│   ├── session.py                  # Menyimpan sesi pengguna yang login
│   └── validators.py               # Memeriksa format dan nilai input
├── docs/
│   └── erd_ipk.png                 # Gambar diagram database
└── README.md                       # Panduan proyek
```

Folder <code>**pycache**/</code> dibuat otomatis oleh Python dan tidak perlu di-commit.

## Database

Backend saat ini menggunakan skema akademik yang mencakup <code>users</code>, <code>roles</code>, <code>mahasiswa</code>, <code>dosen</code>, <code>jurusan</code>, <code>program_studi</code>, <code>kurikulum</code>, <code>mata_kuliah</code>, <code>semester_akademik</code>, <code>kelas</code>, <code>kelas_dosen</code>, <code>krs</code>, <code>krs_detail</code>, <code>nilai_akhir</code>, dan tabel pendukung lainnya.

> **Peringatan:** <code>database/schema.sql</code> yang ada di repository masih merupakan skema prototipe lama. File itu menjalankan <code>DROP DATABASE IF EXISTS siakad</code> dan membuat hanya delapan tabel yang tidak sesuai dengan kebutuhan backend saat ini. Menjalankannya akan menghapus database <code>siakad</code> beserta isinya. Jangan jalankan file tersebut pada database aktif.

File <code>seed.sql</code> dan <code>triggers_views.sql</code> juga mengacu pada skema akademik yang lebih lengkap, sehingga belum dapat dipakai sebagai proses instalasi baru bersama <code>schema.sql</code> yang sekarang. Setup database dari nol belum terdokumentasi secara lengkap; skema utama perlu diselaraskan terlebih dahulu.

### File migrasi dan seed

File-file berikut mengubah database. Buat backup terlebih dahulu dan jalankan hanya jika kondisi awalnya sesuai:

- <code>database/migrate_fakultas_to_jurusan.sql</code>: migrasi satu kali untuk database lama yang memiliki tabel <code>fakultas</code> dan kolom <code>program_studi.fakultas_id</code>. Migrasi ini menghapus tabel lama <code>fakultas</code> setelah memindahkan datanya.
- <code>database/migrate_student_public_registration.sql</code>: membuat kolom akun dan biodata tertentu menerima <code>NULL</code>, sesuai formulir pendaftaran mahasiswa publik. Jalankan satu kali pada skema yang memiliki tabel dan constraint yang disebut di dalam file.
- <code>database/seed_jurusan_prodi.sql</code>: memasukkan data 10 jurusan dan 25 program studi kampus. Dapat dijalankan ulang berdasarkan kode jurusan/prodi.
- <code>database/seed.sql</code>: data referensi dan contoh untuk skema penuh. Berisi data mahasiswa dan nilai contoh.
- <code>database/triggers_views.sql</code>: membuat view <code>v_transkrip</code>, <code>v_ips</code>, dan <code>v_ipk</code>; memerlukan tabel KRS, kelas, dan nilai pada skema penuh.

Jangan menjalankan ulang migrasi satu kali pada database yang sudah dimigrasikan. Pastikan database dan kondisi awal sesuai dengan komentar di setiap file.

## Persiapan lingkungan

Gunakan Python 3.10 atau lebih baru, MySQL 8.0+, serta Laragon jika bekerja di Windows. Tkinter/ttk disertakan pada instalasi Python Windows standar.

1.  Clone repository dan masuk ke folder proyek.

    git clone https://github.com/rhalstlyapp/AcademicManagementSystem.git
    cd AcademicManagementSystem

2.  Buat virtual environment dan pasang dependensi.

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

3.  Salin <code>.env.example</code> menjadi <code>.env</code>, lalu sesuaikan koneksi database lokal.

        Copy-Item .env.example .env

    Untuk Laragon bawaan, umumnya <code>DB_HOST=localhost</code>, <code>DB_PORT=3306</code>, <code>DB_USER=root</code>, dan <code>DB_PASSWORD=</code> (kosong). Isi <code>DB_NAME=siakad</code>. Jangan commit <code>.env</code> ke Git.

4.  Pastikan MySQL aktif dan database <code>siakad</code> sudah memakai skema lengkap yang sesuai dengan backend. **Jangan gunakan <code>database/schema.sql</code> saat ini untuk menyiapkan database**, karena file itu menghapus database dan membuat skema lama yang tidak kompatibel.

5.  Setelah skema <code>users</code> dan <code>roles</code> tersedia, buat akun admin:

        python database/create_admin.py

    Password diminta di terminal dan disimpan sebagai hash bcrypt.

6.  Jalankan aplikasi dari folder proyek:

    python main.py

## Konfigurasi dan keamanan

- <code>config.py</code> membaca konfigurasi lokal dari <code>.env</code>.
- <code>.env</code> berisi rahasia dan dikecualikan oleh <code>.gitignore</code>; gunakan <code>.env.example</code> sebagai templat tanpa rahasia.
- Password admin dan dosen disimpan sebagai hash bcrypt.
- Mahasiswa login dengan nama lengkap dan NIM sesuai alur aplikasi saat ini.
- Jangan menyimpan dump database atau file backup berisi data pribadi di repository.

## Status proyek

Proyek masih dalam pengembangan. Sebelum repository dapat dipasang dari database kosong, <code>database/schema.sql</code>, seed, view, dan dokumentasi setup perlu diselaraskan dengan skema yang dipakai backend.
