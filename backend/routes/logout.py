# backend/routes/logout.py

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("telegram_id")
    return response
