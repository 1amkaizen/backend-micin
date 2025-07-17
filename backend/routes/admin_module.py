# backend/routes/admin_module.py

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from backend.utils.admin_auth_helper import require_admin
from config import supabase

router = APIRouter()


@router.post("/admin/modules/add")
async def tambah_modul(
    request: Request,
    level: str = Form(...),
    title: str = Form(...),
    video_url: str = Form(...),
    admin_data: dict = Depends(require_admin)
):
    if level not in ["SDM", "SMM", "SMA", "UMM"]:
        raise HTTPException(status_code=400, detail="Level tidak valid")

    # Ambil order_index terakhir untuk level ini
    result = supabase.table("Modules")\
        .select("order_index")\
        .eq("level", level)\
        .order("order_index", desc=True)\
        .limit(1)\
        .execute()

    last_index = result.data[0]["order_index"] if result.data else 0
    next_index = last_index + 1

    # Simpan ke Supabase
    supabase.table("Modules").insert({
        "level": level,
        "title": title,
        "video_url": video_url,
        "order_index": next_index
    }).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)



# 🔧 Perbaikan: Edit modul tanpa order_index
@router.post("/admin/modules/edit")
async def edit_modul(
    request: Request,
    id: str = Form(...),
    level: str = Form(...),
    title: str = Form(...),
    video_url: str = Form(...),
    admin_data: dict = Depends(require_admin)
):
    # Validasi data level
    if level not in ["SDM", "SMM", "SMA", "UMM"]:
        raise HTTPException(status_code=400, detail="Level tidak valid")

    # Update ke Supabase
    supabase.table("Modules").update({
        "level": level,
        "title": title,
        "video_url": video_url
    }).eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)

@router.post("/admin/modules/delete")
async def delete_modul(
    request: Request,
    id: str = Form(...),
    admin_data: dict = Depends(require_admin)
):
    # Validasi ID (optional)
    if not id:
        raise HTTPException(status_code=400, detail="ID modul tidak valid")

    # Hapus modul dari Supabase
    supabase.table("Modules").delete().eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)