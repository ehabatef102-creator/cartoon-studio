"""محرك الحركة السينمائي: كاميرا ناعمة (easing + handheld + استمرارية اتجاه) + خطاف تحريك حقيقي.

- zoompan بـ smoothstep (بدل الزوم الخطي) فتتحرك الكاميرا بشكل سينمائي مهني.
- اهتزاز يدوي خفيف (handheld) يتناسب مع التوتر ويخف تدريجيًا (استقرار).
- استمرارية اتجاه الحركة بين اللقطات المتتالية = إحساس كاميرا واحدة تتحرك عبر المشاهد.
- خطاف اختياري لتحريك حقيقي للشخصيات عبر Replicate (Kling/Veo/wan) عند ضبط
  MOTION_PROVIDER + REPLICATE_API_TOKEN. الافتراضي هو المحرك المحلي المجاني.
"""

import math
import os
import subprocess
import sys
import time

FPS = 24
OUT_W, OUT_H = 1280, 720
SOURCE_W, SOURCE_H = 1920, 1080

# ---------------------------------------------------------------------------
# أنيميشن "ب": تمايل عضوي بالشرائح (2.5D sway) — شخصية حية بلا GPU.
# كل شريحة رأسية تتحرك بأطوار متدرجة فتبدو الشخصية تتنفس/تتأرجح/تطير.
# ---------------------------------------------------------------------------

# كلمات الحركة → (سعة التموج px، تردد الموجة، ميل الطيران، نبض عمودي px)
_ACTION_MODES = {
    "fly":       (26, 1.1, 0.10, 16),
    "swoop":     (38, 1.5, 0.16, 26),
    "dive":      (34, 1.7, 0.20, 30),
    "run":       (20, 2.8, 0.04, 10),
    "leap":      (24, 2.2, 0.10, 22),
    "jump":      (24, 2.2, 0.10, 22),
    "climb":     (12, 1.0, 0.02, 5),
    "wave":      (16, 1.6, 0.03, 8),
    "turn":      (8,  0.9, 0.24, 3),
    "fight":     (28, 2.4, 0.12, 16),
    "shake":     (30, 3.2, 0.06, 18),
    "breathe":   (5,  0.5, 0.0,  0),
}

_ACTION_WORDS = {
    "fly": ("يطير", "طيران", "تحليق", "يحلق", "في الهواء", "أجنحة", "flying", "flies", "flight", "soar"),
    "swoop": ("ينقض", "انقضاض", "يهاجم من الجو", "swoop", "diving attack"),
    "dive": ("يغطس", "غوص", "ينزل بسرعة", "dive", "plummet"),
    "run": ("يجري", "جري", "ركض", "يهرب", "مطارد", "run", "running", "chase", "flee"),
    "leap": ("يقفز", "وثبة", "ينط", "leap", "leaping", "bound"),
    "climb": ("يتسلق", "تسلق", "climb", "climbing"),
    "wave": ("يلوح", "تلويح", "تحية", "wave", "waving"),
    "turn": ("يستدير", "التفات", "يلتفت", "turn", "turning", "twist"),
    "fight": ("يقاتل", "ضربات", "لكم", "قتال", "معركة", "fight", "fighting", "punch", "kick"),
    "shake": ("يهتز", "اهتزاز", "يرتجف", "زلزال", "shake", "shaking", "tremble", "quake"),
}


def action_mode(scene):
    """يحدد نوع حركة الشخصية من وصف المشهد (action/title/mood) أو beat."""
    text = " ".join([
        str(scene.get("action") or ""),
        str(scene.get("title") or ""),
        str(scene.get("mood") or ""),
    ]).lower()
    for mode, words in _ACTION_WORDS.items():
        if any(w in text for w in words):
            return mode
    beat = (scene.get("beat") or "setup").lower()
    if beat in ("climax", "rising2"):
        return "shake"
    if beat == "rising1":
        return "breathe"
    return "breathe"


def plan_action(scene, prev_plan=None):
    """خطة أنيميشن الشخصية: تموج بالشرائح + ميل طيران + نبض عمودي."""
    mode = action_mode(scene)
    amp, freq, tilt, bounce = _ACTION_MODES[mode]
    try:
        tension = int(scene.get("tension", 5))
    except (TypeError, ValueError):
        tension = 5
    amp = amp * (0.7 + tension * 0.06)
    motion = plan_motion(scene, prev_plan=prev_plan)
    return {
        "mode": mode,
        "amp": round(amp, 1),
        "freq": freq,
        "tilt": tilt,
        "bounce": bounce,
        "segments": int(os.environ.get("MOTION_SEGMENTS", "6")),
        "camera": motion,
    }


def _shot_of(scene):
    shot = (scene.get("shot") or [{}])
    return shot[0] if isinstance(shot, list) and shot else (shot if isinstance(shot, dict) else {})


def _movement_dir(movement):
    """اتجاه الحركة الجانبية من وصف الحركة: -1 يسار، +1 يمين، 0 محايد."""
    m = (movement or "").lower()
    if "pan left" in m or "move left" in m or "tracking left" in m or "slide left" in m:
        return -1
    if "pan right" in m or "move right" in m or "tracking right" in m or "slide right" in m:
        return 1
    if "orbit" in m:
        return -1
    return 0


def plan_motion(scene, prev_plan=None):
    """يُخطط حركة الكاميرا للمشهد: نطاق زوم، اتجاه انجراف، اهتزاز، واستمرارية مع اللقطة السابقة."""
    beat = (scene.get("beat") or "setup").lower()
    try:
        tension = int(scene.get("tension", 5))
    except (TypeError, ValueError):
        tension = 5
    shot = _shot_of(scene)
    movement = shot.get("movement") or "" if isinstance(shot, dict) else ""
    direction = _movement_dir(movement)
    if direction == 0 and prev_plan and prev_plan.get("direction"):
        # استمرارية: لا اتجاه محدد هنا → نكمل اتجاه الكاميرا السابقة (إحساس لقطة واحدة متصلة)
        direction = prev_plan["direction"]

    zoom_in = beat not in ("falling", "resolution")
    if "zoom-out" in movement or "zoom out" in movement:
        zoom_in = False

    # نطاق الزوم: أعلى مع التوتر، محدود للحفاظ على جودة الصورة
    if zoom_in:
        z_start, z_end = 1.02, min(1.14, 1.05 + tension * 0.012)
    else:
        z_start, z_end = min(1.14, 1.05 + tension * 0.012), 1.02

    # انجراف جانبي حسب الاتجاه (استمرارية) أو حركة طفيفة محايدة
    drift = 34 if direction else 14
    drift_x = drift * (direction if direction else 1)

    # اهتزاز يدوي: صفر في الهدوء، أعلى في الذروة، ينخفض تدريجيًا (استقرار الكاميرا)
    handheld = 0.0 if beat in ("setup", "resolution") else (2.5 + tension * 0.55)
    hand_freq = 0.6 if tension >= 7 else 0.4

    return {
        "zoom_in": zoom_in,
        "z_start": round(z_start, 4),
        "z_end": round(z_end, 4),
        "drift_x": round(drift_x, 2),
        "drift_y": 10.0,
        "direction": direction,
        "handheld": round(handheld, 2),
        "hand_freq": hand_freq,
    }


def _smooth(t):
    """smoothstep: تدرج ناعم (0 عند 0، 1 عند 1) بلا اهتزاز في البداية والنهاية."""
    return f"({t}*{t}*(3-2*{t}))"


def _zoom_expr(plan):
    """معادلة zoompan: زوم smoothstep مطلق لكل إطار + انجراف + اهتزاز يدوي خفيف."""
    d = f"min(1,(on-1)/{max(1, int(plan.get('frames', 1)) - 1)})" if plan.get("frames", 1) > 1 else "1"
    ease = _smooth(d)
    zs, ze = plan["z_start"], plan["z_end"]
    z = f"{zs}+({ze}-{zs})*{ease}"
    dx = plan["drift_x"]
    dy = plan["drift_y"]
    hs = plan["handheld"]
    hf = plan["hand_freq"]
    # x: توسيط + انجراف باتجاه الحركة + اهتزاز (يتلاشى مع استقرار الكاميرا عبر ease)
    x = f"(iw/2-(iw/zoom/2))+{dx}*{ease}+sin(on*{hf})*{hs}*{ease}"
    y = f"(ih/2-(ih/zoom/2))+{dy}*sin(on*{hf}*0.6)*{hs}*{ease}"
    return z, x, y


def render_scene_clip(ffmpeg, image, audio, out_mp4, seconds, plan):
    """يُنتج مقطع فيديو من صورة ثابتة بحركة كاميرا ناعمة (easing + handheld + انجراف) + الصوت."""
    frames = max(2, int(seconds * FPS))
    plan = dict(plan)
    plan["frames"] = frames
    z, x, y = _zoom_expr(plan)
    filter_complex = (
        f"[0:v]scale={SOURCE_W}:{SOURCE_H}:force_original_aspect_ratio=increase,"
        f"crop={SOURCE_W}:{SOURCE_H},"
        f"zoompan=z='{z}':d={frames}:x='{x}':y='{y}':s={OUT_W}x{OUT_H}:fps={FPS}[v]"
    )
    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(image)]
    if audio and os.path.exists(str(audio)):
        cmd += ["-i", str(audio)]
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    else:
        cmd += ["-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=24000:cl=mono"]
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    cmd += ["-t", str(seconds), "-shortest", str(out_mp4)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        raise RuntimeError(f"فشل رندر المقطع: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return out_mp4


def _sway_expr(seg, seg_count, plan, pad_x, pad_y):
    """معادلة نافذة الشريحة: إزاحة أفقية جيبية بطور متدرج لكل شريحة + نبض عمودي.

    كل شريحة ترى نافذة من الصورة تنزلق يسارًا/يمينًا على إيقاع الموجة بأطوار
    متتالية — فتظهر الشخصية وكأنها تتمايل/تتنفس/تطير. pad_x/pad_y هامش الصورة
    المضاف (أصلاً = السعة) كي تظل الإزاحة ضمن حدود الصورة دون حواف سوداء.
    """
    t = "t"
    amp = float(plan.get("amp", 14))
    freq = float(plan.get("freq", 1.2))
    bounce = float(plan.get("bounce", 0))
    shift = float(plan.get("phase", 0))
    phase = f"{2 * math.pi * seg / max(1, seg_count) + shift}"
    base_x = f"({pad_x} + {seg}*{SOURCE_W}/{seg_count})"
    sway = f"({amp}*sin(2*{math.pi}*{freq}*{t}+{phase}))"
    x = f"({base_x}+{sway})"
    y = f"({pad_y}+{bounce}*sin(2*{math.pi}*{freq}*{t}+{phase}+{math.pi}/2))"
    return x, y


def render_action_clip(ffmpeg, image, audio, out_mp4, seconds, plan):
    """أنيميشن شخصية حي (2.5D sway): تقسيم الصورة لشرائح تنزلق بتموج متدرج.

    - pad يضيف هامشًا = سعة التموج كي لا تظهر حواف سوداء عند انزلاق الشرائح.
    - الشرائح تتحرك بأطوار متتالية → تمايل عضوي (تنفس/طيران/ارتعاش) حقيقي.
    - ميل طيران (rotate) اختياري للمشاهد الهوائية.
    - يقع على محرك الكاميرا (zoompan) فيُجمع أنيميشن + كاميرا معًا.
    """
    frames = max(2, int(seconds * FPS))
    seg_count = max(3, min(8, int(plan.get("segments", 6))))
    amp = max(6, float(plan.get("amp", 14)))
    bounce = max(0, float(plan.get("bounce", 0)))
    tilt = float(plan.get("tilt", 0))
    cam = dict(plan.get("camera") or {})
    cam["frames"] = frames
    z, cx, cy = _zoom_expr(cam)

    pad_x = int(amp)
    pad_y = int(bounce)
    seg_w = SOURCE_W // seg_count
    pad_w = SOURCE_W + 2 * pad_x
    pad_h = SOURCE_H + 2 * pad_y
    base = (
        f"[0:v]scale={SOURCE_W}:{SOURCE_H}:force_original_aspect_ratio=increase,"
        f"crop={SOURCE_W}:{SOURCE_H},"
        f"pad={pad_w}:{pad_h}:{pad_x}:{pad_y}:black[p0]"
    )
    labels = "".join(f"[b{s}]" for s in range(seg_count))
    inputs = [base, f"[p0]split={seg_count}{labels}"]
    seg_parts = []
    for s in range(seg_count):
        x_expr, y_expr = _sway_expr(s, seg_count, plan, pad_x, pad_y)
        seg_parts.append(
            f"[b{s}]crop={seg_w}:{pad_h}:x='{x_expr}':y='{y_expr}'"
            f",scale={OUT_W // seg_count}:{OUT_H}[s{s}]"
        )
    row_labels = "".join(f"[s{s}]" for s in range(seg_count))
    join = f"{row_labels}hstack=inputs={seg_count}[row]"
    if tilt:
        rotate = f"[row]rotate={tilt:.4f}:fillcolor=black,"
    else:
        rotate = f"[row]"
    camera = (
        f"{rotate}zoompan=z='{z}':d={frames}:x='{cx}':y='{cy}':s={OUT_W}x{OUT_H}:fps={FPS}[v]"
    )
    filter_complex = ";".join(inputs + seg_parts + [join, camera])

    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(image)]
    if audio and os.path.exists(str(audio)):
        cmd += ["-i", str(audio)]
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    else:
        cmd += ["-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=24000:cl=mono"]
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    cmd += ["-t", str(seconds), "-shortest", str(out_mp4)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    if proc.returncode != 0:
        raise RuntimeError(f"فشل رندر الأنيميشن: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return out_mp4


def merge_pose_clips(ffmpeg, clip_a, clip_b, out_mp4, seconds):
    """يدمج مقطعي pose متتاليين بـ crossfade في منتصف المدة (pose-to-pose).

    الصوت (الحوار والمؤثرات) من المقطع الأول فقط — لأن pose الثانية مجرد
    تغيير وضعية لا حوار له. overlap 0.7 ثانية كي يبدو الانتقال حركة كرتونية
    سريعة لا "قطع" مفاجئ.
    """
    total = max(2.0, float(seconds))
    overlap = min(0.7, total / 4)
    offset = max(0.0, total / 2 - overlap / 2)
    fc = f"[0:v][1:v]xfade=transition=fade:duration={overlap}:offset={offset}[v]"
    cmd = [ffmpeg, "-y", "-i", str(clip_a), "-i", str(clip_b),
           "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
           "-c:a", "aac", "-c:v", "libx264", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-t", f"{total}", "-shortest", str(out_mp4)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    if proc.returncode != 0:
        raise RuntimeError(f"فشل دمج الـ poses: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return out_mp4


# ---------------------------------------------------------------------------
# خطاف التحريك الحقيقي للشخصيات (Replicate: Kling / Veo / wan).
# ---------------------------------------------------------------------------

_MOTION_MODELS = {
    "kling": "kwaivgi/kling-v1.6-pro",
    "kling-1.6": "kwaivgi/kling-v1.6-pro",
    "kling-1.5": "kwaivgi/kling-v1.5-pro",
    "veo": "google-deepmind/veo-3",
    "veo3": "google-deepmind/veo-3",
    "wan": "lucataco/wan-2.1-i2v",
    "wan-2.1": "lucataco/wan-2.1-i2v",
}


def _replicate_animate(image, prompt, seconds, out_video, token, model):
    import httpx

    api = "https://api.replicate.com/v1/models/{model}/predictions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": "wait=1",
        "Content-Type": "application/json",
    }
    duration = max(4, min(int(seconds), 10))
    inp = {"image": str(image.resolve()), "prompt": prompt, "duration": duration}
    with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
        resp = client.post(api.format(model=model), json={"input": inp}, headers=headers)
        resp.raise_for_status()
        pred = resp.json()
        pred_id = pred["id"]
        status = pred.get("status")
        deadline = time.time() + 300
        while status not in ("succeeded", "failed", "canceled") and time.time() < deadline:
            time.sleep(4)
            p = client.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
            p.raise_for_status()
            pred = p.json()
            status = pred.get("status")
        if status != "succeeded":
            err = pred.get("error") or f"لم يكتمل التحريك ({status})"
            raise RuntimeError(str(err))
        out_url = pred.get("output")
        if isinstance(out_url, list):
            out_url = out_url[0] if out_url else None
        if isinstance(out_url, dict):
            out_url = out_url.get("url")
        if not out_url:
            raise RuntimeError("لا يوجد مخرج فيديو من المزوّد")
        clip = out_video.with_name(out_video.stem + "_anim.mp4")
        d = client.get(out_url, timeout=httpx.Timeout(240.0))
        d.raise_for_status()
        clip.write_bytes(d.content)
    return clip


def _mux_audio(ffmpeg, video, audio, out_path):
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", str(video), "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-shortest", str(out_path)],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"فشل دمج الصوت مع الفيديو المتحرك:\n{proc.stderr[-1500:]}")
    return out_path


def try_external_motion(image, out_video, prompt, seconds, audio=None):
    """تحريك حقيقي للشخصيات عبر مزوّد خارجي (Replicate Kling/Veo/wan).

    يتطلب MOTION_PROVIDER + REPLICATE_API_TOKEN. عند الفشل يعيد None
    فيستخدم المحرك المحلي (Ken Burns ناعم) تلقائيًا — لا تكسر الحلقة أبدًا.
    """
    provider = os.environ.get("MOTION_PROVIDER", "").strip().lower()
    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not provider or not token:
        return None
    model = _MOTION_MODELS.get(provider) or os.environ.get("MOTION_MODEL", "")
    if not model:
        return None
    try:
        clip = _replicate_animate(image, prompt, seconds, out_video, token, model)
        if audio and os.path.exists(str(audio)):
            muxed = out_video.with_name(out_video.stem + "_muxed.mp4")
            _mux_audio(ffmpeg_finder(), clip, audio, muxed)
            return muxed
        return clip
    except Exception as exc:
        try:
            print(f"[motion] تحريك خارجي فشل، استخدام المحرك المحلي: {exc!r}", file=sys.stderr)
        except Exception:
            pass
        return None


def ffmpeg_finder():
    exe = os.environ.get("FFMPEG")
    if exe and os.path.exists(exe):
        return exe
    import shutil

    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("ffmpeg غير متوفر")
