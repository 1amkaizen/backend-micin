# services/midtrans.py

import base64
import hashlib
import requests
from config import MIDTRANS_SERVER_KEY, MIDTRANS_IS_PRODUCTION, BASE_URL

# Pilih base URL Midtrans sesuai env
BASE_URL_MIDTRANS = "https://app.midtrans.com" if MIDTRANS_IS_PRODUCTION else "https://app.sandbox.midtrans.com"
SNAP_URL = f"{BASE_URL_MIDTRANS}/snap/v1/transactions"

# Basic Auth header dari server key
AUTH_HEADER = {
    "Authorization": "Basic " + base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
}

def create_snap_transaction(order_id: str, gross_amount: int, item_details: list, customer: dict) -> str:
    """Buat transaksi Snap dan return snap_token"""
    payload = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": gross_amount
        },
        "item_details": item_details,
        "customer_details": customer,
        "callbacks": {
            "finish": f"{BASE_URL}/dashboard"  # pakai BASE_URL dari config
        }
    }

    response = requests.post(SNAP_URL, headers=AUTH_HEADER, json=payload)
    if response.status_code != 201:
        raise Exception(f"Midtrans Snap error: {response.text}")

    return response.json()["token"]


def is_valid_signature(order_id: str, status_code: str, gross_amount: str, signature_key: str) -> bool:
    """Cek apakah signature dari webhook valid"""
    raw = order_id + status_code + gross_amount + MIDTRANS_SERVER_KEY
    expected = hashlib.sha512(raw.encode()).hexdigest()
    return expected == signature_key
