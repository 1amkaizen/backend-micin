# backend/routes/admin_dashboard.py

from fastapi import APIRouter, Request, Form, HTTPException,Depends,Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

from backend.utils.admin_auth_helper import require_admin
from config import supabase
from backend.routes.admin_exam import get_all_exams
from backend.utils.payment_helper import get_all_transactions
from datetime import datetime,timedelta
router = APIRouter()
templates = Jinja2Templates(directory="frontend")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===============================
# DASHBOARD UTAMA 
# ===============================
from collections import defaultdict
from backend.utils.time_helper import safe_parse_date


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin = await require_admin(request)

    # Statistik user
    total_users = supabase.table("Users").select("id", count="exact").execute().count or 0
    vip_users = supabase.table("Users").select("id", count="exact").eq("is_vip", True).execute().count or 0
    free_users = supabase.table("Users").select("id", count="exact").eq("is_vip", False).execute().count or 0
    modul_aktif = supabase.table("Modules").select("id", count="exact").execute().count or 0

    # Grafik bar: statistik pertumbuhan anggota
    user_created = supabase.table("Users").select("created_at").execute().data or []
    bulan_counter = defaultdict(int)
    for u in user_created:
        created = safe_parse_date(u.get("created_at"))
        if created:
            key = created.strftime("%b")  # Jan, Feb, dll
            bulan_counter[key] += 1

    bulan_order = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    anggota_growth_data = [{"label": b, "percent": min(bulan_counter.get(b, 0) * 5, 100)} for b in bulan_order]

    # Pertumbuhan bulan ini vs sebelumnya
    now = datetime.utcnow()
    this_month = now.strftime("%b")
    prev_month = (now.replace(day=1) - timedelta(days=1)).strftime("%b")

    growth_now = bulan_counter.get(this_month, 0)
    growth_prev = bulan_counter.get(prev_month, 1) or 1  # hindari divide by zero
    user_growth_percent = round((growth_now - growth_prev) / growth_prev * 100, 2)

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin_email": admin["email"],
        "admin_role": admin["role"],
        "created_at": admin["created_at"],
        "permissions": admin["permissions"],
        "total_users": total_users,
        "vip_users": vip_users,
        "free_users": free_users,
        "modul_aktif": modul_aktif,
        "growth_user": "+0%",     # placeholder bisa kamu isi real nanti
        "growth_vip": "+0%",
        "growth_free": "+0%",
        "growth_modul": "+0%",
        "anggota_growth_data": anggota_growth_data,
        "user_growth_percent": user_growth_percent,
    })

# ===============================
# HALAMAN TAMBAH ADMIN (GET)
# ===============================
@router.get("/admin/dashboard/kelola-admin", response_class=HTMLResponse)
async def kelola_admin_form(request: Request):
    admin = await require_admin(request)

    permissions = admin.get("permissions") or {}
    if admin["role"] != "superadmin" and not permissions.get("can_manage_admin"):
        return templates.TemplateResponse("admin/no_access.html", {
            "request": request,
            "message": "Kamu tidak punya akses untuk menambah admin."
        })

    return templates.TemplateResponse("admin/kelola_admin.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": admin["role"] == "superadmin",
        "admins": get_all_admins()
    })



# ===============================
# SUBMIT TAMBAH ADMIN (POST)
# ===============================
@router.post("/admin/dashboard/kelola-admin", response_class=HTMLResponse)
async def kelola_admin_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    admin = await require_admin(request)

    permissions = admin.get("permissions") or {}
    if admin["role"] != "superadmin" and not permissions.get("can_manage_admin"):
        return templates.TemplateResponse("admin/no_access.html", {
            "request": request,
            "message": "Kamu tidak punya akses untuk menambah admin."
        })

    existing = supabase.table("Admins").select("*").eq("email", email).execute().data
    if existing:
        return templates.TemplateResponse("admin/kelola_admin.html", {
            "request": request,
            "admin_email": admin["email"],
            "error": "Email sudah digunakan"
        })

    password_hash = pwd_context.hash(password)
    supabase.table("Admins").insert({
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "is_active": True
    }).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-admin", status_code=303)



# ===============================
# HALAMAN KELOLA USER (GET)
# ===============================
@router.get("/admin/dashboard/kelola-user", response_class=HTMLResponse)
async def kelola_user_page(request: Request):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_edit_user"):
            return templates.TemplateResponse("admin/no_access.html", {
                "request": request,
                "message": "Kamu tidak punya akses ke halaman Kelola User."
            })

    users = get_all_users()
    return templates.TemplateResponse("admin/kelola_user.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": True,
        "users": users
    })

# ===============================
# HALAMAN KELOLA MODUL (GET)
# ===============================
@router.get("/admin/dashboard/kelola-module", response_class=HTMLResponse)
async def kelola_module_page(request: Request):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_manage_module"):
            return templates.TemplateResponse("admin/no_access.html", {
                "request": request,
                "message": "Kamu tidak punya akses ke halaman Kelola Modul."
            })

    modules = get_all_modules()
    return templates.TemplateResponse("admin/kelola_module.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": admin["role"] == "superadmin",
        "modules": modules
    })


# ===============================
# HALAMAN KELOLA UJIAN (GET)
# ===============================
@router.get("/admin/dashboard/kelola-ujian", response_class=HTMLResponse)
async def kelola_ujian_page(request: Request):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_manage_exam"):
            return templates.TemplateResponse("admin/no_access.html", {
                "request": request,
                "message": "Kamu tidak punya akses ke halaman Kelola Ujian."
            })

    exams = await get_all_exams()
    return templates.TemplateResponse("admin/kelola_ujian.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": admin["role"] == "superadmin",
        "exams": exams
    })



# ===============================
# HALAMAN KELOLA TRANSAKSI (GET)
# ===============================
@router.get("/admin/dashboard/kelola-transaksi", response_class=HTMLResponse)
async def kelola_transaksi_page(request: Request):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_manage_transaksi"):
            return templates.TemplateResponse("admin/no_access.html", {
                "request": request,
                "message": "Kamu tidak punya akses ke halaman Kelola Transaksi."
            })

    # gunakan await jika fungsinya async
    transactions =  get_all_transactions()

    return templates.TemplateResponse("admin/kelola_transaksi.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": admin["role"] == "superadmin",
        "transactions": transactions
    })


# ===============================
# HALAMAN KELOLA HARGA (GET)
# ===============================
@router.get("/admin/dashboard/kelola-harga", response_class=HTMLResponse)
async def kelola_harga_page(request: Request):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_manage_prices"):
            return templates.TemplateResponse("admin/no_access.html", {
                "request": request,
                "message": "Kamu tidak punya akses ke halaman Kelola Harga."
            })

    # Ambil harga dari Settings
    result = supabase.table("Settings") \
        .select("key,value") \
        .in_("key", ["vip_price", "addon_sma_price", "addon_umm_price"]) \
        .execute()

    rows = result.data or []
    harga = {row["key"]: row["value"] for row in rows}

    for key in ['vip_price', 'addon_sma_price', 'addon_umm_price']:
        if key not in harga:
            harga[key] = "0"

    # Ambil semua harga ecer dari tabel EcerPrices
    result_ecer = supabase.table("EcerPrices") \
        .select("id,price") \
        .order("price", desc=False) \
        .execute()

    ecer_prices = result_ecer.data or []

    return templates.TemplateResponse("admin/kelola_harga.html", {
        "request": request,
        "admin_email": admin["email"],
        "is_superadmin": admin["role"] == "superadmin",
        "harga": harga,
        "ecer_prices": ecer_prices,  # ini dikirim ke template
    })

# ===============================
# SUBMIT FORM HARGA (POST)
# ===============================
@router.post("/admin/dashboard/kelola-harga/update")
async def update_harga(request: Request, data: dict = Body(...)):
    admin = await require_admin(request)

    if admin["role"] != "superadmin":
        permissions = admin.get("permissions") or {}
        if not permissions.get("can_manage_prices"):
            raise HTTPException(status_code=403, detail="Tidak punya akses.")

    # ✅ Update harga utama (VIP, Addon SMA, Addon UMM)
    allowed_keys = ['vip_price', 'addon_sma_price', 'addon_umm_price']
    updates = {k: v for k, v in data.items() if k in allowed_keys}

    for key, value in updates.items():
        supabase.table("Settings").upsert({
            "key": key,
            "value": str(value)
        }, on_conflict=["key"]).execute()

    # ✅ Update harga eceran (EcerPrices)
    ecer_price_updates = {k: v for k, v in data.items() if k.startswith("ecer_price_")}

    for field_name, value in ecer_price_updates.items():
        try:
            ecer_id = int(field_name.replace("ecer_price_", ""))
            price_value = int(value)
        except ValueError:
            continue  # skip jika parsing gagal

        supabase.table("EcerPrices").update({
            "price": price_value
        }).eq("id", ecer_id).execute()

    return {"message": "Harga berhasil diperbarui"}




# ===============================
# HELPER FUNCTIONS
# ===============================
def get_all_admins():
    result = supabase.table("Admins").select("id, email, role, is_active, created_at").order("created_at").execute()
    return result.data


def get_all_users():
    result = supabase.table("Users").select("id, username, full_name, is_vip, is_active, vip_since, created_at").order("created_at").execute()
    return result.data


def get_all_modules():
    result = supabase.table("Modules").select("*").order("level").order("order_index").execute()
    return result.data or []
