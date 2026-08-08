import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(__file__).resolve().parent / "fonts"


def _font(size, bold=False):
    name = "Amiri-Bold.ttf" if bold else "Amiri-Regular.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _shape(text):
    return get_display(arabic_reshaper.reshape(text))


def _render_text(draw, xy, text, font, fill, anchor="mm"):
    draw.text(xy, _shape(text), font=font, fill=fill, anchor=anchor)


def make_title_card(series_title, episode_title, subtitle, out_path, seed):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (10, 14, 28))
    d = ImageDraw.Draw(img)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    rng_seed = seed % 360
    gd.ellipse([w / 2 - 900, h / 2 - 700, w / 2 + 900, h / 2 + 700], fill=(rng_seed, 120 + rng_seed % 100, 220, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    line_y = h / 2 - 150
    d.rectangle([w / 2 - 220, line_y, w / 2 + 220, line_y + 4], fill=(251, 191, 36))
    _render_text(d, (w / 2, h / 2 - 60), series_title, _font(150, True), (255, 255, 255))
    _render_text(d, (w / 2, h / 2 + 60), episode_title, _font(72, False), (251, 191, 36))
    _render_text(d, (w / 2, h - 160), subtitle, _font(40, False), (148, 163, 184))
    img.save(out_path, quality=95)


def make_end_card(series_title, next_hook, out_path):
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (13, 17, 34))
    d = ImageDraw.Draw(img)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w / 2 - 800, h / 2 - 500, w / 2 + 800, h / 2 + 500], fill=(20, 80, 160, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img)

    _render_text(d, (w / 2, 260), series_title, _font(110, True), (255, 255, 255))
    d.rectangle([w / 2 - 260, 400, w / 2 + 260, 404], fill=(251, 191, 36))
    _render_text(d, (w / 2, h / 2), next_hook, _font(56, False), (226, 232, 240))
    _render_text(d, (w / 2, h - 180), "اشترك ليصلك لغز الحلقة القادمة", _font(46, True), (251, 191, 36))
    img.save(out_path, quality=95)
