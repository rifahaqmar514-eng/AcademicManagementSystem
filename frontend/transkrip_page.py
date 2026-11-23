import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from assets.colors import (
    BG_COLOR,
    CARD_BG,
    TEXT_DARK,
    PRIMARY_COLOR,
    ACCENT_COLOR
)

# Fungsi backend yang sama dengan nilai_page.py:
#   get_all_mahasiswa()  -> (mahasiswa_id, nim, nama_lengkap, prodi_id, nama_prodi,
#                            jenis_kelamin, tanggal_lahir, angkatan, status_mahasiswa)
#   get_skala_nilai()    -> (huruf_mutu, bobot_mutu, nilai_min, nilai_max, is_lulus)
#   get_nilai_by_mahasiswa(mahasiswa_id)
#        -> (nilai_id, mk_id, kode_mk, nama_mk, sks, semester_id, kode_semester,
#            nilai_tugas, nilai_uts, nilai_uas, nilai_akhir)
from backend.mahasiswa import get_all_mahasiswa
from backend.nilai import get_skala_nilai, get_nilai_by_mahasiswa

# Samakan dengan nilai_page.py:
#   True  -> hanya nilai terbaik per mata kuliah yang dihitung di IPK
#   False -> semua percobaan dihitung
IPK_PAKAI_NILAI_TERBAIK = True


class TranskripPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_COLOR)
        self.mahasiswa_map = {}   # "NIM - Nama" -> row mahasiswa
        self.skala = []           # (huruf, bobot, min, max, lulus), urut nilai_min turun
        self.current = None       # row mahasiswa terpilih
        self.export_rows = []     # baris untuk ekspor CSV
        self.export_summary = {}
        self._build_ui()
        self.load_referensi()

    # ---------- UI ----------
    def _build_ui(self):
        tk.Label(self, text="Transkrip Nilai",
                 font=("Arial", 20, "bold"), bg=BG_COLOR, fg=TEXT_DARK).pack(pady=(15, 10))

        pilih = tk.Frame(self, bg=BG_COLOR)
        pilih.pack(fill="x", padx=20)
        tk.Label(pilih, text="Mahasiswa:", font=("Arial", 11),
                 bg=BG_COLOR, fg=TEXT_DARK).pack(side="left")
        self.mhs_var = tk.StringVar()
        self.mhs_combo = ttk.Combobox(pilih, textvariable=self.mhs_var, state="readonly",
                                      font=("Arial", 11), width=45)
        self.mhs_combo.pack(side="left", padx=10)
        self.mhs_combo.bind("<<ComboboxSelected>>", self.on_pilih_mahasiswa)
        tk.Button(pilih, text="Ekspor CSV", command=self.on_ekspor,
                  font=("Arial", 10), bg=ACCENT_COLOR, fg="white",
                  relief="flat", padx=12, pady=3, cursor="hand2").pack(side="right")

        # Identitas mahasiswa
        info = tk.Frame(self, bg=CARD_BG, padx=15, pady=10)
        info.pack(fill="x", padx=20, pady=10)
        self.info_vars = {k: tk.StringVar(value="-")
                          for k in ("NIM", "Nama", "Program Studi", "Angkatan", "Status")}
        for i, (label, var) in enumerate(self.info_vars.items()):
            tk.Label(info, text=label, font=("Arial", 10), bg=CARD_BG,
                     fg=TEXT_DARK).grid(row=i, column=0, sticky="w")
            tk.Label(info, text=":", font=("Arial", 10), bg=CARD_BG,
                     fg=TEXT_DARK).grid(row=i, column=1, padx=6)
            tk.Label(info, textvariable=var, font=("Arial", 10, "bold"), bg=CARD_BG,
                     fg=TEXT_DARK).grid(row=i, column=2, sticky="w")

        # Tabel transkrip (dikelompokkan per semester)
        table_frame = tk.Frame(self, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=20)

        cols = ("mk", "sks", "akhir", "huruf", "bobot", "mutu", "ket")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="tree headings", height=14)
        self.tree.heading("#0", text="Semester / Kode")
        self.tree.column("#0", width=140, anchor="w")
        heads = {"mk": "Mata Kuliah", "sks": "SKS", "akhir": "Nilai", "huruf": "Huruf",
                 "bobot": "Bobot", "mutu": "SKS x Bobot", "ket": "Ket"}
        widths = {"mk": 210, "sks": 50, "akhir": 60, "huruf": 55, "bobot": 55,
                  "mutu": 85, "ket": 70}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="w" if c == "mk" else "center")
        self.tree.tag_configure("semester", font=("Arial", 10, "bold"), background="#e8edf3")
        self.tree.tag_configure("diulang", foreground="#999999")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Ringkasan
        summary = tk.Frame(self, bg=CARD_BG, padx=15, pady=10)
        summary.pack(fill="x", padx=20, pady=15)
        self.sks_label = tk.Label(summary, text="Total SKS: 0", font=("Arial", 12),
                                  bg=CARD_BG, fg=TEXT_DARK)
        self.sks_label.pack(side="left", padx=(0, 25))
        self.sks_lulus_label = tk.Label(summary, text="SKS Lulus: 0", font=("Arial", 12),
                                        bg=CARD_BG, fg=TEXT_DARK)
        self.sks_lulus_label.pack(side="left", padx=(0, 25))
        self.ipk_label = tk.Label(summary, text="IPK: 0.00", font=("Arial", 16, "bold"),
                                  bg=CARD_BG, fg=PRIMARY_COLOR)
        self.ipk_label.pack(side="right")

    # ---------- Data ----------
    def load_referensi(self):
        try:
            mhs = get_all_mahasiswa()
            skala = get_skala_nilai()
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat data referensi: {e}")
            return
        self.mahasiswa_map = {f"{r[1]} - {r[2]}": r for r in mhs}
        self.mhs_combo["values"] = list(self.mahasiswa_map.keys())
        self.skala = sorted(
            [(h, float(b), float(mn), float(mx), bool(lulus)) for h, b, mn, mx, lulus in skala],
            key=lambda x: x[2], reverse=True)

    def konversi(self, nilai_akhir):
        """Return (huruf, bobot, lulus) berdasarkan tabel skala_nilai."""
        for huruf, bobot, nilai_min, _mx, lulus in self.skala:
            if nilai_akhir >= nilai_min:
                return huruf, bobot, lulus
        return "-", 0.0, False

    def on_pilih_mahasiswa(self, _event=None):
        self.current = self.mahasiswa_map.get(self.mhs_var.get())
        if not self.current:
            return
        (_id, nim, nama, _pid, nama_prodi, _jk, _tgl, angkatan, status) = self.current
        self.info_vars["NIM"].set(nim)
        self.info_vars["Nama"].set(nama)
        self.info_vars["Program Studi"].set(nama_prodi)
        self.info_vars["Angkatan"].set(str(angkatan))
        self.info_vars["Status"].set(status)
        self.load_transkrip()

    def load_transkrip(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.export_rows = []

        try:
            data = get_nilai_by_mahasiswa(self.current[0])
        except Exception as e:
            messagebox.showerror("Error", f"Gagal memuat nilai: {e}")
            return

        # Susun baris: urut semester lalu kode MK
        rows = []
        for (_nid, mk_id, kode_mk, nama_mk, sks, _sid, kode_smt,
             _tugas, _uts, _uas, akhir) in data:
            huruf, bobot, lulus = self.konversi(float(akhir))
            rows.append({
                "mk_id": mk_id, "kode_mk": kode_mk, "nama_mk": nama_mk, "sks": int(sks),
                "smt": str(kode_smt), "akhir": float(akhir),
                "huruf": huruf, "bobot": bobot, "lulus": lulus,
            })
        rows.sort(key=lambda r: (r["smt"], r["kode_mk"]))

        # Tentukan baris yang dihitung di IPK
        if IPK_PAKAI_NILAI_TERBAIK:
            terbaik = {}
            for i, r in enumerate(rows):
                cur = terbaik.get(r["mk_id"])
                if cur is None or (r["bobot"], r["smt"]) > (rows[cur]["bobot"], rows[cur]["smt"]):
                    terbaik[r["mk_id"]] = i
            dihitung = set(terbaik.values())
        else:
            dihitung = set(range(len(rows)))

        # Tampilkan per semester
        per_smt = {}
        for i, r in enumerate(rows):
            per_smt.setdefault(r["smt"], []).append(i)

        for smt in sorted(per_smt):
            idxs = per_smt[smt]
            sks_smt = sum(rows[i]["sks"] for i in idxs)
            mutu_smt = sum(rows[i]["sks"] * rows[i]["bobot"] for i in idxs)
            ips = mutu_smt / sks_smt if sks_smt else 0.0

            parent = self.tree.insert(
                "", "end", text=f"Semester {smt}", open=True, tags=("semester",),
                values=(f"IPS: {ips:.2f}", sks_smt, "", "", "", f"{mutu_smt:.1f}", ""))
            self.export_rows.append(
                [f"Semester {smt}", "", f"IPS {ips:.2f}", sks_smt, "", "", "", f"{mutu_smt:.1f}", ""])

            for i in idxs:
                r = rows[i]
                ket = ("Lulus" if r["lulus"] else "Tidak Lulus") if i in dihitung else "Diulang"
                tags = () if i in dihitung else ("diulang",)
                mutu = r["sks"] * r["bobot"]
                self.tree.insert(
                    parent, "end", text=r["kode_mk"], tags=tags,
                    values=(r["nama_mk"], r["sks"], f"{r['akhir']:.2f}", r["huruf"],
                            f"{r['bobot']:.1f}", f"{mutu:.1f}", ket))
                self.export_rows.append(
                    ["", r["kode_mk"], r["nama_mk"], r["sks"], f"{r['akhir']:.2f}",
                     r["huruf"], f"{r['bobot']:.1f}", f"{mutu:.1f}", ket])

        # Ringkasan IPK
        total_sks = sum(rows[i]["sks"] for i in dihitung)
        total_mutu = sum(rows[i]["sks"] * rows[i]["bobot"] for i in dihitung)
        sks_lulus = sum(rows[i]["sks"] for i in dihitung if rows[i]["lulus"])
        ipk = total_mutu / total_sks if total_sks else 0.0

        self.sks_label.config(text=f"Total SKS: {total_sks}")
        self.sks_lulus_label.config(text=f"SKS Lulus: {sks_lulus}")
        self.ipk_label.config(text=f"IPK: {ipk:.2f}")
        self.export_summary = {"total_sks": total_sks, "sks_lulus": sks_lulus, "ipk": ipk}

    # ---------- Ekspor ----------
    def on_ekspor(self):
        if not self.current or not self.export_rows:
            messagebox.showwarning("Peringatan", "Pilih mahasiswa yang sudah memiliki nilai terlebih dahulu.")
            return
        nim = self.current[1]
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=f"transkrip_{nim}.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["TRANSKRIP NILAI"])
                w.writerow(["NIM", nim])
                w.writerow(["Nama", self.current[2]])
                w.writerow(["Program Studi", self.current[4]])
                w.writerow([])
                w.writerow(["Semester", "Kode", "Mata Kuliah", "SKS", "Nilai", "Huruf",
                            "Bobot", "SKS x Bobot", "Ket"])
                w.writerows(self.export_rows)
                w.writerow([])
                w.writerow(["Total SKS", self.export_summary["total_sks"]])
                w.writerow(["SKS Lulus", self.export_summary["sks_lulus"]])
                w.writerow(["IPK", f"{self.export_summary['ipk']:.2f}"])
            messagebox.showinfo("Sukses", f"Transkrip diekspor ke:\n{path}")
        except OSError as e:
            messagebox.showerror("Error", f"Gagal menyimpan file: {e}")


# Untuk menjalankan halaman 
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Transkrip Nilai - SIAKAD")
    window.geometry("800x760")
    window.configure(bg=BG_COLOR)
    TranskripPage(window).pack(fill="both", expand=True)
  
    window.mainloop()
