"""Halaman login dan dialog pendaftaran mahasiswa (Tkinter + ttk).

Alur:
    main_window -> tampilkan_login(root, setelah_login)
      tab Mahasiswa : Nama + NIM            -> auth.login_mahasiswa
      tab Admin     : username + password   -> auth.login_admin
      tombol Daftar : dialog pendaftaran    -> auth.registrasi
Setelah login berhasil, fungsi setelah_login(pengguna) dipanggil; main_window
yang memutuskan layar berikutnya. File ini tidak menulis SQL.
"""
import tkinter as tk
from tkinter import messagebox, ttk

import mysql.connector

from assets import colors as c
from backend import auth
from utils.validators import AppError

PESAN_DB = (
    "Tidak dapat mengakses database. Pastikan MySQL (Laragon) sudah menyala "
    "dan isi file .env benar.\n\n{err}"
)
_WARNA_PESAN = {
    "error": (c.DANGER_COLOR, c.DANGER_BG),
    "sukses": (c.SUCCESS_COLOR, c.SUCCESS_BG),
    "info": (c.PRIMARY_DARK, c.PRIMARY_LIGHT),
}


# ------------------------------------------------------------------ pembantu
def _buat_pesan(parent, latar, lebar=340):
    """Kotak pesan inline setinggi tetap (tidak menggeser tata letak saat muncul)."""
    kotak = tk.Frame(parent, bg=latar, height=46)
    kotak.pack_propagate(False)
    label = tk.Label(
        kotak, text="", bg=latar, fg=c.TEXT_DARK, font=c.FONT_SMALL,
        wraplength=lebar, justify="left", anchor="w", padx=10,
    )
    label.pack(fill="both", expand=True)

    def tampil(teks="", jenis="error"):
        if not teks:
            label.configure(text="", bg=latar)
            return
        warna, bg = _WARNA_PESAN[jenis]
        label.configure(text=teks, fg=warna, bg=bg)

    return kotak, tampil


def _kolom(parent, latar, teks, show=None, lebar=38):
    """Satu kolom isian: label di atas, entry di bawah. Mengembalikan entry-nya."""
    tk.Label(parent, text=teks, bg=latar, fg=c.TEXT_DARK, font=c.FONT_BOLD).pack(anchor="w")
    entry = ttk.Entry(parent, width=lebar, style="Form.TEntry", show=show or "")
    entry.pack(fill="x", pady=(4, 14))
    return entry


def _kosongkan(entry, isi=""):
    entry.delete(0, "end")
    if isi:
        entry.insert(0, isi)


def _tengahkan(jendela, induk, lebar, tinggi):
    induk.update_idletasks()
    x = induk.winfo_rootx() + max((induk.winfo_width() - lebar) // 2, 0)
    y = induk.winfo_rooty() + max((induk.winfo_height() - tinggi) // 2, 0)
    jendela.geometry(f"{lebar}x{tinggi}+{x}+{y}")


# --------------------------------------------------------------------- login
def _panel_brand(frame):
    kiri = tk.Frame(frame, bg=c.PRIMARY_DARK)
    kiri.grid(row=0, column=0, sticky="nsew")
    isi = tk.Frame(kiri, bg=c.PRIMARY_DARK)
    isi.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(isi, text="SIAKAD", font=c.FONT_BRAND, bg=c.PRIMARY_DARK, fg="#FFFFFF").pack(anchor="w")
    tk.Label(
        isi, text="Sistem Informasi Akademik", font=c.FONT_HEADING,
        bg=c.PRIMARY_DARK, fg=c.PRIMARY_LIGHT,
    ).pack(anchor="w", pady=(2, 22))
    for baris in (
        "Nilai, IPS, dan IPK dalam satu tempat",
        "Transkrip nilai kapan saja",
        "Data terkelola rapi dan terstruktur",
    ):
        tk.Label(
            isi, text="\u2713  " + baris, font=c.FONT_BODY,
            bg=c.PRIMARY_DARK, fg="#FFFFFF", anchor="w",
        ).pack(anchor="w", pady=3)
    tk.Label(
        kiri, text="Proyek UAS Basis Data", font=c.FONT_SMALL,
        bg=c.PRIMARY_DARK, fg=c.PRIMARY_LIGHT,
    ).place(relx=0.5, rely=0.95, anchor="center")


def tampilkan_login(root, setelah_login, pesan_awal=None):
    """Membangun layar login di dalam root dan mengembalikan frame-nya.

    setelah_login : fungsi(pengguna) yang dipanggil saat login berhasil.
    pesan_awal    : (teks, jenis) opsional, mis. ("Anda telah keluar.", "info").
    """
    frame = tk.Frame(root, bg=c.BG_COLOR)
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=4, uniform="panel")
    frame.columnconfigure(1, weight=5, uniform="panel")
    _panel_brand(frame)

    kanan = tk.Frame(frame, bg=c.BG_COLOR)
    kanan.grid(row=0, column=1, sticky="nsew")
    kartu = tk.Frame(
        kanan, bg=c.CARD_BG, padx=40, pady=34,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    kartu.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(kartu, text="Selamat datang", font=c.FONT_TITLE, bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="w")
    tk.Label(
        kartu, text="Masuk untuk melanjutkan.", font=c.FONT_BODY, bg=c.CARD_BG, fg=c.TEXT_MUTED,
    ).pack(anchor="w", pady=(2, 18))

    # --- tab pemilih jenis pengguna ---
    bar_tab = tk.Frame(kartu, bg=c.CARD_BG)
    bar_tab.pack(fill="x", pady=(0, 18))
    bar_tab.columnconfigure(0, weight=1, uniform="tab")
    bar_tab.columnconfigure(1, weight=1, uniform="tab")
    tombol_tab = {}
    for kolom, (kunci, teks) in enumerate((("mahasiswa", "Mahasiswa"), ("admin", "Admin"))):
        tombol_tab[kunci] = tk.Button(
            bar_tab, text=teks, font=c.FONT_BOLD, relief="flat", bd=0, cursor="hand2",
            padx=10, pady=8, command=lambda k=kunci: pilih_tab(k),
        )
        tombol_tab[kunci].grid(row=0, column=kolom, sticky="ew", padx=(0, 2) if kolom == 0 else (2, 0))

    area = tk.Frame(kartu, bg=c.CARD_BG)
    area.pack(fill="x")

    form_mhs = tk.Frame(area, bg=c.CARD_BG)
    in_nama = _kolom(form_mhs, c.CARD_BG, "Nama lengkap")
    in_nim = _kolom(form_mhs, c.CARD_BG, "NIM")

    form_admin = tk.Frame(area, bg=c.CARD_BG)
    in_user = _kolom(form_admin, c.CARD_BG, "Username")
    in_pass = _kolom(form_admin, c.CARD_BG, "Password", show="\u2022")
    var_tampil = tk.BooleanVar(value=False)

    def ganti_tampil():
        in_pass.configure(show="" if var_tampil.get() else "\u2022")

    ttk.Checkbutton(
        form_admin, text="Tampilkan password", variable=var_tampil,
        command=ganti_tampil, style="Form.TCheckbutton",
    ).pack(anchor="w", pady=(0, 6))

    kotak_pesan, tampil_pesan = _buat_pesan(kartu, c.CARD_BG)
    kotak_pesan.pack(fill="x", pady=(8, 6))

    tombol_masuk = ttk.Button(kartu, text="Masuk", style="Primary.TButton")
    tombol_masuk.pack(fill="x")

    pemisah = tk.Frame(kartu, bg=c.CARD_BG)
    pemisah.pack(fill="x", pady=(18, 0))
    tk.Label(pemisah, text="Belum punya akun?", font=c.FONT_BODY, bg=c.CARD_BG, fg=c.TEXT_MUTED).pack(side="left")
    tombol_daftar = ttk.Button(pemisah, text="Daftar sebagai mahasiswa", style="Link.TButton")
    tombol_daftar.pack(side="left", padx=(6, 0))

    aktif = {"tab": "mahasiswa"}

    def pilih_tab(kunci, kosongkan_pesan=True):
        aktif["tab"] = kunci
        for k, tombol in tombol_tab.items():
            if k == kunci:
                tombol.configure(bg=c.PRIMARY_COLOR, fg="#FFFFFF", activebackground=c.PRIMARY_HOVER, activeforeground="#FFFFFF")
            else:
                tombol.configure(bg=c.TAB_IDLE_BG, fg=c.TEXT_MUTED, activebackground=c.BORDER_COLOR, activeforeground=c.TEXT_DARK)
        form_mhs.pack_forget()
        form_admin.pack_forget()
        if kunci == "mahasiswa":
            form_mhs.pack(fill="x")
            in_nama.focus_set()
        else:
            form_admin.pack(fill="x")
            in_user.focus_set()
        tombol_daftar.configure(state="normal" if kunci == "mahasiswa" else "disabled")
        if kosongkan_pesan:
            tampil_pesan("")

    def masuk(event=None):
        tampil_pesan("")
        try:
            if aktif["tab"] == "mahasiswa":
                pengguna = auth.login_mahasiswa(in_nama.get(), in_nim.get())
            else:
                pengguna = auth.login_admin(in_user.get(), in_pass.get())
        except AppError as err:
            tampil_pesan(str(err), "error")
            if aktif["tab"] == "admin":
                _kosongkan(in_pass)
                in_pass.focus_set()
            else:
                in_nim.focus_set()
            return
        except mysql.connector.Error as err:
            messagebox.showerror("Database tidak tersedia", PESAN_DB.format(err=err), parent=root)
            return
        root.unbind("<Return>")
        setelah_login(pengguna)

    def setelah_daftar(nim, nama):
        pilih_tab("mahasiswa")
        _kosongkan(in_nama, nama)
        _kosongkan(in_nim, nim)
        tampil_pesan(
            "Pendaftaran berhasil. Klik Masuk. Lengkapi biodata dan dosen PA melalui administrator.",
            "sukses",
        )
        tombol_masuk.focus_set()

    tombol_masuk.configure(command=masuk)
    tombol_daftar.configure(command=lambda: tampilkan_registrasi(root, setelah_daftar))
    root.bind("<Return>", masuk)

    pilih_tab("mahasiswa")
    if pesan_awal:
        tampil_pesan(*pesan_awal)
    return frame


# ---------------------------------------------------------------- pendaftaran
def tampilkan_registrasi(root, setelah_daftar):
    """Dialog pendaftaran mahasiswa: nama, NIM, jurusan, dan program studi.

    setelah_daftar : fungsi(nim, nama) dipanggil setelah pendaftaran berhasil.
    """
    try:
        jurusan = auth.daftar_jurusan()
    except mysql.connector.Error as err:
        messagebox.showerror("Database tidak tersedia", PESAN_DB.format(err=err), parent=root)
        return
    if not jurusan:
        messagebox.showinfo(
            "Pendaftaran",
            "Data jurusan belum tersedia. Hubungi administrator.",
            parent=root,
        )
        return

    dialog = tk.Toplevel(root)
    dialog.title("Daftar Mahasiswa")
    dialog.configure(bg=c.BG_COLOR)
    dialog.resizable(False, False)
    dialog.transient(root)
    _tengahkan(dialog, root, 480, 600)

    kartu = tk.Frame(
        dialog, bg=c.CARD_BG, padx=32, pady=26,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    kartu.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(kartu, text="Daftar Mahasiswa", font=c.FONT_HEADING, bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="w")
    tk.Label(
        kartu, text="Isi data berikut untuk membuat akun.", font=c.FONT_BODY,
        bg=c.CARD_BG, fg=c.TEXT_MUTED,
    ).pack(anchor="w", pady=(2, 14))

    in_nama = _kolom(kartu, c.CARD_BG, "Nama lengkap", lebar=44)
    in_nim = _kolom(kartu, c.CARD_BG, "NIM", lebar=44)

    tk.Label(kartu, text="Jurusan", bg=c.CARD_BG, fg=c.TEXT_DARK, font=c.FONT_BOLD).pack(anchor="w")
    pilih_jurusan = ttk.Combobox(kartu, state="readonly", style="Form.TCombobox", width=42)
    pilih_jurusan["values"] = [f"{j['nama_jurusan']} ({j['kode_jurusan']})" for j in jurusan]
    pilih_jurusan.pack(fill="x", pady=(4, 14))

    tk.Label(kartu, text="Program studi", bg=c.CARD_BG, fg=c.TEXT_DARK, font=c.FONT_BOLD).pack(anchor="w")
    pilih_prodi = ttk.Combobox(kartu, state="disabled", style="Form.TCombobox", width=42)
    pilih_prodi.pack(fill="x", pady=(4, 14))
    prodi_rows = []

    tk.Label(
        kartu,
        text="NIM berfungsi sebagai pengganti password. Simpan baik-baik dan jangan dibagikan.",
        font=c.FONT_SMALL, bg=c.PRIMARY_LIGHT, fg=c.PRIMARY_DARK,
        wraplength=380, justify="left", anchor="w", padx=10, pady=8,
    ).pack(fill="x", pady=(0, 8))

    kotak_pesan, tampil = _buat_pesan(kartu, c.CARD_BG, lebar=380)
    kotak_pesan.pack(fill="x")

    def muat_prodi(event=None):
        nonlocal prodi_rows
        prodi_rows = []
        pilih_prodi.set("")
        indeks = pilih_jurusan.current()
        if indeks < 0:
            return
        try:
            prodi_rows = auth.daftar_prodi(jurusan[indeks]["jurusan_id"])
        except mysql.connector.Error as err:
            messagebox.showerror("Database tidak tersedia", PESAN_DB.format(err=err), parent=dialog)
            return
        pilih_prodi["values"] = [f"{p['nama_prodi']} ({p['jenjang']})" for p in prodi_rows]
        pilih_prodi.configure(state="readonly" if prodi_rows else "disabled")
        if not prodi_rows:
            tampil("Jurusan ini belum memiliki program studi.", "info")
        else:
            tampil("")

    def daftar(event=None):
        tampil("")
        if pilih_jurusan.current() < 0:
            tampil("Pilih jurusan terlebih dahulu.")
            return
        if pilih_prodi.current() < 0 or not prodi_rows:
            tampil("Pilih program studi.")
            return
        try:
            nim = auth.registrasi_mahasiswa(
                in_nama.get(),
                in_nim.get(),
                prodi_rows[pilih_prodi.current()]["prodi_id"],
            )
        except AppError as err:
            tampil(str(err))
            return
        except mysql.connector.IntegrityError:
            tampil("NIM sudah terdaftar.")
            return
        except mysql.connector.Error as err:
            messagebox.showerror("Database tidak tersedia", PESAN_DB.format(err=err), parent=dialog)
            return
        nama = " ".join(in_nama.get().split())
        dialog.destroy()
        setelah_daftar(nim, nama)

    pilih_jurusan.bind("<<ComboboxSelected>>", muat_prodi)

    tombol = tk.Frame(kartu, bg=c.CARD_BG)
    tombol.pack(fill="x", pady=(10, 0))
    ttk.Button(tombol, text="Batal", style="Secondary.TButton", command=dialog.destroy).pack(side="left")
    ttk.Button(tombol, text="Daftar", style="Primary.TButton", command=daftar).pack(side="right")

    dialog.bind("<Return>", daftar)
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    dialog.grab_set()
    in_nama.focus_set()
