# backend/services/pdf_generator.py

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

def generate_sertifikat(nama: str, level: str, filename: str):
    # Lokasi output
    output_path = os.path.join("static", "sertifikat", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Setup Jinja2
    env = Environment(loader=FileSystemLoader("frontend"))
    template = env.get_template("sertifikat_template.html")

    # Format tanggal
    tanggal = datetime.now().strftime("%d %B %Y")

    # Render HTML dengan variabel dinamis
    base_path = os.getcwd()
    html_str = template.render(nama=nama, level=level, tanggal=tanggal, base_path=base_path)


    # Konversi ke PDF
    HTML(string=html_str, base_url=os.getcwd()).write_pdf(output_path)

    return output_path
