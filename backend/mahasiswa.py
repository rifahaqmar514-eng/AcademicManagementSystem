"""Data mahasiswa: daftar, detail, tambah, ubah, dan hapus."""
import re
from datetime import date, datetime

from backend import log
from database import connection as db
from utils import session
from utils.permissions import ADMIN, efektif_mahasiswa_id, require_role
from utils.validators import ValidationError, cek_id, pola_cari

# Sesuaikan dengan definisi kolom/enum di database
NIM_MAKS = 20
NAMA_MAKS = 100
JENIS_KELAMIN_VALID = ("L", "P")
STATUS_VALID = ("Aktif", "Cuti", "Lulus", "Non-Aktif")
STATUS_DEFAULT = "Aktif"
ANGKATAN_MIN, ANGKATAN_MAKS = 1990, 2100  # sama dengan CHECK di tabel

_KOLOM_DATA = (
    "prodi_id", "nim", "nama_lengkap", "jenis_kelamin",
    "tanggal_lahir", "angkatan", "status_mahasiswa",
)


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


def _nim(nim):
    nim = _teks(nim, "NIM", NIM_MAKS)
    if not re.fullmatch(r"[0-9A-Za-z]+", nim):
        raise ValidationError("NIM hanya boleh berisi huruf dan angka.")
    return nim


def _pilihan(nilai, label, daftar):
    if nilai not in daftar:
        raise ValidationError(f"{label} harus salah satu dari: {', '.join(daftar)}.")
    return nilai


def _tanggal_lahir(nilai):
    if isinstance(nilai, datetime):
        nilai = nilai.date()
    if isinstance(nilai, str):
        try:
            nilai = datetime.strptime(nilai.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Tanggal lahir harus berformat YYYY-MM-DD.")
    if not isinstance(nilai, date):
        raise ValidationError("Tanggal lahir wajib diisi.")
    if nilai > date.today() or nilai.year < 1900:
        raise ValidationError("Tanggal lahir tidak valid.")
    return nilai


def _angkatan(nilai):
    try:
        angkatan = int(nilai)
    except (TypeError, ValueError):
        raise ValidationError("Angkatan harus berupa tahun 4 digit.")
    if not ANGKATAN_MIN <= angkatan <= ANGKATAN_MAKS:
        raise ValidationError(f"Angkatan harus antara {ANGKATAN_MIN} dan {ANGKATAN_MAKS}.")
    return angkatan


def _data_valid(prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir, angkatan,
                status_mahasiswa):
    """Validasi semua field; return dict siap simpan."""
    prodi_id = cek_id(prodi_id, "Program studi")
    if db.fetch_one("SELECT 1 AS ada FROM program_studi WHERE prodi_id = %s", (prodi_id,)) is None:
        raise ValidationError("Program studi tidak ditemukan.")
    return {
        "prodi_id": prodi_id,
        "nim": _nim(nim),
        "nama_lengkap": _teks(nama_lengkap, "Nama lengkap", NAMA_MAKS),
        "jenis_kelamin": _pilihan(jenis_kelamin, "Jenis kelamin", JENIS_KELAMIN_VALID),
        "tanggal_lahir": _tanggal_lahir(tanggal_lahir),
        "angkatan": _angkatan(angkatan),
        "status_mahasiswa": _pilihan(status_mahasiswa, "Status", STATUS_VALID),
    }


def _pastikan_nim_unik(nim, kecuali_id=None):
    sql = "SELECT 1 AS ada FROM mahasiswa WHERE nim = %s"
    params = [nim]
    if kecuali_id is not None:
        sql += " AND mahasiswa_id <> %s"
        params.append(kecuali_id)
    if db.fetch_one(sql, params) is not None:
        raise ValidationError("NIM sudah terdaftar.")


def _id_diizinkan(mahasiswa_id):
    """Mahasiswa otomatis dibatasi ke data miliknya; admin wajib menyebut mahasiswa."""
    efektif = efektif_mahasiswa_id(mahasiswa_id)
    if efektif is None:
        raise ValidationError("Pilih mahasiswa terlebih dahulu.")
    return cek_id(efektif, "Mahasiswa")


# ---------- Baca ----------
_SQL_DETAIL = (
    "SELECT m.mahasiswa_id, m.nim, m.nama_lengkap, m.prodi_id, p.kode_prodi, p.nama_prodi, "
    "m.jenis_kelamin, m.tanggal_lahir, m.angkatan, m.status_mahasiswa "
    "FROM mahasiswa m JOIN program_studi p ON p.prodi_id = m.prodi_id"
)


@require_role(ADMIN)
def daftar_mahasiswa(keyword=None, prodi_id=None, status=None):
    """Daftar mahasiswa; bisa dicari dengan NIM/nama dan difilter prodi atau status."""
    sql = _SQL_DETAIL + " WHERE 1 = 1"
    params = []
    pola = pola_cari(keyword)
    if pola:
        sql += " AND (m.nim LIKE %s OR m.nama_lengkap LIKE %s)"
        params += [pola, pola]
    if prodi_id:
        sql += " AND m.prodi_id = %s"
        params.append(cek_id(prodi_id, "Program studi"))
    if status:
        sql += " AND m.status_mahasiswa = %s"
        params.append(_pilihan(status, "Status", STATUS_VALID))
    return db.fetch_all(sql + " ORDER BY m.nim", params)


def detail_mahasiswa(mahasiswa_id=None):
    """Profil satu mahasiswa. Mahasiswa hanya bisa melihat datanya sendiri."""
    mahasiswa_id = _id_diizinkan(mahasiswa_id)
    data = db.fetch_one(_SQL_DETAIL + " WHERE m.mahasiswa_id = %s", (mahasiswa_id,))
    if data is None:
        raise ValidationError("Mahasiswa tidak ditemukan.")
    return data


# ---------- Tulis (khusus admin) ----------
@require_role(ADMIN)
def tambah_mahasiswa(prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir, angkatan,
                     status_mahasiswa=STATUS_DEFAULT):
    """Tambah mahasiswa baru. Return mahasiswa_id."""
    data = _data_valid(prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir,
                       angkatan, status_mahasiswa)
    _pastikan_nim_unik(data["nim"])

    baru_id = db.execute(
        "INSERT INTO mahasiswa (prodi_id, nim, nama_lengkap, jenis_kelamin, "
        "tanggal_lahir, angkatan, status_mahasiswa) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        tuple(data[k] for k in _KOLOM_DATA),
    )
    log.catat(_pelaku(), "TAMBAH", "mahasiswa", record_id=baru_id,
              detail={"nim": data["nim"], "nama_lengkap": data["nama_lengkap"]})
    return baru_id


@require_role(ADMIN)
def ubah_mahasiswa(mahasiswa_id, prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir,
                   angkatan, status_mahasiswa):
    """Ubah data mahasiswa. Return True bila ada yang berubah, False bila tidak ada."""
    mahasiswa_id = cek_id(mahasiswa_id, "Mahasiswa")
    lama = db.fetch_one(
        "SELECT " + ", ".join(_KOLOM_DATA) + " FROM mahasiswa WHERE mahasiswa_id = %s",
        (mahasiswa_id,),
    )
    if lama is None:
        raise ValidationError("Mahasiswa tidak ditemukan.")

    baru = _data_valid(prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir,
                       angkatan, status_mahasiswa)
    _pastikan_nim_unik(baru["nim"], kecuali_id=mahasiswa_id)

    perubahan = {
        k: {"dari": lama[k], "ke": baru[k]}
        for k in _KOLOM_DATA if str(lama[k]) != str(baru[k])
    }
    if not perubahan:
        return False

    db.execute(
        "UPDATE mahasiswa SET prodi_id = %s, nim = %s, nama_lengkap = %s, "
        "jenis_kelamin = %s, tanggal_lahir = %s, angkatan = %s, status_mahasiswa = %s "
        "WHERE mahasiswa_id = %s",
        tuple(baru[k] for k in _KOLOM_DATA) + (mahasiswa_id,),
    )
    log.catat(_pelaku(), "UBAH", "mahasiswa", record_id=mahasiswa_id, detail=perubahan)
    return True


@require_role(ADMIN)
def hapus_mahasiswa(mahasiswa_id):
    """Hapus mahasiswa. Ditolak bila sudah punya nilai (ubah statusnya saja)."""
    mahasiswa_id = cek_id(mahasiswa_id, "Mahasiswa")
    data = db.fetch_one(
        "SELECT nim, nama_lengkap FROM mahasiswa WHERE mahasiswa_id = %s", (mahasiswa_id,)
    )
    if data is None:
        raise ValidationError("Mahasiswa tidak ditemukan.")

    jumlah = db.fetch_one(
        "SELECT COUNT(*) AS n FROM nilai WHERE mahasiswa_id = %s", (mahasiswa_id,)
    )
    if jumlah and jumlah["n"] > 0:
        raise ValidationError(
            "Mahasiswa sudah memiliki data nilai dan tidak bisa dihapus. "
            "Ubah statusnya menjadi Non-Aktif."
        )

    db.execute("DELETE FROM mahasiswa WHERE mahasiswa_id = %s", (mahasiswa_id,))
    log.catat(_pelaku(), "HAPUS", "mahasiswa", record_id=mahasiswa_id,
              detail={"nim": data["nim"], "nama_lengkap": data["nama_lengkap"]})
