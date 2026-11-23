import tkinter as tk
from tkinter import ttk, messagebox

from assets.colors import (
    BG_COLOR,
    CARD_BG,
    TEXT_DARK,
    PRIMARY_COLOR,
    ACCENT_COLOR
)

# Fungsi backend yang diasumsikan
#   get_all_mahasiswa()  -> list of (mahasiswa_id, nim, nama_lengkap, ...)   [backend.mahasiswa]
#   get_all_mk()         -> list of (mk_id, kode_mk, nama_mk, sks)
#   get_all_semester()   -> list of (semester_id, kode_semester, tahun_akademik, jenis)
#   get_skala_nilai()    -> list of (huruf_mutu, bobot_mutu, nilai_min, nilai_max, is_lulus)
#   get_nilai_by_mahasiswa(mahasiswa_id)
#        -> list of (nilai_id, mk_id, kode_mk, nama_mk, sks, semester_id, kode_semester,
#                    nilai_tugas, nilai_uts, nilai_uas, nilai_akhir)
#   tambah_nilai(mahasiswa_id, mk_id, semester_id, tugas, uts, uas, nilai_akhir)
#   update_nilai(nilai_id, mk_id, semester_id, tugas, uts, uas, nilai_akhir)
#   hapus_nilai(nilai_id)
from backend.mahasiswa import get_all_mahasiswa
from backend.nilai import (
    get_all_mk,
    get_all_semester,
    get_skala_nilai,
    get_nilai_by_mahasiswa,
    tambah_nilai,
    update_nilai,
    hapus_nilai
)

# Bobot nilai akhir
BOBOT_TUGAS, BOBOT_UTS, BOBOT_UAS = 0.30, 0.30, 0.40

# Kebijakan mata kuliah yang diulang pada perhitungan IPK:
#   True  -> hanya nilai terbaik per mata kuliah yang dihitung
#   False -> semua percobaan dihitung
IPK_PAKAI_NILAI_TERBAIK = True


def hitung_nilai_akhir(tugas, uts, uas):
    return round(tugas * BOBOT_TUGAS + uts * BOBOT_UTS + uas * BOBOT_UAS, 2)


def hitung_rata(daftar):
    """daftar: list of (sks, bobot_mutu). Return IP/IPK (0.0 jika kosong)."""
    total_sks = sum(sks for sks, _ in daftar)
    if total_sks == 0:
        return 0.0
    return sum(sks * bobot for sks, bobot in daftar) / total_sks


class NilaiPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)
        self.selected_id = None
        self.current_mhs_id = None
        self.mahasiswa_map = {}   # "NIM - Nama" -> mahasiswa_id
        self.mk_map = {}          # "KODE - Nama (n SKS)" -> (mk_id, sks)
        self.semester_map = {}    # "20251 - 2025/2026 Ganjil" -> semester_id
        self.skala = []           # list (huruf, bobot, min, max, is_lulus), urut nilai_min turun
        self.rows = {}            # nilai_id -> row dari backend
        self._build_ui()
        self.load_referensi()

    # ---------- UI ----------
    def _build_ui(self):
        tk.Label(
            self, text="Input Nilai & IPK",
            font=("Arial", 20, "bold"), bg=BG_COLOR, fg=TEXT_DARK
        ).pack(pady=(15, 10))

        pilih = tk.Frame(self, bg=BG_COLOR)
        pilih.pack(fill="x", padx=20)
        tk.Label(pilih, text="Mahasiswa:", font=("Arial", 11),
                 bg=BG_COLOR, fg=TEXT_DARK).pack(side="left")
        self.mhs_var = tk.StringVar()
        self.mhs_combo = ttk.Combobox(
            pilih, textvariable=self.mhs_var, state="readonly",
            font=("Arial", 11), width=45)
        self.mhs_combo.pack(side="left", padx=10)
        self.mhs_combo.bind("<<ComboboxSelected>>", self.on_pilih_mahasiswa)

        # Form nilai
        form = tk.Frame(self, bg=CARD_BG, padx=15, pady=15)
        form.pack(fill="x", padx=20, pady=10)

        self.mk_var = tk.StringVar()
        self.semester_var = tk.StringVar()
        self.tugas_var = tk.StringVar()
        self.uts_var = tk.StringVar()
        self.uas_var = tk.StringVar()
        for var in (self.tugas_var, self.uts_var, self.uas_var):
            var.trace_add("write", lambda *_: self.update_preview())

        def add_row(row, label, widget):
            tk.Label(form, text=label, font=("Arial", 11),
                     bg=CARD_BG, fg=TEXT_DARK).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, padx=10, pady=4, sticky="w")

        self.mk_combo = ttk.Combobox(
            form, textvariable=self.mk_var, state="readonly", font=("Arial", 11), width=40)
        self.semester_combo = ttk.Combobox(
            form, textvariable=self.semester_var, state="readonly", font=("Arial", 11), width=40)
        add_row(0, "Mata Kuliah", self.mk_combo)
        add_row(1, "Semester", self.semester_combo)
        add_row(2, "Nilai Tugas (30%)", tk.Entry(form, textvariable=self.tugas_var, font=("Arial", 11), width=10))
        add_row(3, "Nilai UTS (30%)", tk.Entry(form, textvariable=self.uts_var, font=("Arial", 11), width=10))
        add_row(4, "Nilai UAS (40%)", tk.Entry(form, textvariable=self.uas_var, font=("Arial", 11), width=10))

        self.preview_label = tk.Label(
            form, text="Nilai akhir: -  |  Huruf: -  |  Bobot: -",
            font=("Arial", 11, "bold"), bg=CARD_BG, fg=PRIMARY_COLOR)
        self.preview_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        btn_frame = tk.Frame(form, bg=CARD_BG)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        self._button(btn_frame, "Tambah", self.on_tambah, PRIMARY_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Update", self.on_update, ACCENT_COLOR).pack(side="left", padx=4)
        self._button(btn_frame, "Hapus", self.on_hapus, "#c0392b").pack(side="left", padx=4)
        self._button(btn_frame, "Bersihkan", self.clear_form, "#7f8c8d").pack(side="left", padx=4)

        # Tabel nilai
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=20)

        cols = ("smt", "kode", "mk", "sks", "tugas", "uts", "uas", "akhir", "huruf", "bobot")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        heads = {"smt": "Smt", "kode": "Kode", "mk": "Mata Kuliah", "sks": "SKS",
                 "tugas": "Tugas", "uts": "UTS", "uas": "UAS",
                 "akhir": "Akhir", "huruf": "Huruf", "bobot": "Bobot"}
        widths = {"smt": 60, "kode": 70, "mk": 190, "sks": 40, "tugas": 50,
                  "uts": 50, "uas": 50, "akhir": 55, "huruf": 50, "bobot": 50}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="w" if c == "mk" else "center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Ringkasan IPK
        summary = tk.Frame(self, bg=CARD_BG, padx=15, pady=10)
        summary.pack(fill="x", padx=20, pady=15)
        self.total_sks_label = tk.Label(
            summary, text="Total SKS: 0", font=("Arial", 12), bg=CARD_BG, fg=TEXT_DARK)
        self.total_sks_label.grid(row=0, column=0, sticky="w", padx=(0, 30))
        self.ipk_label = tk.Label(
            summary, text="IPK: 0.00", font=("Arial", 16, "bold"), bg=CARD_BG, fg=PRIMARY_COLOR)
        self.ipk_label.grid(row=0, column=1, sticky="w")
        self.ips_label = tk.Label(
            summary, text="IPS: -", font=("Arial", 10), bg=CARD_BG, fg=TEXT_DARK,
            justify="left", wraplength=600)
        self.ips_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _button(self, parent, text, command, color):
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", 10), bg=color, fg="white",
            relief="flat", padx=12, pady=4, cursor="hand2"
        )

    # ---------- Data referensi ----------
    def load_referensi(self):
        try:
            mhs = get_all_mahasiswa()
            mk = get_all_mk()
            smt = get_all_semester()
            skala = get_skala_nilai()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data referensi: {e}")
            return

        self.mahasiswa_map = {f"{row[1]} - {row[2]}": row[0] for row in mhs}
        self.mk_map = {f"{kode} - {nama} ({sks} SKS)": (mk_id, sks)
                       for mk_id, kode, nama, sks in mk}
        self.semester_map = {f"{kode} - {tahun} {jenis}": sid
                             for sid, kode, tahun, jenis in smt}
        # urut dari nilai_min terbesar agar pencarian huruf mudah
        self.skala = sorted(
            [(h, float(b), float(mn), float(mx), lulus) for h, b, mn, mx, lulus in skala],
            key=lambda x: x[2], reverse=True)

        self.mhs_combo["values"] = list(self.mahasiswa_map.keys())
        self.mk_combo["values"] = list(self.mk_map.keys())
        self.semester_combo["values"] = list(self.semester_map.keys())

    def konversi(self, nilai_akhir):
        """Return (huruf, bobot) berdasarkan tabel skala_nilai."""
        for huruf, bobot, nilai_min, _nilai_max, _lulus in self.skala:
            if nilai_akhir >= nilai_min:
                return huruf, bobot
        return "-", 0.0

    # ---------- Data nilai ----------
    def on_pilih_mahasiswa(self, _event=None):
        self.current_mhs_id = self.mahasiswa_map.get(self.mhs_var.get())
        self.clear_form()
        self.load_nilai()

    def load_nilai(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.rows = {}
        if not self.current_mhs_id:
            return

        try:
            data = get_nilai_by_mahasiswa(self.current_mhs_id)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat nilai: {e}")
            return

        entries = []  # (mk_id, semester_kode, sks, bobot)
        for (nilai_id, mk_id, kode_mk, nama_mk, sks, semester_id, kode_smt,
             tugas, uts, uas, akhir) in data:
            huruf, bobot = self.konversi(float(akhir))
            self.rows[str(nilai_id)] = (mk_id, semester_id)
            self.tree.insert(
                "", "end", iid=str(nilai_id),
                values=(kode_smt, kode_mk, nama_mk, sks, tugas, uts, uas,
                        f"{float(akhir):.2f}", huruf, f"{bobot:.1f}"))
            entries.append((mk_id, kode_smt, int(sks), bobot))

        self.update_ringkasan(entries)

    def update_ringkasan(self, entries):
        # IPK
        if IPK_PAKAI_NILAI_TERBAIK:
            terbaik = {}
            for mk_id, _smt, sks, bobot in entries:
                if mk_id not in terbaik or bobot > terbaik[mk_id][1]:
                    terbaik[mk_id] = (sks, bobot)
            ipk_data = list(terbaik.values())
        else:
            ipk_data = [(sks, bobot) for _mk, _smt, sks, bobot in entries]

        total_sks = sum(sks for sks, _ in ipk_data)
        self.total_sks_label.config(text=f"Total SKS: {total_sks}")
        self.ipk_label.config(text=f"IPK: {hitung_rata(ipk_data):.2f}")

        # IPS per semester
        per_smt = {}
        for _mk, smt, sks, bobot in entries:
            per_smt.setdefault(smt, []).append((sks, bobot))
        if per_smt:
            teks = "  |  ".join(
                f"{smt}: {hitung_rata(d):.2f}" for smt, d in sorted(per_smt.items()))
            self.ips_label.config(text=f"IPS per semester -> {teks}")
        else:
            self.ips_label.config(text="IPS: -")

    # ---------- Form ----------
    def _baca_nilai(self):
        """Return (tugas, uts, uas) float, atau None jika belum valid."""
        try:
            nilai = tuple(float(v.get().replace(",", "."))
                          for v in (self.tugas_var, self.uts_var, self.uas_var))
        except ValueError:
            return None
        if any(n < 0 or n > 100 for n in nilai):
            return None
        return nilai

    def update_preview(self):
        nilai = self._baca_nilai()
        if not nilai:
            self.preview_label.config(text="Nilai akhir: -  |  Huruf: -  |  Bobot: -")
            return
        akhir = hitung_nilai_akhir(*nilai)
        huruf, bobot = self.konversi(akhir)
        self.preview_label.config(
            text=f"Nilai akhir: {akhir:.2f}  |  Huruf: {huruf}  |  Bobot: {bobot:.1f}")

    def clear_form(self):
        self.selected_id = None
        for var in (self.mk_var, self.semester_var, self.tugas_var, self.uts_var, self.uas_var):
            var.set("")
        self.tree.selection_remove(self.tree.selection())

    def on_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        self.selected_id = selected[0]
        mk_id, semester_id = self.rows[self.selected_id]
        _smt, _kode, _mk, _sks, tugas, uts, uas, _akhir, _huruf, _bobot = \
            self.tree.item(self.selected_id, "values")

        for label, (mid, _sks) in self.mk_map.items():
            if mid == mk_id:
                self.mk_var.set(label)
                break
        for label, sid in self.semester_map.items():
            if sid == semester_id:
                self.semester_var.set(label)
                break
        self.tugas_var.set(tugas)
        self.uts_var.set(uts)
        self.uas_var.set(uas)

    def _validate(self):
        if not self.current_mhs_id:
            messagebox.showwarning("Peringatan", "Pilih mahasiswa terlebih dahulu.")
            return None
        if not self.mk_var.get() or not self.semester_var.get():
            messagebox.showwarning("Peringatan", "Pilih mata kuliah dan semester.")
            return None
        nilai = self._baca_nilai()
        if not nilai:
            messagebox.showwarning("Peringatan", "Nilai tugas, UTS, dan UAS harus berupa angka 0 sampai 100.")
            return None

        tugas, uts, uas = nilai
        mk_id, _sks = self.mk_map[self.mk_var.get()]
        semester_id = self.semester_map[self.semester_var.get()]
        return mk_id, semester_id, tugas, uts, uas, hitung_nilai_akhir(tugas, uts, uas)

    # ---------- Aksi ----------
    def on_tambah(self):
        data = self._validate()
        if not data:
            return
        try:
            tambah_nilai(self.current_mhs_id, *data)
            self.clear_form()
            self.load_nilai()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Gagal menambah nilai (mata kuliah ini mungkin sudah ada di semester tersebut): {e}")

    def on_update(self):
        if not self.selected_id:
            messagebox.showwarning("Peringatan", "Pilih data nilai di tabel terlebih dahulu.")
            return
        data = self._validate()
        if not data:
            return
        try:
            update_nilai(int(self.selected_id), *data)
            self.clear_form()
            self.load_nilai()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memperbarui nilai: {e}")

    def on_hapus(self):
        if not self.selected_id:
            messagebox.showwarning("Peringatan", "Pilih data nilai di tabel terlebih dahulu.")
            return
        if not messagebox.askyesno("Konfirmasi", "Hapus data nilai ini?"):
            return
        try:
            hapus_nilai(int(self.selected_id))
            self.clear_form()
            self.load_nilai()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menghapus nilai: {e}")


# Untuk menjalankan halaman
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Nilai & IPK - SIAKAD")
    window.geometry("760x780")
    window.configure(bg=BG_COLOR)
    NilaiPage(window).pack(fill="both", expand=True)
  
    window.mainloop()
