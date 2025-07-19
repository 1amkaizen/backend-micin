# backend/routes/payment.py

from fastapi import APIRouter, Request, BackgroundTasks, Depends,Body
from fastapi.responses import HTMLResponse, JSONResponse
from config import supabase, MIDTRANS_CLIENT_KEY
from backend.utils.auth_helper import require_login
from backend.services.midtrans import create_snap_transaction, is_valid_signature
from backend.services.telegram_notify import send_telegram_notify,send_telegram_notify_manual
from datetime import datetime
import uuid
from fastapi import Form
import logging
import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from config import BASE_URL, MIDTRANS_CLIENT_KEY, MIDTRANS_SNAP_URL
from fastapi import BackgroundTasks  # pastikan sudah di-import
from backend.services.email_notify import send_email_notify_manual  # pastikan juga ini di-import



router = APIRouter()
templates = Jinja2Templates(directory="frontend")

async def get_setting_price(key: str) -> int:
    result = supabase.table("Settings").select("value").eq("key", key).single().execute()
    if result.data and result.data.get("value"):
        return int(result.data["value"])
    return 0


# ===============================
# BAYAR VIP (GET)
# ===============================
@router.get("/bayar/vip", response_class=HTMLResponse)
async def bayar_vip(request: Request, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id  # redirect ke login kalau belum login

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return HTMLResponse("User tidak ditemukan", status_code=404)

    order_id = f"VIPWEB-{uuid.uuid4().hex[:10].upper()}"
    gross_amount = await get_setting_price("vip_price")

    item_details = [{
        "id": "vip",
        "price": gross_amount,
        "quantity": 1,
        "name": "Membership VIP Micin"
    }]
    customer = {
        "first_name": user["full_name"] or user["username"],
        "email": f"{user['username']}@telegram.micin",
    }

    snap_token = create_snap_transaction(order_id, gross_amount, item_details, customer)

    supabase.table("Transactions").insert({
        "order_id": order_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "gross_amount": gross_amount,
        "transaction_status": "pending",
        "transaction_time": datetime.utcnow().replace(microsecond=0).isoformat()
    }).execute()

    return templates.TemplateResponse("user/bayar_vip.html", {
        "request": request,
        "snap_token": snap_token,
        "client_key": MIDTRANS_CLIENT_KEY,
        "gross_amount": gross_amount,
        "snap_url": MIDTRANS_SNAP_URL, 
    })


# ===============================
# BAYAR VIP TANPA LOGIN (MANUAL)
# ===============================
@router.post("/bayar/vip/manual", response_class=HTMLResponse)
async def bayar_vip_manual(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    fullname: str = Form(...),
    email: str = Form(...)
):
    order_id = f"VIPWEB-{uuid.uuid4().hex[:10].upper()}"
    gross_amount = await get_setting_price("vip_price")

    item_details = [{
        "id": "vip",
        "price": gross_amount,
        "quantity": 1,
        "name": "Membership VIP Micin"
    }]

    customer = {
        "first_name": fullname or username,
        "email": email
    }

    snap_token = create_snap_transaction(order_id, gross_amount, item_details, customer)

    supabase.table("Transactions").insert({
        "order_id": order_id,
        "user_id": None,
        "username": username,
        "full_name": fullname,
        "email": email,
        "gross_amount": gross_amount,
        "transaction_status": "pending",
        "transaction_time": datetime.utcnow().replace(microsecond=0).isoformat()
    }).execute()

    # Tidak kirim email dulu di sini.
    # Email akan dikirim setelah webhook konfirmasi pembayaran.

    return templates.TemplateResponse("user/bayar_vip.html", {
        "request": request,
        "snap_token": snap_token,
        "client_key": MIDTRANS_CLIENT_KEY,
        "gross_amount": gross_amount,
        "snap_url": MIDTRANS_SNAP_URL,
    })


@router.get("/join-vip", response_class=HTMLResponse)
async def join_vip(request: Request, telegram_id: str = Depends(require_login)):
    return templates.TemplateResponse("user/join_vip.html", {
        "request": request,
        "telegram_id": telegram_id
    })


# ===============================
# BAYAR SMA ADDON (GET)
# ===============================
@router.get("/bayar/sma", response_class=HTMLResponse)
async def bayar_sma(request: Request, telegram_id: str = Depends(require_login)):
    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return HTMLResponse("User tidak ditemukan", status_code=404)

    if not user.get("is_vip"):
        return HTMLResponse("Kamu harus menjadi member VIP terlebih dahulu.", status_code=403)

    order_id = f"SMAADD-{uuid.uuid4().hex[:10].upper()}"
    gross_amount = await get_setting_price("addon_sma_price")  # ✅ Ambil harga dari Settings

    item_details = [{
        "id": "sma_addon",
        "price": gross_amount,
        "quantity": 1,
        "name": "Addon SMA Membership"
    }]
    customer = {
        "first_name": user["full_name"] or user["username"],
        "email": f"{user['username']}@telegram.micin",
    }

    snap_token = create_snap_transaction(order_id, gross_amount, item_details, customer)

    supabase.table("Transactions").insert({
        "order_id": order_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "gross_amount": gross_amount,
        "transaction_status": "pending",
        "transaction_time": datetime.utcnow().replace(microsecond=0).isoformat()
    }).execute()

    return templates.TemplateResponse("user/bayar_sma.html", {
        "request": request,
        "snap_token": snap_token,
        "client_key": MIDTRANS_CLIENT_KEY,
        "gross_amount": gross_amount,
        "snap_url": MIDTRANS_SNAP_URL,
    })

# ===============================
# BAYAR UMM ADDON (GET)
# ===============================
@router.get("/bayar/umm", response_class=HTMLResponse)
async def bayar_umm(request: Request, telegram_id: str = Depends(require_login)):
    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return HTMLResponse("User tidak ditemukan", status_code=404)

    if not user.get("is_vip"):
        return HTMLResponse("Kamu harus menjadi member VIP terlebih dahulu.", status_code=403)

    if not user.get("is_sma_addon"):
        return templates.TemplateResponse("user/bayar_umm.html", {
            "request": request,
            "snap_token": None,
            "client_key": MIDTRANS_CLIENT_KEY,
            "snap_url": MIDTRANS_SNAP_URL,
            "pesan": "Kamu harus membeli Addon SMA terlebih dahulu sebelum bisa membeli Addon UMM."
        })

    order_id = f"UMMWEB-{uuid.uuid4().hex[:10].upper()}"
    gross_amount = await get_setting_price("addon_umm_price")  # ✅ Ambil harga dari Settings

    item_details = [{
        "id": "umm_addon",
        "price": gross_amount,
        "quantity": 1,
        "name": "Addon UMM Membership"
    }]
    customer = {
        "first_name": user["full_name"] or user["username"],
        "email": f"{user['username']}@telegram.micin",
    }

    snap_token = create_snap_transaction(order_id, gross_amount, item_details, customer)

    supabase.table("Transactions").insert({
        "order_id": order_id,
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "gross_amount": gross_amount,
        "transaction_status": "pending",
        "transaction_time": datetime.utcnow().replace(microsecond=0).isoformat()
    }).execute()

    return templates.TemplateResponse("user/bayar_umm.html", {
        "request": request,
        "snap_token": snap_token,
        "client_key": MIDTRANS_CLIENT_KEY,
        "gross_amount": gross_amount,
        "snap_url": MIDTRANS_SNAP_URL
    })


# ===============================
# BAYAR SOLANA (POST)
# ===============================
@router.post("/bayar/solana")
async def bayar_solana(request: Request, telegram_id: str = Depends(require_login)):
    data = await request.json()
    full_name = data.get("full_name")
    wallet = data.get("wallet")
    nominal = int(data.get("nominal"))

    # ✅ Ambil daftar harga ecer resmi dari DB
    result = supabase.table("EcerPrices").select("price").execute()
    valid_prices = [row["price"] for row in (result.data or [])]

    # Validasi input
    if not full_name or not wallet or nominal not in valid_prices:
        return JSONResponse({"error": "Data tidak valid"}, status_code=400)

    # Generate order ID & detail transaksi
    order_id = f"SOLWEB-{uuid.uuid4().hex[:10].upper()}"
    item_details = [{
        "id": "solana",
        "price": nominal,
        "quantity": 1,
        "name": f"Beli Solana - Rp {nominal}"
    }]
    customer = {
        "first_name": full_name,
        "email": f"{wallet}@micin.sol"
    }

    # Generate Snap Token dari Midtrans
    snap_token = create_snap_transaction(order_id, nominal, item_details, customer)

    # ✅ Simpan transaksi ke DB
    supabase.table("Transactions").insert({
        "order_id": order_id,
        "user_id": int(telegram_id),
        "username": full_name,
        "full_name": full_name,
        "gross_amount": nominal,
        "tipe": "solana",  # digunakan di webhook
        "transaction_status": "pending",
        "transaction_time": datetime.utcnow().replace(microsecond=0).isoformat()
    }).execute()

    return {"snap_token": snap_token}





# ===============================
# WEBHOOK MIDTRANS
# ===============================
@router.post("/webhook/midtrans")
async def midtrans_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    order_id = data.get("order_id")
    status_code = data.get("status_code")
    gross_amount = data.get("gross_amount")
    signature_key = data.get("signature_key")

    # Filter hanya order yang valid
    if not order_id or not (
        order_id.startswith("VIPWEB-") or 
        order_id.startswith("SMAADD-") or 
        order_id.startswith("UMMWEB-") or 
        order_id.startswith("SOLWEB-")
    ):
        return JSONResponse({"status": "skipped"}, status_code=200)

    # Cek validitas signature Midtrans
    if not is_valid_signature(order_id, status_code, gross_amount, signature_key):
        return JSONResponse({"error": "Invalid signature"}, status_code=403)

    # Update status transaksi
    supabase.table("Transactions").update({
        "transaction_status": data.get("transaction_status"),
        "transaction_id": data.get("transaction_id"),
        "payment_type": data.get("payment_type"),
        "wallet": data.get("wallet_type"),
        "currency": data.get("currency"),
        "status_message": data.get("status_message"),
        "fraud_status": data.get("fraud_status"),
        "settlement_time": data.get("settlement_time"),
        "signature_key": signature_key,
        "merchant_id": data.get("merchant_id")
    }).eq("order_id", order_id).execute()

    # Kalau transaksi berhasil
    if data.get("transaction_status") == "settlement":
        trans_res = supabase.table("Transactions") \
            .select("user_id, username, email") \
            .eq("order_id", order_id).single().execute()

        if not trans_res.data:
            return JSONResponse({"error": "Transaksi tidak ditemukan"}, status_code=404)

        user_id = trans_res.data.get("user_id")
        username = trans_res.data.get("username")
        email = trans_res.data.get("email")
        now_date = datetime.utcnow().strftime("%Y-%m-%d")

        if order_id.startswith("VIPWEB-"):
            if user_id:
                # Update keanggotaan VIP
                supabase.table("Users").update({
                    "is_vip": True,
                    "vip_since": now_date
                }).eq("user_id", user_id).execute()
                background_tasks.add_task(send_telegram_notify, user_id, "vip")
            else:
                # Manual user (tidak login)
                background_tasks.add_task(send_telegram_notify_manual, username, email)

                if email:
                    background_tasks.add_task(send_email_notify_manual, email, username)

        elif order_id.startswith("SMAADD-"):
            if user_id:
                supabase.table("Users").update({
                    "is_sma_addon": True
                }).eq("user_id", user_id).execute()
                background_tasks.add_task(send_telegram_notify, user_id, "sma_addon")

        elif order_id.startswith("UMMWEB-"):
            if user_id:
                supabase.table("Users").update({
                    "is_umm": True
                }).eq("user_id", user_id).execute()
                background_tasks.add_task(send_telegram_notify, user_id, "umm_addon")

        elif order_id.startswith("SOLWEB-"):
            if user_id and user_id != 0:
                background_tasks.add_task(send_telegram_notify, user_id, "solana")

    return {"status": "ok"}
