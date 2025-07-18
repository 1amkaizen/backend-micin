# File: main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from backend.routes import admin_user
from backend.routes import admin_module
from backend.routes import admin_exam
import typing

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

# === Middleware custom untuk limit upload size ===
class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next: typing.Callable):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_upload_size:
            return Response("File terlalu besar", status_code=413)
        return await call_next(request)

# Init FastAPI app
app = FastAPI()

# Middleware sessions
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Middleware limit upload
app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=10 * 1024 * 1024)  # 10MB

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template engine
templates = Jinja2Templates(directory="frontend")

# Home page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("user/home.html", {
        "request": request,
        "telegram_login_username": TELEGRAM_LOGIN_BOT_USERNAME,
        "BASE_URL": BASE_URL,
    })

# Custom 404 page
@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    raise exc

# Favicon
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")

# Auth routes
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
app.include_router(admin_user.router)
app.include_router(admin_module.router)
app.include_router(admin_exam.router)
