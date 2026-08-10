"""محرك التصميم الصوتي السينمائي:
- موسيقى تصويرية مولّدة محليًا (numpy) حسب مزاج/شدّة المشهد — مجانية تمامًا.
- مؤثرات صوتية (SFX) مُصنّعة رقميًا من وصف عربي.
- مكس نهائي: حوار مسيطر + موسيقى تنخفض تلقائيًا تحت الحوار (ducking) + ليمتر.
"""
import os
import subprocess

try:
    import numpy as _np
except Exception:  # pragma: no cover
    _np = None

RATE = 16000
A2 = 110.0

_CHORD_PROGRESSIONS = {
    "minor": [(0, 3, 7, 10), (8, 0, 3, 7), (3, 7, 10, 14), (5, 0, 3, 7)],
    "major": [(0, 4, 7, 11), (9, 0, 4, 7), (5, 9, 0, 4), (7, 0, 4, 7)],
}


def _freq(root, semis):
    return root * (2.0 ** (semis / 12.0))


def _write_wav(path, samples, rate=RATE):
    import wave

    samples = _np.clip(samples, -1.0, 1.0)
    pcm = (_np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def synth_music(path, seconds, mode="minor", intensity=5, tempo=80, root=A2):
    """موسيقى تصويرية: وسادات وترية (pads) + باس + هواء، تتطور عبر الأوتار."""
    if _np is None:
        raise RuntimeError("numpy غير متوفر لتوليد الموسيقى")
    seconds = max(1.0, float(seconds))
    mode = mode if mode in _CHORD_PROGRESSIONS else "minor"
    intensity = max(1, min(10, int(intensity)))
    sr = RATE
    n = int(seconds * sr)
    t = _np.arange(n, dtype=float) / sr
    buf = _np.zeros(n, dtype=float)

    bar = 4 * 60.0 / max(40, int(tempo))
    prog = _CHORD_PROGRESSIONS[mode]
    bars = max(1, int(_np.ceil(seconds / bar)))
    for b in range(bars):
        start = int(b * bar * sr)
        end = min(n, int((b + 1) * bar * sr))
        if start >= end:
            break
        seg_t = t[start:end] - t[start]
        chord = prog[b % len(prog)]
        seg = _np.zeros(end - start, dtype=float)
        for semi in chord:
            f = _freq(root, semi)
            seg += _np.sin(2 * _np.pi * f * seg_t) * 0.42
            seg += _np.sin(2 * _np.pi * f * 2 * seg_t) * 0.16
        root_note = any(semi % 12 == 0 for semi in chord)
        if root_note:
            seg += _np.sin(2 * _np.pi * root * 0.5 * seg_t) * 0.22
        L = len(seg)
        a = min(L, int(0.9 * sr))
        r = min(L, int(1.1 * sr))
        env = _np.ones(L, dtype=float)
        if a > 0:
            env[:a] = _np.linspace(0.0, 1.0, a)
        if r > 0:
            env[-r:] = _np.linspace(1.0, 0.0, r)
        buf[start:end] += seg * env

    buf += _np.sin(2 * _np.pi * (root / 2) * t) * 0.16

    rng = _np.random.default_rng(7)
    noise = rng.normal(0.0, intensity * 0.009, n)
    k = 96
    if n > k:
        noise = _np.convolve(noise, _np.ones(k) / k, mode="same")
    buf += noise

    buf *= 0.7 + 0.3 * _np.sin(2 * _np.pi * 0.15 * t)
    buf *= 0.22 + intensity * 0.028
    _write_wav(path, buf, sr)


def _envelope(n, sr, attack=0.25, release=0.5):
    a = min(n, int(attack * sr))
    r = min(n, int(release * sr))
    env = _np.ones(n, dtype=float)
    if a > 0:
        env[:a] = _np.linspace(0.0, 1.0, a)
    if r > 0:
        env[-r:] = _np.linspace(1.0, 0.0, r)
    return env


def synth_sfx(path, labels, seconds):
    """يُركّب مؤثرات صوتية من أوصاف عربية: رياح، أجراس، خطوات، رعد، صفحات، بوق، شرر."""
    if _np is None:
        raise RuntimeError("numpy غير متوفر لتوليد المؤثرات")
    seconds = max(1.0, float(seconds))
    sr = RATE
    n = int(seconds * sr)
    t = _np.arange(n, dtype=float) / sr
    rng = _np.random.default_rng(3)
    buf = _np.zeros(n, dtype=float)

    def add(sig, start_sec=0.0):
        i0 = int(start_sec * sr)
        if i0 < 0 or i0 >= n:
            return
        i1 = min(n, i0 + len(sig))
        if i1 <= i0:
            return
        buf[i0:i1] += sig[: i1 - i0]

    center = seconds / 2.0
    for lab in (labels or []):
        lab = str(lab).lower()
        if any(k in lab for k in ("رياح", "wind", "هواء")):
            env = _envelope(n, sr, attack=0.6, release=1.5) * _np.sin(_np.pi * t / max(seconds, 1.0)) ** 2
            sig = rng.normal(0, 0.5, n)
            k = 32
            sig = _np.convolve(sig, _np.ones(k) / k, mode="same") * env * 0.5
            add(sig)
        elif any(k in lab for k in ("جرس", "أجراس", "bell", "ناقوس")):
            for f, amp, dur in ((880, 0.32, 1.2), (1320, 0.18, 0.8)):
                seg_t = _np.arange(int(dur * sr)) / sr
                sig = _np.sin(2 * _np.pi * f * seg_t) * _np.exp(-seg_t * 3.0) * amp
                add(sig, center - 0.6)
        elif any(k in lab for k in ("خطوات", "footstep", "أقدام")):
            step_i = 0.0
            while step_i < seconds - 0.3:
                seg_t = _np.arange(int(0.12 * sr)) / sr
                sig = _np.sin(2 * _np.pi * 120 * seg_t) * _np.exp(-seg_t * 40) * 0.5
                add(sig, step_i)
                step_i += 0.55
        elif any(k in lab for k in ("رعد", "thunder", "زئير", "زعيق")):
            seg_t = _np.arange(int(2.2 * sr)) / sr
            sig = _np.sin(2 * _np.pi * 48 * seg_t) * _np.exp(-seg_t * 1.6) * 0.9
            sig += rng.normal(0, 0.4, len(seg_t)) * _np.exp(-seg_t * 2.0)
            add(sig, center - 1.0)
        elif any(k in lab for k in ("صفحات", "ورق", "paper", "كتب")):
            for i in range(3):
                start = center - 1.0 + i * 0.5
                burst = rng.normal(0, 0.5, int(0.09 * sr))
                add(burst, start)
        elif any(k in lab for k in ("بوق", "horn", "صفير", "whistle", "بواق")):
            seg_t = _np.arange(int(1.8 * sr)) / sr
            f = 300 + 500 * (seg_t / seg_t[-1])
            phase = 2 * _np.pi * _np.cumsum(f) / sr
            sig = _np.sin(phase) * _np.minimum(seg_t * 8, 1) * _np.exp(-seg_t * 0.8) * 0.5
            add(sig, center - 0.8)
        elif any(k in lab for k in ("شرر", "spark", "كهرباء", "زنانة")):
            for i in range(5):
                f0 = 1200 + i * 400
                seg_t = _np.arange(int(0.25 * sr)) / sr
                sig = _np.sin(2 * _np.pi * f0 * seg_t) * _np.exp(-seg_t * 14) * 0.25
                add(sig, center - 1.0 + i * 0.18)
        else:
            env = _np.sin(_np.pi * t / max(seconds, 1.0)) ** 2
            sig = rng.normal(0, 0.4, n)
            k = 64
            sig = _np.convolve(sig, _np.ones(k) / k, mode="same") * env * 0.35
            add(sig)

    _write_wav(path, buf, sr)


def build_scene_mix(ffmpeg, voice, music, sfx, seconds, out_aac):
    """مكس سينمائي: حوار أمامي، موسيقى تنخفض تحت الحوار (ducking)، مؤثرات بمستوى وسط."""
    inputs = [voice]
    has_music = music is not None and os.path.exists(str(music))
    has_sfx = sfx is not None and os.path.exists(str(sfx))
    if has_music:
        inputs.append(music)
    if has_sfx:
        inputs.append(sfx)
    cmd = [ffmpeg, "-y"]
    for f in inputs:
        cmd += ["-i", str(f)]

    g = []
    nxt = 1
    if has_music:
        g.append("[0:a]aresample=24000,apad,asplit=2[vo1][vo2]")
        g.append(f"[{nxt}:a]aresample=24000,apad,volume=0.55[m]")
        g.append("[m][vo2]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=900,volume=0.5[duck]")
        nxt += 1
    else:
        g.append("[0:a]aresample=24000,apad[vo1]")
    if has_sfx:
        g.append(f"[{nxt}:a]aresample=24000,apad,volume=0.7[sf]")
        nxt += 1

    mix_inputs = ["[vo1]"]
    if has_music:
        mix_inputs.append("[duck]")
    if has_sfx:
        mix_inputs.append("[sf]")
    nmix = len(mix_inputs)
    tail = f"{seconds - 0.7:.2f}" if seconds > 1.2 else "0.0"
    g.append(
        "".join(mix_inputs) + f"amix=inputs={nmix}:duration=longest:normalize=0,"
        f"atrim=0:{seconds},alimiter=limit=0.93,"
        f"afade=t=in:d=0.2,afade=t=out:st={tail}:d=0.7[a]"
    )
    cmd += ["-filter_complex", ";".join(g), "-map", "[a]", "-ar", "24000", "-ac", "1", "-c:a", "aac", str(out_aac)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"فشل المكس الصوتي: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return out_aac
