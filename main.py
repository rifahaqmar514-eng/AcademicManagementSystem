"""Titik masuk aplikasi. Jalankan dari folder proyek:  python main.py"""
import ctypes
import tkinter as tk

from frontend import main_window


def _teks_tajam():
    """Di Windows, mencegah teks tampak buram pada layar beresolusi tinggi."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # bukan Windows, atau sudah diatur: abaikan


def main():
    _teks_tajam()
    root = tk.Tk()
    main_window.mulai(root)
    root.mainloop()


if __name__ == "__main__":
    main()