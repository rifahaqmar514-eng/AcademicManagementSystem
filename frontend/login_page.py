"""Halaman login dan dialog pendaftaran mahasiswa (Tkinter + ttk).

Tema: Warm & Earthy (Coffee Shop).
Revisi: 
- Perbaikan error Tkinter aktifborderwidth.
- Redesign logo SIAKAD (nuansa akademik, tanpa emoji kopi).
- Form registrasi dibagi menjadi 3 tahap (Wizard).
"""
import tkinter as tk
from tkinter import messagebox, ttk

import mysql.connector

from assets import colors as c
from assets.styles import terapkan_style
from backend import auth
from utils.recent_accounts import muat_akun, simpan_akun
from utils.validators import AppError, nim_input_diizinkan

PESAN_DB = (
    "Tidak dapat mengakses database. Pastikan MySQL (Laragon) sudah menyala "
    "dan isi file .env benar.\n\n{err}"
)
_IKON = {"error": "✕", "sukses": "✓", "info": "ℹ"}
_WARNA = {
    "error": (c.DANGER_COLOR, c.DANGER_BG),
    "sukses": (c.SUCCESS_COLOR, c.SUCCESS_BG),
    "info": (c.INFO_COLOR, c.INFO_BG),
}


# ------------------------------------------------------------------ pembantu
def _buat_pesan(parent, latar, lebar=340):
    """Banner pesan dengan ikon & warna status. Disembunyikan saat kosong."""
    luar = tk.Frame(parent, bg=latar)
    # Biarkan tinggi banner mengikuti jumlah baris pesan agar teks tidak terpotong.
    kotak = tk.Frame(luar, bg=latar)

    ikon = tk.Label(kotak, text="", bg=latar, fg=c.TEXT_DARK,
                    font=("Segoe UI", 11, "bold"), width=3)
    ikon.pack(side="left", padx=(10, 0), fill="y")

    label = tk.Label(kotak, text="", bg=latar, fg=c.TEXT_DARK,
                     font=c.FONT_SMALL, wraplength=lebar,
                     justify="left", anchor="w", padx=6, pady=7)
    label.pack(side="left", fill="both", expand=True, padx=(0, 10))

    def tampil(teks="", jenis="error"):
        if not teks:
            kotak.pack_forget()
            return
        warna, bg = _WARNA.get(jenis, _WARNA["error"])
        kotak.configure(bg=bg)
        ikon.configure(text=_IKON.get(jenis, "•"), fg=warna, bg=bg)
        label.configure(text=teks, fg=warna, bg=bg)
        kotak.pack(fill="x")

    return luar, tampil


def _kolom(parent, latar, teks, show=None, lebar=38, nim=False):
    """Label + entry. Focus ring ditangani lewat style Form.TEntry."""
    bungkus = tk.Frame(parent, bg=latar)
    bungkus.pack(fill="x", pady=(0, 12))

    tk.Label(bungkus, text=teks, bg=latar, fg=c.TEXT_DARK,
             font=c.FONT_BOLD, anchor="w").pack(fill="x", pady=(0, 5))

    entry = ttk.Entry(bungkus, width=lebar, style="Form.TEntry", show=show or "")
    if nim:
        validasi = (entry.register(nim_input_diizinkan), "%P")
        entry.configure(validate="key", validatecommand=validasi)
    entry.pack(fill="x")
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


# --------------------------------------------------------------- brand panel
def _panel_brand(frame):
    """Panel kiri: gradasi espresso -> dark roast + ornamen abstrak."""
    kiri = tk.Frame(frame, bg=c.PRIMARY_GRADIENT_BOT)
    kiri.grid(row=0, column=0, sticky="nsew")

    kanvas = tk.Canvas(kiri, highlightthickness=0, bd=0)
    kanvas.place(relwidth=1, relheight=1)

    def _gambar_gradasi(event=None):
        kanvas.delete("grad")
        w = kanvas.winfo_width() or 1
        h = kanvas.winfo_height() or 1
        langkah = max(h // 40, 1)
        for i in range(0, h, langkah):
            rasio = i / h
            # #3E2723 (espresso) -> #1B0E0A (dark roast)
            r = int(0x3E + (0x1B - 0x3E) * rasio)
            g = int(0x27 + (0x0E - 0x27) * rasio)
            b = int(0x23 + (0x0A - 0x23) * rasio)
            kanvas.create_rectangle(
                0, i, w, i + langkah,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="", tags="grad",
            )
        # Ornamen glow hangat (caramel & mocha transparan)
        kanvas.create_oval(-140, -140, 260, 260, fill="#5D4037",
                           outline="", stipple="gray50", tags="grad")
        kanvas.create_oval(w - 180, h - 180, w + 100, h + 100,
                           fill="#C68B59", outline="",
                           stipple="gray25", tags="grad")

    kanvas.bind("<Configure>", _gambar_gradasi)

    isi = tk.Frame(kanvas, bg=c.PRIMARY_GRADIENT_TOP)
    isi.place(relx=0.5, rely=0.5, anchor="center")

    # --- LOGO BARU (Lebih Premium) ---
    badge = tk.Frame(isi, bg=c.PRIMARY_ACCENT, padx=16, pady=8)
    badge.pack(anchor="w", pady=(0, 24))
    
    # Ikon geometris akademik
    tk.Label(badge, text="❖", font=("Segoe UI", 18, "bold"),
             bg=c.PRIMARY_ACCENT, fg="#FFF8F0").pack(side="left", padx=(0, 6))
    tk.Label(badge, text="SIAKAD", font=("Segoe UI", 16, "bold"),
             bg=c.PRIMARY_ACCENT, fg="#FFF8F0").pack(side="left")

    tk.Label(isi, text="Sistem Informasi\nAkademik Terpadu",
             font=("Segoe UI", 22, "bold"), bg=c.PRIMARY_GRADIENT_TOP,
             fg="#FFF8F0", justify="left").pack(anchor="w")
    tk.Label(isi, text="Pantau capaian belajar, IPS, IPK,\ndan transkrip nilai secara real-time.",
             font=("Segoe UI", 11), bg=c.PRIMARY_GRADIENT_TOP,
             fg=c.PRIMARY_LIGHT, justify="left").pack(anchor="w", pady=(8, 24))

    for baris in (
        "Evaluasi hasil studi terpadu",
        "Transkrip nilai akurat",
        "Data akademik aman & rapi",
    ):
        baris_frame = tk.Frame(isi, bg=c.PRIMARY_GRADIENT_TOP)
        baris_frame.pack(anchor="w", pady=4)
        tk.Label(baris_frame, text="✓", font=("Segoe UI", 11, "bold"),
                 bg=c.PRIMARY_GRADIENT_TOP, fg=c.PRIMARY_ACCENT,
                 width=2, anchor="w").pack(side="left")
        tk.Label(baris_frame, text=baris, font=("Segoe UI", 10),
                 bg=c.PRIMARY_GRADIENT_TOP, fg="#E6C9A8",
                 anchor="w").pack(side="left")

    tk.Label(kiri, text="© Proyek UAS Basis Data",
             font=("Segoe UI", 9), bg=c.PRIMARY_GRADIENT_BOT,
             fg="#A1887F").place(relx=0.5, rely=0.96, anchor="center")


# --------------------------------------------------------------------- login
def tampilkan_login(root, setelah_login, pesan_awal=None):
    """Membangun layar login di dalam root dan mengembalikan frame-nya."""
    terapkan_style(root)

    frame = tk.Frame(root, bg=c.BG_COLOR)
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=5, uniform="panel")
    frame.columnconfigure(1, weight=6, uniform="panel")
    _panel_brand(frame)

    kanan = tk.Frame(frame, bg=c.BG_COLOR)
    kanan.grid(row=0, column=1, sticky="nsew")

    kartu = tk.Frame(
        kanan, bg=c.CARD_BG, padx=44, pady=38,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    kartu.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(kartu, text="Selamat datang", font=c.FONT_TITLE,
             bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="w")
    tk.Label(kartu, text="Masuk untuk melanjutkan ke dasbor akademik.",
             font=c.FONT_BODY, bg=c.CARD_BG, fg=c.TEXT_MUTED).pack(
        anchor="w", pady=(2, 20))

    # --- segmented control (tab) ---
    bar_tab = tk.Frame(kartu, bg=c.TAB_IDLE_BG, padx=4, pady=4)
    bar_tab.pack(fill="x", pady=(0, 18))
    bar_tab.columnconfigure(0, weight=1, uniform="tab")
    bar_tab.columnconfigure(1, weight=1, uniform="tab")
    tombol_tab = {}
    for kolom, (kunci, teks) in enumerate((("mahasiswa", "🎓  Mahasiswa"),
                                           ("admin", "🛡️  Admin"))):
        # PERBAIKAN: activeborderwidth dihapus untuk mencegah crash
        tombol_tab[kunci] = tk.Button(
            bar_tab, text=teks, font=c.FONT_BOLD, relief="flat", bd=0,
            cursor="hand2", padx=12, pady=9,
            command=lambda k=kunci: pilih_tab(k),
        )
        tombol_tab[kunci].grid(row=0, column=kolom, sticky="ew")

    area = tk.Frame(kartu, bg=c.CARD_BG)
    area.pack(fill="x")

    form_mhs = tk.Frame(area, bg=c.CARD_BG)
    tk.Label(form_mhs, text="Nama lengkap", bg=c.CARD_BG, fg=c.TEXT_DARK,
             font=c.FONT_BOLD, anchor="w").pack(fill="x", pady=(0, 5))
    in_nama = ttk.Entry(form_mhs, width=38, style="Form.TEntry")
    in_nama.pack(fill="x", pady=(0, 12))
    in_nim = _kolom(form_mhs, c.CARD_BG, "NIM (9 digit)", lebar=38, nim=True)
    var_ingat = tk.BooleanVar(master=root, value=True)
    ingat_card = tk.Frame(
        form_mhs, bg=c.SURFACE_MUTED, padx=11, pady=8,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
        takefocus=True,
    )
    ingat_card.pack(fill="x", pady=(0, 10))
    indikator_ingat = tk.Canvas(
        ingat_card, width=20, height=20, bg=c.SURFACE_MUTED,
        highlightthickness=0, cursor="hand2",
    )
    indikator_ingat.pack(side="left", padx=(0, 10))
    teks_ingat = tk.Frame(ingat_card, bg=c.SURFACE_MUTED, cursor="hand2")
    teks_ingat.pack(side="left", fill="x", expand=True)
    judul_ingat = tk.Label(
        teks_ingat, text="Ingat akun di perangkat ini", bg=c.SURFACE_MUTED,
        fg=c.TEXT_DARK, font=c.FONT_BOLD, anchor="w", cursor="hand2",
    )
    judul_ingat.pack(fill="x")
    keterangan_ingat = tk.Label(
        teks_ingat, text="Nama dan NIM terenkripsi untuk login berikutnya.",
        bg=c.SURFACE_MUTED, fg=c.TEXT_MUTED, font=c.FONT_SMALL,
        anchor="w", cursor="hand2",
    )
    keterangan_ingat.pack(fill="x", pady=(2, 0))
    def gambar_ingat():
        aktif_ingat = var_ingat.get()
        latar = "#F3E7D8" if aktif_ingat else c.CARD_BG
        garis = c.PRIMARY_ACCENT if aktif_ingat else c.BORDER_COLOR
        ingat_card.configure(bg=latar, highlightbackground=garis)
        teks_ingat.configure(bg=latar)
        judul_ingat.configure(bg=latar)
        keterangan_ingat.configure(bg=latar)
        indikator_ingat.configure(bg=latar)
        indikator_ingat.delete("all")
        indikator_ingat.create_rectangle(
            2, 2, 18, 18,
            fill=c.PRIMARY_ACCENT if aktif_ingat else c.CARD_BG,
            outline=c.PRIMARY_ACCENT if aktif_ingat else c.BORDER_COLOR,
            width=2,
        )
        if aktif_ingat:
            indikator_ingat.create_line(
                5, 10, 8, 13, 14, 6,
                fill="#FFF8F0", width=2, capstyle="round", joinstyle="round",
            )

    def toggle_ingat(event=None):
        var_ingat.set(not var_ingat.get())
        gambar_ingat()
        ingat_card.focus_set()
        return "break"

    for widget_ingat in (
        ingat_card, indikator_ingat, teks_ingat, judul_ingat, keterangan_ingat,
    ):
        widget_ingat.bind("<Button-1>", toggle_ingat)
        widget_ingat.bind("<space>", toggle_ingat)
    gambar_ingat()

    akun_terakhir = muat_akun()
    popup_saran = tk.Toplevel(root)
    popup_saran.withdraw()
    popup_saran.overrideredirect(True)
    popup_saran.transient(root)
    daftar_saran = tk.Listbox(
        popup_saran, height=5, activestyle="none", exportselection=False,
        bg=c.CARD_BG, fg=c.TEXT_DARK,
        selectbackground=c.PRIMARY_ACCENT, selectforeground="#FFF8F0",
        font=c.FONT_BODY, relief="solid", borderwidth=1,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    daftar_saran.pack(fill="both", expand=True)
    akun_cocok = []

    def tutup_saran():
        popup_saran.withdraw()

    def pointer_di(widget):
        x = root.winfo_pointerx()
        y = root.winfo_pointery()
        kiri = widget.winfo_rootx()
        atas = widget.winfo_rooty()
        return (
            kiri <= x < kiri + widget.winfo_width()
            and atas <= y < atas + widget.winfo_height()
        )

    def pointer_di_area_saran():
        return pointer_di(in_nama) or (
            popup_saran.winfo_viewable() and pointer_di(daftar_saran)
        )

    def tampilkan_saran(event=None, semua=False):
        if not pointer_di_area_saran():
            tutup_saran()
            return
        teks = in_nama.get().strip().casefold()
        akun_cocok[:] = [
            akun for akun in akun_terakhir
            if semua or not teks or teks in akun["nama"].casefold()
        ]
        daftar_saran.delete(0, "end")
        for akun in akun_cocok:
            daftar_saran.insert("end", akun["nama"])
        if not akun_cocok:
            tutup_saran()
            return

        daftar_saran.configure(height=min(len(akun_cocok), 5))
        root.update_idletasks()
        x = in_nama.winfo_rootx()
        y = in_nama.winfo_rooty() + in_nama.winfo_height()
        lebar = in_nama.winfo_width()
        tinggi = daftar_saran.winfo_reqheight() + 2
        if y + tinggi > popup_saran.winfo_screenheight():
            y = in_nama.winfo_rooty() - tinggi
        popup_saran.geometry(f"{lebar}x{tinggi}+{x}+{y}")
        popup_saran.deiconify()
        popup_saran.lift()

    def sorot_saran(event):
        indeks = daftar_saran.nearest(event.y)
        if 0 <= indeks < len(akun_cocok):
            daftar_saran.selection_clear(0, "end")
            daftar_saran.selection_set(indeks)
            daftar_saran.activate(indeks)

    def hilangkan_sorot(event=None):
        daftar_saran.selection_clear(0, "end")

    def pilih_saran(event=None):
        pilihan = daftar_saran.curselection()
        if not pilihan or pilihan[0] >= len(akun_cocok):
            return "break"
        akun = akun_cocok[pilihan[0]]
        _kosongkan(in_nama, akun["nama"])
        _kosongkan(in_nim, akun["nim"])
        tutup_saran()
        in_nama.focus_set()
        in_nama.icursor("end")
        return "break"

    def panah_bawah(event=None):
        if popup_saran.winfo_viewable() and akun_cocok:
            daftar_saran.selection_clear(0, "end")
            daftar_saran.selection_set(0)
            daftar_saran.activate(0)
            daftar_saran.focus_set()
            return "break"

    def enter_saran(event=None):
        if popup_saran.winfo_viewable() and akun_cocok:
            if not daftar_saran.curselection():
                daftar_saran.selection_set(0)
            return pilih_saran()

    def escape_saran(event=None):
        tutup_saran()
        in_nama.focus_set()
        return "break"

    def tutup_jika_fokus_pindah():
        fokus = root.focus_get()
        if fokus not in (in_nama, daftar_saran):
            tutup_saran()

    def nama_kehilangan_fokus(event=None):
        root.after(120, tutup_jika_fokus_pindah)

    def pointer_keluar_area(event=None):
        root.after(120, lambda: (
            None if pointer_di_area_saran() else tutup_saran()
        ))

    def tombol_dilepas(event=None):
        if event.keysym not in ("Up", "Down", "Return", "Escape", "Tab"):
            tampilkan_saran()

    in_nama.bind("<Enter>", lambda event: tampilkan_saran(semua=True))
    in_nama.bind("<Leave>", pointer_keluar_area)
    in_nama.bind("<KeyRelease>", tombol_dilepas)
    in_nama.bind("<Down>", panah_bawah)
    in_nama.bind("<Return>", enter_saran)
    in_nama.bind("<Escape>", escape_saran)
    in_nama.bind("<FocusOut>", nama_kehilangan_fokus)
    daftar_saran.bind("<ButtonRelease-1>", pilih_saran)
    daftar_saran.bind("<Motion>", sorot_saran)
    daftar_saran.bind("<Leave>", hilangkan_sorot)
    daftar_saran.bind("<Leave>", pointer_keluar_area, add="+")
    daftar_saran.bind("<Return>", pilih_saran)
    daftar_saran.bind("<Escape>", escape_saran)
    daftar_saran.bind("<FocusOut>", nama_kehilangan_fokus)

    def ingat_akun(nama, nim):
        if not var_ingat.get():
            return
        if simpan_akun(nama, nim):
            akun_terakhir[:] = muat_akun()
            if popup_saran.winfo_viewable():
                tampilkan_saran()

    form_admin = tk.Frame(area, bg=c.CARD_BG)
    in_user = _kolom(form_admin, c.CARD_BG, "Username", lebar=38)
    in_pass = _kolom(form_admin, c.CARD_BG, "Password", show="•", lebar=38)
    var_tampil = tk.BooleanVar(value=False)

    def ganti_tampil():
        in_pass.configure(show="" if var_tampil.get() else "•")

    ttk.Checkbutton(form_admin, text="Tampilkan password",
                    variable=var_tampil, command=ganti_tampil,
                    style="Form.TCheckbutton").pack(anchor="w", pady=(0, 4))

    kotak_pesan, tampil_pesan = _buat_pesan(kartu, c.CARD_BG)
    kotak_pesan.pack(fill="x", pady=(6, 4))

    tombol_masuk = ttk.Button(kartu, text="Masuk  →", style="Primary.TButton")
    tombol_masuk.pack(fill="x", pady=(4, 0))

    pemisah = tk.Frame(kartu, bg=c.CARD_BG)
    pemisah.pack(fill="x", pady=(20, 0))
    tk.Label(pemisah, text="Belum punya akun?", font=c.FONT_BODY,
             bg=c.CARD_BG, fg=c.TEXT_MUTED).pack(side="left")
    tombol_daftar = ttk.Button(pemisah, text="Daftar sebagai mahasiswa",
                               style="Link.TButton")
    tombol_daftar.pack(side="left", padx=(4, 0))

    aktif = {"tab": "mahasiswa"}

    def pilih_tab(kunci, kosongkan_pesan=True):
        aktif["tab"] = kunci
        for k, tombol in tombol_tab.items():
            if k == kunci:
                tombol.configure(bg=c.TAB_ACTIVE_BG, fg="#FFF8F0",
                                 activebackground=c.PRIMARY_ACCENT,
                                 activeforeground="#FFF8F0")
            else:
                tombol.configure(bg=c.TAB_IDLE_BG, fg=c.TEXT_MUTED,
                                 activebackground=c.INPUT_BORDER,
                                 activeforeground=c.TEXT_DARK)
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
            messagebox.showerror("Database tidak tersedia",
                                 PESAN_DB.format(err=err), parent=root)
            return
        if aktif["tab"] == "mahasiswa":
            ingat_akun(in_nama.get(), in_nim.get())
        root.unbind("<Return>")
        setelah_login(pengguna)

    def setelah_daftar(nim, nama):
        pilih_tab("mahasiswa")
        ingat_akun(nama, nim)
        _kosongkan(in_nama, nama)
        _kosongkan(in_nim, nim)
        tampil_pesan(
            "Pendaftaran berhasil! Klik Masuk, lalu lengkapi biodata & dosen PA "
            "melalui administrator.", "sukses")
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
    """Dialog pendaftaran mahasiswa (Satu Halaman Utuh & Layout Rapi)."""
    terapkan_style(root)
    try:
        jurusan = auth.daftar_jurusan()
    except mysql.connector.Error as err:
        messagebox.showerror("Database tidak tersedia",
                             PESAN_DB.format(err=err), parent=root)
        return
    if not jurusan:
        messagebox.showinfo("Pendaftaran",
                            "Data jurusan belum tersedia. Hubungi administrator.",
                            parent=root)
        return

    dialog = tk.Toplevel(root)
    dialog.title("Daftar Mahasiswa")
    dialog.configure(bg=c.BG_COLOR)
    dialog.resizable(False, False)
    dialog.transient(root)
    # Ukuran diperbesar (720px) agar semua elemen dan tombol pasti muat
    _tengahkan(dialog, root, 760, 720)

    kartu = tk.Frame(
        dialog, bg=c.CARD_BG, padx=40, pady=14,
        highlightthickness=1, highlightbackground=c.BORDER_COLOR,
    )
    kartu.pack(fill="both", expand=True, padx=20, pady=20)

    # --- Header ---
    tk.Label(kartu, text="Buat Akun Mahasiswa", font=c.FONT_HEADING,
             bg=c.CARD_BG, fg=c.TEXT_DARK).pack(anchor="w")
    tk.Label(kartu, text="Lengkapi data identitas dan akademik Anda di bawah ini.",
             font=c.FONT_BODY, bg=c.CARD_BG, fg=c.TEXT_MUTED,
             wraplength=500, justify="left").pack(anchor="w", pady=(4, 8))

    # ================= FORM =================
    in_nama = _kolom(kartu, c.CARD_BG, "Nama lengkap", lebar=44)
    in_nim = _kolom(kartu, c.CARD_BG, "NIM (9 digit angka)", lebar=44, nim=True)

    # Jurusan
    tk.Label(kartu, text="Jurusan", bg=c.CARD_BG, fg=c.TEXT_DARK,
             font=c.FONT_BOLD).pack(anchor="w", pady=(0, 6))
    pilih_jurusan = ttk.Combobox(kartu, state="readonly",
                                 style="Form.TCombobox", width=42)
    pilih_jurusan["values"] = [f"{j['nama_jurusan']} ({j['kode_jurusan']})"
                               for j in jurusan]
    pilih_jurusan.pack(fill="x", pady=(0, 10))

    # Program Studi
    tk.Label(kartu, text="Program studi", bg=c.CARD_BG, fg=c.TEXT_DARK,
             font=c.FONT_BOLD).pack(anchor="w", pady=(0, 6))
    pilih_prodi = ttk.Combobox(kartu, state="disabled",
                               style="Form.TCombobox", width=42)
    pilih_prodi.pack(fill="x", pady=(0, 10))
    prodi_rows = []

    # --- Hint Banner (Penempatan & Padding Diperbaiki) ---
    frame_hint = tk.Frame(kartu, bg="#F0E3D2", padx=12, pady=8)
    frame_hint.pack(fill="x", pady=(0, 4))
    tk.Label(
        frame_hint, text="🔒 NIM berfungsi sebagai pengganti password.\nSimpan baik-baik dan jangan dibagikan.",
        font=c.FONT_SMALL, bg="#F0E3D2", fg="#6B4423",
        justify="left", anchor="w"
    ).pack(fill="x")

    # --- Kotak Pesan Error/Sukses ---
    kotak_pesan, tampil = _buat_pesan(kartu, c.CARD_BG, lebar=420)
    kotak_pesan.pack(fill="x", pady=(0, 2))

    # ================= TOMBOL NAVIGASI =================
    # Menggunakan frame terpisah agar tombol tidak terdorong ke bawah
    tombol_nav = tk.Frame(kartu, bg=c.CARD_BG)
    tombol_nav.pack(fill="x", side="bottom", pady=(0, 0))
    
    ttk.Button(tombol_nav, text="Batal", style="Secondary.TButton",
               command=dialog.destroy).pack(side="left")
    ttk.Button(tombol_nav, text="Lanjutkan & Daftar  →", style="Primary.TButton",
               command=lambda: daftar()).pack(side="right")

    # ================= LOGIKA =================
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
            messagebox.showerror("Database tidak tersedia",
                                 PESAN_DB.format(err=err), parent=dialog)
            return
        pilih_prodi["values"] = [f"{p['nama_prodi']} ({p['jenjang']})"
                                 for p in prodi_rows]
        pilih_prodi.configure(state="readonly" if prodi_rows else "disabled")
        if not prodi_rows:
            tampil("Jurusan ini belum memiliki program studi.", "info")
        else:
            tampil("")

    pilih_jurusan.bind("<<ComboboxSelected>>", muat_prodi)

    def daftar(event=None):
        tampil("")
        
        # Validasi Kolom Kosong
        if not in_nama.get().strip() or not in_nim.get().strip():
            tampil("Nama dan NIM tidak boleh kosong.", "error")
            return
            
        # Validasi Panjang NIM (Wajib 9 Digit)
        if len(in_nim.get().strip()) != 9:
            tampil("NIM harus berisi tepat 9 digit angka.", "error")
            in_nim.focus_set()
            return
            
        if pilih_jurusan.current() < 0:
            tampil("Pilih jurusan terlebih dahulu.", "error")
            pilih_jurusan.focus_set()
            return
            
        if pilih_prodi.current() < 0 or not prodi_rows:
            tampil("Pilih program studi.", "error")
            pilih_prodi.focus_set()
            return

        # Eksekusi Pendaftaran
        try:
            nim = auth.registrasi_mahasiswa(
                in_nama.get(), in_nim.get(),
                prodi_rows[pilih_prodi.current()]["prodi_id"],
            )
        except AppError as err:
            tampil(str(err), "error")
            return
        except mysql.connector.IntegrityError as err:
            if err.errno == 1062:
                tampil("NIM sudah terdaftar di sistem.", "error")
                in_nim.focus_set()
            elif err.errno == 1048:
                tampil(
                    "Struktur database belum mendukung pendaftaran mandiri. "
                    "Jalankan database/migrate_student_public_registration.sql "
                    "pada database siakad.",
                    "error",
                )
            else:
                messagebox.showerror(
                    "Pendaftaran gagal",
                    f"Database menolak data pendaftaran.\n\n{err}",
                    parent=dialog,
                )
            return
        except mysql.connector.Error as err:
            messagebox.showerror("Database tidak tersedia",
                                 PESAN_DB.format(err=err), parent=dialog)
            return
            
        nama = " ".join(in_nama.get().split())
        dialog.destroy()
        setelah_daftar(nim, nama)

    dialog.bind("<Return>", daftar)
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    dialog.grab_set()
    in_nama.focus_set()
