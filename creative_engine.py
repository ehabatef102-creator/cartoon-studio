import copy
import os
import re
from pathlib import Path

from packs import PACKS, get_pack
from universe import UNIVERSE

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

CINEMATIC = (
    "cinematic anamorphic 2.39:1 wide framing, dramatic volumetric lighting, cinematic teal-orange color grade, "
    "shallow depth of field, epic composition, subtle film grain, high detail feature-film quality"
)


def cinematic_prompt(base_prompt):
    return f"{base_prompt} {CINEMATIC}"


def slugify(text):
    text = re.sub(r"[^\w]+", "-", str(text)).strip("-").lower()
    return text or "series"


def seconds_to_mmss(total):
    total = int(total)
    return f"{total // 60:02d}:{total % 60:02d}"


def _fmt_dialogue(dialogue):
    if not dialogue:
        return "لا يوجد حوار"
    lines = []
    for speaker, line in dialogue:
        lines.append(f'- **{speaker}:** "{line}"')
    return "\n".join(lines)


def _fmt_list(items):
    if not items:
        return "- لا يوجد"
    return "\n".join(f"- {item}" for item in items)


def _fmt_tts(tts, scene):
    if tts:
        return "\n".join(f"- {line}" for line in tts)
    lines = []
    speakers = set(s for s, _ in scene["dialogue"])
    for speaker in speakers:
        lines.append(f"- سطر {speaker} → نص الحوار أعلاه (اضبطه للقراءة لا للكلام العامي) ")
    if not lines:
        lines.append("- لا حاجة لتعليق صوتي في هذا المشهد")
    return "\n".join(lines)


def render_bible(pack):
    out = []
    out.append(f"# {pack['title']}")
    out.append("")
    out.append(f"- **النوع:** {pack['genre']}")
    out.append(f"- **الجمهور:** {pack['audience']}")
    out.append(f"- **مدة الحلقة:** {pack['episode_length']}")
    out.append("")
    out.append("## اللوغلاين (Logline)")
    out.append(pack["logline"])
    out.append("")
    out.append("## الثيمة الأساسية (Theme)")
    out.append(pack["theme"])
    out.append("")
    out.append("## ملخص السلسلة")
    out.append(pack["series_synopsis"])
    out.append("")
    out.append("## الهوية البصرية (Visual Style)")
    out.append("> " + pack["visual_style"])
    out.append("")
    out.append("## الشخصيات")
    out.append("")
    for ch in pack["characters"]:
        out.append(f"### {ch['name']} — {ch['role']}")
        out.append(ch["desc"])
        out.append("")
        out.append("**برومبت تصميم الشخصية (لتوليد الصور باستمرارية):**")
        out.append("> " + ch["design_prompt"])
        out.append("")
    out.append("## الأبطال والخصوم على مدى الموسم")
    out.append("")
    for i, line in enumerate(pack["next_episodes"], 1):
        out.append(f"- **حلقة محتملة {i + 1}:** {line}")
    out.append("")
    out.append("---")
    out.append("*ملاحظة حقوق: كل الشخصيات والأماكن والأسماء أصلية 100% ومُنتجة لهذا العمل فقط.*")
    out.append("")
    return "\n".join(out)


def render_pilot_script(pack):
    pilot = pack["pilot"]
    out = []
    out.append(f"# سيناريو الحلقة التجريبية: {pilot['title']}")
    out.append("")
    out.append(f"- **المدة:** {pilot['duration']}")
    out.append(f"- **الخطاف (Hook):** {pilot['hook']}")
    out.append(f"- **العبرة (Moral):** {pilot['moral']}")
    out.append("")
    out.append("| # | المشهد | التوقيت | المكان | المدة |")
    out.append("|---|--------|---------|--------|-------|")
    for sc in pilot["scenes"]:
        out.append(f"| {sc['num']} | {sc['title']} | {sc['timing']} | {sc['location']} | {sc['seconds']} ث |")
    if pack.get("post_credits"):
        out.append(f"| + | {pack['post_credits']['title']} | بعد الشارة | عالم مشترك | — |")
    out.append("")
    out.append("---")
    out.append("")
    for sc in pilot["scenes"]:
        out.append(f"## المشهد {sc['num']} — {sc['title']}")
        out.append("")
        out.append(f"- **التوقيت:** {sc['timing']} (مدة ≈ {sc['seconds']} ثانية)")
        out.append(f"- **المكان:** {sc['location']}")
        out.append(f"- **المزاج:** {sc['mood']}")
        out.append("")
        out.append(f"### الوصف (Action)")
        out.append(sc["action"])
        out.append("")
        out.append("### الحوار (Dialogue)")
        out.append(_fmt_dialogue(sc["dialogue"]))
        out.append("")
        out.append("---")
        out.append("")

    if pack.get("post_credits"):
        pc = pack["post_credits"]
        out.append(f"## المشهد + — {pc['title']} (بعد الشارة — مثل مارفل)")
        out.append("")
        out.append("### الوصف (Action)")
        out.append(pc["description"])
        out.append("")
        out.append("### الحوار (Dialogue)")
        out.append(_fmt_dialogue(pc["dialogue"]))
        out.append("")
        out.append("> هذا المشهد يربط السلسلة بالعالم المشترك ويهيّئ حدث الالتقاء. راجع `05_universe_bible.md`.")
        out.append("")
    return "\n".join(out)


def render_scene_brief(pack, scene):
    from server import visual

    out = []
    out.append(f"# بريف المشهد {scene['num']} — {scene['title']}")
    out.append("")
    out.append(f"**السلسلة:** {pack['title']} | **الحلقة:** {pack['pilot']['title']}")
    out.append(f"- **التوقيت:** {scene['timing']} (≈ {scene['seconds']} ثانية)")
    out.append(f"- **المكان:** {scene['location']}")
    out.append(f"- **المزاج:** {scene['mood']}")
    out.append(f"- **قوس القصة (Beat):** {scene.get('beat', 'setup')} | **مستوى التوتر:** {scene.get('tension', 5)}/10")
    cast = scene.get("cast") or [c["name"] for c in visual.extract_cast(pack, scene)]
    out.append(f"- **الممثلون (Cast):** {('، '.join(cast)) if cast else '—'}")
    out.append("")
    out.append("## 1) وصف المشهد")
    out.append(scene["action"])
    out.append("")
    out.append("## 2) برومبت الصورة السينمائي (لتوليد الصور الخارجية)")
    out.append("> " + cinematic_prompt(scene["image_prompt"]))
    out.append("")
    out.append("**إرشادات برومبت:** احتفظ بنفس الأسلوب العام في كل المشاهد للاستمرارية، وثبّت ملامح الشخصيات "
               "من ملف البايبِل. لوحة سينمائية 2.39:1 (ما يعادل 1920×1080 أو أوسع)، تدرج ألوان دافئ، وإضاءة درامية.")
    out.append("")
    shots = scene.get("shot") or visual.shot_plan(scene, scene.get("beat", "setup"))
    out.append("## 2ب) الستوريبورد السينمائي (كيف تُصور)")
    for i, s in enumerate(shots, 1):
        out.append(f"- **لقطة {i}:** {s.get('framing')} · {s.get('angle')} · {s.get('movement')} · {s.get('lens')} · تركيز: {s.get('focus')}")
    out.append("")
    out.append("## 3) الحوار")
    out.append(_fmt_dialogue(scene["dialogue"]))
    out.append("")
    out.append("## 4) التعليق الصوتي / النصوص الصوتية (TTS)")
    out.append(_fmt_tts(scene.get("tts"), scene))
    out.append("")
    out.append("## 5) التصميم الصوتي (Sound Design)")
    music = scene.get("music") or visual.music_score(scene.get("beat", "setup"), scene.get("mood", ""), scene["num"])
    out.append(f"- **الموسيقى التصويرية:** {music.get('mode')} · شدّة {music.get('intensity')}/10 · إيقاع {music.get('tempo')} BPM · {', '.join(music.get('keywords', []))}")
    out.append("- **المؤثرات الصوتية (SFX):**")
    out.append(_fmt_list(scene["sfx"]))
    out.append("")
    out.append("## 6) الكاميرا والمونتاج (CapCut / DaVinci Resolve)")
    out.append(_fmt_list(scene["camera"]))
    out.append("")
    return "\n".join(out)


def render_post_credit_brief(pack):
    from server import visual

    pc = pack["post_credits"]
    out = []
    out.append(f"# بريف مشهد ما بعد الشارة — {pc['title']}")
    out.append("")
    out.append(f"**السلسلة:** {pack['title']} | **العالم:** {UNIVERSE['name']}")
    cast = pc.get("cast") or [c["name"] for c in visual.extract_cast(pack, pc)]
    out.append(f"**الممثلون (Cast):** {('، '.join(cast)) if cast else '—'}")
    out.append("")
    out.append("## 1) وصف المشهد")
    out.append(pc["description"])
    out.append("")
    out.append("## 2) برومبت الصورة السينمائي")
    out.append("> " + cinematic_prompt(pc["image_prompt"]))
    out.append("")
    shots = pc.get("shot") or visual.shot_plan(pc, "crossover")
    for i, s in enumerate(shots, 1):
        out.append(f"- **لقطة {i}:** {s.get('framing')} · {s.get('angle')} · {s.get('movement')} · {s.get('lens')}")
    out.append("")
    out.append("## 3) الحوار")
    out.append(_fmt_dialogue(pc["dialogue"]))
    out.append("")
    out.append("## 4) لماذا هذا المشهد؟")
    out.append("يربط السلسلة بالعالم المشترك «أفق السحاب» ويحمل تلميحًا واحدًا نحو حدث الالتقاء. "
               "وظيفته التحفيزية: جعل المشاهد يتابع باقي السلاسل ليجمع اللغز.")
    out.append("")
    return "\n".join(out)


def render_universe_bible(pack):
    out = []
    out.append(f"# عالم أفق السحاب (Cloudverse) — بايبِل العالم المشترك")
    out.append("")
    out.append(f"> **{UNIVERSE['name']}** — {UNIVERSE['tagline']}")
    out.append("")
    out.append("## الوصف العام")
    out.append(UNIVERSE["description"])
    out.append("")
    out.append("## التهديد الرئيسي")
    out.append(f"### {UNIVERSE['threat']['name']}")
    out.append(UNIVERSE["threat"]["description"])
    out.append("")
    out.append("## خريطة المراحل (Phases)")
    out.append("")
    for phase in UNIVERSE["phases"]:
        out.append(f"### {phase['phase']} — {phase['goal']}")
        for step in phase["steps"]:
            out.append(f"- {step}")
        out.append(f"- **حدث التقاء:** {phase['crossover']}")
        out.append("")
    out.append("## قوانين العالم الثابتة (Canon Rules)")
    out.append("")
    for rule in UNIVERSE["canon_rules"]:
        out.append(f"- {rule}")
    out.append("")
    out.append(f"## موقع هذه السلسلة في المرحلة 1")
    out.append("")
    out.append(f"**{pack['title']}** هي إحدى السلاسل الثلاث المؤسِّسة. تلميحاتها الحالية نحو العالم المشترك:")
    out.append("")
    out.append("### مشهد ما بعد الشارة لهذه السلسلة")
    out.append(pack["post_credits"]["description"])
    out.append("")
    out.append("### الكاميو المخطط عبر السلاسل")
    out.append("")
    out.append("| السلسلة | الكاميو |")
    out.append("|---|---|")
    out.append("| مدينة السحاب | بُرد (روبت الغلاية من وادي بوت) يلوّح خلف الغيوم |")
    out.append("| مكتبة الأحلام | ريشة بوقة الذهبية فوق غلاف كتاب، واسم لولا |")
    out.append("| وادي بوت | صدى بوقة على راديو بَرَش وإحداثيات مدينة السحاب |")
    out.append("")
    out.append("## الفيلم الجامع المخطط")
    out.append("")
    out.append(f"### {UNIVERSE['teamup_name']}")
    out.append(UNIVERSE["teamup_logline"])
    out.append("")
    out.append("> المبدأ المارفلي: كل حلقة تخدم قوسها الخاص + تلميح واحد للمرحلة. لا أحد يُصرّح بالتهديد كاملًا قبل المرحلة الثانية.")
    out.append("")
    return "\n".join(out)


def render_production_guide():
    out = []
    out.append("# دليل الإنتاج — من سكربت إلى فيديو يوتيوب")
    out.append("")
    out.append("## تدفق العمل (Workflow)")
    out.append("")
    out.append("1. **السيناريو:** ملف `01_pilot_script.md` (جاهز) — بنية 3 فصول + مشهد ما بعد الشارة.")
    out.append("2. **الصور السينمائية:** برومبتات جاهزة بإخراج سينمائي (2.39:1، إضاءة درامية، تدرج ألوان) في `02_scenes/`.")
    out.append("3. **الحركة:** الزوم المتناوب + تدرج الألوان + حبيبات الفيلم يجريها السيرفر تلقائيًا عند طلب الفيديو، "
               "أو يدويًا بـ CapCut/DaVinci بأسلوب Ken Burns.")
    out.append("4. **الأصوات:** توليد الحوار بالعربية (راجع الجدول)، ثم مزامنة كل سطر مع مشهده.")
    out.append("5. **المونتاج:** ترتيب المشاهد بالترتيب المذكور، إضافة SFX والموسيقى من مكتبة يوتيوب المجانية.")
    out.append("6. **الشارة (Marvel Style):** بطاقة افتتاحية + بطاقة ختامية + مشهد بعد الشارة يربط بالعالم المشترك.")
    out.append("7. **التصدير:** 1920×1080، 30 إطار/ث، تدرج ألوان سينمائي.")
    out.append("8. **الرفع:** ملف `04_youtube_checklist.md` للميتاداتا والحقوق، و`05_universe_bible.md` لخريطة المراحل.")
    out.append("")
    out.append("## الأدوات الخارجية الموصى بها")
    out.append("")
    out.append("### توليد الصور")
    out.append("| الأداة | مجانية؟ | ملاحظات |")
    out.append("|---|---|---|")
    out.append("| Bing Image Creator (DALL-E) | نعم | رخصة استخدام مدمجة مع حساب مايكروسوفت |")
    out.append("| Leonardo.ai | رصيد يومي مجاني | تحكم جيد بالأسلوب |")
    out.append("| Stable Diffusion (AUTOMATIC1111) | نعم (مفتوح) | يعمل على جهازك، بلا قيود |")
    out.append("| Midjourney | مدفوعة | أعلى جودة فنية |")
    out.append("| DALL-E 3 عبر ChatGPT | مدفوعة | متاح بالعربي للبرومبتات |")
    out.append("")
    out.append("### توليد الصوت (TTS) بالعربية")
    out.append("| الأداة | مجانية؟ | ملاحظات |")
    out.append("|---|---|---|")
    out.append("| Edge TTS (بايثون: edge-tts) | نعم | أصوات عربية طبيعية مجانية |")
    out.append("| Google Text-to-Speech | نعم | أصوات جيدة للمواليد |")
    out.append("| ElevenLabs | رصيد مجاني ثم مدفوعة | أفضل جودة عاطفية، يدعم العربية |")
    out.append("| Azure TTS | مدفوعة | أصوات عربية ممتازة، خيارات تعابير |")
    out.append("")
    out.append("### المونتاج والتحريك")
    out.append("| الأداة | مجانية؟ | ملاحظات |")
    out.append("|---|---|---|")
    out.append("| CapCut | نعم | الأسهل: زوم، انتقالات، نص، مؤثرات |")
    out.append("| DaVinci Resolve | نعم | احترافي مجانًا (حركة كاميرا، تصحيح ألوان، عزل ألوان) |")
    out.append("| Kling AI | رصيد مجاني | تحريك مشاهد كاملة (يليق بالإنتاج السينمائي) |")
    out.append("| Runway Gen-3 | مدفوعة | تحريك عالي الجودة بالكادر والصوت |")
    out.append("| Pika | رصيد مجاني | تحريك الصور الثابتة لمشاهد قصيرة |")
    out.append("")
    out.append("### موسيقى ومؤثرات مجانية وآمنة حقوقيًا")
    out.append("| المصدر | ملاحظات |")
    out.append("|---|---|")
    out.append("| YouTube Audio Library | مجانية 100% وبلا حقوق ملكية — الأنسب لقناة يوتيوب |")
    out.append("| Pixabay Music | مجانية برخصة حرّة |")
    out.append("| Suno (أصوات عبر الذكاء الاصطناعي) | مجانية محدودة | موسيقى تصويرية أصلية لا تُنسب لحقوق أحد |")
    out.append("| FreePD | موسيقى ملكية عامة |")
    out.append("")
    out.append("## الاستراتيجية السينمائية (مارفل-ستايل)")
    out.append("")
    out.append("- **بطاقة افتتاحية:** شعار السلسلة + اسم الحلقة (يولّده السيرفر تلقائيًا في الفيديو).")
    out.append("- **مشهد ما بعد الشارة:** يربط الحلقة بالعالم المشترك «أفق السحاب» — إلزامي في كل حلقة.")
    out.append("- **الكاميو:** شخصية من سلسلة أخرى تظهر ثوانٍ داخل حلقة — يبني متابعة متقاطعة بين القنوات/السلاسل.")
    out.append("- **التدرج اللوني (Color Grade):** دافئ بظلال زرقاء (Teal-Orange) — يولّده السيرفر تلقائيًا.")
    out.append("- **الاستمرارية:** نفس برومبت الشخصية في كل المشاهد وكل الحلقات لثبات الملامح.")
    out.append("")
    out.append("## حساب المدة لهدف 20 دقيقة")
    out.append("")
    out.append("الحلقة التجريبية = 3 دقائق. لتجميع حلقة 20 دقيقة:")
    out.append("- القصة تحتاج 4-5 قصص فرعية مترابطة (حوالي 16 مشهدًا إجمالًا).")
    out.append("- يمكنني (المحرك + الكتابة اليدوية) توليد حلقة كاملة 20 دقيقة عند الطلب بعد نجاح الحلقة التجريبية.")
    out.append("- أعد نفس برومبت الصورة لكل مشهد في جميع الحلقات للحفاظ على الاستمرارية البصرية.")
    out.append("")
    return "\n".join(out)


def render_youtube_checklist(pack):
    out = []
    out.append("# تشيك ليست النشر على يوتيوب (حقوق + تحسين)")
    out.append("")
    out.append("## 1) حقوق المحتوى (إثبات أن القناة «حقوقية» 100%)")
    out.append("")
    out.append("- الشخصيات والقصة والأسماء أصلية بالكامل (راجع ملف البايبِل) — لا يوجد CopyRight Claim من استوديوهات.")
    out.append("- كل الموسيقى والمؤثرات من YouTube Audio Library أو Pixabay (بلا حقوق ملكية).")
    out.append("- الصور مولّدة عبر برومبتات أصلية خاصة بالعمل؛ لا تستخدم صورًا من الإنترنت مباشرة.")
    out.append("- الأصوات: إما TTS مجاني أو أصوات ممثلين بعقودك الخاصة.")
    out.append("- رقّم حلقاتك وقم بتسجيل عنوان العمل لديك (أبسط سجل تاريخ يثبت الأولوية).")
    out.append("")
    out.append("## 2) إعدادات القناة")
    out.append("")
    out.append("- [ ] القناة موجهة للأطفال؟ حدّدها ضمن إعدادات القناة (COPPA) بما يتناسب مع فئة الجمهور.")
    out.append("- [ ] صورة القناة + بانر موحّد بلون الهوية البصرية.")
    out.append("- [ ] وصف القناة يشرح نوع المحتوى وموعد الحلقات الأسبوعي.")
    out.append("")
    out.append("## 3) ميتاداتا الحلقة")
    out.append("")
    out.append(f"- **عنوان الحلقة:** {pack['title']} — {pack['pilot']['title']} (الحلقة التجريبية)")
    out.append("- **وصف الحلقة:** نسخ الخطاف + ملخص السلسلة + رموز زمنية (0:00، 1:00...) للمشاهد.")
    out.append("- **كلمات مفتاحية:** اسم السلسلة + النوع + «كرتون عربي، رسوم متحركة، قصص أطفال» + لغة عربية.")
    out.append("- **وصف مصغر (Thumbnail):** لقطة بارزة + نص قصير واضح، ألوان عالية التباين.")
    out.append("")
    out.append("## 4) نشر وتوسيع")
    out.append("")
    out.append("- [ ] جدول ثابت: حلقة كل أسبوع في نفس الموعد.")
    out.append("- [ ] في نهاية كل حلقة رابط للحلقة السابقة + التالية (Playlist).")
    out.append("- [ ] أنشئ بلاي ليست لكل موسم.")
    out.append("- [ ] شغّل الفيديو بجودة 1080p/1440p للتصنيف الأفضل.")
    out.append("- [ ] تفاعل مع التعليقات بسرعة في أول 48 ساعة.")
    out.append("")
    out.append("## 5) خطة التوسع إلى 20 دقيقة")
    out.append("")
    out.append("- حلقة تجريبية 3 دقائق → قياس تفاعل المشاهدين.")
    out.append("- الحلقة الكاملة 20 دقيقة: بنية 3 فصول (مقدمة، وسط، حل) + قصة فرعية A/B.")
    out.append("- عند طلبك: يمكن إضافة حلقة كاملة جديدة بنفس الجودة والاستمرارية.")
    out.append("")
    out.append("## 6) التسويق المارفلي (Shared Universe)")
    out.append("")
    out.append(f"- هذه السلسلة جزء من عالم «{UNIVERSE['name']}» — اذكر ذلك في وصف كل حلقة.")
    out.append("- انشر بلاي ليستات منفصلة لكل سلسلة + بلاي ليست «عالم أفق السحاب» للتقاطعات.")
    out.append("- مشهد ما بعد الشارة (بعد الدقيقة الثالثة) يحمل تلميحًا للمرحلة — أشِر إليه في التعليق المثبت.")
    out.append("- الكاميو عبر السلاسل يبني فضولًا متقاطعًا: «من هذه البومة؟»")
    out.append("- عند اكتمال المرحلة الأولى (12 حلقة) تطلق حدث الالتقاء «حرب الصبغة» كحدث مشترك.")
    out.append("")
    return "\n".join(out)


def build_pack(index=None, title=None, seed=None, out_dir=None):
    pack = get_pack(index=index, seed=seed)
    if title:
        pack = {**pack, "title": title}
    base = Path(out_dir or OUTPUT_DIR) / pack["slug"]
    count = render_and_write_pack(pack, base)
    return base, count, pack


def render_and_write_pack(pack, base):
    base = Path(base)
    scenes_dir = base / "02_scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    _apply_timings(pack)

    files = {
        base / "00_series_bible.md": render_bible(pack),
        base / "01_pilot_script.md": render_pilot_script(pack),
        base / "03_production_guide.md": render_production_guide(),
        base / "04_youtube_checklist.md": render_youtube_checklist(pack),
        base / "05_universe_bible.md": render_universe_bible(pack),
    }
    for sc in pack["pilot"]["scenes"]:
        files[scenes_dir / f"scene_{sc['num']:02d}_{slugify(sc['title'])}.md"] = render_scene_brief(pack, sc)
    if pack.get("post_credits"):
        files[scenes_dir / "scene_08_post_credits.md"] = render_post_credit_brief(pack)

    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    return len(files)


def _apply_timings(pack):
    from server import visual

    t = 0
    for scene in pack["pilot"]["scenes"]:
        secs = int(scene.get("seconds", 25))
        scene["seconds"] = secs
        scene["timing"] = f"{t // 60:02d}:{t % 60:02d} - {(t + secs) // 60:02d}:{(t + secs) % 60:02d}"
        t += secs
    visual.enrich_pack(pack)
    return pack


def _idea_title(idea):
    first = next((ln.strip() for ln in idea.splitlines() if ln.strip()), "")
    if first:
        return first[:50]
    return "سلسلة مخصصة"


def build_custom_pack(idea, seed=None):
    idea = (idea or "").strip()
    if not idea:
        return None
    try:
        from server.llm import transform_idea

        pack = transform_idea(idea)
        if pack:
            pack["_source"] = "llm"
            return _apply_timings(pack)
    except Exception:
        pass

    base = get_pack(seed=seed)
    pack = copy.deepcopy(base)
    pack["slug"] = "custom-" + (str(seed) if seed else "template")
    pack["title"] = _idea_title(idea)
    pack["logline"] = idea[:400]
    pack["_source"] = "template"
    pack["pilot"]["hook"] = idea[:200]
    return _apply_timings(pack)


def list_packs():
    return [(i + 1, p["title"], p["genre"], p["audience"]) for i, p in enumerate(PACKS)]
