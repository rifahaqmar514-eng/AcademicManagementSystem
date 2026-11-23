import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from assets.colors import (
    BG_COLOR,
    CARD_BG,
    TEXT_DARK,
    PRIMARY_COLOR,
    ACCENT_COLOR
)

# Fungsi backend yang diasumsikan
#   get_all_prodi()        -> list of (prodi_id, kode_prodi, nama_prodi, jenjang)
#   get_all_mahasiswa()    -> list of (mahasiswa_id, nim, nama_lengkap, prodi_id, nama_prodi,
#                                      jenis_kelamin, tanggal_lahir, angkatan, status_mahasiswa)
#   tambah_mahasiswa(prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir, angkatan, status)
#   update_mahasiswa(mahasiswa_id, prodi_id, nim, nama_lengkap, jenis_kelamin, tanggal_lahir, angkatan, status)
#   hapus_mahasiswa(mahasiswa_id)
from backend.mahasiswa import (
    get_all_prodi,
    get_all_mahasiswa,
    tambah_mahasiswa,
    update_mahasiswa,
    hapus_mahasiswa
)

# Sesuaikan dengan isi enum status_mahasiswa di database
STATUS_LIST = ["Aktif", "Cuti", "Lulus", "Non-Aktif"]
JK_LIST = ["L", "P"]


class MahasiswaPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)
        self.selected_id = None
        self.prodi_map = {}  # "KODE - Nama (Jenjang)" -> prodi_id
        self._build_ui()
        self.load_prodi()
        self.load_data()

    # ---------- UI ----------
    def _build_ui(self):
        tk.Label(
            self, text="Data Mahasiswa",
            font=("Arial", 20, "bold"), bg=BG_COLOR, fg=TEXT_DARK
        ).pack(pady=(15, 10))

        form = tk.Frame(self, bg=CARD_BG, padx=15, pady=15)
        form.pack(fill="x", padx=20)

        self.nim_var = tk.StringVar()
        self.nama_var = tk.StringVar()
        self.prodi_var = tk.StringVar()
        self.jk_var = tk.StringVar()
        self.tgl_var = tk.StringVar()
        self.angkatan_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Aktif")

        def add_row(row, label, widget):
            tk.Label(
                form, text=label, font=("Arial", 11),
                bg=CARD_BG, fg=TEXT_DARK
            ).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, padx=10, pady=4, sticky="w")

        add_row(0, "NIM", tk.Entry(form, textvariable=self.nim_var, font=("Arial", 11), width=30))
        add_row(1, "Nama Lengkap", tk.Entry(form, textvariable=self.nama_var, font=("Arial", 11), width=30))
        self.prodi_combo = ttk.Combobox(
            form, textvariable=self.prodi_var, state="readonly", font=("Arial", 11), width=28)
        add_row(2, "Program Studi", self.prodi_combo)
        add_row(3, "Jenis Kelamin", ttk.Combobox(
            form, textvariable=self.jk_var, values=JK_LIST, state="readonly", font=("Arial", 11), width=5))
        add_row(4, "Tanggal Lahir", tk.Entry(form, textvariable=self.tgl_var, font=("Arial", 11), width=15))
        tk.Label(form, text="(YYYY-MM-DD)", font=("Arial", 9), bg=CARD_BG, fg=TEXT_DARK
                 ).grid(row=4, column=2, sticky="w")
        add_row(5, "Angkatan", tk.Entry(form, textvariable=self.angkatan_var, font=("Arial", 11), width=10))
        add_row(6, "Status", ttk.Combobox(
            form, textvariable=self.status_var, values=STATUS_LIST, state="readonly", font=("Arial", 11), width=12))

        btn_frame = tk.Frame(form, bg=CARD_BG)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        self._button(btn_frame, "Tambah", self.on_tambah, PRIMARY_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Update", self.on_update, ACCENT_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Hapus", self.on_hapus, "#c0392b").pack(side="left", padx=4)
        self._button(btn_frame, "Bersihkan", self.clear_form, "#7f8c8d").pack(side="left", padx=4)

        # Pencarian
        search_frame = tk.Frame(self, bg=BG_COLOR)
        search_frame.pack(fill="x", padx=20, pady=(12, 4))
        tk.Label(
            search_frame, text="Cari (NIM/Nama):",
            font=("Arial", 11), bg=BG_COLOR, fg=TEXT_DARK
        ).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.load_data())
        tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 11), width=25
                 ).pack(side="left", padx=8)

        # Tabel
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(4, 15))

        cols = ("nim", "nama", "prodi", "jk", "tgl", "angkatan", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        heads = {"nim": "NIM", "nama": "Nama", "prodi": "Prodi", "jk": "JK",
                 "tgl": "Tgl Lahir", "angkatan": "Angkatan", "status": "Status"}
        widths = {"nim": 100, "nama": 170, "prodi": 150, "jk": 40,
                  "tgl": 90, "angkatan": 70, "status": 80}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def _button(self, parent, text, command, color):
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", 10), bg=color, fg="white",
            relief="flat", padx=12, pady=4, cursor="hand2"
        )

    # ---------- Data ----------
    def load_prodi(self):
        try:
            data = get_all_prodi()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat program studi: {e}")
            return
        self.prodi_map = {
            f"{kode} - {nama} ({jenjang})": prodi_id
            for prodi_id, kode, nama, jenjang in data
        }
        self.prodi_combo["values"] = list(self.prodi_map.keys())

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip().lower()
        try:
            data = get_all_mahasiswa()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data: {e}")
            return

        for (mhs_id, nim, nama, prodi_id, nama_prodi,
             jk, tgl, angkatan, status) in data:
            if keyword and keyword not in str(nim).lower() and keyword not in str(nama).lower():
                continue
            # iid = mahasiswa_id; prodi_id disimpan di tag agar bisa dipakai saat edit
            self.tree.insert(
                "", "end", iid=str(mhs_id), tags=(str(prodi_id),),
                values=(nim, nama, nama_prodi, jk, str(tgl), angkatan, status)
            )

    def clear_form(self):
        self.selected_id = None
        for var in (self.nim_var, self.nama_var, self.prodi_var,
                    self.jk_var, self.tgl_var, self.angkatan_var):
            var.set("")
        self.status_var.set("Aktif")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = selected[0]
        nim, nama, nama_prodi, jk, tgl, angkatan, status = self.tree.item(self.selected_id, "values")
        prodi_id = int(self.tree.item(self.selected_id, "tags")[0])

        self.nim_var.set(nim)
        self.nama_var.set(nama)
        for label, pid in self.prodi_map.items():
            if pid == prodi_id:
                self.prodi_var.set(label)
                break
        self.jk_var.set(jk)
        self.tgl_var.set(tgl)
        self.angkatan_var.set(angkatan)
        self.status_var.set(status)

    def _validate(self):
        nim = self.nim_var.get().strip()
        nama = self.nama_var.get().strip()
        prodi_label = self.prodi_var.get()
        jk = self.jk_var.get()
        tgl = self.tgl_var.get().strip()
        angkatan = self.angkatan_var.get().strip()
        status = self.status_var.get()

        if not (nim and nama and prodi_label and jk and tgl and angkatan and status):
            messagebox.showwarning("Peringatan", "Semua field harus diisi.")
            return None
        try:
            datetime.strptime(tgl, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Peringatan", "Format tanggal lahir harus YYYY-MM-DD.")
            return None
        if not angkatan.isdigit() or not (1990 <= int(angkatan) <= 2100):
            messagebox.showwarning("Peringatan", "Angkatan harus berupa tahun antara 1990 dan 2100.")
            return None

        return (self.prodi_map[prodi_label], nim, nama, jk, tgl, int(angkatan), status)

    # ---------- Aksi ----------
    def on_tambah(self):
        data = self._validate()
        if not data:
            return
        try:
            tambah_mahasiswa(*data)
            messagebox.showinfo("Sukses", "Data mahasiswa berhasil ditambahkan.")
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menambah data (NIM mungkin sudah ada): {e}")

    def on_update(self):
        if not self.selected_id:
            messagebox.showwarning("Peringatan", "Pilih data di tabel terlebih dahulu.")
            return
        data = self._validate()
        if not data:
            return
        try:
            update_mahasiswa(int(self.selected_id), *data)
            messagebox.showinfo("Sukses", "Data mahasiswa berhasil diperbarui.")
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memperbarui data: {e}")

    def on_hapus(self):
        if not self.selected_id:
            messagebox.showwarning("Peringatan", "Pilih data di tabel terlebih dahulu.")
            return
        if not messagebox.askyesno(
            "Konfirmasi",
            "Hapus mahasiswa ini? Data nilainya mungkin ikut terhapus atau penghapusan ditolak "
            "tergantung aturan foreign key."
        ):
            return
        try:
            hapus_mahasiswa(int(self.selected_id))
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {e}")


# Untuk menjalankan halaman 
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Data Mahasiswa - SIAKAD")
    window.geometry("780x720")
    window.configure(bg=BG_COLOR)
    MahasiswaPage(window).pack(fill="both", expand=True)
    window.mainloop()