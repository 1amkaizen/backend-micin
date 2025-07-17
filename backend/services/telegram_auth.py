# backend/services/telegram_auth.py

import hashlib
import hmac
from config import TELEGRAM_BOT_TOKEN

def check_telegram_auth(data: dict) -> bool:
    auth_data = data.copy()
    hash_check = auth_data.pop("hash", None)

    sorted_data = "\n".join([f"{k}={auth_data[k]}" for k in sorted(auth_data)])
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, sorted_data.encode(), hashlib.sha256).hexdigest()

    return hmac_hash == hash_check
