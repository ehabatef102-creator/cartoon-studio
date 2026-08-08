import argparse
import random
import sys
from pathlib import Path

from creative_engine import build_pack, list_packs

SCRIPT_DIR = Path(__file__).resolve().parent

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="cartoon_studio",
        description="أداة توليد باكس إنتاج مسلسلات كرتونية أصلية (بايبل + حلقة تجريبية 3 دقائق + بريف مشاهد + دليل نشر يوتيوب).",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_new = sub.add_parser("new", help="توليد سلسلة جديدة")
    p_new.add_argument("--index", type=int, help="رقم السلسلة من قائمة list (1-3)")
    p_new.add_argument("--title", help="عنوان مخصص للسلسلة (اختياري)")
    p_new.add_argument("--seed", type=int, help="بذرة عشوائية لتكرار نفس النتيجة")
    p_new.add_argument("--out", help="مجلد مخرجات مخصص (اختياري)")

    sub.add_parser("list", help="عرض السلاسل المتاحة")

    p_view = sub.add_parser("view", help="عرض أسماء الملفات المولّدة لسلسلة موجودة")
    p_view.add_argument("--path", required=True, help="مسار مجلد المخرجات")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        print("السلاسل المتاحة:")
        for i, title, genre, audience in list_packs():
            print(f"  [{i}] {title} — {genre} ({audience})")
        return 0

    if args.cmd == "view":
        path = Path(args.path)
        if not path.exists():
            print(f"المسار غير موجود: {path}", file=sys.stderr)
            return 1
        print(f"ملفات السلسلة ({path}):")
        for f in sorted(path.rglob("*.md")):
            print(f"  {f.relative_to(path)}")
        return 0

    if args.cmd == "new":
        if args.index is not None and not (1 <= args.index <= len(list_packs())):
            print(f"رقم غير صالح، اختر من 1 إلى {len(list_packs())}", file=sys.stderr)
            return 1
        base, count, _ = build_pack(index=args.index, title=args.title, seed=args.seed, out_dir=args.out)
        print(f"تم توليد باكس الإنتاج بنجاح: {base}")
        print(f"عدد الملفات: {count}")
        print("ابدأ من: 00_series_bible.md ثم 01_pilot_script.md ثم مجلد 02_scenes")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
