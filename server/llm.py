import json
import os
import re
import uuid

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = (
    "أنت كاتب سيناريو رسوم متحركة عربية محترف بمستوى استوديوهات عالمية (مارفل/ديزني/ستوديو جيبلي). "
    "تحترف البنية الدرامية من 3 فصول، أقواس الشخصيات، الصراع والتوتر التصاعدي، واللحظات العاطفية. "
    "حوّل فكرة المستخدم إلى باك إنتاج كامل بهذا الهيكل JSON الصارم فقط، لا شيء آخر:\n"
    "{\n"
    '  "title": "اسم السلسلة (عربي)",\n'
    '  "genre": "النوع",\n'
    '  "audience": "الفئة العمرية",\n'
    '  "logline": "جملة تسويقية للفكرة",\n'
    '  "theme": "العبرة الأخلاقية",\n'
    '  "arc": "قوس الشخصية الرئيسية: من أين تبدأ ومن تصبح",\n'
    '  "pilot": {\n'
    '    "title": "عنوان الحلقة التجريبية",\n'
    '    "hook": "خطاف الافتتاح",\n'
    '    "moral": "عبرة الحلقة",\n'
    '    "act1": "ماذا يحدث في الفصل الأول",\n'
    '    "act2": "ماذا يحدث في الفصل الثاني (التصاعد)",\n'
    '    "act3": "ماذا يحدث في الفصل الثالث (الحل)",\n'
    '    "scenes": [\n'
    "      {\"num\": 1, \"title\": \"اسم المشهد\", \"seconds\": 20, \"location\": \"المكان\", \"mood\": \"المزاج\", "
    '"beat": "setup", "tension": 3, "cast": ["اسم شخصية"], '
    '        "action": "وصف الحركة بالعربية", "dialogue": [[\"المتكلم\", \"الجملة\"], [\"المتكلم2\", \"الجملة\"]], '
    '        "image_prompt": "English cinematic image prompt, 2D animation style", '
    '        "sfx": ["مؤثر صوتي", "موسيقى"], "camera": ["توجيه كاميرا/مونتاج"], '
    '        "shot": {"framing": "wide establishing shot", "angle": "eye level", "movement": "slow push-in", "lens": "24mm", "focus": "وصف التركيز"}, '
    '        "music": {"mode": "minor", "intensity": 7, "tempo": 96, "keywords": ["dark strings"]}}\n'
    "    ]\n"
    "  },\n"
    '  "characters": [{"name": "اسم الشخصية", "role": "الدور", "desc": "وصف مختصر", "design_prompt": "English character design prompt", "arc": "قوسه في الحلقة"}],\n'
    '  "next_episodes": ["فكرة حلقة قادمة", "فكرة أخرى"],\n'
    '  "post_credits": {"title": "عنوان", "description": "وصف مشهد ما بعد الشارة يلمح لعالم مشترك", "dialogue": [["المتكلم", "الجملة"]], "image_prompt": "English prompt"}\n'
    "}\n"
    "قواعد: 7 مشاهد بالضبط موزعة على 3 فصول (فصل أول مشهدان، فصل ثان ثلاثة مشاهد، فصل ثالث مشهدان). "
    "مجموع الثواني = 180 تقريبًا (مشهد الذروة هو الأطول). "
    "كل مشهد له beat من القيم: setup, inciting, rising1, rising2, climax, falling, resolution بالترتيب عبر الحلقة. "
    "tension قيمة من 1 إلى 10 ترتفع نحو الذروة ثم تنخفض في الخاتمة. "
    "cast أسماء الشخصيات الظاهرة فعليًا في المشهد فقط. "
    "image_prompt بالإنجليزية بأسلوب رسوم متحركة سينمائي متسق مع وصف شخصية ثابت. "
    "كل شخصية في characters لها design_prompt بالإنجليزية يثبت ملامحها الجسدية والملابس (يُعاد استخدامه في كل المشاهد). "
    "حوار عربي فصيح ممتع للأطفال. شخصيات أصلية 100%. "
    "مشهد بعد الشارة يحتوي كاميو/تلميحًا لعالم مشترك مستقبلي."
)

SCHEMA_HINTS = ("title", "logline", "characters", "scenes")

DIRECTOR_PROMPT = (
    "أنت مخرج إنتاج استوديو رسوم متحركة عالمي (مثل Ben 10, Spider-Verse, Arcane) يتولى تنفيذ حلقة من مسلسل كرتوني عربي فاخر. "
    "تعمل وفق مذكرة إنتاج مرسلة من المنتج تحتوي الفكرة، وصف الشخصيات، وملخص الأحداث. "
    "مهمتك: تحويلها إلى حلقة متكاملة بمعايير استوديو حقيقي:\n"
    "1) البنية الدرامية: افتتاحية قوية، صراع تصاعدي، ذروة مثيرة، حوار شخصي مميز لا يُكتب بالصدفة.\n"
    "2) الشخصيات: احترم وصف المخرج حرفيًا (الاسم، الدور، الملامح، الصوت). لا تخترع شخصيات بديلة عن المذكورة.\n"
    "3) الحوار: لكل شخصية شخصية لغوية مختلفة (متهور حاد، حكيم هادئ، مرح خفيف...) — حوار عربي فصيح مفعم بالعاطفة.\n"
    "4) الاخراج السينمائي: كل مشهد له كاميرا (framing/angle/movement/lens/focus) وإضاءة ومزاج وحركة محددة.\n"
    "5) مذكرة الأحداث تحدد أقواس الفصول — حوّلها لمشاهد، وأضف المشاهد الانتقالية اللازمة.\n"
    "أخرج JSON صارمًا فقط بهذا الهيكل (لا شيء غيره):\n"
    "{\n"
    '  "title": "اسم السلسلة (عربي)",\n'
    '  "genre": "النوع",\n'
    '  "audience": "الفئة العمرية",\n'
    '  "episode_length": "25 دقيقة",\n'
    '  "series_synopsis": "ملخص السلسلة الكاملة",\n'
    '  "visual_style": "الوصف البصري الموحد للأسلوب",\n'
    '  "logline": "جملة تسويقية",\n'
    '  "theme": "العبرة الأخلاقية",\n'
    '  "arc": "قوس الشخصية الرئيسية",\n'
    '  "pilot": {\n'
    '    "title": "عنوان الحلقة",\n'
    '    "duration": "25 دقيقة / 1500 ثانية",\n'
    '    "hook": "خطاف الافتتاح",\n'
    '    "moral": "عبرة الحلقة",\n'
    '    "act1": "الفصل الأول",\n'
    '    "act2": "الفصل الثاني",\n'
    '    "act3": "الفصل الثالث",\n'
    '    "scenes": [\n'
    "      {\"num\": 1, \"title\": \"اسم المشهد\", \"seconds\": 30, \"location\": \"المكان\", \"mood\": \"المزاج\", "
    '"beat": "setup", "tension": 3, "cast": ["اسم شخصية"], '
    '        "action": "وصف حركي مسرحي بالعربية", "dialogue": [["المتكلم", "الجملة"]], '
    '        "image_prompt": "English cinematic 2D animation image prompt", '
    '        "sfx": ["مؤثر صوتي"], "camera": ["توجيه كاميرا"], '
    '        "shot": {"framing": "wide establishing shot", "angle": "eye level", "movement": "slow push-in", "lens": "24mm", "focus": "التركيز"}, '
    '        "music": {"mode": "minor", "intensity": 7, "tempo": 96, "keywords": ["epic brass"]}}\n'
    "    ]\n"
    "  },\n"
    '  "characters": [{"name": "الاسم", "role": "الدور", "desc": "وصف مختصر", "personality": "طباعه وطريقة كلامه", '
    '"voice": "ar-SA-HamedNeural أو ar-EG-SalmaNeural أو صوت edge-tts عربي يناسب الجنس والسن", "design_prompt": "English character design, ثابت الملامح والملابس"}],\n'
    '  "next_episodes": ["فكرة حلقة قادمة"],\n'
    '  "post_credits": {"title": "عنوان", "description": "مشهد بعد الشارة", "dialogue": [["المتكلم", "الجملة"]], "image_prompt": "English prompt"}\n'
    "}\n"
    "قواعد الإخراج: عدد المشاهد حسب القصة — من 12 إلى 50 مشهدًا، وكلما كانت القصة أطول وأكثر أحداثًا زاد عدد المشاهد "
    "(قصة بسيطة ≈ 12-15 مشهدًا، قصة متوسطة ≈ 25-30، قصة ملحمية واسعة ≈ 45-50). "
    "كل مشهد بين 25 و 35 ثانية فقط — لا تجعل أي مشهد أطول من 40 ثانية أبدًا؛ إن احتجت وقتًا أكثر اكتب مشاهد إضافية قصيرة. "
    "القاعدة الذهبية: عدد المشاهد × 30 ≈ 1500. لا تزيد مدد المشاهد للوصول للهدف؛ زِد عدد المشاهد."
    "مجموع الثواني ≈ 1500 (25 دقيقة). توزيع beats عبر المشاهد بالتصاعد الدرامي: setup, inciting, rising1, rising2, "
    "climax, falling, resolution — ويمكن أن يتكرر نفس الـ beat في مشاهد متتالية من نفس الفصل (مثلًا 4 مشاهد rising1). "
    "المشهد الأخير من الحلقة beat=resolution، والذروة climax منتصف الحلقة تقريبًا. "
    "tension من 1 إلى 10 يرتفع نحو الذروة. cast = الشخصيات الظاهرة فعليًا. "
    "image_prompt بالإنجليزية، يتضمن أسماء وأوصاف الشخصيات الظاهرة لضمان ثباتها بصريًا، بأسلوب 2D سينمائي فاخر. "
    "design_prompt لكل شخصية بالإنجليزية: الملامح، البنية، الملابس، الألوان — يُعاد استخدامه كما هو في كل المشاهد. "
    "voice: صوت edge-tts عربي حقيقي من القائمة: ar-EG-SalmaNeural (أنثى مصرية)، ar-EG-ShakirNeural (ذكر مصري)، "
    "ar-SA-ZariyahNeural (أنثى سعودية)، ar-SA-HamedNeural (ذكر سعودي)، ar-SY-AmanyNeural (أنثى شامية)، "
    "ar-AE-FatimaNeural (أنثى إماراتية)، ar-AE-HamdanNeural (ذكر إماراتي). اختر الأنسب لجنس وطابع الشخصية، والراوي ar-EG-SalmaNeural."
)


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
        scene = {
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
        }
        if sc.get("beat"):
            scene["beat"] = str(sc["beat"])
        if sc.get("tension") is not None:
            try:
                scene["tension"] = int(sc["tension"])
            except (TypeError, ValueError):
                pass
        if sc.get("cast"):
            scene["cast"] = [str(x) for x in sc["cast"] if str(x)]
        if isinstance(sc.get("shot"), dict):
            scene["shot"] = {k: str(v) for k, v in sc["shot"].items() if v is not None}
        if isinstance(sc.get("music"), dict):
            music = {}
            for k, v in sc["music"].items():
                if v is None:
                    continue
                if k == "intensity":
                    try:
                        music[k] = int(v)
                    except (TypeError, ValueError):
                        pass
                elif k == "tempo":
                    try:
                        music[k] = int(v)
                    except (TypeError, ValueError):
                        pass
                elif k == "keywords":
                    music[k] = [str(x) for x in v]
                else:
                    music[k] = str(v)
            if music:
                scene["music"] = music
        scenes.append(scene)
    post = data.get("post_credits", {})
    characters = []
    for ch in data.get("characters", []):
        item = {
            "name": str(ch.get("name", "")),
            "role": str(ch.get("role", "")),
            "desc": str(ch.get("desc", "")),
            "design_prompt": str(ch.get("design_prompt", "")),
        }
        if ch.get("arc"):
            item["arc"] = str(ch["arc"])
        if ch.get("personality"):
            item["personality"] = str(ch["personality"])
        if ch.get("voice"):
            item["voice"] = str(ch["voice"])
        characters.append(item)
    return {
        "slug": "custom-" + uuid.uuid4().hex[:6],
        "title": str(data.get("title", "سلسلة مخصصة")),
        "genre": str(data.get("genre", "مغامرة")),
        "audience": str(data.get("audience", "6 - 12 سنوات")),
        "episode_length": str(data.get("episode_length", "20 دقيقة (الحلقة التجريبية: 3 دقائق)")),
        "series_synopsis": str(data.get("series_synopsis", data.get("logline", ""))),
        "visual_style": str(data.get("visual_style", "2D سينمائي فاخر بألوان دافئة وإضاءة درامية")),
        "logline": str(data.get("logline", "")),
        "theme": str(data.get("theme", "")),
        "arc": str(data.get("arc", "")),
        "pilot": {
            "title": str(data.get("pilot", {}).get("title", "الحلقة التجريبية")),
            "duration": str(data.get("pilot", {}).get("duration", "3 دقائق / 180 ثانية")),
            "hook": str(data.get("pilot", {}).get("hook", "")),
            "moral": str(data.get("pilot", {}).get("moral", "")),
            "act1": str(data.get("pilot", {}).get("act1", "")),
            "act2": str(data.get("pilot", {}).get("act2", "")),
            "act3": str(data.get("pilot", {}).get("act3", "")),
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
    with httpx.Client(timeout=httpx.Timeout(600.0)) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def transform_idea(idea):
    return transform_brief(idea)


def transform_brief(brief):
    prompt = DIRECTOR_PROMPT + "\n\nمذكرة الإنتاج من المنتج:\n" + (brief or "")[:12000]
    if GROQ_API_KEY:
        try:
            data = _call_openai_style(
                "https://api.groq.com/openai/v1/chat/completions",
                {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 24000,
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
                    "messages": [{"role": "system", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 16000,
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
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
            }
            data = _call_openai_style(url, {"Content-Type": "application/json"}, payload)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _normalize(_extract_json(text))
        except Exception:
            pass
    return None
