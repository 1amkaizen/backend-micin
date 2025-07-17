# backend/routes/ujian.py

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from config import supabase
from backend.utils.auth_helper import require_login
from backend.services.pdf_generator import generate_sertifikat
from backend.utils.logger import log_activity  # ✅ Tambahkan ini
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="frontend")


@router.get("/ujian/cek/{level}")
async def cek_kelayakan_ujian(level: str, telegram_id: str = Depends(require_login)):
    modul_res = supabase.table("Modules").select("id").eq("level", level).execute()
    modul_ids = [m["id"] for m in modul_res.data or []]

    if not modul_ids:
        return {"boleh_ujian": False}

    progress_res = supabase.table("ModuleProgress").select("module_id, is_completed") \
        .eq("user_id", int(telegram_id)).in_("module_id", modul_ids).execute()
    progress_map = {p["module_id"]: p["is_completed"] for p in (progress_res.data or [])}

    semua_selesai = all(progress_map.get(mid, False) for mid in modul_ids)
    return {"boleh_ujian": semua_selesai}


@router.get("/ujian/{level}")
async def tampil_ujian(level: str, request: Request, telegram_id: str = Depends(require_login)):
    res = supabase.table("Exams").select("id, question, options").eq("level", level).execute()
    soal_list = res.data or []

    return templates.TemplateResponse("/user/dashboard/partials/ujian_isi.html", {
        "request": request,
        "level": level,
        "soal_list": soal_list,
        "telegram_id": telegram_id
    })



@router.post("/ujian/{level}", response_class=HTMLResponse)
async def proses_ujian(level: str, request: Request, telegram_id: str = Depends(require_login)):
    # 🔒 Validasi apakah semua modul sudah selesai
    modul_res = supabase.table("Modules").select("id").eq("level", level).execute()
    modul_ids = [m["id"] for m in modul_res.data or []]

    progress_res = supabase.table("ModuleProgress").select("module_id, is_completed") \
        .eq("user_id", int(telegram_id)).in_("module_id", modul_ids).execute()
    progress_map = {p["module_id"]: p["is_completed"] for p in (progress_res.data or [])}
    semua_selesai = all(progress_map.get(mid, False) for mid in modul_ids)

    if not semua_selesai:
        return templates.TemplateResponse("/user/dashboard/partials/hasil_ujian.html", {
            "request": request,
            "level": level,
            "nilai": 0,
            "lulus": False,
            "total": 0,
            "benar": 0,
            "attempt": 0,
            "pesan_error": "⚠️ Kamu belum menyelesaikan semua modul. Harap selesaikan terlebih dahulu sebelum mengikuti ujian."
        })

    # 🔽 Lanjut proses ujian seperti biasa
    user_res = supabase.table("Users").select("full_name, last_reset").eq("user_id", int(telegram_id)).single().execute()
    last_reset = user_res.data.get("last_reset") if user_res.data else None
    nama_user = user_res.data.get("full_name") or f"User {telegram_id}"

    # Hitung gagal sejak reset terakhir
    query = supabase.table("ExamResults").select("id", "created_at") \
        .eq("user_id", int(telegram_id)).eq("level", level).eq("passed", False)
    if last_reset:
        query = query.gte("created_at", last_reset)
    gagal_res = query.execute()
    jumlah_gagal = len(gagal_res.data or [])

    # Ambil soal
    soal_res = supabase.table("Exams").select("id, answer").eq("level", level).execute()
    soal_data = soal_res.data or []

    total = len(soal_data)
    benar = 0
    form_data = await request.form()

    for soal in soal_data:
        qid = soal["id"]
        jawaban_user = form_data.get(f"jawaban_{qid}")
        if jawaban_user is not None and int(jawaban_user) == soal["answer"]:
            benar += 1

    nilai = round((benar / total) * 100) if total > 0 else 0
    lulus = nilai >= 100
    attempt_ke = jumlah_gagal + 1

    # Simpan hasil ujian
    supabase.table("ExamResults").insert({
        "user_id": int(telegram_id),
        "level": level,
        "score": nilai,
        "passed": lulus,
        "attempt": attempt_ke
    }).execute()

    # Logging & Reset jika gagal 3x
    if not lulus and jumlah_gagal + 1 >= 3:
        for mid in modul_ids:
            supabase.table("ModuleProgress").update({"is_completed": False}) \
                .eq("user_id", int(telegram_id)).eq("module_id", mid).execute()

        supabase.table("Users").update({
            "last_reset": datetime.utcnow().isoformat()
        }).eq("user_id", int(telegram_id)).execute()

        log_activity(
            user_id=int(telegram_id),
            title=f"Ujian {level}",
            description="Gagal 3x berturut-turut. Progress telah di-reset.",
            icon="alert-triangle"
        )

        return templates.TemplateResponse("/user/dashboard/partials/hasil_ujian.html", {
            "request": request,
            "level": level,
            "nilai": nilai,
            "lulus": False,
            "total": total,
            "benar": benar,
            "attempt": attempt_ke,
            "pesan_error": "❌ Kamu sudah gagal 3x. Progress di-reset. Silakan ulang modul dari awal."
        })

    if not lulus:
        log_activity(
            user_id=int(telegram_id),
            title=f"Ujian {level}",
            description=f"Gagal ujian {level} (percobaan ke-{attempt_ke})",
            icon="x"
        )

    if lulus:
        log_activity(
            user_id=int(telegram_id),
            title=f"Ujian {level}",
            description=f"Berhasil lulus ujian {level} dengan skor {nilai}/100",
            icon="check"
        )

    filename = None
    if lulus:
        filename = f"sertifikat_{telegram_id}_{level}.pdf"
        generate_sertifikat(nama_user, level, filename)

    context = {
        "request": request,
        "level": level,
        "nilai": nilai,
        "lulus": lulus,
        "total": total,
        "benar": benar,
        "attempt": attempt_ke,
    }
    if filename:
        context["filename"] = filename

    return templates.TemplateResponse("/user/dashboard/partials/hasil_ujian.html", context)
