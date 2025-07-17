# backend/routes/kursus.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from uuid import UUID

from config import supabase
from backend.utils.auth_helper import require_login
from backend.utils.logger import log_activity  # ✅ Tambahkan import logger

router = APIRouter()
templates = Jinja2Templates(directory="frontend")


@router.post("/modul/{modul_id}/selesai")
async def tandai_selesai(modul_id: UUID, telegram_id: str = Depends(require_login)):
    user_id = int(telegram_id)

    # ✅ Periksa apakah progress sudah ada
    existing_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", user_id).eq("module_id", str(modul_id)).execute()
    existing = existing_res.data

    if existing:
        supabase.table("ModuleProgress").update({"is_completed": True}) \
            .eq("user_id", user_id).eq("module_id", str(modul_id)).execute()
    else:
        supabase.table("ModuleProgress").insert({
            "user_id": user_id,
            "module_id": str(modul_id),
            "is_completed": True
        }).execute()

    # ✅ Ambil detail modul
    modul_res = supabase.table("Modules").select("level, title").eq("id", str(modul_id)).single().execute()
    modul = modul_res.data
    if not modul:
        return RedirectResponse("/dashboard", status_code=303)

    # ✅ Logging aktivitas
    log_activity(
        user_id=user_id,
        title=f"Modul: {modul['title']}",
        description=f"Selesaikan modul {modul['title']}",
        icon="clock"
    )

    level = modul["level"].lower()
    return RedirectResponse(f"/{level}/modul/{modul_id}", status_code=303)
