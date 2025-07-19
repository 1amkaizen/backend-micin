# backend/services/telegram_notify.py

import requests
from datetime import datetime
from config import (
    TELEGRAM_BOT_TOKEN,
    ADMIN_CHAT_ID,
    CHANNEL_VIP_LINK,
    GROUP_VIP_LINK,
    supabase
)

def send_telegram_notify(user_id: int, tipe: str = "vip"):
    # Gunakan tanpa .single() biar tidak error jika 0 row
    user_res = supabase.table("Users").select("*").eq("user_id", user_id).execute()

    if not user_res.data or len(user_res.data) == 0:
        print(f"[ERROR] Gagal kirim notifikasi Telegram: user_id {user_id} tidak ditemukan.")
        return

    user = user_res.data[0]

    now_str = datetime.now().strftime("%d %b %Y %H:%M:%S")

    if tipe == "vip":
        paket = "VIP Membership"
        emoji = "✅"
    elif tipe == "sma_addon":
        paket = "Addon SMA"
        emoji = "🧩"
    elif tipe == "umm_addon":
        paket = "Addon UMM"
        emoji = "📚"
    elif tipe == "solana":
        paket = "Pembelian Solana"
        emoji = "💎"
    else:
        paket = "Transaksi"
        emoji = "💳"

    # Pesan utama (tanpa link)
    base_message = (
        f"{emoji} Pembayaran berhasil (via Website)!!\n"
        f"🗓 Tanggal: {now_str}\n\n"
        f"👤 Nama: {user.get('full_name') or user.get('username', 'Tanpa Nama')}\n"
        f"🆔 ID: {user['user_id']}\n"
        f"📦 Paket: {paket}"
    )

    # Tambah link hanya untuk user jika VIP
    user_message = base_message
    if tipe == "vip":
        user_message += (
            "\n\n"
            f"👥 Group VIP: {GROUP_VIP_LINK}\n"
            f"📢 Channel VIP: {CHANNEL_VIP_LINK}"
        )

    # Kirim ke user (dengan link kalau VIP)
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": user["user_id"],
        "text": user_message
    })

    # Kirim ke admin (tanpa link)
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": ADMIN_CHAT_ID,
        "text": f"📢 Notifikasi Admin:\n\n{base_message}"
    })

def send_telegram_notify_manual(username: str, email: str = "", full_name: str = ""):
    now_str = datetime.now().strftime("%d %b %Y %H:%M:%S")
    paket = "VIP Membership"
    emoji = "✅"

    base_message = (
        f"{emoji} Pembayaran berhasil (Manual - Tanpa Login)!!\n"
        f"🗓 Tanggal: {now_str}\n\n"
        f"👤 Nama: {full_name or username}\n"
        f"🆔 Username: {username}\n"
        f"📦 Paket: {paket}"
    )

    if email:
        base_message += f"\n📧 Email: {email}"

    # Kirim hanya ke admin
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": ADMIN_CHAT_ID,
        "text": f"📢 Notifikasi Admin:\n\n{base_message}"
    })

    # Note: nanti bisa ditambahkan kirim email di sini juga kalau mau
