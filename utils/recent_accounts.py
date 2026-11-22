"""Simpan akun mahasiswa terakhir secara lokal dan terenkripsi di Windows."""
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


_MAX_AKUN = 5
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _lokasi_file():
    local_app_data = os.getenv("LOCALAPPDATA")
    if os.name != "nt" or not local_app_data:
        return None
    return Path(local_app_data) / "AcademicManagementSystem" / "recent_students.dat"


def _dpapi(data, lindungi):
    """Enkripsi/dekripsi dengan Windows DPAPI untuk akun Windows saat ini."""
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    input_buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(
        len(data), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_byte))
    )
    output_blob = _DataBlob()
    flags = _CRYPTPROTECT_UI_FORBIDDEN

    if lindungi:
        fungsi = crypt32.CryptProtectData
        fungsi.argtypes = [
            ctypes.POINTER(_DataBlob), wintypes.LPCWSTR,
            ctypes.POINTER(_DataBlob), wintypes.LPVOID, wintypes.LPVOID,
            wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        fungsi.restype = wintypes.BOOL
        berhasil = fungsi(
            ctypes.byref(input_blob), "SIAKAD akun mahasiswa", None,
            None, None, flags, ctypes.byref(output_blob),
        )
    else:
        fungsi = crypt32.CryptUnprotectData
        fungsi.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.POINTER(wintypes.LPWSTR),
            ctypes.POINTER(_DataBlob), wintypes.LPVOID, wintypes.LPVOID,
            wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        fungsi.restype = wintypes.BOOL
        fungsi(
            ctypes.byref(input_blob), None, None, None, None,
            flags, ctypes.byref(output_blob),
        )
        berhasil = bool(output_blob.pbData)

    if not berhasil:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p
        kernel32.LocalFree(output_blob.pbData)


def muat_akun():
    """Kembalikan daftar akun tersimpan; file tidak tersedia berarti daftar kosong."""
    lokasi = _lokasi_file()
    if lokasi is None or not lokasi.exists():
        return []
    try:
        isi = json.loads(_dpapi(lokasi.read_bytes(), lindungi=False).decode("utf-8"))
        return [
            akun for akun in isi
            if isinstance(akun, dict)
            and akun.get("nama")
            and str(akun.get("nim", "")).isdigit()
            and len(str(akun["nim"])) == 9
        ][:_MAX_AKUN]
    except (OSError, ValueError, TypeError, ctypes.ArgumentError):
        return []


def simpan_akun(nama, nim):
    """Simpan akun terbaru terenkripsi; hanya dapat dibuka oleh akun Windows ini."""
    lokasi = _lokasi_file()
    nama = " ".join((nama or "").split())
    nim = str(nim or "").strip()
    if lokasi is None or not nama or not nim.isdigit() or len(nim) != 9:
        return False

    akun = [item for item in muat_akun() if item["nim"] != nim]
    akun.insert(0, {"nama": nama, "nim": nim})
    try:
        lokasi.parent.mkdir(parents=True, exist_ok=True)
        terenkripsi = _dpapi(
            json.dumps(akun[:_MAX_AKUN], ensure_ascii=False).encode("utf-8"),
            lindungi=True,
        )
        lokasi.write_bytes(terenkripsi)
        return True
    except (OSError, ValueError, ctypes.ArgumentError):
        return False
