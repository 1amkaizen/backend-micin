# File: backend/routes/admin_module.py

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from backend.utils.admin_auth_helper import require_admin
from config import supabase
from fastapi import UploadFile, File
import uuid
import shutil
import os

router = APIRouter()


@router.post("/admin/modules/add")
async def tambah_modul(
    request: Request,
    level: str = Form(...),
    title: str = Form(...),
    video_url: str = Form(...),
    thumbnail: UploadFile = File(...),
    admin_data: dict = Depends(require_admin)
):
    if level not in ["SDM", "SMM", "SMA", "UMM"]:
        raise HTTPException(status_code=400, detail="Level tidak valid")

    # Upload thumbnail ke Supabase Storage modulthumbnails bucket
    ext = thumbnail.filename.split(".")[-1]
    filename = f"modulthumbnails/{uuid.uuid4()}.{ext}"
    content = await thumbnail.read()

    upload_response = supabase.storage.from_("modulthumbnails").upload(
        path=filename,
        file=content,
        file_options={"content-type": thumbnail.content_type}
    )

    if upload_response.get("error"):
        raise HTTPException(status_code=500, detail="Gagal upload thumbnail")

    public_url = supabase.storage.from_("modulthumbnails").get_public_url(filename)

    # Ambil order_index terakhir
    result = supabase.table("Modules")\
        .select("order_index")\
        .eq("level", level)\
        .order("order_index", desc=True)\
        .limit(1)\
        .execute()

    last_index = result.data[0]["order_index"] if result.data else 0
    next_index = last_index + 1

    # Simpan data modul ke Supabase
    supabase.table("Modules").insert({
        "level": level,
        "title": title,
        "video_url": video_url,
        "thumbnail_url": public_url,
        "order_index": next_index
    }).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)

@router.post("/admin/modules/edit")
async def edit_modul(
    request: Request,
    id: str = Form(...),
    level: str = Form(...),
    title: str = Form(...),
    video_url: str = Form(...),
    thumbnail: UploadFile = File(None),  # Optional thumbnail
    admin_data: dict = Depends(require_admin)
):
    if level not in ["SDM", "SMM", "SMA", "UMM"]:
        raise HTTPException(status_code=400, detail="Level tidak valid")

    data_update = {
        "level": level,
        "title": title,
        "video_url": video_url
    }

    if thumbnail:
        ext = thumbnail.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        content = await thumbnail.read()

        upload_response = supabase.storage.from_("modulthumbnails").update(
            path=filename,
            file=content,
            file_options={"content-type": thumbnail.content_type}
        )

        if upload_response.get("error"):
            raise HTTPException(status_code=500, detail="Gagal upload thumbnail")

        public_url = supabase.storage.from_("modulthumbnails").get_public_url(filename)
        data_update["thumbnail_url"] = public_url

    supabase.table("Modules").update(data_update).eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)


@router.post("/admin/modules/delete")
async def delete_modul(
    request: Request,
    id: str = Form(...),
    admin_data: dict = Depends(require_admin)
):
    if not id:
        raise HTTPException(status_code=400, detail="ID modul tidak valid")

    supabase.table("Modules").delete().eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-module", status_code=302)
