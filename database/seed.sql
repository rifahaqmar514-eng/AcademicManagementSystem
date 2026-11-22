-- =====================================================================
-- seed.sql : Data awal dan data contoh. Jalankan SETELAH schema.sql.
-- Aman dijalankan ulang (baris yang sudah ada dilewati).
-- Akun admin TIDAK dibuat di sini; gunakan: python database/create_admin.py
-- Mahasiswa tidak punya password: login memakai Nama + NIM.
-- =====================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
USE siakad;

INSERT IGNORE INTO roles (nama_role) VALUES ('admin'), ('dosen'), ('mahasiswa');

-- ---------------------------------------------------------------------
-- 1. Skala nilai (sesuai asumsi: D dianggap lulus, E tidak lulus)
-- ---------------------------------------------------------------------
INSERT IGNORE INTO skala_nilai (huruf_mutu, bobot_mutu, nilai_min, nilai_max, is_lulus) VALUES
    ('A',  4.00, 85.00, 100.00, TRUE),
    ('AB', 3.50, 80.00,  84.99, TRUE),
    ('B',  3.00, 70.00,  79.99, TRUE),
    ('BC', 2.50, 65.00,  69.99, TRUE),
    ('C',  2.00, 55.00,  64.99, TRUE),
    ('D',  1.00, 40.00,  54.99, TRUE),
    ('E',  0.00,  0.00,  39.99, FALSE);

-- ---------------------------------------------------------------------
-- 2. Data contoh (fiktif, untuk uji coba dan demo; ganti sesuai kampus)
-- ---------------------------------------------------------------------
INSERT IGNORE INTO jurusan (kode_jurusan, nama_jurusan) VALUES
    ('JTI', 'Teknologi Informasi'),
    ('JTE', 'Teknik Elektro');

INSERT IGNORE INTO program_studi (jurusan_id, kode_prodi, nama_prodi, jenjang)
SELECT j.jurusan_id, t.kode_prodi, t.nama_prodi, t.jenjang
FROM (
    SELECT 'JTI' AS kode_jurusan, 'TI' AS kode_prodi, 'Teknik Informatika' AS nama_prodi, 'S1' AS jenjang
    UNION ALL SELECT 'JTI', 'SI', 'Sistem Informasi',       'S1'
    UNION ALL SELECT 'JTE', 'TE', 'Teknik Elektro',         'S1'
    UNION ALL SELECT 'JTE', 'TT', 'Teknik Telekomunikasi',  'D4'
) AS t
JOIN jurusan j ON j.kode_jurusan = t.kode_jurusan;

INSERT IGNORE INTO semester_akademik (kode_semester, tahun_akademik, jenis) VALUES
    ('20251', '2025/2026', 'Ganjil'),
    ('20252', '2025/2026', 'Genap'),
    ('20261', '2026/2027', 'Ganjil');

INSERT IGNORE INTO mata_kuliah (kode_mk, nama_mk, sks) VALUES
    ('IF101', 'Algoritma dan Pemrograman', 3),
    ('IF102', 'Basis Data',                3),
    ('IF103', 'Matematika Diskrit',        3),
    ('IF104', 'Struktur Data',             3),
    ('IF105', 'Jaringan Komputer',         2),
    ('IF106', 'Pemrograman Web',           3);

INSERT IGNORE INTO mahasiswa (nim, prodi_id, nama_lengkap, jenis_kelamin, tanggal_lahir, angkatan)
SELECT t.nim, p.prodi_id, t.nama, t.jk, t.tgl, t.angkatan
FROM (
    SELECT '2501001' AS nim, 'Budi Santoso' AS nama, 'L' AS jk, '2006-03-14' AS tgl, 2025 AS angkatan, 'TI' AS prodi
    UNION ALL SELECT '2501002', 'Siti Aminah', 'P', '2006-07-02', 2025, 'TI'
    UNION ALL SELECT '2502001', 'Andi Wijaya', 'L', '2005-11-21', 2025, 'SI'
) AS t
JOIN program_studi p ON p.kode_prodi = t.prodi;

-- ---------------------------------------------------------------------
-- 3. Nilai contoh. Hasil yang seharusnya muncul di view (hitung manual):
--
--   2501001 Budi : IF101 diulang (20251 = D, 20252 = B)
--     IPS 20251 = 25.5 / 9  = 2.83      IPS 20252 = 24.5 / 8 = 3.06
--     IPK (nilai terbaik) = 47.0 / 14 = 3.36   (bila semua dihitung: 2.94)
--   2501002 Siti : IPS 20251 = 3.00     IPK = 3.00
--   2502001 Andi : IPS 20251 = 2.00     IPK = 2.00 (IF101 = E, tidak lulus)
-- ---------------------------------------------------------------------
INSERT IGNORE INTO nilai (nim, mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas)
SELECT t.nim, k.mk_id, s.semester_id, t.tugas, t.uts, t.uas
FROM (
    SELECT '2501001' AS nim, 'IF101' AS kode_mk, '20251' AS kode_semester, 60 AS tugas, 50 AS uts, 45 AS uas
    UNION ALL SELECT '2501001', 'IF102', '20251', 90, 85, 88
    UNION ALL SELECT '2501001', 'IF103', '20251', 80, 78, 82
    UNION ALL SELECT '2501001', 'IF101', '20252', 80, 75, 78
    UNION ALL SELECT '2501001', 'IF104', '20252', 70, 72, 68
    UNION ALL SELECT '2501001', 'IF105', '20252', 85, 80, 90
    UNION ALL SELECT '2501002', 'IF101', '20251', 95, 90, 92
    UNION ALL SELECT '2501002', 'IF102', '20251', 75, 70, 72
    UNION ALL SELECT '2501002', 'IF103', '20251', 60, 62, 58
    UNION ALL SELECT '2502001', 'IF101', '20251', 40, 35, 30
    UNION ALL SELECT '2502001', 'IF102', '20251', 65, 60, 62
    UNION ALL SELECT '2502001', 'IF106', '20251', 88, 85, 90
) AS t
JOIN mata_kuliah k       ON k.kode_mk       = t.kode_mk
JOIN semester_akademik s ON s.kode_semester = t.kode_semester;
