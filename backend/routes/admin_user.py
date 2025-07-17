# backend/routes/admin_user.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from backend.utils.admin_auth_helper import require_admin
from config import supabase
from datetime import datetime
from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
from typing import Optional
templates = Jinja2Templates(directory="frontend")

router = APIRouter()

@router.post("/admin/edit-user")
async def edit_user(
    request: Request,
    id: str = Form(...),
    is_vip: str = Form(...),
    is_active: str = Form(...)
):
    current_admin = await require_admin(request)

    is_vip_bool = is_vip.lower() == "true"
    is_active_bool = is_active.lower() == "true"

    supabase.table("Users").update({
        "is_vip": is_vip_bool,
        "is_active": is_active_bool,
        "vip_since": datetime.utcnow().strftime("%Y-%m-%d") if is_vip_bool else None
    }).eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-user", status_code=303)


# ===============================
# HALAMAN EDIT ADMIN (GET)
# ===============================
@router.get("/admin/dashboard/edit-admin/{admin_id}")
async def edit_admin_form(request: Request, admin_id: str):
    current_admin = await require_admin(request)
    if current_admin["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin")

    admin_res = supabase.table("Admins").select("*").eq("id", admin_id).single().execute()
    admin_data = admin_res.data
    if not admin_data:
        raise HTTPException(status_code=404, detail="Admin tidak ditemukan")

    return templates.TemplateResponse("admin/edit_admin.html", {
        "request": request,
        "admin": admin_data
    })

# ===============================
# SUBMIT EDIT ADMIN (POST)
# ===============================
@router.post("/admin/dashboard/edit-admin/{admin_id}")
async def edit_admin_submit(
    request: Request,
    admin_id: str,
    email: str = Form(...),
    role: str = Form(...),
    is_active: str = Form(...)
):
    current_admin = await require_admin(request)
    if current_admin["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin")

    is_active_bool = is_active.lower() == "true"

    supabase.table("Admins").update({
        "email": email,
        "role": role,
        "is_active": is_active_bool
    }).eq("id", admin_id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-admin", status_code=303)


# ===============================
# HAPUS ADMIN (POST)
# ===============================
@router.post("/admin/dashboard/delete-admin/{admin_id}")
async def delete_admin(request: Request, admin_id: str):
    current_admin = await require_admin(request)
    if current_admin["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin")

    supabase.table("Admins").delete().eq("id", admin_id).execute()
    return RedirectResponse(url="/admin/dashboard/kelola-admin", status_code=303)


# ===============================
# HALAMAN PERMISSIONS ADMIN (GET)
# ===============================
@router.get("/admin/dashboard/permissions/{admin_id}")
async def permissions_form(request: Request, admin_id: str):
    current_admin = await require_admin(request)
    if current_admin["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin")

    admin_res = supabase.table("Admins").select("*").eq("id", admin_id).single().execute()
    admin_data = admin_res.data
    if not admin_data:
        raise HTTPException(status_code=404, detail="Admin tidak ditemukan")

    # default permission jika kosong
    permissions = admin_data.get("permissions") or {}

    return templates.TemplateResponse("admin/permissions_admin.html", {
        "request": request,
        "admin": admin_data,
        "permissions": permissions
    })

# ===============================
# SUBMIT PERMISSIONS ADMIN (POST)
# ===============================
@router.post("/admin/dashboard/permissions/{admin_id}")
async def update_permissions(
    request: Request,
    admin_id: str,
    can_edit_user: Optional[str] = Form(None),
    can_manage_module: Optional[str] = Form(None),
    can_manage_exam: Optional[str] = Form(None),
    can_manage_transaksi: Optional[str] = Form(None),
    can_manage_prices: Optional[str] = Form(None),  # 🆕
    can_manage_addon_permissions: Optional[str] = Form(None),  # 🆕
):
    current_admin = await require_admin(request)
    if current_admin["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Hanya superadmin")

    permissions = {
        "can_edit_user": bool(can_edit_user),
        "can_manage_module": bool(can_manage_module),
        "can_manage_exam": bool(can_manage_exam),
        "can_manage_transaksi": bool(can_manage_transaksi),
        "can_manage_prices": bool(can_manage_prices),  # 🆕
        "can_manage_addon_permissions": bool(can_manage_addon_permissions),  # 🆕
    }

    supabase.table("Admins").update({
        "permissions": permissions
    }).eq("id", admin_id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-admin", status_code=303)
