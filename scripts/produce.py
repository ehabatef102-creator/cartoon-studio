"""تشغيل الإنتاج الكامل (سيناريو + صور + صوت + موسيقى + مونتاج فيديو)
بلا أي خادم محلي — يعمل على أي سحابة مجانية فيها بايثون (GitHub Actions / Colab).

الاستخدام:
  python scripts/produce.py --story "قصة..." [--video] [--music] [--motion] [--out dir] [--seed N]
  python scripts/produce.py --story "فكرة" --characters "فول|دبابة نينجا|..." --events "أحداث الحلقة" [--video]
  python scripts/produce.py --index 1 [--video] [--music] [--motion] [--out dir] [--seed N]
"""
import argparse
import asyncio
import json
import random
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from creative_engine import build_studio_pack, get_pack
from server import pipeline


def _seed_int(seed):
    return seed if seed is not None else random.randint(1, 10**9)


def compose_brief(story, characters, events):
    parts = []
    if story and story.strip():
        parts.append("الفكرة:\n" + story.strip())
    if characters and characters.strip():
        parts.append("الشخصيات:\n" + characters.strip())
    if events and events.strip():
        parts.append("الأحداث:\n" + events.strip())
    return "\n\n".join(parts)


async def produce(args):
    story = args.story
    if args.story_file:
        story = Path(args.story_file).read_text(encoding="utf-8") if Path(args.story_file).exists() else ""
    characters = args.characters
    if args.characters_file:
        characters = Path(args.characters_file).read_text(encoding="utf-8") if Path(args.characters_file).exists() else ""
    events = args.events
    if args.events_file:
        events = Path(args.events_file).read_text(encoding="utf-8") if Path(args.events_file).exists() else ""
    brief = compose_brief(story, characters, events)
    if brief.strip():
        pack = build_studio_pack(brief, seed=args.seed)
        if not pack:
            print("error: story empty", flush=True)
            return 1
        print(f"pack: {pack.get('_source', '?')} ({pack.get('title')})", flush=True)
    elif args.index:
        pack = get_pack(index=args.index)
        print(f"pack: index {args.index} ({pack.get('title')})", flush=True)
    else:
        print("error: provide --story or --index", flush=True)
        return 1

    job_id = uuid.uuid4().hex[:12]
    workspace = Path(args.out or ROOT / "output")
    job = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "phase": "في الانتظار",
        "scene": None,
        "error": None,
        "seed": _seed_int(args.seed),
        "_dir": workspace / "jobs" / job_id,
    }
    job["_dir"].mkdir(parents=True, exist_ok=True)
    pipeline.save_job(job)

    await pipeline.run_job(
        job, workspace, pack,
        render_video=args.video,
        audio_design="auto" if args.music else None,
        use_motion="auto" if args.motion else None,
    )

    job_dir = job["_dir"]
    if job["status"] != "done":
        print(f"error: production failed — {job.get('error')}", flush=True)
        return 1

    zip_path = workspace / f"{job_id}_{pack['slug']}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in job_dir.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(job_dir))
    shutil.rmtree(job_dir, ignore_errors=True)

    print(f"done: {zip_path}", flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="إنتاج كرتون كامل على السحابة المجانية")
    parser.add_argument("--story", help="الفكرة / قصة الحلقة")
    parser.add_argument("--story-file", help="مسار ملف فيه القصة (بديل عن --story للنصوص الطويلة)")
    parser.add_argument("--characters", help="الشخصيات: سطر لكل شخصية (الاسم | الدور | الوصف البصري | الصوت)")
    parser.add_argument("--characters-file", help="مسار ملف فيه الشخصيات (بديل آمن عن --characters)")
    parser.add_argument("--events", help="ملخص الأحداث / نقاط الحبكة لتوجيه المخرج")
    parser.add_argument("--events-file", help="مسار ملف فيه الأحداث (بديل آمن عن --events)")
    parser.add_argument("--index", type=int, help="رقم سلسلة جاهزة من المكتبة (1-3)")
    parser.add_argument("--video", action="store_true", help="توليد فيديو مونتاج نهائي")
    parser.add_argument("--music", action="store_true", help="موسيقى تصويرية + مؤثرات")
    parser.add_argument("--motion", action="store_true", help="حركة كاميرا سينمائية")
    parser.add_argument("--out", help="مجلد المخرجات (افتراضي: output/)")
    parser.add_argument("--seed", type=int, help="بذرة عشوائية للتكرار")
    args = parser.parse_args(argv)
    return asyncio.run(produce(args))


if __name__ == "__main__":
    raise SystemExit(main())
