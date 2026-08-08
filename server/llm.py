import json
import os
import re
import uuid

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = (
    "أنت كاتب سيناريو رسوم متحركة عربية محترف بأسلوب استوديوهات عالمية (مارفل/ديزني). "
    "حوّل فكرة المستخدم إلى باك إنتاج كامل بهذا الهيكل JSON الصارم فقط، لا شيء آخر:\n"
    "{\n"
    '  "title": "اسم السلسلة (عربي)",\n'
    '  "genre": "النوع",\n'
    '  "audience": "الفئة العمرية",\n'
    '  "logline": "جملة تسويقية للفكرة",\n'
    '  "theme": "العبرة الأخلاقية",\n'
    '  "pilot": {\n'
    '    "title": "عنوان الحلقة التجريبية",\n'
    '    "hook": "خطاف الافتتاح",\n'
    '    "moral": "عبرة الحلقة",\n'
    '    "scenes": [\n'
    "      {\"num\": 1, \"title\": \"اسم المشهد\", \"seconds\": 20, \"location\": \"المكان\", \"mood\": \"المزاج\", "
    '        "action": "وصف الحركة بالعربية", "dialogue": [[\"المتكلم\", \"الجملة\"], [\"المتكلم2\", \"الجملة\"]], '
    '        "image_prompt": "English cinematic image prompt, 2D animation style", '
    '        "sfx": ["مؤثر صوتي", "موسيقى"], "camera": ["توجيه كاميرا/مونتاج"]}\n'
    "    ]\n"
    "  },\n"
    '  "characters": [{"name": "اسم الشخصية", "role": "الدور", "desc": "وصف مختصر", "design_prompt": "English character design prompt"}],\n'
    '  "next_episodes": ["فكرة حلقة قادمة", "فكرة أخرى"],\n'
    '  "post_credits": {"title": "عنوان", "description": "وصف مشهد ما بعد الشارة يلمح لعالم مشترك", "dialogue": [["المتكلم", "الجملة"]], "image_prompt": "English prompt"}\n'
    "}\n"
    "قواعد: 7 مشاهد بالضبط، مجموع الثواني = 180 تقريبًا (مشهد ذروة أطول). حوار عربي فصيح ممتع للأطفال. "
    "image_prompt بالإنجليزية بأسلوب رسوم متحركة سينمائي متسق. شخصيات أصلية 100%. "
    "مشهد بعد الشارة يحتوي كاميو/تلميحًا لعالم مشترك مستقبلي."
)

SCHEMA_HINTS = ("title", "logline", "characters", "scenes")


def _extract_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("لا يوجد JSON في رد النموذج")
    return json.loads(text[start : end + 1])


def _normalize(data):
    data = data or {}
    scenes = []
    for i, sc in enumerate(data.get("pilot", {}).get("scenes", [])):
        dialogue = []
        for row in sc.get("dialogue", []):
            if isinstance(row, list) and len(row) >= 2:
                dialogue.append([str(row[0]), str(row[1])])
            elif isinstance(row, dict) and "speaker" in row:
                dialogue.append([str(row["speaker"]), str(row.get("text", ""))])
        scenes.append({
            "num": int(sc.get("num", i + 1)),
            "title": str(sc.get("title", f"مشهد {i + 1}")),
            "seconds": int(sc.get("seconds", 25)),
            "location": str(sc.get("location", "")),
            "mood": str(sc.get("mood", "")),
            "action": str(sc.get("action", "")),
            "dialogue": dialogue,
            "image_prompt": str(sc.get("image_prompt", "")),
            "sfx": [str(x) for x in sc.get("sfx", [])],
            "camera": [str(x) for x in sc.get("camera", [])],
        })
    post = data.get("post_credits", {})
    characters = []
    for ch in data.get("characters", []):
        characters.append({
            "name": str(ch.get("name", "")),
            "role": str(ch.get("role", "")),
            "desc": str(ch.get("desc", "")),
            "design_prompt": str(ch.get("design_prompt", "")),
        })
    return {
        "slug": "custom-" + uuid.uuid4().hex[:6],
        "title": str(data.get("title", "سلسلة مخصصة")),
        "genre": str(data.get("genre", "مغامرة")),
        "audience": str(data.get("audience", "6 - 12 سنوات")),
        "logline": str(data.get("logline", "")),
        "theme": str(data.get("theme", "")),
        "pilot": {
            "title": str(data.get("pilot", {}).get("title", "الحلقة التجريبية")),
            "hook": str(data.get("pilot", {}).get("hook", "")),
            "moral": str(data.get("pilot", {}).get("moral", "")),
            "scenes": scenes,
        },
        "characters": characters,
        "next_episodes": [str(x) for x in data.get("next_episodes", [])],
        "post_credits": {
            "title": str(post.get("title", "مشهد ما بعد الشارة")),
            "description": str(post.get("description", "")),
            "dialogue": [list(row) for row in _norm_dialogue(post.get("dialogue", []))],
            "image_prompt": str(post.get("image_prompt", "")),
        },
    }


def _norm_dialogue(dialogue):
    out = []
    for row in dialogue:
        if isinstance(row, list) and len(row) >= 2:
            out.append([str(row[0]), str(row[1])])
        elif isinstance(row, dict):
            out.append([str(row.get("speaker", "")), str(row.get("text", ""))])
    return out


def _call_openai_style(url, headers, payload):
    with httpx.Client(timeout=httpx.Timeout(240.0)) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def transform_idea(idea):
    if GROQ_API_KEY:
        try:
            data = _call_openai_style(
                "https://api.groq.com/openai/v1/chat/completions",
                {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": idea[:8000]},
                    ],
                    "temperature": 0.8,
                    "response_format": {"type": "json_object"},
                },
            )
            return _normalize(_extract_json(data["choices"][0]["message"]["content"]))
        except Exception:
            pass
    if OPENAI_API_KEY:
        try:
            data = _call_openai_style(
                "https://api.openai.com/v1/chat/completions",
                {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": idea[:8000]},
                    ],
                    "temperature": 0.8,
                    "response_format": {"type": "json_object"},
                },
            )
            return _normalize(_extract_json(data["choices"][0]["message"]["content"]))
        except Exception:
            pass
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nفكرة المستخدم:\n" + idea[:8000]}]}],
                "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"},
            }
            data = _call_openai_style(url, {"Content-Type": "application/json"}, payload)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _normalize(_extract_json(text))
        except Exception:
            pass
    return None
