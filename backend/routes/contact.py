# Letak file: backend/routes/contact.py

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from email.message import EmailMessage
from aiosmtplib import send
from config import (
    SMTP_SUPPORT_USER,
    SMTP_SUPPORT_PASS,
    SUPPORT_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
)
import logging

router = APIRouter()

@router.post("/contact")
async def contact_form(
    nama: str = Form(...),
    email: str = Form(...),
    pesan: str = Form(...)
):
    msg = EmailMessage()
    msg["Subject"] = "Pesan Baru dari Form Kontak"
    msg["From"] = SMTP_SUPPORT_USER
    msg["To"] = SUPPORT_EMAIL

    msg.set_content(f"""
Pesan dari pengguna:

Nama: {nama}
Email: {email}

Pesan:
{pesan}
""")

    try:
        await send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_SUPPORT_USER,
            password=SMTP_SUPPORT_PASS,
            use_tls=True,
        )
        # Kirim email konfirmasi ke user
        await send_email_confirm_user(email, nama)

        logging.info(f"[KONTAK] Pesan dari {email} berhasil dikirim")
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logging.error(f"[KONTAK] Gagal kirim pesan: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

async def send_email_confirm_user(to_email: str, nama: str):
    msg = EmailMessage()
    msg["Subject"] = "Pesan Anda Telah Diterima - Micin.id"
    msg["From"] = SMTP_SUPPORT_USER
    msg["To"] = to_email

    msg.set_content(f"""
Halo {nama},

Terima kasih telah menghubungi tim support Micin.id.

Kami sudah menerima pesan Anda dan akan segera menindaklanjutinya. Mohon ditunggu maksimal 1x24 jam.

Hormat kami,
Team Micin.id
""")

    await send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_SUPPORT_USER,
        password=SMTP_SUPPORT_PASS,
        use_tls=True,
    )