import re
import tkinter as tk
from tkinter import ttk, messagebox

from assets.colors import (
    BG_COLOR,
    CARD_BG,
    TEXT_DARK,
    PRIMARY_COLOR,
    ACCENT_COLOR
)

# Fungsi backend yang diasumsikan di backend/master.py (sesuaikan dengan backend kamu).
# Setiap get_* mengembalikan baris dengan urutan: (id, field1, field2, ...)
# sesuai urutan field pada konfigurasi tab di bawah.
#
#   get_all_prodi()    -> (prodi_id, kode_prodi, nama_prodi, jenjang)
#   tambah_prodi(kode_prodi, nama_prodi, jenjang)
#   update_prodi(prodi_id, kode_prodi, nama_prodi, jenjang)
#   hapus_prodi(prodi_id)
#
#   get_all_mk()       -> (mk_id, kode_mk, nama_mk, sks)
#   tambah_mk(kode_mk, nama_mk, sks) / update_mk(mk_id, ...) / hapus_mk(mk_id)
#
#   get_all_semester() -> (semester_id, kode_semester, tahun_akademik, jenis)
#   tambah_semester(kode_semester, tahun_akademik, jenis) / update_semester(semester_id, ...) / hapus_semester(semester_id)
#
#   get_all_skala()    -> (skala_id, huruf_mutu, bobot_mutu, nilai_min, nilai_max, is_lulus)
#   tambah_skala(huruf_mutu, bobot_mutu, nilai_min, nilai_max, is_lulus)
#   update_skala(skala_id, ...) / hapus_skala(skala_id)
from backend.master import (
    get_all_prodi, tambah_prodi, update_prodi, hapus_prodi,
    get_all_mk, tambah_mk, update_mk, hapus_mk,
    get_all_semester, tambah_semester, update_semester, hapus_semester,
    get_all_skala, tambah_skala, update_skala, hapus_skala,
)

JENJANG_LIST = ["D3", "D4", "S1", "S2", "S3"]
JENIS_SEMESTER_LIST = ["Ganjil", "Genap", "Pendek"]
YA_TIDAK = ["Ya", "Tidak"]


# ---------- Parser validasi (raise ValueError dengan pesan singkat) ----------
def parse_text(v):
    v = v.strip()
    if not v:
        raise ValueError("tidak boleh kosong")
    return v


def parse_int_range(lo, hi):
    def parser(v):
        try:
            n = int(v.strip())
        except ValueError:
            raise ValueError("harus berupa bilangan bulat")
        if not lo <= n <= hi:
            raise ValueError(f"harus antara {lo} dan {hi}")
        return n
    return parser


def parse_decimal_range(lo, hi):
    def parser(v):
        try:
            n = float(v.strip().replace(",", "."))
        except ValueError:
            raise ValueError("harus berupa angka")
        if not lo <= n <= hi:
            raise ValueError(f"harus antara {lo} dan {hi}")
        return n
    return parser


def parse_regex(pattern, hint):
    def parser(v):
        v = v.strip()
        if not re.fullmatch(pattern, v):
            raise ValueError(hint)
        return v
    return parser


def parse_choice(values):
    def parser(v):
        if v not in values:
            raise ValueError("wajib dipilih")
        return v
    return parser


def parse_ya_tidak(v):
    if v not in YA_TIDAK:
        raise ValueError("wajib dipilih")
    return v == "Ya"


def parse_huruf(v):
    v = v.strip().upper()
    if not re.fullmatch(r"[A-E][A-E+\-]?", v):
        raise ValueError("huruf mutu A sampai E, contoh A atau AB")
    return v


def show_ya_tidak(v):
    return "Ya" if v in (True, 1, "1", "Ya") else "Tidak"


# ---------- Tab CRUD generik ----------
class MasterTab(tk.Frame):
    """
    fields: list of dict dengan kunci:
        key, label, width (kolom tabel), kind ("entry" / "combo"),
        values (untuk combo), parse (callable), show (callable, opsional), hint (opsional)
    """

    def __init__(self, parent, fields, get_rows, add, update, delete, validate=None):
        super().__init__(parent, bg=BG_COLOR)
        self.fields = fields
        self.get_rows = get_rows
        self.add = add
        self.update_fn = update
        self.delete = delete
        self.validate = validate
        self.selected_id = None
        self.vars = {}
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        form = tk.Frame(self, bg=CARD_BG, padx=15, pady=15)
        form.pack(fill="x", padx=15, pady=(15, 8))

        for i, f in enumerate(self.fields):
            var = tk.StringVar()
            self.vars[f["key"]] = var
            tk.Label(form, text=f["label"], font=("Arial", 11),
                     bg=CARD_BG, fg=TEXT_DARK).grid(row=i, column=0, sticky="w", pady=4)
            if f.get("kind") == "combo":
                widget = ttk.Combobox(form, textvariable=var, values=f["values"],
                                      state="readonly", font=("Arial", 11), width=18)
            else:
                widget = tk.Entry(form, textvariable=var, font=("Arial", 11), width=30)
            widget.grid(row=i, column=1, padx=10, pady=4, sticky="w")
            if f.get("hint"):
                tk.Label(form, text=f["hint"], font=("Arial", 9),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=i, column=2, sticky="w")

        btn_frame = tk.Frame(form, bg=CARD_BG)
        btn_frame.grid(row=len(self.fields), column=0, columnspan=3, pady=(10, 0))
        self._button(btn_frame, "Tambah", self.on_tambah, PRIMARY_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Update", self.on_update, ACCENT_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Hapus", self.on_hapus, "#c0392b").pack(side="left", padx=4)
        self._button(btn_frame, "Bersihkan", self.clear_form, "#7f8c8d").pack(side="left", padx=4)

        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        cols = [f["key"] for f in self.fields]
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for f in self.fields:
            self.tree.heading(f["key"], text=f["label"])
            self.tree.column(f["key"], width=f.get("width", 120), anchor="w")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def _button(self, parent, text, command, color):
        return tk.Button(parent, text=text, command=command,
                         font=("Arial", 10), bg=color, fg="white",
                         relief="flat", padx=12, pady=4, cursor="hand2")

    # ---------- Data ----------
    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = self.get_rows()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data: {e}")
            return
        for row in rows:
            row_id, values = row[0], row[1:]
            shown = []
            for f, v in zip(self.fields, values):
                shown.append(f["show"](v) if "show" in f else str(v))
            self.tree.insert("", "end", iid=str(row_id), values=shown)

    def clear_form(self):
        self.selected_id = None
        for var in self.vars.values():
            var.set("")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = selected[0]
        values = self.tree.item(self.selected_id, "values")
        for f, v in zip(self.fields, values):
            self.vars[f["key"]].set(v)

    def _read(self):
        parsed = {}
        for f in self.fields:
            try:
                parsed[f["key"]] = f["parse"](self.vars[f["key"]].get())
            except ValueError as e:
                messagebox.showwarning("Peringatan", f"{f['label']}: {e}")
                return None
        if self.validate:
            err = self.validate(parsed)
            if err:
                messagebox.showwarning("Peringatan", err)
                return None
        return [parsed[f["key"]] for f in self.fields]

    # ---------- Aksi ----------
    def on_tambah(self):
        values = self._read()
        if values is None:
            return
        try:
            self.add(*values)
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menambah data (kode mungkin sudah ada): {e}")

    def on_update(self):
        if not self.selected_id:
            messagebox.showwarning("Peringatan", "Pilih data di tabel terlebih dahulu.")
            return
        values = self._read()
        if values is None:
            return
        try:
            self.update_fn(int(self.selected_id), *values)
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
            "Hapus data ini? Jika sudah dipakai di data lain (mahasiswa/nilai), "
            "penghapusan akan ditolak oleh database."
        ):
            return
        try:
            self.delete(int(self.selected_id))
            self.clear_form()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus data: {e}")


# ---------- Validasi lintas field ----------
def validate_skala(v):
    if v["nilai_min"] >= v["nilai_max"]:
        return "Nilai min harus lebih kecil dari nilai max."
    return None


# ---------- Halaman utama ----------
class AkademikMasterPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)

        tk.Label(self, text="Master Data Akademik",
                 font=("Arial", 20, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(pady=(15, 5))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        notebook.add(MasterTab(
            notebook,
            fields=[
                {"key": "kode_prodi", "label": "Kode Prodi", "width": 100, "parse": parse_text},
                {"key": "nama_prodi", "label": "Nama Prodi", "width": 250, "parse": parse_text},
                {"key": "jenjang", "label": "Jenjang", "width": 80, "kind": "combo",
                 "values": JENJANG_LIST, "parse": parse_choice(JENJANG_LIST)},
            ],
            get_rows=get_all_prodi, add=tambah_prodi, update=update_prodi, delete=hapus_prodi,
        ), text="Program Studi")

        notebook.add(MasterTab(
            notebook,
            fields=[
                {"key": "kode_mk", "label": "Kode MK", "width": 100, "parse": parse_text},
                {"key": "nama_mk", "label": "Nama Mata Kuliah", "width": 250, "parse": parse_text},
                {"key": "sks", "label": "SKS", "width": 60,
                 "parse": parse_int_range(1, 6), "hint": "1 sampai 6"},
            ],
            get_rows=get_all_mk, add=tambah_mk, update=update_mk, delete=hapus_mk,
        ), text="Mata Kuliah")

        notebook.add(MasterTab(
            notebook,
            fields=[
                {"key": "kode_semester", "label": "Kode Semester", "width": 110,
                 "parse": parse_regex(r"\d{5}", "5 digit, contoh 20251"), "hint": "contoh 20251"},
                {"key": "tahun_akademik", "label": "Tahun Akademik", "width": 130,
                 "parse": parse_regex(r"\d{4}/\d{4}", "format YYYY/YYYY"), "hint": "contoh 2025/2026"},
                {"key": "jenis", "label": "Jenis", "width": 90, "kind": "combo",
                 "values": JENIS_SEMESTER_LIST, "parse": parse_choice(JENIS_SEMESTER_LIST)},
            ],
            get_rows=get_all_semester, add=tambah_semester,
            update=update_semester, delete=hapus_semester,
        ), text="Semester")

        notebook.add(MasterTab(
            notebook,
            fields=[
                {"key": "huruf_mutu", "label": "Huruf Mutu", "width": 80, "parse": parse_huruf},
                {"key": "bobot_mutu", "label": "Bobot Mutu", "width": 90,
                 "parse": parse_decimal_range(0, 4), "hint": "0 sampai 4"},
                {"key": "nilai_min", "label": "Nilai Min", "width": 80,
                 "parse": parse_decimal_range(0, 100)},
                {"key": "nilai_max", "label": "Nilai Max", "width": 80,
                 "parse": parse_decimal_range(0, 100)},
                {"key": "is_lulus", "label": "Lulus", "width": 60, "kind": "combo",
                 "values": YA_TIDAK, "parse": parse_ya_tidak, "show": show_ya_tidak},
            ],
            get_rows=get_all_skala, add=tambah_skala, update=update_skala, delete=hapus_skala,
            validate=validate_skala,
        ), text="Skala Nilai")


# Untuk menjalankan halaman 
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Master Data Akademik - SIAKAD")
    window.geometry("760x640")
    window.configure(bg=BG_COLOR)
    AkademikMasterPage(window).pack(fill="both", expand=True)
  
    window.mainloop()
