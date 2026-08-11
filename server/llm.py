import json
import os
import re
import sys
import time
import uuid

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def _target_scene_count():
    """عدد المشاهد المستهدف من المدة (للتشغيل التجريبي السريع). يُعيد None بدون ضبط.

    تُقرأ من البيئة عند كل استدعاء (وليس عند الاستيراد) حتى يضمن caller تعديلها
    (مثلاً produce.py بمعامل --target-seconds) قبل البناء.
    """
    raw = os.environ.get("TARGET_SECONDS", "").strip()
    try:
        ts = int(raw)
    except (TypeError, ValueError):
        return None
    if ts < 60:
        return None
    return max(3, min(50, int(round(ts / 30))))


def _length_directive():
    """سطر تعليمات يُلحق بالبرومبتات يفرض عدد المشاهد/المدة المطلوبة."""
    n = _target_scene_count()
    if n is None:
        return ""
    total = n * 30
    return (
        f"\nمطلوب {n} مشاهد بالضبط (هذه حلقة اختبار قصيرة). "
        f"كل مشهد 25-35 ثانية ومجموعها ≈ {total} ثانية ({total // 60} دقيقة تقريبًا). "
        "لا تزيد عن ذلك إطلاقًا."
    )

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

JSON_SCHEMA = (
    '{"title":"سلسلة","genre":"نوع","audience":"فئة","episode_length":"25 دقيقة",'
    '"series_synopsis":"ملخص","visual_style":"أسلوب بصري","logline":"جملة",'
    '"theme":"عبرة","arc":"قوس","pilot":{"title":"عنوان","hook":"خطاف","moral":"عبرة",'
    '"act1":"ف1","act2":"ف2","act3":"ف3"},'
    '"characters":[{"name":"اسم","role":"دور","desc":"وصف","personality":"طباع","voice":"صوت edge-tts",'
    '"design_prompt":"English design"}],'
    '"next_episodes":["فكرة"],'
    '"post_credits":{"title":"عنوان","description":"وصف","dialogue":[["متكلم","جملة"]],"image_prompt":"English"}}'
)

OUTLINE_PROMPT = (
    "أنت مخرج كرتون عربي فاخر. ضع خطة حلقة كاملة: قسم أحداث المذكرة على محاور القصة "
    "(افتتاحية، تصاعد، ذروة، خاتمة) وأضف مشاهد انتقالية. "
    "أخرج JSON واحدًا فقط (بدون نص آخر)، حقوله: title, genre, audience, series_synopsis, visual_style, logline, theme, arc, "
    'pilot{title,hook,moral,act1,act2,act3}, characters[{"name","role","desc","personality","voice","design_prompt(English)"}], '
    'next_episodes, post_credits{title,description,dialogue,image_prompt}, '
    'scenes[{title,location,beat}] — scenes تعرّف كل أحداث الحلقة بالترتيب (مشهد لكل حدث أو انتقال).\n'
    "قواعد:\n"
    "1) عدد المشاهد حسب القصة: بسيطة 12-15، متوسطة 25-30، ملحمية غنية 45-50، ولا تقل الملحمية عن 40.\n"
    "2) beats بتصاعد: setup, inciting, rising1, rising2, climax, falling, resolution — تتكرر في الفصل، الذروة قرب المنتصف، والآخر resolution.\n"
    "3) في scenes اكتب title+location+beat فقط، التفاصيل تُكتب لاحقًا.\n"
    "4) voice من: ar-EG-SalmaNeural، ar-EG-ShakirNeural، ar-SA-ZariyahNeural، ar-SA-HamedNeural، ar-SY-AmanyNeural، ar-AE-FatimaNeural، ar-AE-HamdanNeural.\n"
    "5) للمدة المستهدفة: مطلوب عدد محدد من المشاهد ومدة كل مشهد ثابتة — الالتزام حرفيًا وعدم تجاوز العدد.\n"
    "6) إن كانت القصة بسيطة جدًا: يمكن التقليل قليلًا حسب المدة المطلوبة في التعليمات.\n"
    + _length_directive()
)

SCENES_BATCH_PROMPT = (
    "أنت مخرج كرتون عربي. اكتب المشاهد من رقم {start} إلى {end} كاملة بالتفاصيل التنفيذية، "
    "مطابقة للخطة أدناه وباستمرارية مع المكتملة.\n"
    "المذكرة:\n{production}\n"
    "الخطة:\n{outline}\n"
    "الشخصيات (التزم بها حرفيًا):\n{characters}\n"
    "المكتمل سابقًا:\n{existing}\n"
    "أخرج JSON واحدًا فقط: {\"scenes\":[{\"num\":1,\"title\":\"اسم\",\"seconds\":30,\"location\":\"مكان\","
    "\"mood\":\"مزاج\",\"beat\":\"setup\",\"tension\":3,\"cast\":[\"اسم\"],\"action\":\"وصف حركي عربي\","
    "\"dialogue\":[[\"متكلم\",\"جملة\"]],\"image_prompt\":\"English cinematic 2D prompt\","
    "\"sfx\":[\"مؤثر\"],\"camera\":[\"كاميرا\"],"
    "\"shot\":{\"framing\":\"wide\",\"angle\":\"eye level\",\"movement\":\"slow push-in\",\"lens\":\"24mm\",\"focus\":\"التركيز\"},"
    "\"music\":{\"mode\":\"minor\",\"intensity\":7,\"tempo\":96,\"keywords\":[\"epic brass\"]}}, ...]}\n"
    "قواعد: عدد المشاهد {start}-{end} بالضبط، كل مشهد 25-35 ثانية (لا يزيد عن 40)، "
    "لكل مشهد shot+music+sfx+camera+image_prompt كاملة، حوار عربي فصيح لكل شخصية طباعها، "
    "المواقع والشخصيات من الخطة حرفيًا، image_prompt بالإنجليزية يذكر الشخصيات الظاهرة."
    + _length_directive()
)

OUTLINE_FALLBACK_SCENE_TEMPLATE = (
    "أنت مخرج كرتون عربي فاخر. حوّل المذكرة التالية إلى حلقة كاملة بكل التفاصيل.\n"
    "المذكرة:\n{production}\n"
    "أخرج JSON واحدًا فقط (بدون نص آخر):\n"
    + JSON_SCHEMA
    + " لكن داخل pilot أضف scenes:[{num,title,seconds,location,mood,beat,tension,cast,action,dialogue,image_prompt,sfx,camera,shot,music}]\n"
    "قواعد: عدد المشاهد حسب القصة من 12 إلى 50 (ملحمية 45-50)، كل مشهد 25-35 ثانية ومجموعها ≈ 1500 (25 دقيقة)، "
    "beats بتصاعد (setup, inciting, rising1, rising2, climax, falling, resolution) تتكرر في الفصل، "
    "لكل مشهد shot+music+sfx+camera+image_prompt كاملة، حوار عربي فصيح."
)

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
        for k in ("colors", "shape", "features"):
            if ch.get(k):
                item[k] = str(ch[k])
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


def _call_llm(prompt, max_tokens=24000, attempts=2):
    """يستدعي أول مزود LLM متاح (Groq ثم OpenAI ثم Gemini) ويعيد JSON مُحلَّل.

    عند 413 (payload كبير) يضغط المذكرة تدريجيًا ويعيد المحاولة؛ عند 429 ينتظر ويعيد.
    """
    text = prompt
    for attempt in range(attempts + 1):
        try:
            if GROQ_API_KEY:
                data = _call_openai_style(
                    "https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": text}],
                        "temperature": 0.7,
                        "max_tokens": max_tokens,
                        "response_format": {"type": "json_object"},
                    },
                )
                return _extract_json(data["choices"][0]["message"]["content"])
        except Exception as exc:
            code = getattr(exc, "response", None)
            status = code.status_code if code is not None else None
            if status == 429:
                print(f"[director] GROQ 429 (rate limit) — retry {attempt}", file=sys.stderr)
                time.sleep(3 * (attempt + 1))
                continue
            if status == 413 and len(text) > 3000:
                # الطلب أكبر من حد Groq: نضغط المذكرة إلى النصف
                cut = max(1500, len(text) // 2)
                text = text[:cut]
                print(f"[director] GROQ 413 — shrunk prompt to {cut} chars", file=sys.stderr)
                continue
            print(f"[director] GROQ failed ({status}): {exc!r}", file=sys.stderr)
            break
    if OPENAI_API_KEY:
        try:
            data = _call_openai_style(
                "https://api.openai.com/v1/chat/completions",
                {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "system", "content": text}],
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                },
            )
            return _extract_json(data["choices"][0]["message"]["content"])
        except Exception as exc:
            print(f"[director] OpenAI failed: {exc!r}", file=sys.stderr)
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
            }
            data = _call_openai_style(url, {"Content-Type": "application/json"}, payload)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(text)
        except Exception as exc:
            print(f"[director] Gemini failed: {exc!r}", file=sys.stderr)
    return None


def transform_brief(brief):
    raw = (brief or "").strip()

    # المرحلة 1: خطة الحلقة (توزيع الأحداث على محاور القصة) — استجابة صغيرة تنجح دائمًا
    production_short = "\n\nمذكرة الإنتاج من المنتج:\n" + raw[:1500]
    outline = _call_llm(OUTLINE_PROMPT + production_short, max_tokens=2200)
    if not outline:
        # فشلت الخطة: استخدم القالب الشامل كحل أخير
        fallback = OUTLINE_FALLBACK_SCENE_TEMPLATE.format(
            production="\n\nمذكرة الإنتاج:\n" + raw[:2500]
        )
        data = _call_llm(fallback, max_tokens=3200)
        return _normalize(data) if data else None
    return _finish_from_outline(outline, raw)


def _finish_from_outline(outline, raw):
    """المرحلة 2: يكتب المخرج المشاهد كاملة على دفعات صغيرة، ثم نجمّع الحلقة."""
    scenes = outline.get("scenes") or []
    total = len(scenes)
    if total < 4:
        fallback = OUTLINE_FALLBACK_SCENE_TEMPLATE.format(
            production="\n\nمذكرة الإنتاج:\n" + (raw or "")[:2500]
        )
        data = _call_llm(fallback, max_tokens=3200)
        return _normalize(data) if data else None
    target = _target_scene_count()
    if target is not None:
        # التشغيل التجريبي: نحسم العدد المطلوب (نأخذ أول N من الخطة)
        total = min(target, len(scenes))
    total = min(total, 50)

    characters = outline.get("characters") or []
    char_text = json.dumps(characters, ensure_ascii=False)[:3000]
    outline_copy = dict(outline)
    outline_copy["scenes"] = scenes[:total]
    outline_text = json.dumps(outline_copy, ensure_ascii=False)[:3500]
    production = "\n\nمذكرة الإنتاج من المنتج (تفاصيل إضافية اختيارية):\n" + (raw or "")[:2500]

    BATCH = 6
    completed = []
    for start in range(1, total + 1, BATCH):
        if completed:
            time.sleep(12)  # احترام حد 6000 TPM على free tier
        end = min(start + BATCH - 1, total)
        existing_summary = _summarize_scenes(completed)
        prompt = (
            SCENES_BATCH_PROMPT
            .replace("{production}", production)
            .replace("{outline}", outline_text)
            .replace("{characters}", char_text)
            .replace("{existing}", existing_summary)
            .replace("{start}", str(start))
            .replace("{end}", str(end))
        )
        data = _call_llm(prompt, max_tokens=2800)
        if not data:
            break
        batch_scenes = data.get("scenes") or []
        if not batch_scenes:
            break
        # إصلاح الترقيم: نرقم تسلسليًا من 1
        for k, sc in enumerate(batch_scenes, len(completed) + 1):
            sc["num"] = k
        completed.extend(batch_scenes)
        if len(completed) >= total:
            break

    if not completed:
        return None

    data = dict(outline)
    pilot = dict(outline.get("pilot") or {})
    pilot["scenes"] = completed
    data["pilot"] = pilot
    pack = _normalize(data)
    if pack:
        # مساعد المخرج: يراجع الاتساق ويصلح الدقيق (لا يكسر البنية)
        try:
            pack = assistant_review(pack)
        except Exception:
            pass
    return pack


def _summarize_scenes(scenes):
    if not scenes:
        return "لا يوجد — هذا أول دفعة."
    lines = []
    for sc in scenes[-4:]:
        title = sc.get("title", "")
        loc = sc.get("location", "")
        beat = sc.get("beat", "")
        action = (sc.get("action") or "")[:90]
        lines.append(f"- مشهد {sc.get('num')}: {title} ({loc}, beat={beat}) — {action}")
    return "\n".join(lines)


CONSISTENCY_PROMPT = (
    "أنت مساعد مخرج (Assistant Director) في استوديو رسوم متحركة. مهمتك: مراجعة جودة الاتساق "
    "في حلقة كتبها المخرج وإخراج قائمة تصحيحات دقيقة.\n"
    "تحقق من:\n"
    "1) أسماء الشخصيات مطابقة تمامًا لقائمة الشخصيات الرسمية (لا أسماء غريبة/مشابهة).\n"
    "2) أسماء الأماكن والمواقع ثابتة (لا يتغير اسم نفس المكان في مشاهد مختلفة).\n"
    "3) تسلسل beats منطقي: setup ← inciting ← rising ← climax ← falling ← resolution (يُسمح بتكرار نفس beat ضمن الفصل).\n"
    "4) مدة كل مشهد بين 25 و 40 ثانية (أقل/أكثر يُصحح ضمن الحدود).\n"
    "5) لا شخصية خارج قائمة الـ cast في حوار أو وصف، ولا مشهد بلا action.\n"
    "أخرج JSON واحدًا فقط:\n"
    '{"notes": ["ملاحظة مختصرة...", "..."], '
    '"fixes": [{"num": 1, "field": "seconds|location|beat|cast|action|dialogue", '
    '"value": "القيمة المصححة", "reason": "السبب"}], '
    '"summary": "تقييم عام بجملة واحدة"}\n'
    "إن لم يوجد ما يُصحح أخرج fixes فارغة.\n"
    "الحلقة:\n{data}"
)


_VALID_BEATS = {"setup", "inciting", "rising1", "rising2", "climax", "falling", "resolution", "crossover"}


def assistant_review(pack):
    """مساعد المخرج: يراجع الحلقة المكتملة ويُطبق تصحيحات الاتساق.

    لا يغير بنية الحلقة (عدد المشاهد/العناوين/الحوارات) إلا للتصحيحات الدقيقة.
    عند فشل النداء أو غياب fixes تعود الحلقة كما هي دون كسر.
    """
    scenes = (pack.get("pilot") or {}).get("scenes") or []
    if not scenes:
        return pack
    payload = json.dumps({
        "characters": [c.get("name") for c in pack.get("characters", [])],
        "locations": [s.get("location") for s in scenes],
        "scenes": [
            {"num": s.get("num"), "title": s.get("title"), "location": s.get("location"),
             "beat": s.get("beat", "setup"), "seconds": s.get("seconds"),
             "cast": s.get("cast", []), "action": s.get("action", ""),
             "dialogue": s.get("dialogue", [])}
            for s in scenes
        ],
    }, ensure_ascii=False)[:8000]
    prompt = CONSISTENCY_PROMPT.replace("{data}", payload)
    try:
        data = _call_llm(prompt, max_tokens=2000)
    except Exception:
        return pack
    if not data:
        return pack
    by_num = {int(s.get("num")): s for s in scenes}
    for fix in data.get("fixes") or []:
        try:
            num = int(fix.get("num"))
            field = (fix.get("field") or "").strip()
            value = fix.get("value")
        except (TypeError, ValueError):
            continue
        scene = by_num.get(num)
        if not scene or field not in ("seconds", "location", "beat", "cast", "action", "dialogue"):
            continue
        if field == "seconds":
            try:
                v = int(value)
            except (TypeError, ValueError):
                continue
            scene["seconds"] = max(20, min(40, v))
        elif field == "cast":
            allowed = {c.get("name") for c in pack.get("characters", [])}
            if isinstance(value, list):
                scene["cast"] = [str(x) for x in value if str(x) in allowed]
        elif field == "beat":
            if isinstance(value, str) and value.strip().lower() in _VALID_BEATS:
                scene["beat"] = value.strip().lower()
        else:
            scene[field] = str(value)
    return pack
