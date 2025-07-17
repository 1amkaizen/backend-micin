# backend/utils/payment_helper.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from config import supabase


# backend/utils/payment_helper.py

def parse_tipe(order_id: str) -> str:
    order_id = order_id.upper()

    if "VIP" in order_id:
        return "vip"
    elif "SMAADD" in order_id:
        return "addon_sma"
    elif "UMM" in order_id:
        return "addon_umm"
    elif "SOL" in order_id or "ECER" in order_id:
        return "solana"
    else:
        return "unknown"





def get_all_transactions():
    res = supabase.table("Transactions").select("*").order("transaction_time", desc=True).execute()
    data = res.data or []

    for trx in data:
        trx["parsed_tipe"] = parse_tipe(trx.get("order_id") or "")

    return data
