# config.py

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# === Telegram Bot ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_LOGIN_BOT_USERNAME = os.getenv("TELEGRAM_LOGIN_BOT_USERNAME")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
CHANNEL_VIP_LINK = os.getenv("CHANNEL_VIP_LINK")
GROUP_VIP_LINK = os.getenv("GROUP_VIP_LINK")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# === Secret Key App ===
SECRET_KEY = os.getenv("SECRET_KEY")

# === Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Midtrans ===
MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY")
MIDTRANS_CLIENT_KEY = os.getenv("MIDTRANS_CLIENT_KEY")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

# Snap URL Midtrans (otomatis switch sandbox/production)
MIDTRANS_SNAP_URL = (
    "https://app.midtrans.com/snap/snap.js"
    if MIDTRANS_IS_PRODUCTION
    else "https://app.sandbox.midtrans.com/snap/snap.js"
)

# === Base URL Project ===
BASE_URL = os.getenv("BASE_URL")

ADMIN_TELEGRAM_USERNAME = os.getenv("ADMIN_TELEGRAM_USERNAME")


# === SMTP (Email Notifikasi) ===
SMTP_ADMIN_USER = os.getenv("SMTP_ADMIN_USER")
SMTP_ADMIN_PASS = os.getenv("SMTP_ADMIN_PASS")

SMTP_SUPPORT_USER = os.getenv("SMTP_SUPPORT_USER")
SMTP_SUPPORT_PASS = os.getenv("SMTP_SUPPORT_PASS")

SMTP_HOST = os.getenv("SMTP_HOST", "mail.micin.id")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

SUPPORT_EMAIL = "support@micin.id"  # nilai tetap