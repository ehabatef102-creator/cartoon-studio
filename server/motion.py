"""محرك الحركة السينمائي: حركة كاميرا ذكية حسب نوع اللقطة (Ken Burns مطوّر).
يوجد خطاف لمزوّد فيديو خارجي اختياري (MOTION_PROVIDER) لكن الافتراضي هو محرك محلي مجاني."""

import os
import subprocess

FPS = 24
OUT_W, OUT_H = 1280, 720
SOURCE_W, SOURCE_H = 1920, 1080


def plan_motion(scene):
    """يُخطط حركة الكاميرا للمشهد من الستوريبورد: اتجاه الزوم، سرعته، وانجراف جانبي."""
    beat = scene.get("beat", "setup")
    try:
        tension = int(scene.get("tension", 5))
    except (TypeError, ValueError):
        tension = 5
    shot = (scene.get("shot") or [{}])[0]
    movement = (shot.get("movement") or "") if isinstance(shot, dict) else ""
    zoom_in = "zoom-out" not in movement and "zoom out" not in movement
    if beat in ("falling", "resolution"):
        zoom_in = False
    step = round(0.0004 + tension * 0.00007, 6)
    drift_x = 26 if "pan" in movement else 12
    drift_y = 20 if ("tilt" in movement or " up" in movement or " down" in movement) else 8
    osc = 1.6 if tension >= 7 else 0.7
    return {
        "zoom_in": zoom_in,
        "step": step,
        "drift_x": drift_x,
        "drift_y": drift_y,
        "osc": osc,
    }


def _zoom_expr(plan):
    z = f"min(zoom+{plan['step']},1.16)" if plan["zoom_in"] else f"if(lte(zoom,1.0),1.16,max(1.001,zoom-{plan['step']}))"
    osc = float(plan.get("osc", 1.0))
    dx = float(plan.get("drift_x", 0)) * osc
    dy = float(plan.get("drift_y", 0)) * osc
    x = f"iw/2-(iw/zoom/2)+sin(on/{FPS}*0.55)*{dx}"
    y = f"ih/2-(ih/zoom/2)+cos(on/{FPS}*0.7)*{dy}"
    return z, x, y


def render_scene_clip(ffmpeg, image, audio, out_mp4, seconds, plan):
    """يُنتج مقطع فيديو من صورة ثابتة بحركة كاميرا مدروسة + الصوت."""
    z, x, y = _zoom_expr(plan)
    filter_complex = (
        f"[0:v]scale={SOURCE_W}:{SOURCE_H}:force_original_aspect_ratio=increase,"
        f"crop={SOURCE_W}:{SOURCE_H},"
        f"zoompan=z='{z}':d={int(seconds * FPS)}:x='{x}':y='{y}':s={OUT_W}x{OUT_H}:fps={FPS}[v]"
    )
    cmd = [ffmpeg, "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(image)]
    if audio and os.path.exists(audio):
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


def try_external_motion(image, out_video, prompt, seconds):
    """خطاف للمزوّدات الخارجية (Kling/Veo/Replicate...). يُعيد مسار الفيديو أو None إن لم يُضبط.
    يتطلب MOTION_PROVIDER + MOTION_API_KEY. الافتراضي هو المحرك المحلي المجاني."""
    provider = os.environ.get("MOTION_PROVIDER", "").strip()
    api_key = os.environ.get("MOTION_API_KEY", "").strip()
    if not provider or not api_key:
        return None
    raise RuntimeError(
        f"مزوّد الحركة الخارجي '{provider}' لم يُربط بعد (تحريك الفيديو الحقيقي يتطلب حسابًا مدفوعًا). "
        "المحرك المحلي السينمائي يعمل افتراضيًا."
    )
