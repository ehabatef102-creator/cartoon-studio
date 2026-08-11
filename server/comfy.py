"""مزوّد الصور الاحترافي عبر ComfyUI (SDXL + ControlNet OpenPose + IP-Adapter).

كل شيء يعمل بلا مجهود يدوي:
- توليد "شيت شخصية" (صورة مرجعية ثابتة الملامح) لكل شخصية تلقائيًا قبل المشاهد.
- توليد هيكل OpenPose (عصا الحركة) لكل لقطة من beat المشهد برمجيًا (Pillow).
- ثم كل مشهد يُنشأ عبر: SDXL + ControlNet (OpenPose) + IP-Adapter (مرجع الشخصية)
  لضمان ثبات الملامح والملابس في كل اللقطات.

الإعداد (متغيرات البيئة):
  IMAGE_PROVIDER=comfy            # تفعيل هذا المسار (يظل Pollinations احتياطيًا تلقائيًا)
  COMFY_URL=http://127.0.0.1:8188 # أو رابط cloudflared/ngrok من النوتبوك المجاني
  COMFY_CKPT=                     # اسم checkpoint (اختياري: يُكتشف تلقائيًا)
  COMFY_NEGATIVE=                 # برومبت سلبي إضافي (اختياري)
  COMFY_STEPS=32                  # عدد خطوات KSampler (جودة أعلى = أبطأ)

متطلبات خادم ComfyUI: SDXL checkpoint + ControlNet openpose + IPAdapter_plus
(النوتبوك notebooks/ComfyUI_Cloud.ipynb يثبّتها مجانًا على Colab/Kaggle).
"""
import asyncio
import io
import json
import math
import os
import sys
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

COMFY_URL = os.environ.get("COMFY_URL", "").strip().rstrip("/")
COMFY_CKPT = os.environ.get("COMFY_CKPT", "").strip()
COMFY_STEPS = int(os.environ.get("COMFY_STEPS", "32"))
COMFY_NEGATIVE = os.environ.get(
    "COMFY_NEGATIVE",
    "lowres, blurry, extra limbs, extra fingers, deformed, bad anatomy, watermark, text, logo, jpeg artifacts, oversaturated",
).strip()

IMG_W, IMG_H = 1920, 1080

_AUX = None  # كاش لأسماء ControlNet/checkpoints من /object_info


def _ws_url():
    return COMFY_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws"


async def _get(client, path):
    resp = await client.get(COMFY_URL + path, timeout=httpx.Timeout(60.0))
    resp.raise_for_status()
    return resp.json()


async def _object_info(client):
    global _AUX
    if _AUX is None:
        _AUX = await _get(client, "/object_info")
    return _AUX


def _names(info, node, field):
    try:
        spec = info[node]["input"]["required"][field][0]
        return list(spec.get("options", []))
    except Exception:
        return []


def pick_ckpt(available):
    if not available:
        return "SDXL"
    for name in available:
        low = name.lower()
        if any(k in low for k in ("toon", "cartoon", "comic", "cel", "animate", "animation")):
            return name
    return available[0]


def pick_controlnet(available):
    for name in available:
        low = name.lower()
        if "openpose" in low or "dwpose" in low or "open-pose" in low:
            return name
    return available[0] if available else "control_openpose-sdxl-1.0"


# ---------------- توليد هيكل OpenPose برمجيًا (Pillow) ----------------

_POSE_TEMPLATES = {
    "idle": {
        "head": (0.30, 0.16), "neck": (0.30, 0.30), "shoulder": (0.30, 0.38),
        "elbow": (0.42, 0.46), "hand": (0.55, 0.46), "hip": (0.42, 0.62),
        "knee": (0.52, 0.78), "ankle": (0.60, 0.95),
    },
    "run": {
        "head": (0.30, 0.16), "neck": (0.30, 0.30), "shoulder": (0.30, 0.38),
        "elbow": (0.38, 0.44), "hand": (0.34, 0.50), "hip": (0.42, 0.62),
        "knee": (0.62, 0.72), "ankle": (0.72, 0.92),
    },
    "action": {
        "head": (0.30, 0.15), "neck": (0.30, 0.30), "shoulder": (0.30, 0.38),
        "elbow": (0.22, 0.42), "hand": (0.14, 0.34), "hip": (0.42, 0.62),
        "knee": (0.50, 0.80), "ankle": (0.58, 0.96),
    },
    "wide": {
        "head": (0.40, 0.18), "neck": (0.40, 0.32), "shoulder": (0.40, 0.40),
        "elbow": (0.52, 0.46), "hand": (0.60, 0.46), "hip": (0.50, 0.64),
        "knee": (0.58, 0.80), "ankle": (0.66, 0.95),
    },
}

_BEAT_POSE = {
    "setup": "idle", "inciting": "idle", "rising1": "run", "rising2": "action",
    "climax": "action", "falling": "run", "resolution": "idle", "crossover": "wide",
}


def pose_template_for(beat):
    return _POSE_TEMPLATES.get(_BEAT_POSE.get((beat or "setup").lower(), "idle"), _POSE_TEMPLATES["idle"])


def build_pose_sequence(beat=None, frames=16, cycle=1.0):
    """يُنتج قائمة مواقع (dicts) لهيكل OpenPose تتحرك بسلاسة بين قوامين.

    يحاكي حلقة مشي/جري (walk cycle) أو حركة قتال حسب الـ beat، فيُحرَّك
    الرأس والذراعان والساقان بموجات جيبية متقابلة — تفاصيل OpenPose حقيقية
    لقيادة ControlNet خلال إطارات AnimateDiff.
    """
    base = pose_template_for(beat)
    keys = ["head", "neck", "shoulder", "elbow", "hand", "hip", "knee", "ankle"]
    frames_out = []
    for f in range(frames):
        t = (f / max(1, frames - 1)) * math.tau
        ph = t * cycle
        step = math.sin(ph)
        bob = math.sin(ph * 2) * 0.015          # قفز خفيف للجذع
        swing = math.sin(ph) * 0.09             # تأرجح الذراعين
        bounce = math.sin(ph) * 0.10            # رفع الساقين بالتناوب
        pts = {k: (v[0], v[1]) for k, v in base.items()}
        pts["head"] = (pts["head"][0], pts["head"][1] + bob)
        pts["neck"] = (pts["neck"][0], pts["neck"][1] + bob)
        pts["shoulder"] = (pts["shoulder"][0], pts["shoulder"][1] + bob)
        pts["hip"] = (pts["hip"][0], pts["hip"][1] + bob)
        # ذراع أمامية/خلفية تتأرجح بطور متقابل
        pts["elbow"] = (pts["shoulder"][0] + 0.12 + swing, pts["shoulder"][1] + 0.10)
        pts["hand"] = (pts["shoulder"][0] + 0.24 + swing * 1.4, pts["shoulder"][1] + 0.20)
        # ساقا تتحركان بالتناوب مع رفع الركبة
        pts["knee"] = (pts["hip"][0] + 0.10 + bounce, pts["hip"][1] + 0.16 + max(0.0, step) * 0.06)
        pts["ankle"] = (pts["hip"][0] + 0.18 + bounce * 1.3, pts["hip"][1] + 0.33)
        frames_out.append({k: tuple(pts[k]) for k in keys})
    return frames_out


def build_pose_sequence_image(beat=None, frames=16, cycle=1.0):
    """يعيد (قائمة صور PNG متعددة الإطارات متجاورة أفقيا) لسلسلة حركة — دفعة واحدة لـ AnimateDiff."""
    seq = build_pose_sequence(beat, frames, cycle)
    w, h = IMG_W // max(1, frames // 4), IMG_H
    from PIL import Image, ImageDraw

    sheet = Image.new("RGB", (w * frames, h), (0, 0, 0))
    for fi, pts in enumerate(seq):
        img = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(img)
        p = {k: (int(v[0] * w), int(v[1] * h)) for k, v in pts.items()}
        bones = [
            ("head", "neck"), ("neck", "shoulder"), ("shoulder", "hip"),
            ("hip", "knee"), ("knee", "ankle"), ("shoulder", "elbow"), ("elbow", "hand"),
        ]
        for a, b in bones:
            if a in p and b in p:
                d.line([p[a], p[b]], fill=(255, 255, 255), width=7)
        r = 11
        for v in p.values():
            d.ellipse([v[0] - r, v[1] - r, v[0] + r, v[1] + r], fill=(255, 255, 255))
        hp = p["head"]
        d.ellipse([hp[0] - 24, hp[1] - 24, hp[0] + 24, hp[1] + 24], outline=(255, 255, 255), width=7)
        sheet.paste(img, (fi * w, 0))
    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    return buf.getvalue()


def build_pose_image(path, beat=None):
    """يرسم هيكل OpenPose (عصا بيضاء على خلفية سوداء) 1920x1080 بلا مكتبات إضافية."""
    from PIL import Image, ImageDraw

    w, h = IMG_W, IMG_H
    img = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    tpl = pose_template_for(beat)
    pts = {k: (int(v[0] * w), int(v[1] * h)) for k, v in tpl.items()}
    bones = [
        ("head", "neck"), ("neck", "shoulder"), ("shoulder", "hip"),
        ("hip", "knee"), ("knee", "ankle"), ("shoulder", "elbow"), ("elbow", "hand"),
    ]
    for a, b in bones:
        if a in pts and b in pts:
            d.line([pts[a], pts[b]], fill=(255, 255, 255), width=7)
    r = 11
    for p in pts.values():
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(255, 255, 255))
    hp = pts["head"]
    d.ellipse([hp[0] - 24, hp[1] - 24, hp[0] + 24, hp[1] + 24], outline=(255, 255, 255), width=7)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    Path(path).write_bytes(buf.getvalue())
    return str(path)


# ---------------- بناء Graph ---------------


class _Graph:
    def __init__(self):
        self.nodes = {}
        self._n = 0

    def add(self, class_type, **inputs):
        self._n += 1
        i = self._n
        self.nodes[i] = {"class_type": class_type, "inputs": inputs}
        return i


async def _upload_image(client, image_bytes, filename):
    """يرفع صورة إلى ComfyUI ويعيد (name, subfolder)."""
    files = {"image": (filename, image_bytes, "image/png")}
    resp = await client.post(COMFY_URL + "/upload/image", files=files, timeout=httpx.Timeout(60.0))
    resp.raise_for_status()
    data = resp.json()
    return data.get("name", filename), data.get("subfolder", "")


async def build_graph(client, prompt, negative, seed, ckpt, pose_bytes=None, ref_bytes=None):
    """يبني Graph كامل: SDXL + (ControlNet OpenPose) + (IP-Adapter)."""
    info = await _object_info(client)
    g = _Graph()
    ckpts = _names(info, "CheckpointLoaderSimple", "ckpt_name")
    cn_names = _names(info, "ControlNetLoader", "control_net_name")
    ckpt = ckpt or pick_ckpt(ckpts)

    ckpt_node = g.add("CheckpointLoaderSimple", ckpt_name=ckpt)
    pos_node = g.add("CLIPTextEncode", clip=[ckpt_node, 1], text=prompt)
    neg_node = g.add("CLIPTextEncode", clip=[ckpt_node, 1], text=negative)
    latent = g.add("EmptyLatentImage", width=IMG_W, height=IMG_H, batch_size=1)

    cur_pos, cur_neg = [pos_node, 0], [neg_node, 0]
    sampler_model = [ckpt_node, 0]

    if pose_bytes:
        name, sub = await _upload_image(client, pose_bytes, f"pose_{uuid.uuid4().hex[:6]}.png")
        pose_load = g.add("LoadImage", image=name)
        cn_load = g.add("ControlNetLoader", control_net_name=pick_controlnet(cn_names))
        cn_apply = g.add(
            "ControlNetApplyAdvanced",
            positive=cur_pos, negative=cur_neg,
            control_net=[cn_load, 0], image=[pose_load, 0],
            strength=0.85, start_percent=0.0, end_percent=0.9,
        )
        cur_pos, cur_neg = [cn_apply, 0], [cn_apply, 1]

    if ref_bytes:
        name, sub = await _upload_image(client, ref_bytes, f"ref_{uuid.uuid4().hex[:6]}.png")
        ref_load = g.add("LoadImage", image=name)
        ip_load = g.add("IPAdapterUnifiedLoader", preset="PLUS FACE (portraits)")
        ip_apply = g.add(
            "IPAdapterAdvanced",
            model=[ip_load, 0], ipadapter=[ip_load, 1],
            image=[ref_load, 0],
            weight=0.85, weight_type="linear", combine_embeds="concat",
            start_at=0.0, end_at=0.9, embeds_scaling="V only",
        )
        sampler_model = [ip_apply, 0]

    sampler = g.add(
        "KSampler",
        model=sampler_model, positive=cur_pos, negative=cur_neg,
        latent_image=[latent, 0],
        seed=seed, steps=COMFY_STEPS, cfg=7.0,
        sampler_name="dpmpp_2m", scheduler="karras", denoise=1.0,
    )
    vae = g.add("VAEDecode", samples=[sampler, 0], vae=[ckpt_node, 2])
    g.add("SaveImage", images=[vae, 0], filename_prefix="cartoon_studio")
    return g.nodes


# ---------------- تنفيذ ---------------


async def _run_graph(client, graph, timeout=900):
    client_id = uuid.uuid4().hex[:8]
    resp = await client.post(COMFY_URL + "/prompt", json={"prompt": graph, "client_id": client_id},
                             timeout=httpx.Timeout(60.0))
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"ComfyUI رفض الـ Graph: {data.get('error')} — {data.get('node_errors')}")
    prompt_id = data.get("prompt_id")

    import websockets

    try:
        async with websockets.connect(_ws_url() + f"?clientId={client_id}") as ws:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                data = json.loads(msg)
                if data.get("type") == "executing" and data.get("data", {}).get("node") is None:
                    break
    except (asyncio.TimeoutError, Exception):
        pass

    hist = await _get(client, f"/history/{prompt_id}")
    outputs = hist.get(prompt_id, {}).get("outputs", {})
    images = [img for node in outputs.values() for img in node.get("images", [])]
    if not images:
        raise RuntimeError("ComfyUI انتهى دون صور مخرجة")
    return images


async def _download_image(client, meta, out_path):
    params = {"filename": meta["filename"], "subfolder": meta.get("subfolder", ""), "type": "output"}
    resp = await client.get(COMFY_URL + "/view", params=params, timeout=httpx.Timeout(120.0))
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path


async def generate_scene_image(prompt, out_path, seed, ref_path=None, beat=None):
    """صورة مشهد عبر SDXL + ControlNet(OpenPose) + IP-Adapter(ref الشخصية)."""
    pose_bytes = None
    if beat:
        tmp_pose = Path(out_path).with_name(".pose_tmp.png")
        build_pose_image(tmp_pose, beat=beat)
        pose_bytes = tmp_pose.read_bytes()
        tmp_pose.unlink(missing_ok=True)
    ref_bytes = None
    if ref_path and Path(ref_path).exists():
        ref_bytes = Path(ref_path).read_bytes()

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        graph = await build_graph(client, prompt, COMFY_NEGATIVE, seed, COMFY_CKPT,
                                  pose_bytes=pose_bytes, ref_bytes=ref_bytes)
        images = await _run_graph(client, graph)
        await _download_image(client, images[0], out_path)
    return out_path


async def generate_character_sheet(design_prompt, out_path, seed):
    """شيت شخصية مرجعي (واجهة كاملة) يُستخدم في IP-Adapter لكل المشاهد."""
    prompt = (f"{design_prompt}, character reference sheet, front view, neutral pose, "
              "full body, centered, plain background")
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        graph = await build_graph(client, prompt, COMFY_NEGATIVE, seed, COMFY_CKPT)
        images = await _run_graph(client, graph)
        await _download_image(client, images[0], out_path)
    return out_path


async def verify_server():
    """فحص سريع: هل خادم ComfyUI متاح وأسماء النماذج تُقرأ؟"""
    if not COMFY_URL:
        raise RuntimeError("COMFY_URL غير مضبوط")
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        info = await _object_info(client)
    ckpts = _names(info, "CheckpointLoaderSimple", "ckpt_name")
    return {"url": COMFY_URL, "checkpoints": len(ckpts), "controlnet": len(_names(info, "ControlNetLoader", "control_net_name"))}


# ---------------------------------------------------------------------------
# أنيميشن حقيقي للشخصيات عبر AnimateDiff (إذا كانت العقد مثبتة على الخادم).
# ---------------------------------------------------------------------------

_ANIM_NODES = ("AnimateDiffLoaderV1", "AnimateDiffLoaderWithContext", "ADE_AnimateDiffLoaderWithContext")


async def _has_anim_nodes(client):
    info = await _object_info(client)
    return any(n in info for n in _ANIM_NODES)


async def build_graph_animated(client, prompt, negative, seed, ckpt, pose_bytes=None, ref_bytes=None, frames=16, fps=12):
    """Graph أنيميشن: SD1.5/2.1 checkpoint + AnimateDiff + ControlNet(سلسلة OpenPose).

    pose_bytes هنا يجب أن يكون صورة sheet أفقي بإطارات متعددة متجاورة
    (تُستخدم ControlNet للمساعدة في تثبيت الحركة عبر الفريمات).
    """
    info = await _object_info(client)
    g = _Graph()
    ckpts = _names(info, "CheckpointLoaderSimple", "ckpt_name")
    ckpt = ckpt or pick_ckpt(ckpts)

    ckpt_node = g.add("CheckpointLoaderSimple", ckpt_name=ckpt)
    pos_node = g.add("CLIPTextEncode", clip=[ckpt_node, 1], text=prompt)
    neg_node = g.add("CLIPTextEncode", clip=[ckpt_node, 1], text=negative)
    latent = g.add("EmptyLatentImage", width=IMG_W, height=IMG_H, batch_size=frames)

    cur_pos, cur_neg = [pos_node, 0], [neg_node, 0]
    sampler_model = [ckpt_node, 0]

    # أنيميشن: نبذل محاولة على اسم معروف لكل إصدار متاح
    loader = None
    for node_name in _ANIM_NODES:
        if node_name in info:
            try:
                loader = g.add(node_name, model=[ckpt_node, 0], length=frames, batch_size=1,
                               fps=fps, loop=True)
                sampler_model = [loader, 0]
                break
            except Exception:
                continue

    if pose_bytes:
        name, sub = await _upload_image(client, pose_bytes, f"pose_seq_{uuid.uuid4().hex[:6]}.png")
        pose_load = g.add("LoadImage", image=name)
        cn_load = g.add("ControlNetLoader", control_net_name=pick_controlnet(_names(info, "ControlNetLoader", "control_net_name")))
        cn_apply = g.add(
            "ControlNetApplyAdvanced",
            positive=cur_pos, negative=cur_neg,
            control_net=[cn_load, 0], image=[pose_load, 0],
            strength=0.75, start_percent=0.0, end_percent=0.75,
        )
        cur_pos, cur_neg = [cn_apply, 0], [cn_apply, 1]

    if ref_bytes:
        name, sub = await _upload_image(client, ref_bytes, f"ref_{uuid.uuid4().hex[:6]}.png")
        ref_load = g.add("LoadImage", image=name)
        ip_load = g.add("IPAdapterUnifiedLoader", preset="PLUS FACE (portraits)")
        ip_apply = g.add(
            "IPAdapterAdvanced",
            model=[ip_load, 0], ipadapter=[ip_load, 1],
            image=[ref_load, 0],
            weight=0.7, weight_type="linear", combine_embeds="concat",
            start_at=0.0, end_at=0.85, embeds_scaling="V only",
        )
        sampler_model = [ip_apply, 0]

    sampler = g.add(
        "KSampler",
        model=sampler_model, positive=cur_pos, negative=cur_neg,
        latent_image=[latent, 0],
        seed=seed, steps=COMFY_STEPS, cfg=7.0,
        sampler_name="dpmpp_2m", scheduler="karras", denoise=1.0,
    )
    vae = g.add("VAEDecode", samples=[sampler, 0], vae=[ckpt_node, 2])
    g.add("SaveImage", images=[vae, 0], filename_prefix="cartoon_studio_anim")
    return g.nodes


async def generate_animated_scene(prompt, out_video, seed, beat=None, ref_path=None, frames=16, fps=12):
    """يولّد مقطع أنيميشن قصير عبر AnimateDiff إن توفر، وإلا يعيد None (صورة ثابتة تُستخدم)."""
    if not COMFY_URL:
        return None
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        if not await _has_anim_nodes(client):
            return None
        pose_bytes = build_pose_sequence_image(beat=beat, frames=frames)
        ref_bytes = None
        if ref_path and Path(ref_path).exists():
            ref_bytes = Path(ref_path).read_bytes()
        graph = await build_graph_animated(client, prompt, COMFY_NEGATIVE, seed, COMFY_CKPT,
                                           pose_bytes=pose_bytes, ref_bytes=ref_bytes, frames=frames, fps=fps)
        images = await _run_graph(client, graph, timeout=1800)
        # نجمع الإطارات المُخرجة من SaveImage في ملف فيديو
        if not images:
            return None
        video = out_video
        if len(images) == 1:
            # بعض الإعدادات تُخرج PNG واحد متعدد الفريمات — نعتبره صورة أولى فقط
            await _download_image(client, images[0], video)
            return None
        # مخرجات متعددة الإطارات → نقوم بتحميل كل إطار ثم دمجها
        frames_dir = Path(out_video).parent / (Path(out_video).stem + "_frames")
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_files = []
        for i, meta in enumerate(images):
            fp = frames_dir / f"{i:04d}.png"
            await _download_image(client, meta, fp)
            frame_files.append(fp)
        _frames_to_video(frame_files, out_video, fps)
        return out_video


def _frames_to_video(frame_files, out_video, fps=12):
    """يجمع إطارات PNG في فيديو mp4 (يستخدم ffmpeg المتوفر في المشروع)."""
    import subprocess

    exe = os.environ.get("FFMPEG") or "ffmpeg"
    import shutil

    if not shutil.which(exe):
        try:
            import imageio_ffmpeg

            exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return None
    lst = Path(out_video).with_name(Path(out_video).stem + "_list.txt")
    lst.write_text("\n".join(f"file '{f.resolve().as_posix()}'" for f in frame_files), encoding="utf-8")
    cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-vf", f"fps={fps},scale=1280:720", "-c:v", "libx264", "-preset", "fast", str(out_video)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            return out_video
    except Exception:
        pass
    return None
