"""Palet warna dan font aplikasi. Semua tampilan mengambil dari sini agar konsisten.

Nama lama (BG_COLOR, CARD_BG, PRIMARY_COLOR, TEXT_DARK) tetap ada supaya
kode yang sudah memakainya tidak rusak.
"""

# --- warna utama ---
PRIMARY_COLOR = "#1D4ED8"
PRIMARY_DARK = "#1E3A8A"
PRIMARY_HOVER = "#1E40AF"
PRIMARY_LIGHT = "#DBEAFE"

# --- latar dan teks ---
BG_COLOR = "#F1F5F9"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
BORDER_COLOR = "#CBD5E1"
TAB_IDLE_BG = "#E2E8F0"

# --- status ---
DANGER_COLOR = "#B91C1C"
DANGER_BG = "#FEE2E2"
SUCCESS_COLOR = "#15803D"
SUCCESS_BG = "#DCFCE7"

# --- sidebar ---
SIDEBAR_BG = "#0F172A"
SIDEBAR_HOVER = "#1E293B"
SIDEBAR_ACTIVE = "#2563EB"
SIDEBAR_TEXT = "#CBD5E1"

# --- font ---
FONT_FAMILY = "Segoe UI"
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_LINK = (FONT_FAMILY, 10, "underline")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_BRAND = (FONT_FAMILY, 32, "bold")
