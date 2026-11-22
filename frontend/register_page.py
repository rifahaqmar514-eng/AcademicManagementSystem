"""Formulir pendaftaran mahasiswa baru."""
import tkinter as tk
from tkinter import messagebox, ttk

import mysql.connector

from assets.colors import BG_COLOR, CARD_BG, PRIMARY_COLOR, TEXT_DARK
from backend import auth
from utils.validators import AppError, nim_input_diizinkan


def tampilkan_registrasi(root):
    dialog = tk.Toplevel(root)
    dialog.title("Daftar Mahasiswa - SIAKAD")
    dialog.geometry("720x680")
    dialog.minsize(680, 640)
    dialog.configure(bg=BG_COLOR)
    dialog.transient(root)
    dialog.grab_set()

    try:
        prodi_rows = auth.opsi_prodi_registrasi()
    except mysql.connector.Error as err:
        messagebox.showerror(
            "Database tidak tersedia",
            f"Tidak dapat memuat program studi. Periksa server MySQL.\n\n{err}",
            parent=dialog,
        )
        dialog.destroy()
        return

    if not prodi_rows:
        messagebox.showerror(
            "Registrasi",
            "Belum ada program studi. Hubungi administrator untuk menyiapkan data akademik.",
            parent=dialog,
        )
        dialog.destroy()
        return

    card = tk.Frame(dialog, bg=CARD_BG, padx=32, pady=24)
    card.pack(fill="both", expand=True, padx=36, pady=24)

    tk.Label(
        card,
        text="Daftar Mahasiswa",
        font=("Segoe UI", 22, "bold"),
        bg=CARD_BG,
        fg=PRIMARY_COLOR,
    ).pack(anchor="w")
    tk.Label(
        card,
        text="Isi data akun dan profil akademik untuk membuat akun baru.",
        bg=CARD_BG,
        fg=TEXT_DARK,
    ).pack(anchor="w", pady=(2, 16))

    form = tk.Frame(card, bg=CARD_BG)
    form.pack(fill="x")
    form.columnconfigure(0, weight=1, uniform="register")
    form.columnconfigure(1, weight=1, uniform="register")
    entries = {}

    def entry_field(key, label, row, column, password=False):
        field = tk.Frame(form, bg=CARD_BG)
        field.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=(0, 10) if column == 0 else (10, 0),
            pady=6,
        )
        tk.Label(field, text=label, bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w")
        widget = ttk.Entry(field, show="*" if password else "")
        if key == "nim":
            validasi = (widget.register(nim_input_diizinkan), "%P")
            widget.configure(validate="key", validatecommand=validasi)
        widget.pack(fill="x", pady=(3, 0))
        entries[key] = widget
        return widget

    entry_field("nim", "NIM (9 digit)", 0, 0)
    entry_field("nama", "Nama lengkap", 0, 1)
    entry_field("email", "Email", 1, 0)
    entry_field("angkatan", "Angkatan (contoh: 2026)", 1, 1)
    entry_field("password", "Password (minimal 8 karakter)", 2, 0, password=True)
    entry_field("konfirmasi", "Ulangi password", 2, 1, password=True)

    tk.Label(form, text="Program studi", bg=CARD_BG, fg=TEXT_DARK).grid(
        row=3, column=0, sticky="w", padx=(0, 10), pady=(6, 2)
    )
    prodi_choice = ttk.Combobox(
        form,
        state="readonly",
        values=[f"{row['kode_prodi']} - {row['nama_prodi']} ({row['jenjang']})" for row in prodi_rows],
    )
    prodi_choice.grid(row=4, column=0, sticky="ew", padx=(0, 10))

    tk.Label(form, text="Dosen PA", bg=CARD_BG, fg=TEXT_DARK).grid(
        row=3, column=1, sticky="w", padx=(10, 0), pady=(6, 2)
    )
    dosen_choice = ttk.Combobox(form, state="readonly")
    dosen_choice.grid(row=4, column=1, sticky="ew", padx=(10, 0))
    dosen_rows = []

    tk.Label(form, text="Tanggal lahir (YYYY-MM-DD)", bg=CARD_BG, fg=TEXT_DARK).grid(
        row=5, column=0, sticky="w", padx=(0, 10), pady=(6, 2)
    )
    entries["tanggal_lahir"] = ttk.Entry(form)
    entries["tanggal_lahir"].grid(row=6, column=0, sticky="ew", padx=(0, 10))
    tk.Label(form, text="Jenis kelamin", bg=CARD_BG, fg=TEXT_DARK).grid(
        row=5, column=1, sticky="w", padx=(10, 0), pady=(6, 2)
    )
    gender_choice = ttk.Combobox(form, state="readonly", values=("L - Laki-laki", "P - Perempuan"))
    gender_choice.grid(row=6, column=1, sticky="ew", padx=(10, 0))

    def muat_dosen_pa(event=None):
        nonlocal dosen_rows
        index = prodi_choice.current()
        dosen_rows = []
        dosen_choice.set("")
        if index < 0:
            dosen_choice["values"] = ()
            return
        try:
            dosen_rows = auth.opsi_dosen_pa(prodi_rows[index]["prodi_id"])
        except mysql.connector.Error as err:
            messagebox.showerror("Database", f"Gagal memuat dosen PA.\n\n{err}", parent=dialog)
            dosen_choice["values"] = ()
            return
        dosen_choice["values"] = [row["nama_lengkap"] for row in dosen_rows]
        if dosen_rows:
            dosen_choice.current(0)

    prodi_choice.bind("<<ComboboxSelected>>", muat_dosen_pa)
    prodi_choice.current(0)
    muat_dosen_pa()

    def daftar():
        if entries["password"].get() != entries["konfirmasi"].get():
            messagebox.showerror("Registrasi", "Konfirmasi password tidak sama.", parent=dialog)
            return
        prodi_index = prodi_choice.current()
        dosen_index = dosen_choice.current()
        if prodi_index < 0 or dosen_index < 0:
            messagebox.showerror(
                "Registrasi",
                "Pilih program studi yang memiliki dosen PA aktif.",
                parent=dialog,
            )
            return

        nim = entries["nim"].get().strip()
        try:
            auth.registrasi(
                username=nim,
                email=entries["email"].get(),
                password=entries["password"].get(),
                nim=nim,
                nama=entries["nama"].get(),
                prodi_id=prodi_rows[prodi_index]["prodi_id"],
                dosen_pa_id=dosen_rows[dosen_index]["dosen_id"],
                jenis_kelamin=gender_choice.get().split(" - ", 1)[0],
                tanggal_lahir=entries["tanggal_lahir"].get(),
                angkatan=entries["angkatan"].get(),
            )
        except AppError as err:
            messagebox.showerror("Registrasi gagal", str(err), parent=dialog)
            return
        except mysql.connector.IntegrityError:
            messagebox.showerror(
                "Registrasi gagal",
                "NIM atau email sudah digunakan.",
                parent=dialog,
            )
            return
        except mysql.connector.Error as err:
            messagebox.showerror("Database", f"Gagal menyimpan akun.\n\n{err}", parent=dialog)
            return

        messagebox.showinfo(
            "Registrasi berhasil",
            "Akun berhasil dibuat. Silakan masuk menggunakan NIM dan password yang didaftarkan.",
            parent=dialog,
        )
        dialog.destroy()

    actions = tk.Frame(card, bg=CARD_BG)
    actions.pack(fill="x", pady=(20, 0))
    ttk.Button(actions, text="Kembali ke Login", command=dialog.destroy).pack(side="left")
    ttk.Button(actions, text="Daftar", command=daftar).pack(side="right")
