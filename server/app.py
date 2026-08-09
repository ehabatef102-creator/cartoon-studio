import asyncio
import io
import json
import os
import random
import sys
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from creative_engine import list_packs
from packs import get_pack
from universe import UNIVERSE
from server import pipeline

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", ROOT / "workspace"))
JOBS_DIR = WORKSPACE / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Cartoon Studio", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS = {}


def load_jobs():
    for job_file in JOBS_DIR.glob("*/job.json"):
        try:
            data = json.loads(job_file.read_text(encoding="utf-8"))
            data["_dir"] = job_file.parent
            JOBS[data["id"]] = data
        except Exception:
            continue


load_jobs()


def require_admin(x_admin_token: str = Header(default=""), token: str = Query(default="")):
    if (x_admin_token or token) != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")
    return True


def job_dir_for(job_id):
    return JOBS_DIR / job_id


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=FileResponse)
def index():
    web_index = ROOT / "web" / "index.html"
    if web_index.exists():
        return FileResponse(web_index)
    return FileResponse(Path(__file__).resolve().parent / "index.html")


@app.get("/packs.json", response_class=FileResponse)
def packs_json():
    f = ROOT / "web" / "packs.json"
    if not f.exists():
        raise HTTPException(status_code=404, detail="غير متاح")
    return FileResponse(f)


if (ROOT / "web" / "assets").exists():
    app.mount("/assets", StaticFiles(directory=ROOT / "web" / "assets"), name="assets")


@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    if body.get("password") == ADMIN_PASSWORD:
        return {"token": ADMIN_PASSWORD}
    raise HTTPException(status_code=401, detail="كلمة المرور غير صحيحة")


@app.get("/api/packs")
def packs(x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    data = []
    for i, title, genre, audience in list_packs():
        p = get_pack(index=i)
        data.append({
            "index": i,
            "title": title,
            "genre": genre,
            "audience": audience,
            "logline": p["logline"],
            "pilot_title": p["pilot"]["title"],
            "pilot_duration": p["pilot"]["duration"],
            "scenes": len(p["pilot"]["scenes"]),
        })
    return {
        "packs": data,
        "universe": {"name": UNIVERSE["name"], "tagline": UNIVERSE["tagline"]},
    }


@app.get("/api/jobs")
def jobs(x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    items = []
    for job in JOBS.values():
        items.append(summary(job))
    items.sort(key=lambda j: j["created"], reverse=True)
    return {"jobs": items}


@app.post("/api/jobs")
async def create_job(request: Request, x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    body = await request.json()
    index = body.get("index")
    idea = (body.get("idea") or "").strip()
    if idea:
        from creative_engine import build_custom_pack

        pack = await asyncio.to_thread(build_custom_pack, idea, random.randint(1, 10**9))
        if not pack:
            raise HTTPException(status_code=400, detail="اكتب فكرة/سيناريو أولًا")
    else:
        if index is None or not (1 <= index <= len(list_packs())):
            raise HTTPException(status_code=400, detail="اختر سلسلة أو اكتب فكرة")
        from creative_engine import get_pack

        pack = get_pack(index=index)
        if body.get("title"):
            pack = {**pack, "title": body["title"]}
    job = {
        "id": uuid.uuid4().hex[:12],
        "status": "queued",
        "progress": 0,
        "phase": "في الانتظار",
        "scene": None,
        "error": None,
        "pack_slug": pack.get("slug"),
        "pack_title": pack.get("title"),
        "source": pack.get("_source", "template"),
        "title_override": body.get("title"),
        "render_video": bool(body.get("render_video", False)),
        "audio_design": body.get("audio_design"),
        "motion": body.get("motion"),
        "seed": random.randint(1, 10**9),
        "created": _now(),
    }
    job["_dir"] = job_dir_for(job["id"])
    job["_dir"].mkdir(parents=True, exist_ok=True)
    JOBS[job["id"]] = job
    pipeline.save_job(job)
    asyncio.create_task(
        pipeline.run_job(
            job, WORKSPACE, pack, job["render_video"],
            audio_design=job.get("audio_design"), use_motion=job.get("motion"),
        )
    )
    return {"id": job["id"]}


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def summary(job):
    return {
        "id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "phase": job["phase"],
        "scene": job["scene"],
        "error": job["error"],
        "pack_slug": job["pack_slug"],
        "pack_title": job["pack_title"] or job["title_override"],
        "source": job.get("source", "template"),
        "render_video": job["render_video"],
        "audio_design": job.get("audio_design"),
        "motion": job.get("motion"),
        "created": job["created"],
        "has_video": (job["_dir"] / "video" / "final.mp4").exists(),
        "has_images": (job["_dir"] / "images").exists(),
        "images": job.get("images", []),
    }


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    return summary(job)


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str, x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    if job["status"] != "done":
        raise HTTPException(status_code=400, detail="المهمة لم تكتمل بعد")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in (job["_dir"] / "pack").rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(job["_dir"] / "pack"))
        for p in (job["_dir"] / "images").rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(job["_dir"]))
        for p in (job["_dir"] / "voice").rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(job["_dir"]))
        final = job["_dir"] / "video" / "final.mp4"
        if final.exists():
            zf.write(final, "video/final.mp4")
    buf.seek(0)
    name = (job["pack_slug"] or job["id"]) + ".zip"
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": f"attachment; filename={name}"})


@app.get("/api/jobs/{job_id}/asset")
def asset(job_id: str, path: str, x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    target = (job["_dir"] / path).resolve()
    if not str(target).startswith(str(job["_dir"].resolve())):
        raise HTTPException(status_code=400, detail="مسار غير صالح")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    return FileResponse(target)


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, x_admin_token: str = Header(default=""), token: str = Query(default="")):
    require_admin(x_admin_token=x_admin_token, token=token)
    job = JOBS.pop(job_id, None)
    if not job:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    if job["status"] == "running":
        raise HTTPException(status_code=400, detail="لا يمكن حذف مهمة قيد التشغيل")
    d = job["_dir"]
    if d.exists():
        import shutil
        shutil.rmtree(d, ignore_errors=True)
    return {"ok": True}
