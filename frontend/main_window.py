"""Kerangka aplikasi: tema, navigasi antar layar, dan menu sesuai role.

Alur layar:
    mulai(root) -> login -> aplikasi (header + menu samping + isi halaman) -> keluar -> login

Setiap halaman isi dipanggil melalui peta HALAMAN agar navigasi mengikuti
fungsi yang benar-benar disediakan oleh tiap modul.
"""
import importlib
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from assets import colors as c
from backend import auth, dashboard
from frontend import login_page
from utils import permissions, session

JUDUL = "SIAKAD - Nilai & IPK"
CEK_SESI_MS = 30_000

# kunci menu (sama dengan utils/permissions.MENU_ACCESS) -> label tampilan
MENU = {
    "dashboard":       "Beranda",
    "mahasiswa":       "Data Mahasiswa",
    "akademik_master": "Master Akademik",
    "dosen":           "Data Dosen",
    "kelas":           "Kelas Kuliah",
    "krs":             "Kartu Rencana Studi",
    "nilai":           "Input Nilai",
    "transkrip":       "Transkrip & IPK",
}
HALAMAN = {
    "mahasiswa": ("frontend.mahasiswa_page", "tampilkan_mahasiswa", False),
    "akademik_master": ("frontend.akademik_master_page", "tampilkan_master", False),
    "dosen": ("frontend.dosen_page", "tampilkan_dosen", False),
    "kelas": ("frontend.kelas_page", "tampilkan_kelas", False),
    "krs": ("frontend.krs_page", "tampilkan_krs", True),
    "nilai": ("frontend.nilai_page", "tampilkan_nilai", True),
    "transkrip": ("frontend.transkrip_page", "tampilkan_transkrip", True),
}
NAMA_ROLE = {"admin": "Administrator", "dosen": "Dosen", "mahasiswa": "Mahasiswa"}

_state = {"after_id": None}


# --------------------------------------------------------------- jendela & tema
def _tengahkan(root, lebar, tinggi):
    x = max((root.winfo_screenwidth() - lebar) // 2, 0)
    y = max((root.winfo_screenheight() - tinggi) // 2 - 20, 0)
    root.geometry(f"{lebar}x{tinggi}+{x}+{y}")


def terapkan_tema(root):
    """Menyeragamkan tampilan widget ttk (kolom isian, tombol, tabel)."""
    gaya = ttk.Style(root)
    gaya.theme_use("clam")
    root.option_add("*TCombobox*Listbox.font", c.FONT_BODY)

    gaya.configure(".", font=c.FONT_BODY, background=c.CARD_BG, foreground=c.TEXT_DARK)

    kolom = dict(
        padding=(10, 8), fieldbackground=c.CARD_BG, foreground=c.TEXT_DARK,
        bordercolor=c.BORDER_COLOR, lightcolor=c.BORDER_COLOR, darkcolor=c.BORDER_COLOR,
    )
    fokus = dict(
        bordercolor=[("focus", c.PRIMARY_COLOR)],
        lightcolor=[("focus", c.PRIMARY_COLOR)],
        darkcolor=[("focus", c.PRIMARY_COLOR)],
    )
    gaya.configure("Form.TEntry", **kolom)
    gaya.map("Form.TEntry", **fokus)
    gaya.configure("Form.TCombobox", arrowcolor=c.TEXT_MUTED, background=c.CARD_BG, **kolom)
    gaya.map(
        "Form.TCombobox",
        fieldbackground=[("readonly", c.CARD_BG), ("disabled", c.BG_COLOR)],
        selectbackground=[("readonly", c.CARD_BG)],
        selectforeground=[("readonly", c.TEXT_DARK)],
        foreground=[("disabled", c.TEXT_MUTED)],
        **fokus,
    )
    gaya.configure("Form.TCheckbutton", background=c.CARD_BG, foreground=c.TEXT_MUTED)

    gaya.configure(
        "Primary.TButton", background=c.PRIMARY_COLOR, foreground="#FFFFFF", font=c.FONT_BUTTON,
        padding=(16, 11), borderwidth=0, focusthickness=0, relief="flat",
    )
    gaya.map(
        "Primary.TButton",
        background=[("disabled", "#93C5FD"), ("pressed", c.PRIMARY_DARK), ("active", c.PRIMARY_HOVER)],
        foreground=[("disabled", "#FFFFFF")],
    )
    gaya.configure(
        "Secondary.TButton", background=c.CARD_BG, foreground=c.TEXT_DARK, font=c.FONT_BUTTON,
        padding=(16, 11), bordercolor=c.BORDER_COLOR, focusthickness=0, relief="flat",
    )
    gaya.map("Secondary.TButton", background=[("active", c.BG_COLOR)])
    gaya.configure(
        "Link.TButton", background=c.CARD_BG, foreground=c.PRIMARY_COLOR, font=c.FONT_LINK,
        borderwidth=0, padding=(0, 2), focusthickness=0, relief="flat",
    )
    gaya.map(
        "Link.TButton",
        foreground=[("disabled", c.TEXT_MUTED), ("active", c.PRIMARY_HOVER)],
        background=[("active", c.CARD_BG)],
    )

    # dipakai halaman data (tabel) yang dibuat nanti
    gaya.configure(
        "Treeview", background=c.CARD_BG, fieldbackground=c.CARD_BG, foreground=c.TEXT_DARK,
        rowheight=30, bordercolor=c.BORDER_COLOR, borderwidth=0,
    )
    gaya.map("Treeview", background=[("selected", c.PRIMARY_LIGHT)], foreground=[("selected", c.TEXT_DARK)])
    gaya.configure(
        "Treeview.Heading", background=c.PRIMARY_DARK, foreground="#FFFFFF",
        font=c.FONT_BOLD, padding=(8, 8), relief="flat",
    )
    gaya.map("Treeview.Heading", background=[("active", c.PRIMARY_HOVER)])
    gaya.configure("TNotebook", background=c.BG_COLOR, borderwidth=0, tabmargins=(0, 8, 0, 0))
    gaya.configure(
        "TNotebook.Tab", background=c.TAB_IDLE_BG, foreground=c.TEXT_MUTED,
        padding=(14, 9), font=c.FONT_BOLD,
    )
    gaya.map(
        "TNotebook.Tab",
        background=[("selected", c.CARD_BG), ("active", c.PRIMARY_LIGHT)],
        foreground=[("selected", c.PRIMARY_DARK), ("active", c.TEXT_DARK)],
    )


def mulai(root):
    """Menyiapkan jendela, tema, lalu menampilkan layar login."""
    root.title(JUDUL)
    root.configure(bg=c.BG_COLOR)
    root.minsize(980, 620)
    _tengahkan(root, 1100, 700)
    terapkan_tema(root)
    root.protocol("WM_DELETE_WINDOW", lambda: _tutup(root))
    tampilkan_login(root)


def _tutup(root):
    auth.logout()
    root.destroy()


def _bersihkan(root):
    """Membuang layar yang sedang tampil dan semua pewaktu/pintasan miliknya."""
    if _state["after_id"] is not None:
        try:
            root.after_cancel(_state["after_id"])
        except tk.TclError:
            pass
        _state["after_id"] = None
    root.unbind("<Return>")
    for anak in root.winfo_children():
        anak.destroy()


# ------------------------------------------------------------------- navigasi
def tampilkan_login(root, pesan=None, jenis="info"):
    _bersihkan(root)
    return login_page.tampilkan_login(
        root,
        setelah_login=lambda pengguna: tampilkan_aplikasi(root, pengguna),
        pesan_awal=(pesan, jenis) if pesan else None,
    )


def keluar(root):
    if not messagebox.askyesno("Keluar", "Yakin ingin keluar dari aplikasi?", parent=root):
        return
    auth.logout()
    tampilkan_login(root, "Anda telah keluar.", "info")


def _cek_sesi(root):
    """Dipanggil berkala: bila sesi habis, kembali ke login dengan pesan."""
    _state["after_id"] = None
    if not session.is_logged_in():
        auth.logout()
        tampilkan_login(root, "Sesi Anda telah berakhir. Silakan masuk kembali.", "info")
        return
    _state["after_id"] = root.after(CEK_SESI_MS, lambda: _cek_sesi(root))


def _halaman_pengganti(parent, judul, pesan, warna=c.TEXT_MUTED):
    kartu = tk.Frame(parent, bg=c.CARD_BG, padx=28, pady=24, highlightthickness=1, highlightbackground=c.BORDER_COLOR)
    tk.Label(kartu, text=judul, font=c.FONT_HEADING, bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="w")
    tk.Label(
        kartu, text=pesan, font=c.FONT_BODY, bg=c.CARD_BG, fg=warna,
        wraplength=620, justify="left", anchor="w",
    ).pack(anchor="w", pady=(8, 0))
    return kartu


def _buat_beranda(parent, pengguna):
    """Beranda ringkas dengan statistik database dan petunjuk sesuai role."""
    halaman = tk.Frame(parent, bg=c.BG_COLOR)
    hero = tk.Frame(halaman, bg=c.PRIMARY_DARK, padx=28, pady=24)
    hero.pack(fill="x", pady=(0, 20))
    tk.Label(
        hero, text=f"Selamat datang, {pengguna.get('nama', 'Pengguna')}!",
        font=(c.FONT_FAMILY, 23, "bold"), bg=c.PRIMARY_DARK, fg="#FFFFFF",
    ).pack(anchor="w")
    role = NAMA_ROLE.get(pengguna.get("role"), "Pengguna")
    tk.Label(
        hero, text=f"{role}  •  Ringkasan aktivitas akademik",
        font=c.FONT_BODY, bg=c.PRIMARY_DARK, fg=c.PRIMARY_LIGHT,
    ).pack(anchor="w", pady=(5, 0))

    try:
        data = dashboard.ringkasan()
    except Exception as err:
        traceback.print_exc()
        _halaman_pengganti(
            halaman, "Ringkasan belum tersedia", f"Data dashboard tidak dapat dimuat:\n{err}", c.DANGER_COLOR,
        ).pack(fill="x")
        return halaman

    ringkasan = tk.Frame(halaman, bg=c.BG_COLOR)
    ringkasan.pack(fill="x")
    statistik = (
        ("Mahasiswa", data.get("jumlah_mahasiswa", 0)),
        ("Dosen aktif", data.get("jumlah_dosen_aktif", 0)),
        ("Program studi", data.get("jumlah_prodi", 0)),
        ("Semester aktif", data.get("semester_aktif") or "Belum diatur"),
    )
    for kolom, (label, nilai) in enumerate(statistik):
        ringkasan.columnconfigure(kolom, weight=1, uniform="statistik")
        kartu = tk.Frame(
            ringkasan, bg=c.CARD_BG, padx=18, pady=16,
            highlightthickness=1, highlightbackground=c.BORDER_COLOR,
        )
        kartu.grid(row=0, column=kolom, sticky="nsew", padx=(0 if kolom == 0 else 8, 0 if kolom == 3 else 8))
        tk.Label(kartu, text=label, bg=c.CARD_BG, fg=c.TEXT_MUTED, font=c.FONT_BODY).pack(anchor="w")
        tk.Label(
            kartu, text=str(nilai), bg=c.CARD_BG, fg=c.PRIMARY_DARK,
            font=(c.FONT_FAMILY, 18, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    petunjuk = tk.Frame(
        halaman, bg=c.CARD_BG, padx=22, pady=20,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    petunjuk.pack(fill="x", pady=(18, 0))
    tk.Label(
        petunjuk, text="Mulai dari menu", bg=c.CARD_BG, fg=c.TEXT_DARK,
        font=c.FONT_HEADING,
    ).pack(anchor="w")
    pesan = {
        "admin": "Kelola data mahasiswa, dosen, kelas, nilai, dan master akademik.",
        "dosen": "Lihat mahasiswa bimbingan, kelola nilai, dan tinjau rencana studi.",
        "mahasiswa": "Periksa KRS, nilai, serta transkrip dan IPK melalui menu di samping.",
    }.get(pengguna.get("role"), "Pilih menu di samping untuk melanjutkan.")
    tk.Label(
        petunjuk, text=pesan, bg=c.CARD_BG, fg=c.TEXT_MUTED,
        font=c.FONT_BODY, wraplength=760, justify="left",
    ).pack(anchor="w", pady=(7, 0))
    return halaman


def _buat_halaman(kunci, parent, pengguna):
    """Muat halaman yang sesuai menu dan role tanpa menjatuhkan aplikasi."""
    label = MENU[kunci]
    if kunci == "dashboard":
        return _buat_beranda(parent, pengguna)

    nama_modul, nama_fungsi, pakai_user = HALAMAN[kunci]
    try:
        modul = importlib.import_module(nama_modul)
        fungsi = getattr(modul, nama_fungsi)
        return fungsi(parent, pengguna) if pakai_user else fungsi(parent)
    except ModuleNotFoundError as err:
        if err.name == nama_modul:
            return _halaman_pengganti(parent, label, "Halaman ini belum tersedia.")
        traceback.print_exc()
        return _halaman_pengganti(parent, label, f"Gagal memuat halaman: {err}", c.DANGER_COLOR)
    except Exception as err:
        traceback.print_exc()
        return _halaman_pengganti(parent, label, f"Halaman tidak dapat dibuka:\n{err}", c.DANGER_COLOR)


def tampilkan_aplikasi(root, pengguna):
    """Layar utama setelah login: header, menu samping sesuai role, dan area isi."""
    _bersihkan(root)
    kerangka = tk.Frame(root, bg=c.BG_COLOR)
    kerangka.pack(fill="both", expand=True)
    kerangka.rowconfigure(1, weight=1)
    kerangka.columnconfigure(1, weight=1)

    # --- header ---
    header = tk.Frame(
        kerangka, bg=c.CARD_BG, padx=20, pady=12,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    header.grid(row=0, column=0, columnspan=2, sticky="ew")
    identitas = tk.Frame(header, bg=c.CARD_BG)
    identitas.pack(side="left")
    tk.Label(
        identitas, text="A", font=(c.FONT_FAMILY, 15, "bold"),
        bg=c.PRIMARY_DARK, fg="#FFFFFF", width=3, pady=5,
    ).pack(side="left", padx=(0, 10))
    merek = tk.Frame(identitas, bg=c.CARD_BG)
    merek.pack(side="left")
    tk.Label(
        merek, text="SIAKAD", font=c.FONT_HEADING, bg=c.CARD_BG, fg=c.TEXT_DARK,
    ).pack(anchor="w")
    tk.Label(
        merek, text="Sistem Informasi Akademik", font=c.FONT_SMALL,
        bg=c.CARD_BG, fg=c.TEXT_MUTED,
    ).pack(anchor="w")

    def keluar_dari_akun():
        if messagebox.askyesno("Keluar", "Yakin ingin keluar dari akun?", parent=root):
            auth.logout()
            tampilkan_login(root, "Anda telah keluar.", "info")

    ttk.Button(header, text="Keluar", style="Secondary.TButton", command=keluar_dari_akun).pack(side="right")
    profil = tk.Frame(header, bg=c.CARD_BG)
    profil.pack(side="right", padx=(0, 18))
    nama = pengguna.get("nama", "Pengguna")
    inisial = "".join(kata[0] for kata in nama.split()[:2]).upper() or "U"
    tk.Label(
        profil, text=inisial, font=c.FONT_BOLD, bg=c.PRIMARY_LIGHT,
        fg=c.PRIMARY_DARK, width=3, pady=5,
    ).pack(side="left", padx=(0, 9))
    teks_profil = tk.Frame(profil, bg=c.CARD_BG)
    teks_profil.pack(side="left")
    tk.Label(teks_profil, text=nama, font=c.FONT_BOLD, bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="e")
    keterangan = NAMA_ROLE.get(pengguna.get("role"), pengguna.get("role", "Pengguna"))
    if pengguna.get("nim"):
        keterangan += f"  •  {pengguna['nim']}"
    tk.Label(teks_profil, text=keterangan, font=c.FONT_SMALL, bg=c.CARD_BG, fg=c.TEXT_MUTED).pack(anchor="e")

    # --- menu samping ---
    sidebar = tk.Frame(kerangka, bg=c.SIDEBAR_BG, width=230)
    sidebar.grid(row=1, column=0, sticky="ns")
    sidebar.pack_propagate(False)
    tk.Label(
        sidebar, text="NAVIGASI", font=c.FONT_SMALL, bg=c.SIDEBAR_BG,
        fg=c.PRIMARY_LIGHT, anchor="w", padx=20,
    ).pack(fill="x", pady=(24, 10))

    # --- area isi ---
    konten = tk.Frame(kerangka, bg=c.BG_COLOR, padx=26, pady=24)
    konten.grid(row=1, column=1, sticky="nsew")
    isi = tk.Frame(konten, bg=c.BG_COLOR)
    isi.pack(fill="both", expand=True)

    tombol_menu = {}

    def warnai(kunci_aktif):
        for kunci, tombol in tombol_menu.items():
            aktif = kunci == kunci_aktif
            tombol.configure(
                text=f"{'●' if aktif else '○'}   {MENU[kunci]}",
                bg=c.SIDEBAR_ACTIVE if aktif else c.SIDEBAR_BG,
                fg="#FFFFFF" if aktif else c.SIDEBAR_TEXT,
            )

    def buka(kunci):
        if not session.is_logged_in():
            _cek_sesi(root)
            return
        warnai(kunci)
        for anak in isi.winfo_children():
            anak.destroy()
        hasil = _buat_halaman(kunci, isi, pengguna)
        if hasil is not None:
            hasil.pack(fill="both", expand=True)

    kunci_menu = [k for k in permissions.menus_for_current_user() if k in MENU]
    for kunci in kunci_menu:
        tombol = tk.Button(
            sidebar, text=f"○   {MENU[kunci]}", font=c.FONT_BODY, anchor="w", relief="flat", bd=0,
            cursor="hand2", padx=20, pady=12, bg=c.SIDEBAR_BG, fg=c.SIDEBAR_TEXT,
            activebackground=c.SIDEBAR_HOVER, activeforeground="#FFFFFF",
            command=lambda k=kunci: buka(k),
        )
        tombol.pack(fill="x")
        tombol_menu[kunci] = tombol

    tk.Label(
        sidebar, text="Sistem Informasi Akademik", font=c.FONT_SMALL,
        bg=c.SIDEBAR_BG, fg=c.PRIMARY_LIGHT, anchor="w", padx=20,
        justify="left", wraplength=185,
    ).pack(side="bottom", fill="x", pady=18)

    if kunci_menu:
        buka(kunci_menu[0])
    else:
        _halaman_pengganti(isi, "Tidak ada menu", "Akun ini belum memiliki akses ke menu mana pun.").pack(fill="both", expand=True)

    _state["after_id"] = root.after(CEK_SESI_MS, lambda: _cek_sesi(root))
    return kerangka
