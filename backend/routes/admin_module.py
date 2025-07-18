# File: backend/routes/admin_module.py

from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from backend.utils.admin_auth_helper import require_admin
from config import supabase
import uuid

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

    ext = thumbnail.filename.split(".")[-1].lower()
    filename = f"modulthumbnails/{uuid.uuid4()}.{ext}"
    content = await thumbnail.read()

    print("=== [Upload Thumbnail] ===")
    print("Filename:", thumbnail.filename)
    print("Content Type:", thumbnail.content_type)
    print("Size:", len(content))
    print("Generated path:", filename)

    try:
        supabase.storage.from_("modulthumbnails").upload(
            path=filename,
            file=content,
            file_options={"content-type": thumbnail.content_type}
        )
    except Exception as e:
        print("[ERROR] Gagal upload ke Supabase:", e)
        raise HTTPException(status_code=500, detail=f"Gagal upload thumbnail: {str(e)}")

    public_url = supabase.storage.from_("modulthumbnails").get_public_url(filename)
    print("Public URL:", public_url)

    # Hitung order_index
    try:
        result = supabase.table("Modules")\
            .select("order_index")\
            .eq("level", level)\
            .order("order_index", desc=True)\
            .limit(1)\
            .execute()
        last_index = result.data[0]["order_index"] if result.data else 0
    except Exception as e:
        print("[ERROR] Gagal mengambil order_index:", e)
        raise HTTPException(status_code=500, detail="Gagal menghitung order_index")

    next_index = last_index + 1

    # Simpan modul
    try:
        supabase.table("Modules").insert({
            "level": level,
            "title": title,
            "video_url": video_url,
            "thumbnail_url": public_url,
            "order_index": next_index
        }).execute()
    except Exception as e:
        print("[ERROR] Gagal menyimpan modul:", e)
        raise HTTPException(status_code=500, detail="Gagal menyimpan data modul")

    print("[SUCCESS] Modul berhasil ditambahkan.")
    return RedirectResponse(
        url="/admin/dashboard/kelola-module?success=Modul berhasil ditambahkan", 
        status_code=302
    )



@router.post("/admin/modules/edit")
async def edit_modul(
    request: Request,
    id: str = Form(...),
    level: str = Form(...),
    title: str = Form(...),
    video_url: str = Form(...),
    thumbnail: UploadFile = File(None),
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
        filename = f"modulthumbnails/{uuid.uuid4()}.{ext}"
        content = await thumbnail.read()

        print("=== [Edit Thumbnail Upload] ===")
        print("Filename:", thumbnail.filename)
        print("Content Type:", thumbnail.content_type)
        print("Size:", len(content))
        print("Generated path:", filename)

        try:
            supabase.storage.from_("modulthumbnails").upload(
                path=filename,
                file=content,
                file_options={"content-type": thumbnail.content_type}
            )
        except Exception as e:
            print("[ERROR] Gagal upload saat edit:", e)
            raise HTTPException(status_code=500, detail=f"Gagal upload thumbnail: {str(e)}")

        public_url = supabase.storage.from_("modulthumbnails").get_public_url(filename)
        data_update["thumbnail_url"] = public_url
        print("Public URL (updated):", public_url)

    try:
        supabase.table("Modules").update(data_update).eq("id", id).execute()
    except Exception as e:
        print("[ERROR] Gagal update modul:", e)
        raise HTTPException(status_code=500, detail="Gagal mengupdate modul")

    print("[SUCCESS] Modul berhasil diupdate.")
    return RedirectResponse(
        url="/admin/dashboard/kelola-module?success=Modul berhasil diupdate", 
        status_code=302
    )



@router.post("/admin/modules/delete")
async def delete_modul(
    request: Request,
    id: str = Form(...),
    admin_data: dict = Depends(require_admin)
):
    if not id:
        raise HTTPException(status_code=400, detail="ID modul tidak valid")

    try:
        supabase.table("Modules").delete().eq("id", id).execute()
    except Exception as e:
        print("[ERROR] Gagal menghapus modul:", e)
        raise HTTPException(status_code=500, detail="Gagal menghapus modul")

    print("[SUCCESS] Modul berhasil dihapus.")
    return RedirectResponse(
        url="/admin/dashboard/kelola-module?success=Modul berhasil dihapus", 
        status_code=302
    )

