"""Palet warna & tipografi aplikasi — Tema "Coffee Shop".

Prinsip:
- Hangat & menenangkan (low blue light, earthy tone).
- Kontras teks-latar >= 4.5:1 (WCAG AA).
- Nama konstanta lama dipertahankan agar halaman lain tidak rusak.
"""

# ------------------------------------------------------------------ Brand
PRIMARY_COLOR       = "#C68B59"   # caramel — aksen utama
PRIMARY_DARK        = "#3E2723"   # espresso — brand gelap
PRIMARY_HOVER       = "#B07A48"   # caramel gelap (hover)
PRIMARY_LIGHT       = "#E6C9A8"   # latte — teks di latar gelap
PRIMARY_ACCENT      = "#C68B59"   # alias caramel
PRIMARY_ACCENT_SOFT = "#B07A48"   # caramel untuk tombol primary bg

# Gradasi brand panel
PRIMARY_GRADIENT_TOP = "#3E2723"  # espresso
PRIMARY_GRADIENT_BOT = "#1B0E0A"  # dark roast

# ------------------------------------------------------------------ Surface
BG_COLOR         = "#F5EFE6"      # cream — latar halaman
CARD_BG          = "#FFFCF7"      # foam — kartu
SURFACE_ELEVATED = "#FFFCF7"      # alias CARD_BG
SURFACE_MUTED    = "#EDE3D4"      # cream gelap — tombol sekunder
BORDER_COLOR     = "#D9CBB8"      # tan — garis tepi

# ------------------------------------------------------------------ Input
INPUT_BORDER       = "#D9CBB8"
INPUT_BORDER_FOCUS = "#C68B59"
FOCUS_RING         = "#C68B59"

# ------------------------------------------------------------------ Tab
TAB_ACTIVE_BG = "#C68B59"
TAB_IDLE_BG   = "#EADFCF"

# ------------------------------------------------------------------ Teks
TEXT_DARK  = "#3B2A21"   # coffee bean
TEXT_MUTED = "#8B7355"   # mocha

# ------------------------------------------------------------------ Status
SUCCESS_COLOR = "#4A6741"   # matcha gelap
SUCCESS_BG    = "#E8F0E2"   # matcha soft
DANGER_COLOR  = "#A63A2E"   # chili
DANGER_BG     = "#F8E3DF"   # chili soft
INFO_COLOR    = "#4A6B7C"   # sky brew
INFO_BG       = "#E4EDF2"   # sky soft

# ------------------------------------------------------------------ Sidebar
SIDEBAR_BG     = "#2B1A15"   # espresso sangat gelap
SIDEBAR_ACTIVE = "#C68B59"   # caramel — menu aktif
SIDEBAR_HOVER  = "#4A342B"   # mocha gelap — hover
SIDEBAR_TEXT   = "#D9CBB8"   # tan — teks menu idle

# ------------------------------------------------------------------ Font
FONT_FAMILY = "Segoe UI"
FONT_BRAND   = ("Segoe UI", 26, "bold")
FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEADING = ("Segoe UI", 14, "bold")
FONT_BOLD    = ("Segoe UI", 10, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_BUTTON  = ("Segoe UI", 10, "bold")
FONT_LINK    = ("Segoe UI", 10, "bold")