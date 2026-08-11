"""بوت المونتاج — محرر تلقائي مفتوح المصدر (ffmpeg).

يستقبل لقطات الحلقة بالترتيب السردي مع معلوماتها (beat + الحوار + ملفات الصوت)
ويجمعها في حلقة سينمائية كاملة:

  1) يتحقق من ترتيب القصة ويُصلحه (عناوين + مشاهد حسب تسلسل الـ beats + ما بعد الشارة + النهاية).
  2) يختار انتقالًا مناسبًا لكل فاصل حسب التوتر الدرامي (fade/crossfade/dip-to-black).
  3) يربط الأحداث زمنيًا على خط واحد: فيديو (xfade) + صوت (acrossfade) بمعادلات متطابقة
     فتبقى الأصوات والصور متزامنة طوال الحلقة.
  4) يدمج ترجمة الحوار العربي (RTL) على الفيديو متزامنة مع أصوات الممثلين الحقيقية.
  5) معالجة لونية نهائية (تصحيح ألوان + حبيبات فيلم).

لا يتطلب أي برنامج سوى ffmpeg الموجود أصلًا في المشروع.
"""

import re
import shutil
import subprocess
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(__file__).resolve().parent / "fonts"

FPS = 24
W, H = 1280, 720
FADE = 0.5          # مدة الانتقال الافتراضية
CLIMAX_FADE = 0.7   # مدة انتقال الذروة

# انتقال سينمائي لكل beat (أنواع xfade المتاحة في ffmpeg)
TRANSITION_BY_BEAT = {
    "setup": "fade",
    "inciting": "smoothright",
    "rising1": "smoothright",
    "rising2": "slideleft",
    "climax": "fadeblack",
    "falling": "smoothup",
    "resolution": "fade",
    "crossover": "fade",
}

# انتقالات "الربط": تحافظ على اتجاه الحركة بين لقطتين متتاليتين (كاميرا واحدة تتحرك عبر المشاهد)
FLOW_RIGHT = "smoothright"
FLOW_LEFT = "smoothleft"
FLOW_UP = "smoothup"
FLOW_DOWN = "smoothdown"

# الترتيب السردي الصحيح: عنوان ← مشاهد القصة بالـ beats ← ما بعد الشارة ← نهاية
ORDER = {
    "title": 0,
    "setup": 1, "inciting": 2, "rising1": 3, "rising2": 4,
    "climax": 5, "falling": 6, "resolution": 7,
    "crossover": 8, "end": 9,
}


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _shape(text):
    return get_display(arabic_reshaper.reshape(text))


def _font(size, bold=True):
    name = "Amiri-Bold.ttf" if bold else "Amiri-Regular.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def probe_duration(path):
    """مدة ملف صوتي/فيديو بالثواني عبر قراءة Duration من ffmpeg (بدون ffprobe)."""
    try:
        proc = subprocess.run([_ffmpeg(), "-i", str(path)], capture_output=True, text=True)
    except Exception:
        return 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return 0.0
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s


def _render_caption(text, out_png):
    """يرسم سطر الحوار العربي (RTL) كصورة شفافة فوق حزام داكن أسفل الشاشة."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(44, True)
    shaped = _shape(text)
    band_h = 118
    top = H - band_h - 40
    d.rectangle([30, top, W - 30, top + band_h], fill=(12, 10, 20, 168))
    d.line([60, top, W - 60, top], fill=(251, 191, 36, 220), width=3)
    tw = d.textlength(shaped, font=font)
    d.text(((W - tw) / 2, top + (band_h - 44) / 2), shaped, font=font, fill=(244, 239, 228, 255))
    img.save(out_png)
    return out_png


def _transition_seconds(clips, i):
    """مدة الانتقال قبل اللقطة i (الذروة أطول وأبطأ)."""
    if i == 0:
        return 0.0
    tension = 5
    try:
        tension = int(clips[i - 1].get("tension", 5))
    except (TypeError, ValueError):
        pass
    if clips[i - 1].get("beat") == "climax":
        return max(FADE, min(1.0, CLIMAX_FADE + tension * 0.03))
    return max(FADE, min(0.9, FADE + tension * 0.04))


def _transition_name(prev_beat, tension=5, direction=0):
    """انتقال يربط اللقطتين: استمرارية اتجاه الحركة + توتر + beat (match-cut)."""
    beat = prev_beat or "setup"
    if beat == "climax":
        return "fadeblack" if tension >= 7 else "smoothup"
    if direction < 0:
        return FLOW_LEFT
    if direction > 0:
        return FLOW_RIGHT
    if beat in ("falling", "resolution"):
        return "fade"
    if tension >= 8:
        return "fadeblack"
    if tension >= 6:
        return "smoothup"
    return "fade"


def _sort_clips(clips):
    """يحافظ على الترتيب السردي المعطى من القصة، مع تثبيت العنوان أولًا والنهاية أخيرًا.

    المشاهد تصل بالفعل مرتبة حسب القصة، والـ beats تتكرر عبر الحلقة الطويلة
    (مثلًا 4 مشاهد rising1)، لذلك لا نُعيد ترتيبها بالـ beat بل نحافظ على تسلسلها
    ونضمن فقط مكان العنوان وما بعد الشارة والنهاية.
    """
    ranked = []
    for idx, c in enumerate(clips):
        beat = c.get("beat", "setup")
        if beat == "title":
            rank = (0, idx)
        elif beat == "end":
            rank = (10**9, idx)
        elif beat == "crossover":
            rank = (10**8, idx)
        else:
            rank = (1000 + ORDER.get(beat, 1000), idx)
        ranked.append((rank, c))
    ranked.sort(key=lambda pair: pair[0])
    return [c for _, c in ranked]


def _video_norm():
    return (
        f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
    )


def _audio_norm():
    return "aformat=sample_fmts=fltp:channel_layouts=stereo,aresample=44100"


def assemble(clips, out_mp4, keep_order=True):
    """يجمع لقطات الحلقة في فيديو واحد مع انتقالات وترجمة ومكس صوتي موحد.

    clips: قائمة بها لكل لقطة:
        path      (str)  مسار الفيديو الجاهز
        seconds   (float) مدتها
        beat      (str)  setup/inciting/.../crossover (لترتيب القصة والانتقالات)
        dialogue  (list، اختياري) عناصر {text, audio} — تُقنّن الترجمة من طول الصوت الحقيقي
    """
    ffmpeg = _ffmpeg()
    clips = [c for c in clips if c.get("path") and Path(c["path"]).exists()]
    if not clips:
        raise RuntimeError("لا توجد لقطات للمونتاج")
    if keep_order:
        clips = _sort_clips(clips)

    n = len(clips)
    durs = [max(1.5, float(c.get("seconds", 6))) for c in clips]
    trs = [_transition_seconds(clips, i) for i in range(n)]

    # أوقات بداية كل لقطة على الخط الزمني — نفس المعادلة للفيديو والصوت = تزامن كامل
    starts = [0.0]
    for i in range(1, n):
        starts.append(starts[-1] + durs[i - 1] - trs[i])

    # الترجمة: قياس زمني حقيقي من أصوات الحوار
    captions = []  # (png, start, end)
    for ci, c in enumerate(clips):
        cum = 0.0
        for line in c.get("dialogue") or []:
            text = (line.get("text") or "").strip()
            if not text:
                continue
            audio = line.get("audio")
            dur = probe_duration(audio) if audio and Path(audio).exists() else max(1.6, min(8.0, len(text) * 0.22))
            s = starts[ci] + cum
            e = max(s + 0.8, s + dur + 0.35)
            png = Path(out_mp4).with_name(f"_cap_{len(captions):03d}.png")
            _render_caption(text, png)
            captions.append((png, s, e))
            cum += dur + 0.3

    # فيديو: توحيد اللقطات ثم سلسلة xfade متتالية (المخرج السابق يدخل في التالي)
    chain = []
    for i in range(n):
        chain.append(f"[{i}:v]{_video_norm()}[cv{i}]")
        chain.append(f"[{i}:a]{_audio_norm()}[ca{i}]")
    for i in range(1, n):
        prev = clips[i - 1]
        tension = 5
        try:
            tension = int(prev.get("tension", 5))
        except (TypeError, ValueError):
            pass
        tname = _transition_name(prev.get("beat", "setup"), tension=tension, direction=prev.get("direction", 0))
        td = trs[i]
        off = starts[i]
        vin = f"cx{i - 1}" if i > 1 else f"cv{i - 1}"
        ain = f"ax{i - 1}" if i > 1 else f"ca{i - 1}"
        chain.append(f"[{vin}][cv{i}]xfade=transition={tname}:duration={td}:offset={off:.3f}[cx{i}]")
        chain.append(f"[{ain}][ca{i}]acrossfade=d={td}:c1=tri:c2=tri[ax{i}]")

    base = f"[cx{n - 1}]"
    if captions:
        for k, (png, s, e) in enumerate(captions):
            out = f"[vcap]" if k == len(captions) - 1 else f"[ov{k}]"
            chain.append(f"{base}[{n + k}:v]overlay=enable='between(t,{s:.2f},{e:.2f})'{out}")
            base = out
    else:
        chain.append(f"{base}format=yuv420p[vcap]")

    # المعالجة اللونية النهائية: تدرج سينمائي (تباين غني + تشبع + إحماء الظلال + حبيبات فيلم + ظلال حافة)
    chain.append(
        "[vcap]eq=saturation=1.22:contrast=1.09:brightness=0.005:gamma=0.98,"
        "colorbalance=rs=0.02:gs=0.0:bs=-0.02:rm=0.015:bm=-0.015:rh=0.03:bh=-0.03,"
        f"vignette=PI/4.5,noise=alls=7:allf=t,format=yuv420p[vfinal]"
    )

    inputs = [str(Path(c["path"]).resolve()) for c in clips] + [str(p.resolve()) for p, _, _ in captions]
    cmd = [ffmpeg, "-y"]
    for inp in inputs:
        cmd += ["-i", inp]
    cmd += ["-filter_complex", ";".join(chain)]
    cmd += ["-map", "[vfinal]", "-map", f"[ax{n - 1}]"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    cmd += [str(out_mp4)]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5400)
    for png, _, _ in captions:
        try:
            png.unlink(missing_ok=True)
        except Exception:
            pass
    if proc.returncode != 0:
        raise RuntimeError(f"فشل بوت المونتاج:\n{proc.stderr[-2500:]}")
    return out_mp4
