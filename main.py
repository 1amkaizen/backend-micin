# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from backend.routes import admin_user
from backend.routes import admin_module
from backend.routes import admin_exam  

# Import dari config
from config import TELEGRAM_LOGIN_BOT_USERNAME, BASE_URL, supabase, SECRET_KEY

# Import semua route
from backend.routes import (
    telegram_login,
    logout,
    kursus,
    progress,
    ujian,
    dashboard,
    payment,
    admin_auth,
    admin_dashboard
)

# Init app
app = FastAPI()

# Middleware session harus ditambahkan sebelum router
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files (CSS, sertifikat, dll)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(admin_user.router)
# Template engine (HTML Jinja2)
templates = Jinja2Templates(directory="frontend")

# ==== Routing ====

# Home page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user/home.html", {
        "request": request,
        "telegram_login_username": TELEGRAM_LOGIN_BOT_USERNAME,
        "BASE_URL": BASE_URL,
    })

# 404 page
@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    raise exc


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


# Auth Telegram
app.include_router(telegram_login.router) 
app.include_router(logout.router)

# User routes
app.include_router(dashboard.router)
app.include_router(kursus.router)
app.include_router(progress.router)
app.include_router(ujian.router)
app.include_router(payment.router)

# Admin routes
app.include_router(admin_auth.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_module.router)
app.include_router(admin_exam.router)  
