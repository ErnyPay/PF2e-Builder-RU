from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

CYAN = (28, 132, 133, 255)
AMBER = (188, 120, 33, 255)
INK = (25, 38, 44, 255)
PANEL = (255, 255, 255, 244)


def _diamond(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, *, fill, outline, width: int) -> None:
    pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=width, joint='curve')


def _action_pips(width: int, height: int, count: int) -> Image.Image:
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = height / 2
    r = min(height * 0.29, width / (count * 2.6))
    gap = r * 0.70
    total = count * (2 * r) + max(0, count - 1) * gap
    x0 = (width - total) / 2 + r
    for i in range(count):
        cx = x0 + i * (2 * r + gap)
        _diamond(d, cx, cy, r, fill=PANEL, outline=CYAN, width=max(3, int(height * .045)))
        inner = r * .42
        _diamond(d, cx, cy, inner, fill=CYAN, outline=CYAN, width=1)
    return im


def _reaction(width: int, height: int) -> Image.Image:
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = width/2, height/2
    rr = min(width, height) * .31
    lw = max(4, int(height * .055))
    d.arc((cx-rr, cy-rr, cx+rr, cy+rr), start=38, end=326, fill=AMBER, width=lw)
    # Arrow head at the end of the reaction loop.
    ax = cx + rr * .83
    ay = cy - rr * .56
    ah = rr * .24
    d.polygon([(ax, ay), (ax-ah*.92, ay-ah*.15), (ax-ah*.24, ay+ah*.82)], fill=AMBER)
    _diamond(d, cx, cy, rr * .48, fill=PANEL, outline=CYAN, width=max(3, lw//2))
    _diamond(d, cx, cy, rr * .19, fill=CYAN, outline=CYAN, width=1)
    return im


def _free(width: int, height: int) -> Image.Image:
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = width/2, height/2
    r = min(width, height) * .27
    lw = max(3, int(height * .04))
    _diamond(d, cx, cy, r, fill=(255,255,255,80), outline=CYAN, width=lw)
    # Four small rays make this visually distinct from a paid action pip.
    ray0, ray1 = r * 1.18, r * 1.48
    for dx, dy in [(0,-1),(1,0),(0,1),(-1,0)]:
        d.line((cx+dx*ray0, cy+dy*ray0, cx+dx*ray1, cy+dy*ray1), fill=AMBER, width=lw)
    d.ellipse((cx-r*.13, cy-r*.13, cx+r*.13, cy+r*.13), fill=AMBER)
    return im


def generate_action_assets(out_dir: Path):
    out_dir = Path(out_dir)
    dims = {
        'action_single.png': (200, 200),
        'action_double.png': (286, 200),
        'action_triple.png': (375, 200),
        'action_reaction.png': (200, 200),
        'action_free.png': (200, 200),
    }
    rel_roots = [Path('res/drawable'), Path('assets/Images/Actions')]
    generated = {}
    for name, (w, h) in dims.items():
        if name == 'action_single.png':
            icon = _action_pips(w, h, 1)
        elif name == 'action_double.png':
            icon = _action_pips(w, h, 2)
        elif name == 'action_triple.png':
            icon = _action_pips(w, h, 3)
        elif name == 'action_reaction.png':
            icon = _reaction(w, h)
        else:
            icon = _free(w, h)
        for root in rel_roots:
            p = out_dir / root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            icon.save(p, 'PNG')
            generated[str(p.relative_to(out_dir))] = p
    return generated
