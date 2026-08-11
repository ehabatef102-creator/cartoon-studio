"""محرك الهوية البصرية: شخصيات متسقة، لغة إخراج سينمائية، سكور موسيقي لكل مشهد."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from packs import SERIES_STYLE_GUIDE

CINEMATIC_GRADE = (
    "cinematic anamorphic 2.39:1 wide framing, dramatic volumetric lighting, "
    "high detail feature-film quality, bold cartoon ink outlines, cel shading, "
    "vibrant saturated colors, clean graphic shapes, sharp environment details"
)

# كلمات تحفّز تفاصيل البيئة/المباني عندما يذكر المشهد أماكن بناء
_BUILDING_KEYS = ("city", "town", "village", "building", "street", "tower", "castle",
                  "مدينة", "قرية", "مبنى", "شارع", "قلعة", "برج", "سوق", "حي", "أزقة", "قصر")
_ENV_DETAIL = (
    "detailed background architecture, clearly defined building shapes and silhouettes, "
    "dense urban street details, recognizable landmarks, layered depth between foreground and skyline"
)

LENS = {
    "wide": "24mm wide anamorphic",
    "medium": "40mm anamorphic",
    "close": "85mm anamorphic, compressed background",
    "macro": "100mm macro anamorphic",
}

_BEAT_NAMES = ["setup", "inciting", "rising1", "rising2", "climax", "falling", "resolution"]

_BEAT_DEFAULTS = {
    "setup":     {"framing": "wide establishing shot", "angle": "eye level",       "movement": "slow push-in",   "lens": "wide", "focus": "whole scene in focus"},
    "inciting":  {"framing": "wide to medium shot",    "angle": "eye level",       "movement": "push-in",        "lens": "wide", "focus": "subject emerging from environment"},
    "rising1":   {"framing": "medium shot",            "angle": "slight low angle", "movement": "lateral pan",    "lens": "medium", "focus": "subject"},
    "rising2":   {"framing": "medium close-up",        "angle": "low angle",        "movement": "slow push-in",   "lens": "close", "focus": "face and hands"},
    "climax":    {"framing": "close-up montage",       "angle": "dutch angle",      "movement": "fast push-in",   "lens": "close", "focus": "eyes, intense"},
    "falling":   {"framing": "medium to wide shot",    "angle": "eye level",        "movement": "slow zoom-out",  "lens": "medium", "focus": "subject settling"},
    "resolution": {"framing": "wide shot",             "angle": "high angle",       "movement": "slow zoom-out",  "lens": "wide", "focus": "whole scene, peaceful"},
    "crossover": {"framing": "wide establishing shot", "angle": "low angle",        "movement": "slow push-in",   "lens": "wide", "focus": "mysterious figure in distance"},
}

_MOOD_LIGHT = [
    ("توتر", "خوف", "ظلام", "مشبوه", "انفجار", "معركة", "هجوم"),
    ("حزن", "كآبة", "غروب", "وداع", "فراق"),
    ("مغامرة", "إثارة", "ملحمي", "epic", "حماس", "انتصار"),
    ("غامض", "لغز", "mystery", "suspense", "تساؤل"),
]
_LIGHT_KEYS = [
    "low-key dramatic lighting, hard rim light, long shadows, cool cyan key light",
    "soft diffused overcast light, desaturated cool palette, gentle melancholic glow",
    "heroic backlight, god rays, warm key light with deep teal shadows, dynamic range",
    "volumetric haze, moonlight teal-blue, glowing accents, chiaroscuro contrast",
]
_DEFAULT_LIGHT = "warm golden hour light, soft bounce fill, high-key cheerful atmosphere"

_MOOD_FRAMING = {
    "واسعة": "wide establishing shot", "بعيدة": "wide establishing shot",
    "قريبة": "close-up", "عن قرب": "close-up",
    "متوسطة": "medium shot", "متقاربة": "medium close-up",
}
_MOOD_MOVEMENT = {
    "تتحرك لأسفل": "vertical tilt-down", "لأسفل": "vertical tilt-down",
    "لأعلى": "vertical tilt-up", "تصاعدي": "vertical tilt-up",
    "بان": "lateral pan", "مسح": "lateral pan",
    "زوم": "slow push-in", "تقريب": "slow push-in",
    "دوران": "orbit", "دوار": "orbit",
}
_MOOD_ANGLE = {
    "من الأعلى": "high angle", "علوي": "high angle",
    "منخفض": "low angle", "من تحت": "low angle", "سفلي": "low angle",
    "مائل": "dutch angle", "معكوس": "dutch angle",
}


def _has_any(text, keys):
    text = text or ""
    return any(k.lower() in text.lower() for k in keys)


def beat_for(idx, total):
    if total < 1:
        return "resolution"
    if idx == total - 1:
        return "resolution"
    if total == 7:
        return _BEAT_NAMES[idx]
    ratio = idx / max(1, total - 1)
    if ratio < 0.17:
        return "setup"
    if ratio < 0.34:
        return "inciting"
    if ratio < 0.51:
        return "rising1"
    if ratio < 0.68:
        return "rising2"
    if ratio < 0.85:
        return "climax"
    return "falling"


def tension_for(beat, mood="", title=""):
    base = {
        "setup": 2, "inciting": 5, "rising1": 6, "rising2": 7,
        "climax": 9, "falling": 4, "resolution": 3, "crossover": 7,
    }.get(beat, 5)
    if _has_any(mood + " " + title, ("توتر", "خوف", "معركة", "شدة", "انفجار", "هجوم", "خطر", "صراع")):
        base += 1
    return max(1, min(10, base))


def light_rig(mood):
    for keys, light in zip(_MOOD_LIGHT, _LIGHT_KEYS):
        if _has_any(mood, keys):
            return light
    return _DEFAULT_LIGHT


def strip_guide(text):
    text = text or ""
    if SERIES_STYLE_GUIDE and SERIES_STYLE_GUIDE in text:
        text = text.replace(SERIES_STYLE_GUIDE, "").rstrip(", ")
    return text


def extract_cast(pack, scene):
    """من يتواجد في هذا المشهد (حوار + ذكر في الوصف/العنوان)."""
    names = []
    dialogue = scene.get("dialogue") or []
    text = " ".join(str(s) for s, _ in dialogue) + " " + (scene.get("action") or "") + " " + (scene.get("title") or "")
    seen = set()
    for ch in pack.get("characters", []):
        n = ch["name"]
        hits = any(n == s or n in s or s in n for s, _ in dialogue) or (n and n in text)
        if hits and n not in seen:
            seen.add(n)
            names.append(ch)
    return names


def shot_plan(scene, beat):
    camera = " ".join(scene.get("camera") or [])
    d = _BEAT_DEFAULTS.get(beat, _BEAT_DEFAULTS["setup"])
    framing, movement, angle = d["framing"], d["movement"], d["angle"]
    for k, v in _MOOD_FRAMING.items():
        if k in camera:
            framing = v
            break
    for k, v in _MOOD_MOVEMENT.items():
        if k in camera:
            movement = v
            break
    for k, v in _MOOD_ANGLE.items():
        if k in camera:
            angle = v
            break
    if "زوم" in camera or "تقريب" in camera:
        movement = "slow push-in"
    lens = LENS.get(d["lens"], "40mm anamorphic")
    return [{
        "framing": framing, "angle": angle, "movement": movement,
        "lens": lens, "focus": d["focus"],
    }]


def music_score(beat, mood="", idx=0):
    dramatic = beat in ("inciting", "rising1", "rising2", "climax", "crossover")
    mode = "minor" if dramatic else "major"
    intensity = max(1, min(10, tension_for(beat, mood) if not dramatic else tension_for(beat, mood) + 0))
    tempo = {
        "setup": 72, "inciting": 84, "rising1": 96, "rising2": 106,
        "climax": 122, "falling": 74, "resolution": 66, "crossover": 100,
    }.get(beat, 84)
    keywords = []
    if beat == "climax":
        keywords = ["epic brass", "timpani", "choir swells"]
    elif dramatic:
        keywords = ["dark strings", "pulsing low brass"]
    elif beat == "resolution":
        keywords = ["soft piano", "warm strings", "hopeful"]
    else:
        keywords = ["light woodwinds", "gentle plucked strings"]
    return {"mode": mode, "intensity": intensity, "tempo": tempo, "keywords": keywords}


def _norm_shot(shot):
    if isinstance(shot, dict):
        return [shot]
    if isinstance(shot, list):
        return shot
    return shot_plan({}, "setup")


def _norm_music(music):
    if isinstance(music, dict):
        return music
    return None


def enrich_pack(pack):
    """يحسب beat/tension/cast/shot/music لكل مشهد، ويستكمل أي قيم ناقصة."""
    scenes = (pack.get("pilot") or {}).get("scenes") or []
    total = len(scenes)
    for idx, scene in enumerate(scenes):
        if not scene.get("beat"):
            scene["beat"] = beat_for(idx, total)
        scene["tension"] = int(scene.get("tension", tension_for(scene["beat"], scene.get("mood", ""), scene.get("title", ""))))
        scene["cast"] = scene.get("cast") or [c["name"] for c in extract_cast(pack, scene)]
        scene["shot"] = _norm_shot(scene.get("shot")) or shot_plan(scene, scene["beat"])
        scene["music"] = _norm_music(scene.get("music")) or music_score(scene["beat"], scene.get("mood", ""), idx)
    pc = pack.get("post_credits")
    if pc:
        pc["beat"] = "crossover"
        pc["tension"] = int(pc.get("tension", 7))
        pc["cast"] = pc.get("cast") or [c["name"] for c in extract_cast(pack, pc)]
        pc["shot"] = _norm_shot(pc.get("shot")) or shot_plan(pc, "crossover")
        pc["music"] = _norm_music(pc.get("music")) or music_score("crossover", pc.get("description", ""), 99)
    return pack


def compose_scene_prompt(pack, scene, beat=None):
    """يجمّع برومبت الصورة النهائي: المشهد + الشخصيات + الإخراج + الإضاءة + التفاصيل المعمارية."""
    base = (scene.get("image_prompt") or "").strip().rstrip(".")
    cast = scene.get("cast") or [c["name"] for c in extract_cast(pack, scene)]
    chars = []
    for ch in pack.get("characters", []):
        if ch["name"] in cast and ch.get("design_prompt"):
            chars.append(strip_guide(ch["design_prompt"]).strip().rstrip("."))
    shot = (scene.get("shot") or shot_plan(scene, beat or scene.get("beat", "setup")))[0]
    shot_line = ", ".join([shot.get("framing", ""), shot.get("angle", ""), shot.get("movement", ""), shot.get("lens", ""), shot.get("focus", "")])
    parts = [base]
    if chars:
        parts.append("Characters: " + "; ".join(chars))
    parts.append("Shot: " + shot_line)
    parts.append(light_rig(scene.get("mood", "")))
    if _has_any(" ".join([base, scene.get("mood", ""), scene.get("title", "")]), _BUILDING_KEYS):
        parts.append(_ENV_DETAIL)
    parts.append(CINEMATIC_GRADE)
    return ". ".join(p for p in parts if p).rstrip(".") + "."


def storyboard(pack):
    scenes = []
    for sc in (pack.get("pilot") or {}).get("scenes") or []:
        scenes.append({
            "num": sc.get("num"),
            "title": sc.get("title"),
            "seconds": sc.get("seconds"),
            "beat": sc.get("beat", "setup"),
            "tension": sc.get("tension", 5),
            "cast": sc.get("cast", []),
            "shots": sc.get("shot", []),
            "music": sc.get("music", {}),
        })
    pc = pack.get("post_credits")
    out = {
        "title": pack.get("title"),
        "episode": (pack.get("pilot") or {}).get("title"),
        "genre": pack.get("genre"),
        "theme": pack.get("theme"),
        "logline": pack.get("logline"),
        "scenes": scenes,
    }
    if pc:
        out["post_credits"] = {
            "title": pc.get("title"),
            "beat": "crossover",
            "tension": pc.get("tension", 7),
            "cast": pc.get("cast", []),
            "shots": pc.get("shot", []),
            "music": pc.get("music", {}),
        }
    return out
