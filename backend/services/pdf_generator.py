# backend/services/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_sertifikat(nama: str, level: str, filename: str):
    # Lokasi file output
    output_path = os.path.join("static", "sertifikat", filename)

    # Buat folder jika belum ada
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Setup canvas PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 100, "🎓 SERTIFIKAT KELULUSAN")

    # Nama user
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 150, f"Nama: {nama}")

    # Level
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 180, f"Level: {level}")

    # Tanggal
    tgl = datetime.now().strftime("%d %B %Y")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 210, f"Tanggal: {tgl}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, 50, "© Micin ID")

    # Selesai
    c.showPage()
    c.save()

    return output_path  # bisa dipakai untuk akses file
