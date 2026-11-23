"""Program studi: daftar, tambah, ubah, dan hapus."""
from backend import log
from database import connection as db
from utils import session
from utils.permissions import ADMIN, require_role
from utils.validators import ValidationError, cek_id, pola_cari

# Sesuaikan dengan definisi kolom/enum di database
KODE_MAKS = 10
NAMA_MAKS = 100
JENJANG_VALID = ("D3", "D4", "S1", "S2", "S3")

_KOLOM_DATA = ("kode_prodi", "nama_prodi", "jenjang")


# ---------- Validasi ----------
def _pelaku():
    user = session.get_user()
    return None if user is None else user["user_id"]


def _teks(nilai, label, maks):
    nilai = (nilai or "").strip()
    if not nilai:
        raise ValidationError(f"{label} wajib diisi.")
    if len(nilai) > maks:
        raise ValidationError(f"{label} maksimal {maks} karakter.")
    return nilai


def _data_valid(kode_prodi, nama_prodi, jenjang):
    if jenjang not in JENJANG_VALID:
        raise ValidationError(f"Jenjang harus salah satu dari: {', '.join(JENJANG_VALID)}.")
    return {
        "kode_prodi": _teks(kode_prodi, "Kode prodi", KODE_MAKS),
        "nama_prodi": _teks(nama_prodi, "Nama prodi", NAMA_MAKS),
        "jenjang": jenjang,
    }


def _pastikan_kode_unik(kode_prodi, kecuali_id=None):
    sql = "SELECT 1 AS ada FROM program_studi WHERE kode_prodi = %s"
    params = [kode_prodi]
    if kecuali_id is not None:
        sql += " AND prodi_id <> %s"
        params.append(kecuali_id)
    if db.fetch_one(sql, params) is not None:
        raise ValidationError("Kode prodi sudah terdaftar.")


# ---------- Baca ----------
def daftar_prodi(keyword=None, jenjang=None):
    """Daftar program studi (data referensi, boleh dibaca semua pengguna)."""
    sql = "SELECT prodi_id, kode_prodi, nama_prodi, jenjang FROM program_studi WHERE 1 = 1"
    params = []
    pola = pola_cari(keyword)
    if pola:
        sql += " AND (kode_prodi LIKE %s OR nama_prodi LIKE %s)"
        params += [pola, pola]
    if jenjang:
        if jenjang not in JENJANG_VALID:
            raise ValidationError("Jenjang tidak valid.")
        sql += " AND jenjang = %s"
        params.append(jenjang)
    return db.fetch_all(sql + " ORDER BY kode_prodi", params)


def detail_prodi(prodi_id):
    prodi_id = cek_id(prodi_id, "Program studi")
    data = db.fetch_one(
        "SELECT prodi_id, kode_prodi, nama_prodi, jenjang FROM program_studi "
        "WHERE prodi_id = %s",
        (prodi_id,),
    )
    if data is None:
        raise ValidationError("Program studi tidak ditemukan.")
    return data


# ---------- Tulis (khusus admin) ----------
@require_role(ADMIN)
def tambah_prodi(kode_prodi, nama_prodi, jenjang):
    """Tambah program studi. Return prodi_id baru."""
    data = _data_valid(kode_prodi, nama_prodi, jenjang)
    _pastikan_kode_unik(data["kode_prodi"])

    baru_id = db.execute(
        "INSERT INTO program_studi (kode_prodi, nama_prodi, jenjang) VALUES (%s, %s, %s)",
        tuple(data[k] for k in _KOLOM_DATA),
    )
    log.catat(_pelaku(), "TAMBAH", "prodi", record_id=baru_id, detail=data)
    return baru_id


@require_role(ADMIN)
def ubah_prodi(prodi_id, kode_prodi, nama_prodi, jenjang):
    """Ubah program studi. Return True bila ada yang berubah."""
    prodi_id = cek_id(prodi_id, "Program studi")
    lama = db.fetch_one(
        "SELECT kode_prodi, nama_prodi, jenjang FROM program_studi WHERE prodi_id = %s",
        (prodi_id,),
    )
    if lama is None:
        raise ValidationError("Program studi tidak ditemukan.")

    baru = _data_valid(kode_prodi, nama_prodi, jenjang)
    _pastikan_kode_unik(baru["kode_prodi"], kecuali_id=prodi_id)

    perubahan = {
        k: {"dari": lama[k], "ke": baru[k]}
        for k in _KOLOM_DATA if str(lama[k]) != str(baru[k])
    }
    if not perubahan:
        return False

    db.execute(
        "UPDATE program_studi SET kode_prodi = %s, nama_prodi = %s, jenjang = %s "
        "WHERE prodi_id = %s",
        tuple(baru[k] for k in _KOLOM_DATA) + (prodi_id,),
    )
    log.catat(_pelaku(), "UBAH", "prodi", record_id=prodi_id, detail=perubahan)
    return True


@require_role(ADMIN)
def hapus_prodi(prodi_id):
    """Hapus program studi. Ditolak bila masih dipakai mahasiswa."""
    prodi_id = cek_id(prodi_id, "Program studi")
    data = db.fetch_one(
        "SELECT kode_prodi, nama_prodi FROM program_studi WHERE prodi_id = %s", (prodi_id,)
    )
    if data is None:
        raise ValidationError("Program studi tidak ditemukan.")

    pakai = db.fetch_one(
        "SELECT COUNT(*) AS n FROM mahasiswa WHERE prodi_id = %s", (prodi_id,)
    )
    if pakai and pakai["n"] > 0:
        raise ValidationError(
            f"Program studi masih dipakai oleh {pakai['n']} mahasiswa dan tidak bisa dihapus."
        )

    db.execute("DELETE FROM program_studi WHERE prodi_id = %s", (prodi_id,))
    log.catat(_pelaku(), "HAPUS", "prodi", record_id=prodi_id, detail=data)
