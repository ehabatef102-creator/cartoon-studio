"""تصدير الباكس المُثرّاة (باستمرارية سينمائية وتصميم صوتي) إلى web/packs.json
ليستهلكها الواجهة (GitHub Pages / الخادم) دون حاجة لمحرك بايثون.
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from creative_engine import _apply_timings, list_packs
from packs import get_pack

OUT = ROOT / "web" / "packs.json"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    packs = []
    for index, _title, _genre, _audience in list_packs():
        pack = deepcopy(get_pack(index=index))
        _apply_timings(pack)
        pack["index"] = index
        packs.append(pack)
    payload = {"version": 2, "packs": packs}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Exported {len(packs)} packs to {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
