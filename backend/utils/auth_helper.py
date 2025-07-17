# File: backend/utils/auth_helper.py

from fastapi import Request
from fastapi.responses import RedirectResponse
from config import supabase

async def require_login(request: Request):
    telegram_id = request.cookies.get("telegram_id")

    if not telegram_id:
        return RedirectResponse(url="/login")

    try:
        user_check = supabase.table("Users").select("id").eq("user_id", int(telegram_id)).maybe_single().execute()
    except Exception:
        return RedirectResponse(url="/login")

    if not user_check or not user_check.data:
        return RedirectResponse(url="/login")

    return int(telegram_id)
