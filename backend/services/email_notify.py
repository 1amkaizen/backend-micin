# File: backend/services/email_notify.py

from email.message import EmailMessage
from aiosmtplib import send
from config import SMTP_USER, SMTP_PASS
import logging

async def send_email_notify_manual(to_email: str, username: str):
    msg = EmailMessage()
    msg["Subject"] = "Pembayaran VIP Micin"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    msg.set_content(f"""
Halo {username},

Terima kasih telah melakukan pendaftaran member VIP Micin.

Status pembayaran Anda sedang diproses. Silakan tunggu konfirmasi selanjutnya.

Salam,
Team Micin.id
""")

    try:
        await send(
            msg,  # <-- ini diubah: positional arg
            hostname="mail.micin.id",
            port=465,
            username=SMTP_USER,
            password=SMTP_PASS,
            use_tls=True,
        )
        logging.info(f"[EMAIL] Email berhasil dikirim ke {to_email}")
    except Exception as e:
        logging.error(f"[EMAIL] Gagal kirim ke {to_email}: {e}")
