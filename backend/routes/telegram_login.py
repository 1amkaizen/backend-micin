# backend/routes/telegram_login.py

from fastapi import APIRouter, Request, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.services.telegram_auth import check_telegram_auth
from config import TELEGRAM_LOGIN_BOT_USERNAME, BASE_URL, supabase
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="frontend")  # ← Pastikan sesuai path kamu


# backend/routes/telegram_login.py

@router.get("/login")
async def telegram_login(request: Request, telegram_id: str = Cookie(default=None)):
    params = dict(request.query_params)

    # Sudah login, langsung redirect
    if telegram_id:
        return RedirectResponse(url="/dashboard")

    # Tampilkan halaman login kalau tidak ada param Telegram
    if "id" not in params:
        return templates.TemplateResponse("user/login.html", {
            "request": request,
            "telegram_login_username": TELEGRAM_LOGIN_BOT_USERNAME,
            "BASE_URL": BASE_URL
        })

    # Validasi login Telegram
    if not check_telegram_auth(params):
        return RedirectResponse(url="/login_failed")

    # Proses data user dari Telegram
    user_id = int(params["id"])
    username = params.get("username", "")
    first_name = params.get("first_name", "")
    last_name = params.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    created_at = datetime.utcnow().isoformat()
    photo_url = params.get("photo_url")  


    existing = supabase.table("Users").select("user_id").eq("user_id", user_id).execute()
    if not existing.data:
        supabase.table("Users").insert({
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "created_at": created_at,
            "photo_url": photo_url, 
        }).execute()

    # Set cookie login
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(key="telegram_id", value=str(user_id), httponly=True)
    return response
