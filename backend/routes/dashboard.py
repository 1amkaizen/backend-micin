from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from backend.utils.auth_helper import require_login
from backend.utils.time_helper import safe_parse_date
from config import supabase
from uuid import UUID
from datetime import datetime,timedelta
import os
from starlette.status import HTTP_303_SEE_OTHER
from config import MIDTRANS_CLIENT_KEY, ADMIN_TELEGRAM_USERNAME
from collections import defaultdict


router = APIRouter()
templates = Jinja2Templates(directory="frontend")

# helper: parse ISO date ke datetime
def safe_parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


@router.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard(request: Request, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    # Tentukan badge level berdasarkan status VIP dan addon
    is_vip = user.get("is_vip", False)
    is_sma_addon = user.get("is_sma_addon", False)
    is_umm = user.get("is_umm", False)

    if is_vip and is_sma_addon and is_umm:
        user_badge_level = "UMM"
    elif is_vip and is_sma_addon:
        user_badge_level = "SMA"
    elif is_vip:
        user_badge_level = "SMM"
    else:
        user_badge_level = "SDM"

    now = datetime.utcnow()
    bulan_ini = now.replace(day=1)
    bulan_lalu = (bulan_ini - timedelta(days=1)).replace(day=1)

    def growth_percentage(this_month_count, last_month_count):
        if last_month_count == 0:
            return 100 if this_month_count > 0 else 0
        return round(((this_month_count - last_month_count) / last_month_count) * 100)

    # Statistik komunitas
    total_users = supabase.table("Users").select("id", count="exact").execute().count or 0
    vip_users = supabase.table("Users").select("id", count="exact").eq("is_vip", True).execute().count or 0
    modul_aktif = supabase.table("Modules").select("id", count="exact").execute().count or 0
    free_users = supabase.table("Users").select("id", count="exact").eq("is_vip", False).execute().count or 0

    # Pertumbuhan per kategori
    user_this_month = supabase.table("Users").select("id", count="exact") \
        .gte("created_at", bulan_ini.isoformat()).execute().count or 0
    user_last_month = supabase.table("Users").select("id", count="exact") \
        .gte("created_at", bulan_lalu.isoformat()).lt("created_at", bulan_ini.isoformat()).execute().count or 0
    growth_user = f"+{growth_percentage(user_this_month, user_last_month)}%"

    vip_this_month = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", True).gte("vip_since", bulan_ini.isoformat()).execute().count or 0
    vip_last_month = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", True).gte("vip_since", bulan_lalu.isoformat()).lt("vip_since", bulan_ini.isoformat()).execute().count or 0
    growth_vip = f"+{growth_percentage(vip_this_month, vip_last_month)}%"

    modul_this_month = supabase.table("Modules").select("id", count="exact") \
        .gte("created_at", bulan_ini.isoformat()).execute().count or 0
    modul_last_month = supabase.table("Modules").select("id", count="exact") \
        .gte("created_at", bulan_lalu.isoformat()).lt("created_at", bulan_ini.isoformat()).execute().count or 0
    growth_modul = f"+{growth_percentage(modul_this_month, modul_last_month)}%"

    free_this_month = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", False).gte("created_at", bulan_ini.isoformat()).execute().count or 0
    free_last_month = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", False).gte("created_at", bulan_lalu.isoformat()).lt("created_at", bulan_ini.isoformat()).execute().count or 0
    growth_free = f"+{growth_percentage(free_this_month, free_last_month)}%"

    # Statistik per level
    levels = ["SDM", "SMM", "SMA", "UMM"]
    statistik_per_level = []
    for level in levels:
        mod_res = supabase.table("Modules").select("id").eq("level", level).execute()
        modul_ids = [m["id"] for m in mod_res.data or []]
        total = len(modul_ids)

        prog_res = supabase.table("ModuleProgress").select("module_id") \
            .eq("user_id", int(telegram_id)).in_("module_id", modul_ids) \
            .eq("is_completed", True).execute()
        selesai = len(prog_res.data or [])

        statistik_per_level.append({
            "level": level,
            "total": total,
            "selesai": selesai
        })

    # Ujian terakhir
    ujian_res = supabase.table("ExamResults").select("*") \
        .eq("user_id", int(telegram_id)).order("created_at", desc=True).limit(1).execute()
    last_exam = ujian_res.data[0] if ujian_res.data else None
    has_certificate = last_exam.get("passed") if last_exam else False

    # Aktivitas terakhir
    aktivitas_res = supabase.table("ActivityLogs").select("*") \
        .eq("user_id", int(telegram_id)).order("created_at", desc=True).limit(10).execute()
    aktivitas = aktivitas_res.data or []

    # Grafik bar: statistik pertumbuhan anggota
    user_created = supabase.table("Users").select("created_at").execute().data or []
    bulan_counter = defaultdict(int)
    for u in user_created:
        created = safe_parse_date(u.get("created_at"))
        if created:
            key = created.strftime("%b")
            bulan_counter[key] += 1

    bulan_order = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    anggota_growth_data = [{"label": b, "percent": min(bulan_counter.get(b, 0) * 5, 100)} for b in bulan_order]

    # Tambahan: user_growth_percent
    this_month_label = now.strftime("%b")
    prev_month_label = (now.replace(day=1) - timedelta(days=1)).strftime("%b")
    growth_now = bulan_counter.get(this_month_label, 0)
    growth_prev = bulan_counter.get(prev_month_label, 1) or 1  # hindari 0
    user_growth_percent = round((growth_now - growth_prev) / growth_prev * 100, 2)

    return templates.TemplateResponse("user/dashboard/dashboard.html", {
        "request": request,
        "telegram_id": telegram_id,
        "username": user["username"],
        "is_vip": user["is_vip"],
        "vip_since": user.get("vip_since"),
        "statistik_per_level": statistik_per_level,
        "last_exam": last_exam,
        "has_certificate": has_certificate,
        "user_photo": user.get("photo_url"),
        "total_users": total_users,
        "vip_users": vip_users,
        "modul_aktif": modul_aktif,
        "free_users": free_users,
        "growth_user": growth_user,
        "growth_vip": growth_vip,
        "growth_free": growth_free,
        "growth_modul": growth_modul,
        "client_key": MIDTRANS_CLIENT_KEY,
        "aktivitas": aktivitas,
        "anggota_growth_data": anggota_growth_data,
        "user_growth_percent": user_growth_percent,
        "user_badge_level": user_badge_level
    })

@router.get("/dashboard/partial/{section}", response_class=HTMLResponse)
async def get_dashboard_partial(request: Request, section: str, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")



    if section == "sol":
        # Query harga eceran Solana
        result = supabase.table("EcerPrices").select("id,price").order("price", desc=False).execute()
        ecer_prices = result.data or []

        return templates.TemplateResponse("user/dashboard/partials/sol.html", {
            "request": request,
            "client_key": MIDTRANS_CLIENT_KEY,
            "admin_username": ADMIN_TELEGRAM_USERNAME,
            "ecer_prices": ecer_prices,
        })


    # SECTION: download center
    if section == "download":
        return await partial_download(request, telegram_id)

    # SECTION: akun (profil user)
    if section == "akun":
        vip_since = safe_parse_date(user.get("vip_since"))
        created_at = safe_parse_date(user.get("created_at"))

        return templates.TemplateResponse("user/dashboard/partials/akun.html", {
            "request": request,
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "is_vip": user.get("is_vip"),
            "vip_since": vip_since,
            "created_at": created_at,
            "user_photo": user.get("photo_url"),
        })



    # SECTION: ujian
    if section == "ujian":
        all_exams = supabase.table("Exams").select("*").order("level").execute().data or []
        exam_results = supabase.table("ExamResults").select("*") \
            .eq("user_id", int(telegram_id)).order("created_at").execute().data or []

        allowed_levels = ["SDM"]
        if user.get("is_vip"):
            allowed_levels.append("SMM")
        if user.get("is_vip") and user.get("is_sma_addon"):
            allowed_levels.append("SMA")
        if user.get("is_vip") and user.get("is_sma_addon") and user.get("is_umm"):
            allowed_levels.append("UMM")

        exams_per_level = {}
        for exam in all_exams:
            level = exam.get("level")
            if level not in allowed_levels:
                continue
            exams_per_level.setdefault(level, []).append(exam)

        results_map = {}
        for res in exam_results:
            level = res.get("level")
            if level in allowed_levels:
                results_map.setdefault(level, []).append(res)

        last_reset = user.get("last_reset")
        filtered_gagal_map = {}
        for res in exam_results:
            level = res.get("level")
            if level in allowed_levels and not res.get("passed"):
                if not last_reset or res.get("created_at") >= last_reset:
                    filtered_gagal_map.setdefault(level, []).append(res)

        total_selesai = len(exam_results)
        total_lulus = len([r for r in exam_results if r.get("passed")])
        rata_rata = int(sum([r["score"] for r in exam_results]) / total_selesai) if total_selesai > 0 else 0

        return templates.TemplateResponse("user/dashboard/partials/ujian.html", {
            "request": request,
            "exams_per_level": exams_per_level,
            "results_map": results_map,
            "filtered_gagal_map": filtered_gagal_map,
            "total_selesai": total_selesai,
            "total_lulus": total_lulus,
            "rata_rata": rata_rata,
            "telegram_id": telegram_id
        })

    # SECTION: partial non-level (misc)
    level = section.upper()
    if level not in ["SDM", "SMM", "SMA", "UMM"]:
        path = f"frontend/user/dashboard/partials/{section}.html"
        if not os.path.exists(path):
            return HTMLResponse(f"<div class='alert alert-danger'>Section '{section}' tidak ditemukan.</div>")
        return templates.TemplateResponse(f"user/dashboard/partials/{section}.html", {
            "request": request
        })

    # SECTION: akses level (SMM/SMA/UMM)
    if level == "SMM" and not user.get("is_vip"):
        return HTMLResponse("""
            <div class='alert alert-warning text-center'>
                <p>Butuh VIP untuk mengakses SMM.</p>
                <a href='/dashboard/partial/join-vip' class='btn btn-warning mt-2 fw-bold'>Upgrade VIP</a>
            </div>
        """)

    if level == "SMA":
        if not user.get("is_vip"):
            return HTMLResponse("""
                <div class='alert alert-warning text-center'>
                    <p>Butuh VIP untuk mengakses SMA.</p>
                    <a href='/dashboard/partial/join-vip' class='btn btn-warning mt-2 fw-bold'>Upgrade VIP</a>
                </div>
            """)
        if not user.get("is_sma_addon"):
            return HTMLResponse("""
                <div class='alert alert-warning text-center'>
                    <p>Butuh Addon SMA untuk mengakses level ini.</p>
                    <a href='/bayar/sma' class='btn btn-warning mt-2 fw-bold'>Beli Addon SMA</a>
                </div>
            """)

    if level == "UMM":
        if not user.get("is_vip"):
            return HTMLResponse("""
                <div class='alert alert-warning text-center'>
                    <p>Butuh VIP untuk mengakses UMM.</p>
                    <a href='/dashboard/partial/join-vip' class='btn btn-warning mt-2 fw-bold'>Upgrade VIP</a>
                </div>
            """)
        if not user.get("is_sma_addon"):
            return HTMLResponse("""
                <div class='alert alert-warning text-center'>
                    <p>Butuh Addon SMA sebelum membeli Addon UMM.</p>
                    <a href='/bayar/sma' class='btn btn-warning mt-2 fw-bold'>Beli Addon SMA</a>
                </div>
            """)
        if not user.get("is_umm"):
            return HTMLResponse("""
                <div class='alert alert-warning text-center'>
                    <p>Butuh Addon UMM untuk mengakses level ini.</p>
                    <a href='/bayar/umm' class='btn btn-warning mt-2 fw-bold'>Beli Addon UMM</a>
                </div>
            """)

    # SECTION: load modul level
    mod_res = supabase.table("Modules").select("*").eq("level", level).order("order_index").execute()
    modules = mod_res.data or []

    completed_res = supabase.table("ModuleProgress").select("module_id", "is_completed") \
        .eq("user_id", int(telegram_id)).execute()
    completed_ids = {item["module_id"]: item["is_completed"] for item in completed_res.data or []}

    for idx, modul in enumerate(modules):
        modul["is_completed"] = completed_ids.get(modul["id"], False)
        modul["is_unlocked"] = True
        if idx > 0:
            prev_id = modules[idx - 1]["id"]
            if not completed_ids.get(prev_id, False):
                modul["is_unlocked"] = False

    return templates.TemplateResponse(f"user/dashboard/partials/{section}.html", {
        "request": request,
        "modules": modules,
        "level": level
    })


@router.get("/sdm/modul/{modul_id}")
async def sdm_modul_detail(request: Request, modul_id: UUID, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    modul_res = supabase.table("Modules").select("*").eq("id", str(modul_id)).single().execute()
    modul = modul_res.data
    if not modul:
        raise HTTPException(status_code=404, detail="Modul tidak ditemukan")

    if modul["level"] != "SDM":
        return RedirectResponse("/dashboard")

    progress_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", int(telegram_id)).eq("module_id", str(modul_id)).execute()

    is_completed = False
    if progress_res.data:
        is_completed = progress_res.data[0]["is_completed"]

    return templates.TemplateResponse("user/modul_detail.html", {
        "request": request,
        "modul": modul,
        "user": user,
        "is_completed": is_completed
    })

@router.get("/smm/modul/{modul_id}")
async def smm_modul_detail(request: Request, modul_id: UUID, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    modul_res = supabase.table("Modules").select("*").eq("id", str(modul_id)).single().execute()
    modul = modul_res.data
    if not modul:
        raise HTTPException(status_code=404, detail="Modul tidak ditemukan")

    if modul["level"] != "SMM":
        return RedirectResponse("/dashboard")

    progress_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", int(telegram_id)).eq("module_id", str(modul_id)).execute()

    is_completed = False
    if progress_res.data:
        is_completed = progress_res.data[0]["is_completed"]

    return templates.TemplateResponse("user/modul_detail.html", {
        "request": request,
        "modul": modul,
        "user": user,
        "is_completed": is_completed
    })

@router.get("/sma/modul/{modul_id}")
async def sma_modul_detail(request: Request, modul_id: UUID, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    modul_res = supabase.table("Modules").select("*").eq("id", str(modul_id)).single().execute()
    modul = modul_res.data
    if not modul:
        raise HTTPException(status_code=404, detail="Modul tidak ditemukan")

    if modul["level"] != "SMA":
        return RedirectResponse("/dashboard")

    progress_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", int(telegram_id)).eq("module_id", str(modul_id)).execute()

    is_completed = False
    if progress_res.data:
        is_completed = progress_res.data[0]["is_completed"]

    return templates.TemplateResponse("user/modul_detail.html", {
        "request": request,
        "modul": modul,
        "user": user,
        "is_completed": is_completed
    })

@router.get("/umm/modul/{modul_id}")
async def umm_modul_detail(request: Request, modul_id: UUID, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    user_res = supabase.table("Users").select("*").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    modul_res = supabase.table("Modules").select("*").eq("id", str(modul_id)).single().execute()
    modul = modul_res.data
    if not modul:
        raise HTTPException(status_code=404, detail="Modul tidak ditemukan")

    if modul["level"] != "UMM":
        return RedirectResponse("/dashboard")

    progress_res = supabase.table("ModuleProgress").select("*") \
        .eq("user_id", int(telegram_id)).eq("module_id", str(modul_id)).execute()

    is_completed = False
    if progress_res.data:
        is_completed = progress_res.data[0]["is_completed"]

    return templates.TemplateResponse("user/modul_detail.html", {
        "request": request,
        "modul": modul,
        "user": user,
        "is_completed": is_completed
    })


@router.get("/dashboard/partial/join-vip", response_class=HTMLResponse)
async def join_vip_partial(request: Request, telegram_id: str = Depends(require_login)):
    # Ambil user dari Supabase berdasarkan telegram_id
    result = supabase.table("Users").select("*").eq("user_id", telegram_id).single().execute()

    if result.error or not result.data:
        return HTMLResponse(content="Gagal memuat data user", status_code=500)

    user = result.data

    return templates.TemplateResponse(
        "user/dashboard/partials/join-vip.html",
        {
            "request": request,
            "is_vip": user.get("is_vip", False),
            "vip_since": user.get("vip_since", None),
        },
    )

@router.get("/progress/summary")
async def get_progress_summary(telegram_id: str = Depends(require_login)):
    user_res = supabase.table("Users").select("is_vip, is_sma_addon, is_umm")\
        .eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data or {}

    # Tentukan level yang terbuka untuk user
    level_aktif = ["SDM"]
    if user.get("is_vip"):
        level_aktif.append("SMM")
    if user.get("is_vip") and user.get("is_sma_addon"):
        level_aktif.append("SMA")
    if user.get("is_vip") and user.get("is_sma_addon") and user.get("is_umm"):
        level_aktif.append("UMM")

    summary = {
        "progress": {},
        "ujian": {},
        "modul_terakhir": None
    }

    last_module = None

    # Loop semua level untuk ambil ujian, tapi progress & modul terakhir tetap berdasarkan level aktif
    for level in ["SDM", "SMM", "SMA", "UMM"]:
        if level in level_aktif:
            # --- Hitung progress per level ---
            modul_res = supabase.table("Modules").select("id, order_index, title")\
                .eq("level", level).order("order_index").execute()
            modul_list = modul_res.data or []
            modul_ids = [m["id"] for m in modul_list]
            total = len(modul_ids)

            progress_res = supabase.table("ModuleProgress").select("module_id, is_completed")\
                .eq("user_id", int(telegram_id)).in_("module_id", modul_ids).execute()
            selesai_map = {p["module_id"]: p["is_completed"] for p in progress_res.data or []}
            jumlah_selesai = sum(1 for mid in modul_ids if selesai_map.get(mid, False))

            persen = round((jumlah_selesai / total) * 100) if total > 0 else 0
            summary["progress"][level] = persen

            # --- Modul terakhir ---
            if not last_module:
                belum_selesai = [m for m in modul_list if not selesai_map.get(m["id"], False)]
                modul_terakhir = belum_selesai[0] if belum_selesai else modul_list[-1] if modul_list else None
                if modul_terakhir:
                    last_module = {
                        "level": level,
                        "module_id": modul_terakhir["id"],
                        "title": modul_terakhir["title"]
                    }

        # --- Ambil skor ujian terakhir (tetap diambil meskipun level tidak aktif) ---
        ujian_res = supabase.table("ExamResults").select("score, passed")\
            .eq("user_id", int(telegram_id)).eq("level", level)\
            .order("created_at", desc=True).limit(1).execute()
        if ujian_res.data:
            skor = ujian_res.data[0]["score"]
            lulus = ujian_res.data[0]["passed"]
            sertifikat_url = f"/static/sertifikat/sertifikat_{telegram_id}_{level}.pdf" if lulus else None
            summary["ujian"][level] = {
                "score": skor,
                "sertifikat_url": sertifikat_url
            }

    summary["modul_terakhir"] = last_module
    return summary

@router.get("/dashboard/partial/stats_komu", response_class=HTMLResponse)
async def stats_komunitas_partial(request: Request, telegram_id: str = Depends(require_login)):
    user_res = supabase.table("Users").select("id").eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data
    if not user:
        return RedirectResponse("/login")

    total_users = supabase.table("Users").select("id", count="exact").execute().count or 0

    vip_users = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", True).execute().count or 0

    free_users = supabase.table("Users").select("id", count="exact") \
        .eq("is_vip", False).execute().count or 0

    modul_aktif = supabase.table("Modules").select("id", count="exact").execute().count or 0

    return templates.TemplateResponse("user/dashboard/partials/stats_komu.html", {
        "request": request,
        "total_users": total_users,
        "vip_users": vip_users,
        "free_users": free_users,
        "modul_aktif": modul_aktif,
        "growth_user": "+0%",     # placeholder
        "growth_vip": "+0%",
        "growth_free": "+0%",
        "growth_modul": "+0%",
    })

@router.get("/dashboard/partial/aktifitas", response_class=HTMLResponse)
async def aktivitas_partial(request: Request, telegram_id: str = Depends(require_login)):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    res = supabase.table("ActivityLogs").select("*").eq("user_id", int(telegram_id)) \
        .order("created_at", desc=True).limit(10).execute()
    logs = res.data or []

    return templates.TemplateResponse("user/dashboard/partials/aktifitas.html", {
        "request": request,
        "aktivitas": logs
    })


@router.get("/dashboard/partial/download", response_class=HTMLResponse)
async def partial_download(request: Request, telegram_id: str = Depends(require_login)):
    # ✅ Ambil status akses user
    user_res = supabase.table("Users").select("is_vip, is_sma_addon, is_umm") \
        .eq("user_id", int(telegram_id)).single().execute()
    user = user_res.data or {}

    # ✅ Tentukan level yang aktif berdasarkan status user
    level_aktif = ["SDM"]
    if user.get("is_vip"):
        level_aktif.append("SMM")
    if user.get("is_vip") and user.get("is_sma_addon"):
        level_aktif.append("SMA")
    if user.get("is_vip") and user.get("is_sma_addon") and user.get("is_umm"):
        level_aktif.append("UMM")

    summary = {
        "progress": {},
        "ujian": {},
        "modul_terakhir": None
    }

    last_module = None

    # ✅ Loop tiap level aktif
    for level in level_aktif:
        # ✅ Ambil daftar modul dan hitung progress
        modul_res = supabase.table("Modules").select("id, order_index, title") \
            .eq("level", level).order("order_index").execute()
        modul_list = modul_res.data or []
        modul_ids = [m["id"] for m in modul_list]
        total = len(modul_ids)

        progress_res = supabase.table("ModuleProgress").select("module_id, is_completed") \
            .eq("user_id", int(telegram_id)).in_("module_id", modul_ids).execute()
        selesai_map = {p["module_id"]: p["is_completed"] for p in progress_res.data or []}
        jumlah_selesai = sum(1 for mid in modul_ids if selesai_map.get(mid, False))
        persen = round((jumlah_selesai / total) * 100) if total > 0 else 0
        summary["progress"][level] = persen

        # ✅ Ambil hasil ujian terakhir YANG LULUS
        ujian_res = supabase.table("ExamResults").select("score, passed, level") \
            .eq("user_id", int(telegram_id)) \
            .eq("level", level) \
            .eq("passed", True) \
            .order("created_at", desc=True) \
            .limit(1).execute()

        if ujian_res.data:
            skor = ujian_res.data[0]["score"]
            sertifikat_url = f"/static/sertifikat/sertifikat_{telegram_id}_{level}.pdf"
            summary["ujian"][level] = {
                "score": skor,
                "sertifikat_url": sertifikat_url
            }

        # ✅ Ambil modul terakhir yang belum selesai (1x ambil aja)
        if not last_module:
            belum_selesai = [m for m in modul_list if not selesai_map.get(m["id"], False)]
            modul_terakhir = belum_selesai[0] if belum_selesai else modul_list[-1] if modul_list else None
            if modul_terakhir:
                last_module = {
                    "level": level,
                    "module_id": modul_terakhir["id"],
                    "title": modul_terakhir["title"]
                }

    summary["modul_terakhir"] = last_module

    # ✅ Render ke template partial
    return templates.TemplateResponse("user/dashboard/partials/download.html", {
        "request": request,
        "summary": summary,
        "telegram_id": telegram_id
    })


@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(None),
    telegram_id: str = Depends(require_login)
):
    if isinstance(telegram_id, RedirectResponse):
        return telegram_id

    update_data = {
        "username": username,
        "full_name": full_name,
    }

    supabase.table("Users").update(update_data).eq("user_id", int(telegram_id)).execute()

    return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)


