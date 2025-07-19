# test_generate_sertifikat.py

from backend.services.pdf_generator import generate_sertifikat

if __name__ == "__main__":
    nama = "Zaenal Arifin"
    level = "SMA"
    filename = "sertifikat_test.pdf"

    path = generate_sertifikat(nama, level, filename)
    print(f"Sertifikat PDF berhasil dibuat: {path}")

