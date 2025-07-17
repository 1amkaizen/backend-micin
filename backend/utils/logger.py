# backend/utils/logger.py
from config import supabase
from datetime import datetime
import uuid

def log_activity(user_id: int, title: str, description: str, icon: str = "clock"):
    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "description": description,
        "icon": icon,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("ActivityLogs").insert(data).execute()
