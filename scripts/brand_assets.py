from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

FONT_BOLD = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
]
FONT_REGULAR = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
]


def _font(size: int, bold: bool = True):
    for p in (FONT_BOLD if bold else FONT_REGULAR):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _palette(dark: bool = False):
    if dark:
        return {
            'bg': (17, 24, 29, 255),
            'panel': (28, 37, 43, 255),
            'panel2': (40, 51, 58, 255),
            'accent': (72, 190, 184, 255),
            'text': (239, 244, 246, 255),
            'muted': (164, 177, 183, 255),
            'line': (67, 82, 89, 255),
        }
    return {
        'bg': (245, 247, 247, 255),
        'panel': (255, 255, 255, 255),
        'panel2': (235, 240, 240, 255),
        'accent': (34, 138, 137, 255),
        'text': (29, 39, 44, 255),
        'muted': (99, 112, 118, 255),
        'line': (208, 217, 219, 255),
    }


def _gradient(size, top, bottom):
    w, h = size
    im = Image.new('RGB', size, top[:3])
    px = im.load()
    for y in range(h):
        t = y / max(1, h - 1)
        row = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(w):
            px[x, y] = row
    return im.convert('RGBA')


def _draw_mark(size: int, *, dark: bool = False, transparent: bool = True):
    c = _palette(dark)
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0) if transparent else c['bg'])
    d = ImageDraw.Draw(im)
    cx = cy = size / 2
    r = size * .31
    lw = max(2, size // 36)

    # One restrained RuneSheet mark: circle + faceted compass/diamond.
    d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=c['line'], width=lw)
    pts = [(cx, cy-r*.72), (cx+r*.72, cy), (cx, cy+r*.72), (cx-r*.72, cy)]
    d.polygon(pts, outline=c['accent'])
    d.line(pts + [pts[0]], fill=c['accent'], width=lw)
    inner = r * .22
    d.polygon([(cx, cy-inner), (cx+inner, cy), (cx, cy+inner), (cx-inner, cy)], fill=c['accent'])
    return im


def _fit(draw, text: str, size: int, max_width: int):
    f = _font(size)
    while size > 12 and draw.textbbox((0, 0), text, font=f)[2] > max_width:
        size -= 2
        f = _font(size)
    return f


def _front_card(w: int, h: int, title: str, subtitle: str, action: str, *, dark: bool):
    c = _palette(dark)
    if dark:
        im = _gradient((w, h), (20, 28, 33, 255), (25, 34, 40, 255))
    else:
        im = _gradient((w, h), (250, 251, 251, 255), (240, 244, 244, 255))
    d = ImageDraw.Draw(im)

    # Quiet card, no grids or ornamental double frames.
    pad = int(h * .10)
    d.rounded_rectangle((pad, pad, w-pad, h-pad), radius=int(h*.06), fill=c['panel'], outline=c['line'], width=max(2, w//640))
    mark_size = int(h * .54)
    mark = _draw_mark(mark_size, dark=dark, transparent=True)
    im.alpha_composite(mark, (int(w*.075), int((h-mark_size)/2)))

    split = int(w * .34)
    d.line((split, int(h*.18), split, int(h*.82)), fill=c['line'], width=max(2, w//720))
    tx = split + int(w*.055)
    f1 = _fit(d, title, int(h*.094), int(w*.52))
    f2 = _font(int(h*.042), bold=False)
    d.text((tx, int(h*.28)), title, font=f1, fill=c['text'])
    d.text((tx, int(h*.50)), subtitle, font=f2, fill=c['muted'])

    fa = _font(int(h*.035))
    tb = d.textbbox((0, 0), action, font=fa)
    bw = tb[2]-tb[0] + int(h*.11)
    bh = tb[3]-tb[1] + int(h*.065)
    bx, by = tx, int(h*.66)
    d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=int(bh*.45), fill=c['accent'])
    d.text((bx+int(h*.055), by+int(h*.018)), action, font=fa, fill=(255,255,255,255))
    return im


def _portrait_card(w: int, h: int, title: str, action: str):
    c = _palette(False)
    im = _gradient((w, h), (249, 250, 250, 255), (238, 243, 243, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12, 12, w-12, h-12), radius=18, outline=c['line'], width=2)
    mark = _draw_mark(int(w*.55), dark=False, transparent=True)
    im.alpha_composite(mark, (int(w*.225), int(h*.14)))
    f = _fit(d, title, int(w*.11), int(w*.82))
    box = d.textbbox((0,0), title, font=f)
    d.text(((w-(box[2]-box[0]))/2, int(h*.66)), title, font=f, fill=c['text'])
    fa = _font(int(w*.06), bold=False)
    box = d.textbbox((0,0), action, font=fa)
    d.text(((w-(box[2]-box[0]))/2, int(h*.82)), action, font=fa, fill=c['accent'])
    return im


def _paper_background(w: int, h: int):
    # Neutral sheet surface: almost flat, deliberately no ornament pattern.
    return _gradient((w, h), (249, 250, 250, 255), (241, 244, 244, 255))


def _blank_portrait(w: int, h: int):
    c = _palette(False)
    im = _paper_background(w, h)
    d = ImageDraw.Draw(im)
    cx = w / 2
    d.ellipse((cx-w*.12, h*.19, cx+w*.12, h*.39), fill=(177, 188, 191, 255))
    d.rounded_rectangle((w*.24, h*.43, w*.76, h*.82), radius=int(w*.15), fill=(177, 188, 191, 255))
    return im


def _brace(w: int, h: int, side: str):
    # Minimal separators replacing ornate fantasy braces.
    c = _palette(False)
    im = Image.new('RGBA', (w, h), (0,0,0,0))
    d = ImageDraw.Draw(im)
    lw = max(2, min(w,h)//28)
    if side == 'top':
        y = int(h*.66)
        d.line((int(w*.12), y, int(w*.88), y), fill=c['line'], width=lw)
        d.line((int(w*.40), y, int(w*.60), y), fill=c['accent'], width=lw+1)
    elif side == 'tl':
        d.line((w*.20,h*.82,w*.20,h*.30,w*.72,h*.30), fill=c['line'], width=lw)
    elif side == 'tr':
        d.line((w*.80,h*.82,w*.80,h*.30,w*.28,h*.30), fill=c['line'], width=lw)
    elif side == 'bl':
        d.line((w*.20,h*.18,w*.20,h*.70,w*.72,h*.70), fill=c['line'], width=lw)
    else:
        d.line((w*.80,h*.18,w*.80,h*.70,w*.28,h*.70), fill=c['line'], width=lw)
    return im


def generate_brand_assets(out_dir: Path):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}

    def save(rel, im, fmt=None, **kw):
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if fmt is None:
            fmt = Path(rel).suffix.lstrip('.').upper()
        if fmt == 'JPG':
            fmt = 'JPEG'
        if fmt == 'WEBP' and im.mode == 'RGBA':
            im.save(p, fmt, lossless=True, **kw)
        else:
            im.convert('RGB' if fmt in ('JPEG','WEBP') else im.mode).save(p, fmt, **kw)
        files[str(p.relative_to(out_dir))] = p

    densities = {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
    adaptive = {'mdpi':108,'hdpi':162,'xhdpi':216,'xxhdpi':324,'xxxhdpi':432}
    for den, size in densities.items():
        save(f'res/mipmap-{den}-v4/ic_launcher.webp', _draw_mark(size, dark=True, transparent=False), 'WEBP')
        mark = _draw_mark(size, dark=True, transparent=True)
        mask = Image.new('L', (size,size), 0)
        ImageDraw.Draw(mask).ellipse((0,0,size-1,size-1), fill=255)
        bg = Image.new('RGBA', (size,size), _palette(True)['bg'])
        bg.alpha_composite(mark)
        bg.putalpha(mask)
        save(f'res/mipmap-{den}-v4/ic_launcher_round.webp', bg, 'WEBP')
    for den, size in adaptive.items():
        save(f'res/mipmap-{den}-v4/ic_launcher_background.webp', Image.new('RGBA',(size,size),_palette(True)['bg']), 'WEBP')
        save(f'res/mipmap-{den}-v4/ic_launcher_foreground.webp', _draw_mark(size, dark=True, transparent=True), 'WEBP')

    save('res/drawable/logo.png', _draw_mark(256, dark=False, transparent=True), 'PNG')
    save('res/drawable/logo_dark.png', _draw_mark(256, dark=True, transparent=True), 'PNG')
    save('res/drawable/logo_white.png', _draw_mark(256, dark=True, transparent=True), 'PNG')

    W,H = 1000,200
    c = _palette(True)
    im = _gradient((W,H), (16,23,28,255), (24,33,39,255))
    d = ImageDraw.Draw(im)
    mark = _draw_mark(132, dark=True, transparent=True)
    im.alpha_composite(mark, (34,34))
    d.text((205,42), 'RuneSheet RU', font=_font(62), fill=c['text'])
    d.text((209,119), 'персонаж • правила • сессия', font=_font(24,bold=False), fill=c['muted'])
    save('res/drawable/logo_red.jpg', im, 'JPEG', quality=94)

    for dark, suf in [(False,''),(True,'_dark')]:
        save(f'res/drawable-xxhdpi-v4/frontpage_new_character{suf}_horizontal.png', _front_card(1280,548,'НОВЫЙ ПЕРСОНАЖ','Начать сборку героя','СОЗДАТЬ',dark=dark), 'PNG')
        save(f'res/drawable-xxhdpi-v4/frontpage_load_character{suf}_horizontal.png', _front_card(1280,548,'МОИ ПЕРСОНАЖИ','Продолжить или импортировать','ОТКРЫТЬ',dark=dark), 'PNG')
    save('res/drawable/img_new.jpg', _portrait_card(300,500,'НОВЫЙ','СОЗДАТЬ'), 'JPEG', quality=94)
    save('res/drawable/img_load.jpg', _portrait_card(300,500,'ПЕРСОНАЖИ','ОТКРЫТЬ'), 'JPEG', quality=94)

    save('res/drawable-xxhdpi-v4/parchment.jpg', _paper_background(1280,1920), 'JPEG', quality=94)
    save('res/drawable/portrait_blank.jpg', _blank_portrait(208,312), 'JPEG', quality=92)
    save('assets/portrait_blank.jpg', _blank_portrait(208,312), 'JPEG', quality=92)

    save('res/drawable/brace_top.png', _brace(451,160,'top'), 'PNG')
    save('res/drawable/brace_top_left.png', _brace(133,100,'tl'), 'PNG')
    save('res/drawable/brace_top_right.png', _brace(133,100,'tr'), 'PNG')
    save('res/drawable/brace_bottom_left.png', _brace(133,100,'bl'), 'PNG')
    save('res/drawable/brace_bottom_right.png', _brace(133,100,'br'), 'PNG')

    strip = Image.new('RGBA', (512,135), (250,251,251,245))
    sd = ImageDraw.Draw(strip)
    cc = _palette(False)
    sd.rounded_rectangle((4,4,507,130), radius=14, outline=cc['line'], width=2)
    sd.line((28,20,484,20), fill=cc['accent'], width=2)
    save('res/drawable/scroll_background.png', strip, 'PNG')

    prev = _paper_background(400,300)
    pd = ImageDraw.Draw(prev)
    pc = _palette(False)
    for y, label in [(42,'Имя персонажа'),(105,'Народ'),(168,'Класс')]:
        pd.rounded_rectangle((28,y,372,y+48), radius=10, fill=pc['panel'], outline=pc['line'], width=2)
        pd.text((48,y+12), label, font=_font(18,bold=False), fill=pc['text'])
    pd.rounded_rectangle((28,238,372,278), radius=10, fill=pc['panel2'])
    pd.text((150,247), 'УРОВЕНЬ 1', font=_font(16), fill=pc['text'])
    save('res/drawable/theme_picture_ornate.jpg', prev, 'JPEG', quality=94)

    return files
