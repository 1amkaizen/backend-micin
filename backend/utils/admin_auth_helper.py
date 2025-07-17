# backend/utils/admin_auth_helper.py

from fastapi import Request, HTTPException
from config import supabase

async def require_admin(request: Request):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise HTTPException(status_code=404)

    # Validasi di Supabase, pastikan admin masih aktif
    result = supabase.table("Admins").select("*").eq("id", admin_id).execute()
    data = result.data
    if not data or not data[0]["is_active"]:
        raise HTTPException(status_code=404)

    return data[0]  # balikin data admin
