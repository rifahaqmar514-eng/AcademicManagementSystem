import tkinter as tk
from tkinter import ttk, messagebox

from assets.colors import (
    BG_COLOR,
    CARD_BG,
    TEXT_DARK,
    PRIMARY_COLOR,
    ACCENT_COLOR
)

# Fungsi backend yang diasumsikan:
#   get_all_mahasiswa()                              
#   tambah_mahasiswa(nim, nama, prodi, angkatan)
#   update_mahasiswa(nim, nama, prodi, angkatan)
#   hapus_mahasiswa(nim)
from backend.mahasiswa import (
    get_all_mahasiswa,
    tambah_mahasiswa,
    update_mahasiswa,
    hapus_mahasiswa
)


class MahasiswaPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)
        self.selected_nim = None
        self._build_ui()
        self.load_data()

    # ---------- UI ----------
    def _build_ui(self):
        tk.Label(
            self, text="Data Mahasiswa",
            font=("Arial", 20, "bold"), bg=BG_COLOR, fg=TEXT_DARK
        ).pack(pady=(15, 10))

        # Form input
        form = tk.Frame(self, bg=CARD_BG, padx=15, pady=15)
        form.pack(fill="x", padx=20)

        self.nim_var = tk.StringVar()
        self.nama_var = tk.StringVar()
        self.prodi_var = tk.StringVar()
        self.angkatan_var = tk.StringVar()

        fields = [
            ("NIM", self.nim_var),
            ("Nama", self.nama_var),
            ("Program Studi", self.prodi_var),
            ("Angkatan", self.angkatan_var),
        ]
        for i, (label, var) in enumerate(fields):
            tk.Label(
                form, text=label, font=("Arial", 11),
                bg=CARD_BG, fg=TEXT_DARK
            ).grid(row=i, column=0, sticky="w", pady=4)
            entry = tk.Entry(form, textvariable=var, font=("Arial", 11), width=30)
            entry.grid(row=i, column=1, padx=10, pady=4, sticky="w")
            if label == "NIM":
                self.nim_entry = entry

        # Tombol aksi
        btn_frame = tk.Frame(form, bg=CARD_BG)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))

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
        tk.Entry(
            search_frame, textvariable=self.search_var, font=("Arial", 11), width=25
        ).pack(side="left", padx=8)

        # Tabel
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(4, 15))

        cols = ("nim", "nama", "prodi", "angkatan")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        headings = {"nim": "NIM", "nama": "Nama", "prodi": "Program Studi", "angkatan": "Angkatan"}
        widths = {"nim": 110, "nama": 200, "prodi": 180, "angkatan": 80}
        for c in cols:
            self.tree.heading(c, text=headings[c])
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
    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip().lower()
        try:
            data = get_all_mahasiswa()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data: {e}")
            return

        for nim, nama, prodi, angkatan in data:
            if keyword and keyword not in str(nim).lower() and keyword not in str(nama).lower():
                continue
            self.tree.insert("", "end", values=(nim, nama, prodi, angkatan))

    def clear_form(self):
        self.selected_nim = None
        for var in (self.nim_var, self.nama_var, self.prodi_var, self.angkatan_var):
            var.set("")
        self.nim_entry.config(state="normal")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        nim, nama, prodi, angkatan = self.tree.item(selected[0], "values")
        self.selected_nim = nim
        self.nim_var.set(nim)
        self.nama_var.set(nama)
        self.prodi_var.set(prodi)
        self.angkatan_var.set(angkatan)
        self.nim_entry.config(state="disabled")  # NIM tidak boleh diubah saat edit

    def _validate(self):
        nim = self.nim_var.get().strip()
        nama = self.nama_var.get().strip()
        prodi = self.prodi_var.get().strip()
        angkatan = self.angkatan_var.get().strip()

        if not (nim and nama and prodi and angkatan):
            messagebox.showwarning("Peringatan", "Semua field harus diisi.")
            return None
        if not angkatan.isdigit() or len(angkatan) != 4:
            messagebox.showwarning("Peringatan", "Angkatan harus berupa tahun 4 digit, contoh 2024.")
            return None
        return nim, nama, prodi, angkatan

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
            messagebox.showerror("Error", f"Gagal menambah data: {e}")

    def on_update(self):
        if not self.selected_nim:
            messagebox.showwarning("Peringatan", "Pilih data di tabel terlebih dahulu.")
            return
        data = self._validate()
        if not data:
            return
        try:
            update_mahasiswa(self.selected_nim, *data[1:])
            messagebox.showinfo("Sukses", "Data mahasiswa berhasil diperbarui.")
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memperbarui data: {e}")

    def on_hapus(self):
        if not self.selected_nim:
            messagebox.showwarning("Peringatan", "Pilih data di tabel terlebih dahulu.")
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus mahasiswa dengan NIM {self.selected_nim}?"):
            return
        try:
            hapus_mahasiswa(self.selected_nim)
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {e}")


# Untuk menjalankan halaman ini secara mandiri (testing)
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Data Mahasiswa - SIAKAD")
    window.geometry("700x600")
    window.configure(bg=BG_COLOR)
    MahasiswaPage(window).pack(fill="both", expand=True)
    window.mainloop()
