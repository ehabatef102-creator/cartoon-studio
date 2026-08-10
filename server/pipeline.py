import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

import edge_tts
import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import cards, motion, sound_design, visual

DEFAULT_VOICE = os.environ.get("DEFAULT_VOICE", "ar-EG-SalmaNeural")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
POLLINATIONS_TOKEN = os.environ.get("POLLINATIONS_TOKEN", "")
IMAGE_PROVIDER = os.environ.get("IMAGE_PROVIDER", "auto")
AUDIO_DESIGN = os.environ.get("AUDIO_DESIGN", "1") == "1"
MOTION_ENGINE = os.environ.get("MOTION_ENGINE", "1") == "1"

TITLE_SECONDS = 4
END_SECONDS = 4
POST_CREDIT_SECONDS = 20


def _run(cmd, timeout=900):
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"فشل أمر: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return proc


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return exe
    except Exception:
        pass
    raise RuntimeError("ffmpeg غير متوفر على السيرفر")


_FFMPEG = None


def FFMPEG():
    global _FFMPEG
    if _FFMPEG is None:
        _FFMPEG = ffmpeg_exe()
    return _FFMPEG


async def _pollinations_image(client, prompt, out_path, seed):
    q = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{q}"
        f"?width=1920&height=1080&seed={seed}&nologo=true&model=flux"
        f"&referrer=cartoon-studio&client_id=cartoon-studio-prod"
    )
    headers = {"Authorization": f"Bearer {POLLINATIONS_TOKEN}"} if POLLINATIONS_TOKEN else {}
    last_err = None
    for attempt in range(8):
        try:
            resp = await client.get(url, headers=headers, timeout=httpx.Timeout(240.0))
            ctype = resp.headers.get("content-type", "")
            if ctype.startswith("image/"):
                out_path.write_bytes(resp.content)
                return
            if resp.status_code in (429, 503, 500, 502, 504):
                retry_after = float(resp.headers.get("retry-after", "0") or 0)
                wait = max(retry_after, 5 * (2 ** attempt))
            else:
                wait = 3
            last_err = RuntimeError(f"الرد غير صورة (HTTP {resp.status_code}): {resp.text[:300]}")
            await asyncio.sleep(min(wait, 90))
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(min(5 * (2 ** attempt), 90))
    raise RuntimeError(f"فشل توليد الصورة عبر Pollinations: {last_err}")


async def _stability_image(client, prompt, out_path):
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    payload = {
        "text_prompts": [{"text": prompt}],
        "height": 768,
        "width": 1280,
        "steps": 35,
        "cfg_scale": 7,
    }
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}"}
    resp = await client.post(url, json=payload, headers=headers, timeout=httpx.Timeout(240.0))
    resp.raise_for_status()
    data = resp.json()
    out_path.write_bytes(base64.b64decode(data["artifacts"][0]["base64"]))


def _detect_image_ext(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    return ".jpg"


async def gen_image(client, prompt, out_path, seed, sem):
    async with sem:
        tmp = out_path.with_suffix(".tmp")
        if IMAGE_PROVIDER == "stability" or (IMAGE_PROVIDER == "auto" and STABILITY_API_KEY):
            await _stability_image(client, prompt, tmp)
        else:
            await _pollinations_image(client, prompt, tmp, seed)
        ext = _detect_image_ext(tmp.read_bytes())
        final = tmp.with_suffix(ext)
        tmp.rename(final)
        return final.name


async def _edge_voice(text, out_path, voice=None):
    communicate = edge_tts.Communicate(text, voice or DEFAULT_VOICE, rate="+8%")
    await communicate.save(str(out_path))


async def _eleven_voice(client, text, out_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    resp = await client.post(url, json=payload, headers=headers, timeout=httpx.Timeout(240.0))
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


async def gen_voice(client, text, out_path, voice=None):
    if ELEVENLABS_API_KEY:
        await _eleven_voice(client, text, out_path)
    else:
        await _edge_voice(text, out_path, voice)


def voice_for_speaker(pack, speaker):
    """صوت الشخصية من المذكرة؛ الراوي/المجهول يأخذ الصوت الافتراضي."""
    if not speaker:
        return None
    for ch in pack.get("characters", []):
        if ch.get("name") == speaker and ch.get("voice"):
            return ch["voice"]
    return None


def build_scene_audio(voice_files, out_audio, seconds):
    if voice_files:
        n = len(voice_files)
        cmd = [FFMPEG(), "-y"]
        for f in voice_files:
            cmd += ["-i", str(f)]
        graph = "".join(f"[{i}:a]aresample=24000,atrim=0:60,asetpts=N/SR/TB[{i}a];" for i in range(n))
        graph += "".join(f"[{i}a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]"
        cmd += ["-filter_complex", graph, "-map", "[a]", "-c:a", "aac", str(out_audio)]
        _run(cmd, timeout=300)
    else:
        _run([FFMPEG(), "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(seconds), "-c:a", "aac", str(out_audio)], timeout=120)
    padded = out_audio.with_name(out_audio.stem + "_padded.aac")
    _run([FFMPEG(), "-y", "-i", str(out_audio), "-af", "apad", "-t", str(seconds), "-c:a", "aac", str(padded)], timeout=120)
    padded.replace(out_audio)


def _zoom_expr(zoom_in, step):
    if zoom_in:
        return f"min(zoom+{step},1.14)"
    return f"if(lte(zoom,1.0),1.14,max(1.001,zoom-{step}))"


def render_still_video(image, audio, out_mp4, seconds, zoom_in=True):
    step = 0.0006 if zoom_in else 0.0008
    zoom = (
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        f"zoompan=z='{_zoom_expr(zoom_in, step)}':d={int(seconds * 24)}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=24[v]"
    )
    cmd = [
        FFMPEG(), "-y", "-loop", "1", "-framerate", "24", "-i", str(image),
    ]
    if audio and audio.exists():
        cmd += ["-i", str(audio)]
        cmd += ["-filter_complex", zoom, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    else:
        cmd += ["-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=24000:cl=mono"]
        cmd += ["-filter_complex", zoom, "-map", "[v]", "-map", "1:a", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    cmd += ["-t", str(seconds), "-shortest", str(out_mp4)]
    _run(cmd, timeout=900)


def concat_videos(videos, out_mp4):
    lst = out_mp4.with_name("concat.txt")
    lst.write_text("\n".join(f"file '{f.resolve().as_posix()}'" for f in videos), encoding="utf-8")
    _run([FFMPEG(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out_mp4)], timeout=600)


def color_grade(input_video, out_mp4):
    _run([
        FFMPEG(), "-y", "-i", str(input_video),
        "-vf", "eq=saturation=1.18:contrast=1.06:brightness=0.01,vignette=PI/5,noise=alls=6:allf=t",
        "-c:v", "libx264", "-preset", "veryfast", "-c:a", "copy", str(out_mp4),
    ], timeout=900)


def _build_scene_audio_design(tmp_dir, scene, voice_track, prefix=None, audio_design=True):
    """يبني المكس السينمائي للمشهد (موسيقى + مؤثرات + ducking). يعود لمسار الصوت النهائي."""
    if not audio_design:
        return voice_track
    name = prefix or f"scene_{scene['num']:02d}"
    try:
        music_wav = tmp_dir / f"{name}.music.wav"
        sfx_wav = tmp_dir / f"{name}.sfx.wav"
        music_info = scene.get("music") or {}
        sound_design.synth_music(
            music_wav, scene["seconds"],
            mode=music_info.get("mode", "minor"),
            intensity=music_info.get("intensity", 5),
            tempo=music_info.get("tempo", 80),
        )
        sound_design.synth_sfx(sfx_wav, scene.get("sfx", []), scene["seconds"])
        out_mix = tmp_dir / f"{name}.mix.m4a"
        sound_design.build_scene_mix(FFMPEG(), voice_track, music_wav, sfx_wav, scene["seconds"], out_mix)
        return out_mix
    except Exception as exc:
        try:
            print(f"sound_design fallback: {exc!r}", file=sys.stderr)
        except Exception:
            pass
        return voice_track


def save_job(job):
    job_dir = job["_dir"]
    job_dir.joinpath("job.json").write_text(
        json.dumps({k: v for k, v in job.items() if not k.startswith("_")}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def run_job(job, workspace, pack, render_video, audio_design=None, use_motion=None):
    audio_design = AUDIO_DESIGN if audio_design is None else bool(audio_design)
    motion_enabled = MOTION_ENGINE if use_motion is None else bool(use_motion)
    job["status"] = "running"
    job["progress"] = 0
    job["phase"] = "توليد السيناريو"
    job_dir = workspace / "jobs" / job["id"]
    pack_dir = job_dir / "pack"
    images_dir = job_dir / "images"
    voices_dir = job_dir / "voice"
    tmp_dir = job_dir / "tmp"
    video_dir = job_dir / "video"
    for d in (pack_dir, images_dir, voices_dir, tmp_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    from creative_engine import render_and_write_pack

    try:
        render_and_write_pack(pack, pack_dir / pack["slug"])
        job["pack_slug"] = pack["slug"]
        job["pack_title"] = pack["title"]
        scenes = pack["pilot"]["scenes"]
        total = len(scenes)
        sem = asyncio.Semaphore(1 if not (IMAGE_PROVIDER == "stability" or STABILITY_API_KEY) else 2)
        job["phase"] = "توليد الصور والأصوات (سينمائي)"
        job["images"] = []

        async def generate_scene(prefix, image_prompt, dialogue, seed_off):
            image_path = images_dir / f"{prefix}"
            image_name = await gen_image(client, image_prompt, image_path, seed=job["seed"] + seed_off, sem=sem)
            job["images"].append(f"images/{image_name}")
            scene_voices = voices_dir / prefix
            scene_voices.mkdir(parents=True, exist_ok=True)
            for li, (speaker, text) in enumerate(dialogue):
                voice_path = scene_voices / f"{li + 1:02d}_{speaker}.mp3"
                await gen_voice(client, text, voice_path, voice=voice_for_speaker(pack, speaker))

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
            for si, scene in enumerate(scenes):
                job["scene"] = scene["num"]
                save_job(job)
                prompt = visual.compose_scene_prompt(pack, scene)
                await generate_scene(f"scene_{scene['num']:02d}", prompt, scene["dialogue"], scene["num"])
                job["progress"] = int((si + 1) / total * 100)
                save_job(job)
            if pack.get("post_credits"):
                job["scene"] = "post-credit"
                pc = pack["post_credits"]
                prompt = visual.compose_scene_prompt(pack, pc, beat="crossover")
                await generate_scene("scene_08_post", prompt, pc["dialogue"], 99)
                save_job(job)

        sb = visual.storyboard(pack)
        job_dir.joinpath("storyboard.json").write_text(
            json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if render_video:
            job["phase"] = "رندر الفيديو السينمائي (يستغرق عدة دقائق)"
            save_job(job)
            try:
                FFMPEG()
            except Exception as exc:
                raise RuntimeError("ffmpeg غير متوفر على السيرفر") from exc

            title_card = tmp_dir / "title.png"
            end_card = tmp_dir / "end.png"
            cards.make_title_card(
                pack["title"],
                pack["pilot"]["title"],
                "حلقة تجريبية — من عالم أفق السحاب",
                title_card,
                job["seed"],
            )
            next_hook = pack["next_episodes"][0]
            cards.make_end_card(pack["title"], next_hook, end_card)

            video_parts = []
            title_video = tmp_dir / "title.mp4"
            render_still_video(title_card, None, title_video, TITLE_SECONDS, zoom_in=True)
            video_parts.append(title_video)

            for i, scene in enumerate(scenes):
                image_file = next(images_dir.glob(f"scene_{scene['num']:02d}.*"))
                voice_track = tmp_dir / f"scene_{scene['num']:02d}.voice.m4a"
                voice_files = sorted((voices_dir / f"scene_{scene['num']:02d}").glob("*.mp3"))
                build_scene_audio(voice_files, voice_track, scene["seconds"])
                scene_audio = _build_scene_audio_design(tmp_dir, scene, voice_track, audio_design=audio_design)
                scene_video = tmp_dir / f"scene_{scene['num']:02d}.mp4"
                if motion_enabled:
                    plan = motion.plan_motion(scene)
                    motion.render_scene_clip(FFMPEG(), image_file, scene_audio, scene_video, scene["seconds"], plan)
                else:
                    zoom_in = (i % 2 == 0)
                    render_still_video(image_file, scene_audio, scene_video, scene["seconds"], zoom_in=zoom_in)
                video_parts.append(scene_video)
                job["scene"] = scene["num"]
                save_job(job)

            if pack.get("post_credits"):
                post_image = next(images_dir.glob("scene_08_post.*"))
                post_voice = tmp_dir / "post_credit.voice.m4a"
                voice_files = sorted((voices_dir / "scene_08_post").glob("*.mp3"))
                build_scene_audio(voice_files, post_voice, POST_CREDIT_SECONDS)
                post_audio = _build_scene_audio_design(tmp_dir, pack["post_credits"], post_voice, "post_credit", audio_design=audio_design)
                post_video = tmp_dir / "post_credit.mp4"
                if motion_enabled:
                    plan = motion.plan_motion(pack["post_credits"])
                    motion.render_scene_clip(FFMPEG(), post_image, post_audio, post_video, POST_CREDIT_SECONDS, plan)
                else:
                    render_still_video(post_image, post_audio, post_video, POST_CREDIT_SECONDS, zoom_in=True)
                video_parts.append(post_video)

            end_video = tmp_dir / "end.mp4"
            render_still_video(end_card, None, end_video, END_SECONDS, zoom_in=False)
            video_parts.append(end_video)

            raw_video = tmp_dir / "raw.mp4"
            concat_videos(video_parts, raw_video)
            color_grade(raw_video, video_dir / "final.mp4")

        job["status"] = "done"
        job["progress"] = 100
        job["phase"] = "اكتمل"
    except Exception as exc:
        job["status"] = "error"
        job["error"] = str(exc)
    save_job(job)
