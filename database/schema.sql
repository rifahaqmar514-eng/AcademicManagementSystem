-- =====================================================================
-- schema.sql : Struktur database SIAKAD, fokus Nilai & IPK (8 tabel, 3NF)
-- DBMS       : MySQL 8.0.16+ (CHECK constraint baru ditegakkan mulai versi ini)
--
-- Identitas mahasiswa = NIM (primary key). Mahasiswa login dengan Nama + NIM,
-- sehingga tidak ada kolom password untuk mahasiswa. Admin punya akun tersendiri.
--
-- PERHATIAN: file ini MEMBANGUN ULANG database dari nol. Baris DROP DATABASE
-- di bawah menghapus seluruh data lama. Jalankan hanya saat tahap pengembangan.
-- Urutan impor: schema.sql -> seed.sql -> triggers_views.sql
-- =====================================================================

DROP DATABASE IF EXISTS siakad;

CREATE DATABASE siakad
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE siakad;

-- ---------------------------------------------------------------------
-- 1. jurusan
-- ---------------------------------------------------------------------
CREATE TABLE jurusan (
    jurusan_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kode_jurusan  VARCHAR(10)  NOT NULL,
    nama_jurusan  VARCHAR(100) NOT NULL,
    PRIMARY KEY (jurusan_id),
    UNIQUE KEY uq_jurusan_kode (kode_jurusan)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. program_studi (setiap prodi berada di bawah satu jurusan)
-- ---------------------------------------------------------------------
CREATE TABLE program_studi (
    prodi_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    jurusan_id  INT UNSIGNED NOT NULL,
    kode_prodi  VARCHAR(10)  NOT NULL,
    nama_prodi  VARCHAR(100) NOT NULL,
    jenjang     ENUM('D3','D4','S1','S2','S3') NOT NULL DEFAULT 'S1',
    PRIMARY KEY (prodi_id),
    UNIQUE KEY uq_prodi_kode (kode_prodi),
    KEY idx_prodi_jurusan (jurusan_id),
    CONSTRAINT fk_prodi_jurusan FOREIGN KEY (jurusan_id) REFERENCES jurusan (jurusan_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. mahasiswa : NIM adalah primary key. Jurusan diturunkan dari prodi
--    (tidak disimpan di sini agar tetap 3NF).
--    jenis_kelamin, tanggal_lahir, dan angkatan boleh kosong karena
--    formulir pendaftaran hanya meminta nama, NIM, jurusan, dan prodi.
-- ---------------------------------------------------------------------
CREATE TABLE mahasiswa (
    nim               VARCHAR(15)  NOT NULL,
    prodi_id          INT UNSIGNED NOT NULL,
    nama_lengkap      VARCHAR(100) NOT NULL,
    jenis_kelamin     ENUM('L','P') NULL,
    tanggal_lahir     DATE         NULL,
    angkatan          SMALLINT UNSIGNED NULL,
    status_mahasiswa  ENUM('Aktif','Cuti','Lulus','DO','Keluar') NOT NULL DEFAULT 'Aktif',
    terdaftar_pada    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (nim),
    KEY idx_mhs_prodi_angkatan (prodi_id, angkatan),
    KEY idx_mhs_nama (nama_lengkap),
    KEY idx_mhs_status (status_mahasiswa),
    CONSTRAINT fk_mhs_prodi FOREIGN KEY (prodi_id) REFERENCES program_studi (prodi_id),
    CONSTRAINT chk_mhs_nim CHECK (CHAR_LENGTH(nim) >= 5),
    CONSTRAINT chk_mhs_angkatan CHECK (angkatan IS NULL OR angkatan BETWEEN 1990 AND 2100)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. admin (akun terpisah; admin tidak punya NIM)
-- ---------------------------------------------------------------------
CREATE TABLE admin (
    admin_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username       VARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,          -- hash bcrypt, bukan password asli
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at  DATETIME     NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (admin_id),
    UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. mata_kuliah
-- ---------------------------------------------------------------------
CREATE TABLE mata_kuliah (
    mk_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kode_mk  VARCHAR(15)  NOT NULL,
    nama_mk  VARCHAR(150) NOT NULL,
    sks      TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (mk_id),
    UNIQUE KEY uq_mk_kode (kode_mk),
    KEY idx_mk_nama (nama_mk),
    CONSTRAINT chk_mk_sks CHECK (sks BETWEEN 1 AND 6)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. semester_akademik
-- ---------------------------------------------------------------------
CREATE TABLE semester_akademik (
    semester_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kode_semester   CHAR(5)      NOT NULL,          -- contoh: 20251 (tahun + 1 ganjil / 2 genap / 3 pendek)
    tahun_akademik  VARCHAR(9)   NOT NULL,          -- contoh: 2025/2026
    jenis           ENUM('Ganjil','Genap','Pendek') NOT NULL,
    PRIMARY KEY (semester_id),
    UNIQUE KEY uq_semester_kode (kode_semester)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. skala_nilai (huruf mutu ditentukan dari rentang nilai_akhir)
-- ---------------------------------------------------------------------
CREATE TABLE skala_nilai (
    skala_id    SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    huruf_mutu  CHAR(2)       NOT NULL,
    bobot_mutu  DECIMAL(3,2)  NOT NULL,
    nilai_min   DECIMAL(5,2)  NOT NULL,
    nilai_max   DECIMAL(5,2)  NOT NULL,
    is_lulus    BOOLEAN       NOT NULL,
    PRIMARY KEY (skala_id),
    UNIQUE KEY uq_skala_huruf (huruf_mutu),
    CONSTRAINT chk_skala_bobot   CHECK (bobot_mutu BETWEEN 0 AND 4),
    CONSTRAINT chk_skala_rentang CHECK (nilai_min >= 0 AND nilai_min <= nilai_max AND nilai_max <= 100)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 8. nilai
--    nilai_akhir = tugas 30% + UTS 30% + UAS 40% (kolom turunan, dihitung DB).
--    Huruf mutu TIDAK disimpan di sini (agar 3NF); diperoleh lewat view
--    dengan mencocokkan nilai_akhir ke rentang di skala_nilai.
--    ON UPDATE CASCADE: bila NIM diubah, nilai ikut mengikuti.
-- ---------------------------------------------------------------------
CREATE TABLE nilai (
    nilai_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nim          VARCHAR(15)  NOT NULL,
    mk_id        INT UNSIGNED NOT NULL,
    semester_id  INT UNSIGNED NOT NULL,
    nilai_tugas  DECIMAL(5,2) NOT NULL,
    nilai_uts    DECIMAL(5,2) NOT NULL,
    nilai_uas    DECIMAL(5,2) NOT NULL,
    nilai_akhir  DECIMAL(5,2) GENERATED ALWAYS AS
                 (ROUND(nilai_tugas * 0.30 + nilai_uts * 0.30 + nilai_uas * 0.40, 2)) STORED,
    PRIMARY KEY (nilai_id),
    UNIQUE KEY uq_nilai_nim_mk_semester (nim, mk_id, semester_id),
    KEY idx_nilai_mk (mk_id),
    KEY idx_nilai_semester (semester_id),
    CONSTRAINT fk_nilai_mhs      FOREIGN KEY (nim)         REFERENCES mahasiswa (nim) ON UPDATE CASCADE,
    CONSTRAINT fk_nilai_mk       FOREIGN KEY (mk_id)       REFERENCES mata_kuliah (mk_id),
    CONSTRAINT fk_nilai_semester FOREIGN KEY (semester_id) REFERENCES semester_akademik (semester_id),
    CONSTRAINT chk_nilai_tugas CHECK (nilai_tugas BETWEEN 0 AND 100),
    CONSTRAINT chk_nilai_uts   CHECK (nilai_uts   BETWEEN 0 AND 100),
    CONSTRAINT chk_nilai_uas   CHECK (nilai_uas   BETWEEN 0 AND 100)
) ENGINE=InnoDB;