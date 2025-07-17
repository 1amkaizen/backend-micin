# backend/routes/progress.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from config import supabase
from datetime import datetime
from backend.utils.auth_helper import require_login
from uuid import UUID
from typing import List
from pydantic import BaseModel

router = APIRouter()

class ModuleProgressOut(BaseModel):
    id: str  # <- ganti dari module_id
    title: str
    video_url: str
    order_index: int
    is_completed: bool


@router.post("/progress/{module_id}")
async def mark_progress(module_id: UUID, request: Request, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    print("📥 Mulai upsert progress:", telegram_id, module_id)

    # Cek apakah modul valid
    module_res = supabase.table("Modules").select("id").eq("id", str(module_id)).single().execute()
    if not module_res.data:
        raise HTTPException(status_code=404, detail="Module not found")

    try:
        response = supabase.table("ModuleProgress").upsert({
            "user_id": int(telegram_id),
            "module_id": str(module_id),
            "is_completed": True,
            "completed_at": datetime.utcnow().isoformat()
        }, on_conflict="user_id,module_id").execute()  # ← Fix: ubah ke string

        print("✅ Berhasil upsert:", response)
    except Exception as e:
        print("❌ Gagal upsert:", e)
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {e}")

    return {"status": "success", "message": "Progress updated"}


@router.get("/progress/{level}", response_model=List[ModuleProgressOut])
async def get_progress_by_level(level: str, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    # Ambil semua modul di level ini
    modules_res = supabase.table("Modules").select("*").eq("level", level).order("order_index", desc=False).execute()
    modules = modules_res.data or []

    # Ambil progress user
    progress_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", int(telegram_id)).execute()
    progress = progress_res.data or []

    # Buat map modul yang sudah selesai
    prog_map = {p["module_id"]: p["is_completed"] for p in progress}

    result = []
    for m in modules:
        result.append(ModuleProgressOut(
            module_id=m["id"],
            title=m["title"],
            video_url=m["video_url"],
            order_index=m["order_index"],
            is_completed=prog_map.get(m["id"], False)
        ))
    result = []
    for m in modules:
        result.append(ModuleProgressOut(
            id=m["id"],
            title=m["title"],
            video_url=m["video_url"],
            order_index=m["order_index"],
            is_completed=prog_map.get(m["id"], False)
        ))

    return result

