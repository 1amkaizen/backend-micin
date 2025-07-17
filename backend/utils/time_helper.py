# backend/utils/time_helper.py
from datetime import datetime

def safe_parse_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
