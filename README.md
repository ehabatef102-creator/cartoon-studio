# Cartoon Studio — استوديو كرتون بالذكاء الاصطناعي

اكتب فكرة، يحوّلها إلى حلقة كرتون كاملة: سيناريو + صور مشاهد + تعليق صوتي عربي + فيديو mp4.

## المميزات
- **توليد من فكرة حرة**: اكتب أي فكرة → سيناريو 7 مشاهد + صور + صوت + فيديو.
- **سلاسل جاهزة**: 3 عوالم أصلية (أفق السحاب، صدى الواحة، المحطة الأخيرة).
- **سيناريو مخصص 100%** عند وضع `GROQ_API_KEY` (مجاني) في بيئة التشغيل.
- **صور** عبر Pollinations (مجاني) أو Stability عند وضع المفتاح.
- **صوت عربي** عبر edge-tts (مجاني) أو ElevenLabs عند وضع المفتاح.
- **فيديو سينمائي**: زووم متناوب + تدرج ألوان + بطاقات عنوان عربية + مشهد بعد الشارة.

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

### Render (مجاني)
`render.yaml` موجود ويستخدم Python runtime الأصلي (يدعم الخطة المجانية):
- New → Blueprint → اختر الريبو → Connect
- عيّن `ADMIN_PASSWORD` في Environment بعد أول نشر

### متغيرات البيئة الاختيارية
| المتغير | الفائدة |
|---|---|
| `GROQ_API_KEY` | سيناريو مخصص 100% من الفكرة (مجاني من console.groq.com) |
| `STABILITY_API_KEY` | صور أدق |
| `ELEVENLABS_API_KEY` | أصوات عاطفية |
| `ADMIN_PASSWORD` | كلمة مرور لوحة التحكم |

## البنية
```
server/app.py          FastAPI + API الجوبات
server/pipeline.py     التوليد: صور → صوت → فيديو
creative_engine.py     باك الإنتاج (سيناريو/بريفات/مواد)
packs.py               السلاسل الجاهزة
universe.py            عالم مشترك
```
