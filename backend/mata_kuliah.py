"""Mata kuliah: daftar, tambah, ubah, dan hapus."""
from backend import log
from database import connection as db
from utils import session
from utils.permissions import ADMIN, require_role
from utils.validators import ValidationError, cek_id, pola_cari

# Sesuaikan dengan definisi kolom di database
KODE_MAKS = 15
NAMA_MAKS = 150
SKS_MIN, SKS_MAKS = 1, 6  # sama dengan CHECK di tabel

_KOLOM_DATA = ("kode_mk", "nama_mk", "sks")


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


def _sks(nilai):
    try:
        sks = int(nilai)
    except (TypeError, ValueError):
        raise ValidationError("SKS harus berupa bilangan bulat.")
    if not SKS_MIN <= sks <= SKS_MAKS:
        raise ValidationError(f"SKS harus antara {SKS_MIN} dan {SKS_MAKS}.")
    return sks


def _data_valid(kode_mk, nama_mk, sks):
    return {
        "kode_mk": _teks(kode_mk, "Kode mata kuliah", KODE_MAKS),
        "nama_mk": _teks(nama_mk, "Nama mata kuliah", NAMA_MAKS),
        "sks": _sks(sks),
    }


def _pastikan_kode_unik(kode_mk, kecuali_id=None):
    sql = "SELECT 1 AS ada FROM mata_kuliah WHERE kode_mk = %s"
    params = [kode_mk]
    if kecuali_id is not None:
        sql += " AND mk_id <> %s"
        params.append(kecuali_id)
    if db.fetch_one(sql, params) is not None:
        raise ValidationError("Kode mata kuliah sudah terdaftar.")


# ---------- Baca ----------
def daftar_mata_kuliah(keyword=None, sks=None):
    """Daftar mata kuliah (data referensi, boleh dibaca semua pengguna)."""
    sql = "SELECT mk_id, kode_mk, nama_mk, sks FROM mata_kuliah WHERE 1 = 1"
    params = []
    pola = pola_cari(keyword)
    if pola:
        sql += " AND (kode_mk LIKE %s OR nama_mk LIKE %s)"
        params += [pola, pola]
    if sks:
        sql += " AND sks = %s"
        params.append(_sks(sks))
    return db.fetch_all(sql + " ORDER BY kode_mk", params)


def detail_mata_kuliah(mk_id):
    mk_id = cek_id(mk_id, "Mata kuliah")
    data = db.fetch_one(
        "SELECT mk_id, kode_mk, nama_mk, sks FROM mata_kuliah WHERE mk_id = %s", (mk_id,)
    )
    if data is None:
        raise ValidationError("Mata kuliah tidak ditemukan.")
    return data


# ---------- Tulis (khusus admin) ----------
@require_role(ADMIN)
def tambah_mata_kuliah(kode_mk, nama_mk, sks):
    """Tambah mata kuliah. Return mk_id baru."""
    data = _data_valid(kode_mk, nama_mk, sks)
    _pastikan_kode_unik(data["kode_mk"])

    baru_id = db.execute(
        "INSERT INTO mata_kuliah (kode_mk, nama_mk, sks) VALUES (%s, %s, %s)",
        tuple(data[k] for k in _KOLOM_DATA),
    )
    log.catat(_pelaku(), "TAMBAH", "mata_kuliah", record_id=baru_id, detail=data)
    return baru_id


@require_role(ADMIN)
def ubah_mata_kuliah(mk_id, kode_mk, nama_mk, sks):
    """Ubah mata kuliah. Return True bila ada yang berubah.

    Mengubah SKS memengaruhi IPS/IPK semua mahasiswa yang sudah punya nilai
    di mata kuliah ini, karena perhitungan dilakukan oleh VIEW.
    """
    mk_id = cek_id(mk_id, "Mata kuliah")
    lama = db.fetch_one(
        "SELECT kode_mk, nama_mk, sks FROM mata_kuliah WHERE mk_id = %s", (mk_id,)
    )
    if lama is None:
        raise ValidationError("Mata kuliah tidak ditemukan.")

    baru = _data_valid(kode_mk, nama_mk, sks)
    _pastikan_kode_unik(baru["kode_mk"], kecuali_id=mk_id)

    perubahan = {
        k: {"dari": lama[k], "ke": baru[k]}
        for k in _KOLOM_DATA if str(lama[k]) != str(baru[k])
    }
    if not perubahan:
        return False

    db.execute(
        "UPDATE mata_kuliah SET kode_mk = %s, nama_mk = %s, sks = %s WHERE mk_id = %s",
        tuple(baru[k] for k in _KOLOM_DATA) + (mk_id,),
    )
    log.catat(_pelaku(), "UBAH", "mata_kuliah", record_id=mk_id, detail=perubahan)
    return True


@require_role(ADMIN)
def hapus_mata_kuliah(mk_id):
    """Hapus mata kuliah. Ditolak bila sudah dipakai di data nilai."""
    mk_id = cek_id(mk_id, "Mata kuliah")
    data = db.fetch_one(
        "SELECT kode_mk, nama_mk FROM mata_kuliah WHERE mk_id = %s", (mk_id,)
    )
    if data is None:
        raise ValidationError("Mata kuliah tidak ditemukan.")

    pakai = db.fetch_one("SELECT COUNT(*) AS n FROM nilai WHERE mk_id = %s", (mk_id,))
    if pakai and pakai["n"] > 0:
        raise ValidationError(
            f"Mata kuliah sudah dipakai di {pakai['n']} data nilai dan tidak bisa dihapus."
        )

    db.execute("DELETE FROM mata_kuliah WHERE mk_id = %s", (mk_id,))
    log.catat(_pelaku(), "HAPUS", "mata_kuliah", record_id=mk_id, detail=data)
