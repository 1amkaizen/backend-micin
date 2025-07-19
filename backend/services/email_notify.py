# Letak file: backend/services/email_notify.py

from email.message import EmailMessage
from aiosmtplib import send
from config import (
    SMTP_ADMIN_USER,
    SMTP_ADMIN_PASS,
    SMTP_HOST,
    SMTP_PORT,
    CHANNEL_VIP_LINK,
    GROUP_VIP_LINK,
    BOT_USERNAME
)
import logging

async def send_email_notify_manual(to_email: str, username: str):
    msg = EmailMessage()
    msg["Subject"] = "Pembayaran VIP Micin Berhasil"
    msg["From"] = SMTP_ADMIN_USER  # Kirim dari admin@micin.id
    msg["To"] = to_email            # Tujuan user

    msg.set_content(f"""
Halo {username},

Pembayaran VIP Anda telah berhasil kami terima dan proses.

Selamat! Anda sekarang resmi menjadi member VIP Micin.

Silakan bergabung di channel dan grup VIP berikut untuk mendapatkan update dan akses eksklusif:

Channel VIP: {CHANNEL_VIP_LINK}
Grup VIP: {GROUP_VIP_LINK}

Anda juga bisa menggunakan bot Telegram kami untuk berbagai fitur:
Bot Telegram: https://t.me/{BOT_USERNAME}


Terima kasih telah bergabung dan dukung terus Micin.id!

Salam hangat,
Team Micin.id
""")

    try:
        await send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_ADMIN_USER,
            password=SMTP_ADMIN_PASS,
            use_tls=True,
        )
        logging.info(f"[EMAIL] Email berhasil dikirim ke {to_email}")
    except Exception as e:
        logging.error(f"[EMAIL] Gagal kirim ke {to_email}: {e}")
