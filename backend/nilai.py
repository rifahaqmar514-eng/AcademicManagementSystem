"""Nilai mahasiswa per mata kuliah dan semester.

Huruf mutu, IPS, dan IPK dihitung oleh VIEW di database (lihat backend/ipk.py);
modul ini hanya menyimpan nilai tugas, UTS, UAS, dan nilai akhirnya.
"""
from decimal import Decimal, InvalidOperation

from backend import log
from database import connection as db
from utils import session
from utils.permissions import ADMIN, efektif_mahasiswa_id, require_role
from utils.validators import ValidationError, cek_id

# Bobot nilai akhir 
BOBOT_TUGAS = Decimal("0.30")
BOBOT_UTS = Decimal("0.30")
BOBOT_UAS = Decimal("0.40")

_DUA_DESIMAL = Decimal("0.01")
_KOLOM_DATA = (
    "mk_id", "semester_id", "nilai_tugas", "nilai_uts", "nilai_uas", "nilai_akhir",
)


# ---------- Validasi & perhitungan ----------
def _pelaku():
    user = session.get_user()
    return None if user is None else user["user_id"]


def _id_diizinkan(mahasiswa_id):
    """Mahasiswa otomatis dibatasi ke data miliknya; admin wajib menyebut mahasiswa."""
    efektif = efektif_mahasiswa_id(mahasiswa_id)
    if efektif is None:
        raise ValidationError("Pilih mahasiswa terlebih dahulu.")
    return cek_id(efektif, "Mahasiswa")


def _skor(nilai, label):
    """Ubah input (angka/teks, koma boleh) menjadi Decimal 0-100 dengan 2 desimal."""
    try:
        angka = Decimal(str(nilai).strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValidationError(f"{label} harus berupa angka.")
    if not angka.is_finite():
        raise ValidationError(f"{label} harus berupa angka.")
    if not Decimal("0") <= angka <= Decimal("100"):
        raise ValidationError(f"{label} harus antara 0 dan 100.")
    return angka.quantize(_DUA_DESIMAL)


def hitung_nilai_akhir(nilai_tugas, nilai_uts, nilai_uas):
    """Nilai akhir = 30% tugas + 30% UTS + 40% UAS (2 desimal)."""
    akhir = (_skor(nilai_tugas, "Nilai tugas") * BOBOT_TUGAS
             + _skor(nilai_uts, "Nilai UTS") * BOBOT_UTS
             + _skor(nilai_uas, "Nilai UAS") * BOBOT_UAS)
    return akhir.quantize(_DUA_DESIMAL)


def _data_valid(mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas):
    """Validasi semua field; return dict siap simpan (termasuk nilai_akhir)."""
    mk_id = cek_id(mk_id, "Mata kuliah")
    semester_id = cek_id(semester_id, "Semester")
    if db.fetch_one("SELECT 1 AS ada FROM mata_kuliah WHERE mk_id = %s", (mk_id,)) is None:
        raise ValidationError("Mata kuliah tidak ditemukan.")
    if db.fetch_one(
        "SELECT 1 AS ada FROM semester_akademik WHERE semester_id = %s", (semester_id,)
    ) is None:
        raise ValidationError("Semester tidak ditemukan.")

    tugas = _skor(nilai_tugas, "Nilai tugas")
    uts = _skor(nilai_uts, "Nilai UTS")
    uas = _skor(nilai_uas, "Nilai UAS")
    return {
        "mk_id": mk_id,
        "semester_id": semester_id,
        "nilai_tugas": tugas,
        "nilai_uts": uts,
        "nilai_uas": uas,
        "nilai_akhir": hitung_nilai_akhir(tugas, uts, uas),
    }


def _pastikan_belum_ada(mahasiswa_id, mk_id, semester_id, kecuali_id=None):
    sql = (
        "SELECT 1 AS ada FROM nilai "
        "WHERE mahasiswa_id = %s AND mk_id = %s AND semester_id = %s"
    )
    params = [mahasiswa_id, mk_id, semester_id]
    if kecuali_id is not None:
        sql += " AND nilai_id <> %s"
        params.append(kecuali_id)
    if db.fetch_one(sql, params) is not None:
        raise ValidationError(
            "Nilai mata kuliah ini untuk mahasiswa dan semester tersebut sudah ada."
        )


def _sama(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except InvalidOperation:
        return str(a) == str(b)


# ---------- Baca ----------
def daftar_nilai(mahasiswa_id=None, semester_id=None):
    """Nilai satu mahasiswa (opsional per semester). Mahasiswa hanya melihat nilainya sendiri."""
    mahasiswa_id = _id_diizinkan(mahasiswa_id)
    sql = (
        "SELECT n.nilai_id, n.mahasiswa_id, n.mk_id, mk.kode_mk, mk.nama_mk, mk.sks, "
        "n.semester_id, s.kode_semester, n.nilai_tugas, n.nilai_uts, n.nilai_uas, "
        "n.nilai_akhir "
        "FROM nilai n "
        "JOIN mata_kuliah mk ON mk.mk_id = n.mk_id "
        "JOIN semester_akademik s ON s.semester_id = n.semester_id "
        "WHERE n.mahasiswa_id = %s"
    )
    params = [mahasiswa_id]
    if semester_id:
        sql += " AND n.semester_id = %s"
        params.append(cek_id(semester_id, "Semester"))
    return db.fetch_all(sql + " ORDER BY s.kode_semester, mk.kode_mk", params)


# ---------- Tulis (khusus admin) ----------
@require_role(ADMIN)
def tambah_nilai(mahasiswa_id, mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas):
    """Tambah nilai. Nilai akhir dihitung otomatis. Return nilai_id baru."""
    mahasiswa_id = cek_id(mahasiswa_id, "Mahasiswa")
    if db.fetch_one(
        "SELECT 1 AS ada FROM mahasiswa WHERE mahasiswa_id = %s", (mahasiswa_id,)
    ) is None:
        raise ValidationError("Mahasiswa tidak ditemukan.")

    data = _data_valid(mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas)
    _pastikan_belum_ada(mahasiswa_id, data["mk_id"], data["semester_id"])

    baru_id = db.execute(
        "INSERT INTO nilai (mahasiswa_id, mk_id, semester_id, nilai_tugas, nilai_uts, "
        "nilai_uas, nilai_akhir) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (mahasiswa_id,) + tuple(data[k] for k in _KOLOM_DATA),
    )
    log.catat(_pelaku(), "TAMBAH", "nilai", record_id=baru_id,
              detail={"mahasiswa_id": mahasiswa_id, **data})
    return baru_id


@require_role(ADMIN)
def ubah_nilai(nilai_id, mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas):
    """Ubah nilai. Nilai akhir dihitung ulang. Return True bila ada yang berubah."""
    nilai_id = cek_id(nilai_id, "Nilai")
    lama = db.fetch_one(
        "SELECT mahasiswa_id, " + ", ".join(_KOLOM_DATA) + " FROM nilai WHERE nilai_id = %s",
        (nilai_id,),
    )
    if lama is None:
        raise ValidationError("Data nilai tidak ditemukan.")

    baru = _data_valid(mk_id, semester_id, nilai_tugas, nilai_uts, nilai_uas)
    _pastikan_belum_ada(lama["mahasiswa_id"], baru["mk_id"], baru["semester_id"],
                        kecuali_id=nilai_id)

    perubahan = {
        k: {"dari": lama[k], "ke": baru[k]}
        for k in _KOLOM_DATA if not _sama(lama[k], baru[k])
    }
    if not perubahan:
        return False

    db.execute(
        "UPDATE nilai SET mk_id = %s, semester_id = %s, nilai_tugas = %s, nilai_uts = %s, "
        "nilai_uas = %s, nilai_akhir = %s WHERE nilai_id = %s",
        tuple(baru[k] for k in _KOLOM_DATA) + (nilai_id,),
    )
    log.catat(_pelaku(), "UBAH", "nilai", record_id=nilai_id,
              detail={"mahasiswa_id": lama["mahasiswa_id"], **perubahan})
    return True


@require_role(ADMIN)
def hapus_nilai(nilai_id):
    """Hapus satu data nilai."""
    nilai_id = cek_id(nilai_id, "Nilai")
    data = db.fetch_one(
        "SELECT mahasiswa_id, mk_id, semester_id, nilai_akhir FROM nilai WHERE nilai_id = %s",
        (nilai_id,),
    )
    if data is None:
        raise ValidationError("Data nilai tidak ditemukan.")

    db.execute("DELETE FROM nilai WHERE nilai_id = %s", (nilai_id,))
    log.catat(_pelaku(), "HAPUS", "nilai", record_id=nilai_id, detail=data)
