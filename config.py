"""Konfigurasi aplikasi dari environment lokal proyek."""
import os
from pathlib import Path

from dotenv import load_dotenv


# Pastikan file .env proyek dipakai, termasuk bila environment dari IDE berbeda.
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "siakad"),
    "charset": "utf8mb4",
    "connection_timeout": 10,
}

SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
