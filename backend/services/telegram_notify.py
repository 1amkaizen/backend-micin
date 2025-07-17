# backend/services/telegram_notify.py

import requests
from config import TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, supabase
from datetime import datetime

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

    message = (
        f"{emoji} Pembayaran berhasil (via Website)!!\n"
        f"🗓 Tanggal: {now_str}\n\n"
        f"👤 Nama: {user.get('full_name') or user.get('username', 'Tanpa Nama')}\n"
        f"🆔 ID: {user['user_id']}\n"
        f"📦 Paket: {paket}"
    )

    # Kirim ke user
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": user["user_id"],
        "text": message
    })

    # Kirim ke admin
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": ADMIN_CHAT_ID,
        "text": f"📢 Notifikasi Admin:\n\n{message}"
    })
