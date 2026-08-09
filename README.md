# Cartoon Studio — استوديو كرتون بالذكاء الاصطناعي

اكتب فكرة، يحوّلها إلى حلقة كرتون كاملة: سيناريو + صور مشاهد + تعليق صوتي عربي + فيديو mp4.

## المميزات
- **توليد من فكرة حرة**: اكتب أي فكرة → سيناريو 7 مشاهد + صور + صوت + فيديو.
- **سلاسل جاهزة**: 3 عوالم أصلية (أفق السحاب، صدى الواحة، المحطة الأخيرة).
- **سيناريو مخصص 100%** عند وضع `GROQ_API_KEY` (مجاني) في بيئة التشغيل.
- **صور** عبر Pollinations (مجاني) أو Stability عند وضع المفتاح.
- **صوت عربي** عبر edge-tts (مجاني) أو ElevenLabs عند وضع المفتاح.
- **فيديو سينمائي**: زووم متناوب + تدرج ألوان + بطاقات عنوان عربية + مشهد بعد الشارة.

## محرك الإنتاج السينمائي (Studio Engine)
طبقة استوديوهات فوق البايب لاين، كلها أدوات مجانية ومفتوحة:
- **الهوية البصرية الموحدة** (`server/visual.py`): كل مشهد يتولّد من برومبت مركّب = وصف المشهد + **أوراق الشخصيات** (ملامح ثابتة عبر المشاهد) + لغة الإخراج (framing/angle/movement/lens) + إضاءة حسب المزاج + تدرج لوني سينمائي.
- **قوس القصة والستوريبورد**: كل مشهد يُعلَّم بـ beat (setup→inciting→rising→climax→falling→resolution) و tention و cast، مع لقطات مخططة تُحفظ في `storyboard.json`.
- **قصة استوديوهات** (`server/llm.py`): بنية 3 فصول صريحة + أقواس شخصيات + صراع تصاعدي في برومبت المولّد.
- **حركة كاميرا ذكية** (`server/motion.py`): push-in / pan / tilt / zoom-out حسب اللقطة والذروة، مع انجراف سينمائي خفيف.
- **تصميم صوتي** (`server/sound_design.py`): موسيقى تصويرية مولّدة رقميًا حسب مزاج وشدّة المشهد + مؤثرات صوتية مُصنّعة من الوصف العربي + موسيقى تنخفض تلقائيًا تحت الحوار (ducking).

مفاتيح إضافية في الواجهة: **موسيقى تصويرية + مؤثرات** و**حركة كاميرا سينمائية** (قابلة للتعطيل لكل مهمة).

## الموقع الحي (GitHub Pages)
واجهة استوديو احترافية بالعربية تُنشر تلقائيًا على GitHub Pages عند كل دفع إلى `main`:
```
https://ehabatef102-creator.github.io/cartoon-studio/
```
تعمل في **ثلاثة أوضاع** تلقائيًا:
- **وضع المتصفح** (على Pages بدون خادم): صور عبر Pollinations + موسيقى مولّدة (WebAudio) + مونتاج حقيقي بالمتغيّر المتصفح (Canvas + MediaRecorder → WebM) + استماع بالعربية (Google TTS). تعمل بدون أي خادم.
- **وضع الخادم السحابي** (من Pages): افتح أيقونة الإعدادات ← «عنوان خادم السحابة» ← الصق رابط الخادم المنشور (مثل Render/Railway) ← حفظ. يتحول الموقع فورًا للتوليد عبر السحابة (سيناريو LLM + صور + edge-tts + مونتاج ffmpeg) — جهازك مجرد تحكم.
- **وضع الخادم** (عند تشغيل uvicorn): نفس الواجهة من نفس الأصل، ويعمل التوليد الكامل تلقائيًا على الخادم.

`web/packs.json` يولّد آليًا من `packs.py` عبر `scripts/export_packs.py` في workflow النشر.

## التشغيل المحلي
```powershell
pip install -r requirements.txt
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```
افتح http://localhost:8000 — كلمة المرور الافتراضية `admin123` (غيّرها عبر متغير `ADMIN_PASSWORD`).

## النشر على السحابة
### GitHub Container Registry (GHCR) — مجاني
كل دفع على `main` يبني الصورة ويرفعها تلقائيًا إلى:
```
ghcr.io/<your-user>/cartoon-studio:latest
```
بهذا تستطيع أي منصة سحابية تقبل الصور (Render/Railway/Fly) سحبها بنقرة.

### Render (مجاني) — خادم سحابي واحد يقدّم الموقع + التوليد معًا
`render.yaml` موجود ويستخدم Python runtime الأصلي (يدعم الخطة المجانية):
- New → Blueprint → اختر الريبو → Connect
- عيّن `ADMIN_PASSWORD` في Environment بعد أول نشر (إن لم تُعيّنه يعمل افتراضيًا `admin123`)
- افتح رابط الخدمة: الموقع يكتشف وضع الخادم تلقائيًا ويولّد بالسحابة مباشرة.
- لتوصيل الموقع الحي على Pages بنفس الخادم: Settings ← «عنوان خادم السحابة» ← `https://<خدمتك>.onrender.com`.

ملاحظة: الخطة المجانية تُطفيء الخدمة بعد خمول ~15 دقيقة وتستيقظ تلقائيًا عند أول طلب (ثوانٍ).

### متغيرات البيئة الاختيارية
| المتغير | الفائدة |
|---|---|
| `GROQ_API_KEY` | سيناريو مخصص 100% من الفكرة (مجاني من console.groq.com) |
| `STABILITY_API_KEY` | صور أدق |
| `ELEVENLABS_API_KEY` | أصوات عاطفية |
| `ADMIN_PASSWORD` | كلمة مرور لوحة التحكم |
| `AUDIO_DESIGN` | `1`/`0` تشغيل/إيقاف الموسيقى والمؤثرات |
| `MOTION_ENGINE` | `1`/`0` تشغيل/إيقاف حركة الكاميرا |

## الإنتاج على السحابة المجانية (بدون طاقة جهازك)
مسار الإنتاج الكامل يعمل على **خوادم مجانية** منفصلة تمامًا عن جهازك — جهازك يعمل كجهاز تحكم فقط:

- **GitHub Actions** (سحابة GitHub المجانية): من تبويب *Actions* → *produce-episode* → *Run workflow* → الصق قصتك أو اختر سلسلة → أنزل حزمة الـ ZIP (سيناريو + صور + صوت + فيديو).
- **Google Colab** (سحابة جوجل المجانية): افتح `notebooks/Cartoon_Studio.ipynb` على colab.research.google.com و اضغط Run all — يعمل بنفس المسار على معالج جوجل وينزّل الناتج مباشرة.

```
python scripts/produce.py --story "قصة..." --video --music --motion --out output
python scripts/produce.py --index 1 --video --out output        # سلسلة جاهزة
```

المشغّل `scripts/produce.py` هو نفس محرك الخادم (`server/pipeline.py`) يعمل لاسلكيًا (headless) على أي سحابة فيها Python + ffmpeg.

## البنية
```
server/app.py          FastAPI + API الجوبات
server/pipeline.py     التوليد: صور → صوت → فيديو
server/visual.py       الهوية البصرية + الستوريبورد
server/motion.py       حركة الكاميرا السينمائية
server/sound_design.py موسيقى ومؤثرات ومكس الصوت
server/llm.py          تحويل الفكرة لسيناريو استوديو
creative_engine.py     باك الإنتاج (سيناريو/بريفات/مواد)
packs.py               السلاسل الجاهزة
universe.py            عالم مشترك
web/                   الموقع الحي (واجهة + محرك متصفح)
scripts/export_packs.py تصدير packs.json للواجهة
scripts/produce.py     تشغيل الإنتاج الكامل على السحابة (headless)
notebooks/             دفتر Colab للإنتاج على سحابة جوجل
.github/workflows/pages.yml  نشر GitHub Pages
.github/workflows/produce.yml  إنتاج على سحابة GitHub المجانية
```
