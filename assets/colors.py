"""Palet warna dan font aplikasi. Semua tampilan mengambil dari sini agar konsisten.

Nama lama (BG_COLOR, CARD_BG, PRIMARY_COLOR, TEXT_DARK) tetap ada supaya
kode yang sudah memakainya tidak rusak.
"""

# --- warna utama ---
PRIMARY_COLOR = "#8C624A"   # Cokelat mocha lembut (tombol & aksen utama)
PRIMARY_DARK = "#6F4C38"    # Cokelat hangat untuk status tekan/aktif
PRIMARY_HOVER = "#9E7258"   # Lebih cerah halus saat hover
PRIMARY_LIGHT = "#F2EAE1"   # Krem susu lembut untuk highlight/tab aktif

# --- latar dan teks ---
BG_COLOR = "#F8F5F0"        # Latar utama putih gading/krem sangat lembut
CARD_BG = "#FCFBF8"         # Latar kartu/form terang dan bersih
TEXT_DARK = "#3A2B22"       # Cokelat tua lembut (tidak terlalu tajam)
TEXT_MUTED = "#8A7A70"      # Cokelat keabu-abuan halus untuk teks sekunder
BORDER_COLOR = "#E3D9CE"    # Garis batas tipis dan kalem
TAB_IDLE_BG = "#EFE8DF"     # Tab tidak aktif yang lembut

# --- status ---
DANGER_COLOR = "#B54B4B"    # Merah bata pucat/lembut
DANGER_BG = "#FBECEC"
SUCCESS_COLOR = "#4A785C"   # Hijau sage/daun lembut
SUCCESS_BG = "#ECF4EF"

# --- sidebar ---
SIDEBAR_BG = "#6E4F3E"      # Cokelat susu/cocoa medium yang lembut
SIDEBAR_HOVER = "#7E5C49"
SIDEBAR_ACTIVE = "#9C7660"
SIDEBAR_TEXT = "#FAF7F2"

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