# backend/routes/admin_auth.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from config import supabase

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="frontend")

# Route GET: tampilkan form login admin
@router.get("/admin/login", response_class=HTMLResponse)
async def show_admin_login(request: Request):
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": None
    })

# Route POST: proses login admin
@router.post("/admin/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    result = supabase.table("Admins").select("*").eq("email", email).execute()
    data = result.data

    if not data or not data[0]["is_active"]:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Akun tidak ditemukan atau tidak aktif.",
            "email": email
        }, status_code=401)

    admin = data[0]
    if not pwd_context.verify(password, admin["password_hash"]):
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Password salah.",
            "email": email
        }, status_code=401)

    # Simpan session login
    request.session["admin_id"] = admin["id"]
    request.session["admin_role"] = admin["role"]

    return RedirectResponse(url="/admin/dashboard", status_code=303)
