"""Kerangka aplikasi: tema, navigasi antar layar, dan menu sesuai role.

Alur layar:
    mulai(root) -> login -> aplikasi (header + menu samping + isi halaman) -> keluar -> login

Setiap halaman isi berada di modul sendiri dan cukup menyediakan satu fungsi:

    def buat_halaman(parent):      # parent = frame kosong untuk diisi
        frame = tk.Frame(parent, bg=...)
        ...
        return frame

Bila modul halaman belum ada atau belum punya buat_halaman, kerangka ini
menampilkan halaman pengganti sehingga aplikasi tetap bisa dijalankan.
"""
import importlib
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from assets import colors as c
from backend import auth
from frontend import login_page
from utils import permissions, session

JUDUL = "SIAKAD - Nilai & IPK"
CEK_SESI_MS = 30_000

# kunci menu (sama dengan utils/permissions.MENU_ACCESS) -> (label, modul halaman)
MENU = {
    "mahasiswa":       ("Data Mahasiswa", "frontend.mahasiswa_page"),
    "akademik_master": ("Data Master", "frontend.akademik_master_page"),
    "nilai":           ("Input Nilai", "frontend.nilai_page"),
    "transkrip":       ("Transkrip & IPK", "frontend.transkrip_page"),
}
NAMA_ROLE = {"admin": "Administrator", "mahasiswa": "Mahasiswa"}

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


def _buat_halaman(kunci, parent):
    """Memuat halaman sebuah menu. Tidak pernah menjatuhkan aplikasi."""
    label, nama_modul = MENU[kunci]
    try:
        modul = importlib.import_module(nama_modul)
    except ModuleNotFoundError as err:
        if err.name == nama_modul:      # file halamannya memang belum dibuat
            return _halaman_pengganti(parent, label, "Halaman ini sedang dalam pengembangan.")
        traceback.print_exc()           # ada library lain yang hilang di dalam halaman
        return _halaman_pengganti(parent, label, f"Gagal memuat halaman: {err}", c.DANGER_COLOR)
    except Exception as err:
        traceback.print_exc()
        return _halaman_pengganti(parent, label, f"Terjadi error saat memuat halaman:\n{err}", c.DANGER_COLOR)

    if not hasattr(modul, "buat_halaman"):
        return _halaman_pengganti(
            parent, label,
            f"{nama_modul} belum memiliki fungsi buat_halaman(parent).",
        )
    try:
        return modul.buat_halaman(parent)
    except Exception as err:
        traceback.print_exc()
        return _halaman_pengganti(parent, label, f"Terjadi error saat membuat halaman:\n{err}", c.DANGER_COLOR)


def tampilkan_aplikasi(root, pengguna):
    """Layar utama setelah login: header, menu samping sesuai role, dan area isi."""
    _bersihkan(root)
    kerangka = tk.Frame(root, bg=c.BG_COLOR)
    kerangka.pack(fill="both", expand=True)
    kerangka.rowconfigure(1, weight=1)
    kerangka.columnconfigure(1, weight=1)

    # --- header ---
    header = tk.Frame(kerangka, bg=c.PRIMARY_COLOR)
    header.grid(row=0, column=0, columnspan=2, sticky="ew")
    tk.Label(
        header, text="SIAKAD", font=c.FONT_HEADING, bg=c.PRIMARY_COLOR, fg="#FFFFFF", padx=22, pady=12,
    ).pack(side="left")
    tk.Button(
        header, text="Keluar", font=c.FONT_BOLD, relief="flat", bd=0, cursor="hand2",
        bg=c.PRIMARY_DARK, fg="#FFFFFF", activebackground=c.PRIMARY_HOVER, activeforeground="#FFFFFF",
        padx=16, pady=6, command=lambda: keluar(root),
    ).pack(side="right", padx=18, pady=10)
    info = tk.Frame(header, bg=c.PRIMARY_COLOR)
    info.pack(side="right", padx=(0, 6))
    keterangan = NAMA_ROLE.get(pengguna["role"], pengguna["role"])
    if pengguna.get("nim"):
        keterangan += f"  \u2022  {pengguna['nim']}"
    tk.Label(info, text=pengguna["nama"], font=c.FONT_BOLD, bg=c.PRIMARY_COLOR, fg="#FFFFFF", anchor="e").pack(anchor="e")
    tk.Label(info, text=keterangan, font=c.FONT_SMALL, bg=c.PRIMARY_COLOR, fg=c.PRIMARY_LIGHT, anchor="e").pack(anchor="e")

    # --- menu samping ---
    sidebar = tk.Frame(kerangka, bg=c.SIDEBAR_BG, width=230)
    sidebar.grid(row=1, column=0, sticky="ns")
    sidebar.pack_propagate(False)
    tk.Label(
        sidebar, text="MENU", font=c.FONT_SMALL, bg=c.SIDEBAR_BG, fg=c.TEXT_MUTED, anchor="w", padx=20,
    ).pack(fill="x", pady=(20, 8))

    # --- area isi ---
    konten = tk.Frame(kerangka, bg=c.BG_COLOR, padx=28, pady=22)
    konten.grid(row=1, column=1, sticky="nsew")
    judul = tk.Label(konten, text="", font=c.FONT_TITLE, bg=c.BG_COLOR, fg=c.TEXT_DARK, anchor="w")
    judul.pack(fill="x", pady=(0, 14))
    isi = tk.Frame(konten, bg=c.BG_COLOR)
    isi.pack(fill="both", expand=True)

    tombol_menu = {}

    def warnai(kunci_aktif):
        for kunci, tombol in tombol_menu.items():
            aktif = kunci == kunci_aktif
            tombol.configure(
                bg=c.SIDEBAR_ACTIVE if aktif else c.SIDEBAR_BG,
                fg="#FFFFFF" if aktif else c.SIDEBAR_TEXT,
            )

    def buka(kunci):
        if not session.is_logged_in():
            _cek_sesi(root)
            return
        warnai(kunci)
        judul.configure(text=MENU[kunci][0])
        for anak in isi.winfo_children():
            anak.destroy()
        _buat_halaman(kunci, isi).pack(fill="both", expand=True)

    kunci_menu = [k for k in permissions.menus_for_current_user() if k in MENU]
    for kunci in kunci_menu:
        tombol = tk.Button(
            sidebar, text=MENU[kunci][0], font=c.FONT_BODY, anchor="w", relief="flat", bd=0,
            cursor="hand2", padx=20, pady=11, bg=c.SIDEBAR_BG, fg=c.SIDEBAR_TEXT,
            activebackground=c.SIDEBAR_HOVER, activeforeground="#FFFFFF",
            command=lambda k=kunci: buka(k),
        )
        tombol.pack(fill="x")
        tombol_menu[kunci] = tombol

    if kunci_menu:
        buka(kunci_menu[0])
    else:
        _halaman_pengganti(isi, "Tidak ada menu", "Akun ini belum memiliki akses ke menu mana pun.").pack(fill="both", expand=True)

    _state["after_id"] = root.after(CEK_SESI_MS, lambda: _cek_sesi(root))
    return kerangka