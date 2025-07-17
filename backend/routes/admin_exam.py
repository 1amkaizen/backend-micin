# backend/routes/admin_exam.py

from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from backend.utils.admin_auth_helper import require_admin
from config import supabase
from uuid import uuid4


router = APIRouter()

# ================================
# 🟢 Tambah Soal
# ================================
@router.post("/admin/exams/add")
async def tambah_soal(
    request: Request,
    level: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    answer: int = Form(...),  # 0–3 (A–D)
    admin: dict = Depends(require_admin)
):
    options = [option_a, option_b, option_c, option_d]

    supabase.table("Exams").insert({
        "id": str(uuid4()),  # ← Generate UUID secara manual
        "level": level,
        "question": question,
        "options": options,
        "answer": answer
    }).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-ujian", status_code=303)


# ================================
# 📄 Ambil Semua Soal
# ================================
@router.get("/admin/exams", tags=["Admin - Exams"])
async def get_all_exams(admin_data: dict = Depends(require_admin)):
    result = supabase.table("Exams").select("*").order("level").execute()
    return result.data or []


# ================================
# ✏️ Edit Soal
# ================================
@router.post("/admin/exams/edit")
async def edit_exam(
    id: str = Form(...),
    level: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    answer: int = Form(...),
    admin: dict = Depends(require_admin)
):
    if not id or id.strip() == "":
        raise HTTPException(status_code=400, detail="ID soal tidak valid")

    options = [option_a, option_b, option_c, option_d]

    supabase.table("Exams").update({
        "level": level,
        "question": question,
        "options": options,
        "answer": answer
    }).eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-ujian", status_code=303)


# ================================
# ❌ Hapus Soal
# ================================
@router.post("/admin/exams/delete")
async def hapus_exam(
    id: str = Form(...),
    admin: dict = Depends(require_admin)
):
    if not id or id.strip() == "":
        raise HTTPException(status_code=400, detail="ID soal tidak valid")

    supabase.table("Exams").delete().eq("id", id).execute()

    return RedirectResponse(url="/admin/dashboard/kelola-ujian", status_code=303)
