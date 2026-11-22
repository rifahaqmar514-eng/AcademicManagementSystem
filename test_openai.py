import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Muat .env dari folder proyek, meskipun skrip dijalankan dari folder lain.
load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY belum diisi. Tambahkan key di file .env lokal."
    )

client = OpenAI(api_key=api_key)
response = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-6.2-astra"),
    input="Halo, apakah koneksi API saya berhasil?",
)

print(response.output_text)
