from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

CYAN = (28, 132, 133, 255)
AMBER = (188, 120, 33, 255)
INK = (25, 38, 44, 255)
PANEL = (255, 255, 255, 244)
FACET = (217, 236, 233, 255)


def _diamond_points(cx: float, cy: float, r: float):
    return [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]


def _diamond(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, *, fill, outline, width: int) -> None:
    pts = _diamond_points(cx, cy, r)
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=outline, width=width, joint='curve')


def _faceted_action(width: int, height: int, tier: int) -> Image.Image:
    """Render one stable action glyph whose internal faceting indicates 1/2/3 actions.

    tier 1: simple gem
    tier 2: one central ridge / two major facets
    tier 3: full four-way cut with a small central facet
    """
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = width / 2, height / 2
    r = min(height * .31, width * .31)
    lw = max(3, int(height * .042))

    top, right, bottom, left = _diamond_points(cx, cy, r)
    _diamond(d, cx, cy, r, fill=PANEL, outline=CYAN, width=lw)

    if tier == 1:
        # A single clean central facet; deliberately sparse.
        _diamond(d, cx, cy, r * .34, fill=CYAN, outline=CYAN, width=1)
        return im

    if tier == 2:
        # Two large facets separated by a vertical ridge.
        d.polygon([top, right, bottom, (cx, cy)], fill=FACET)
        d.polygon([top, (cx, cy), bottom, left], fill=PANEL)
        d.line((top[0], top[1], cx, cy, bottom[0], bottom[1]), fill=CYAN, width=max(2, lw // 2))
        _diamond(d, cx, cy, r * .20, fill=CYAN, outline=CYAN, width=1)
        d.line(_diamond_points(cx, cy, r) + [top], fill=CYAN, width=lw, joint='curve')
        return im

    # Three actions: a more complex jewel cut, still one outer silhouette.
    center_r = r * .22
    ctop, cright, cbottom, cleft = _diamond_points(cx, cy, center_r)
    d.polygon([top, right, cright, ctop], fill=FACET)
    d.polygon([right, bottom, cbottom, cright], fill=PANEL)
    d.polygon([bottom, left, cleft, cbottom], fill=FACET)
    d.polygon([left, top, ctop, cleft], fill=PANEL)
    for vertex, inner in [(top, ctop), (right, cright), (bottom, cbottom), (left, cleft)]:
        d.line((vertex[0], vertex[1], inner[0], inner[1]), fill=CYAN, width=max(2, lw // 2))
    _diamond(d, cx, cy, center_r, fill=CYAN, outline=CYAN, width=max(1, lw // 3))
    d.line(_diamond_points(cx, cy, r) + [top], fill=CYAN, width=lw, joint='curve')
    return im


def _reaction(width: int, height: int) -> Image.Image:
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = width / 2, height / 2
    rr = min(width, height) * .32
    lw = max(4, int(height * .052))
    d.arc((cx-rr, cy-rr, cx+rr, cy+rr), start=42, end=326, fill=AMBER, width=lw)
    ax = cx + rr * .82
    ay = cy - rr * .55
    ah = rr * .23
    d.polygon([(ax, ay), (ax-ah*.95, ay-ah*.12), (ax-ah*.25, ay+ah*.84)], fill=AMBER)

    base = _faceted_action(width, height, 1)
    im.alpha_composite(base)
    return im


def _free(width: int, height: int) -> Image.Image:
    im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = width / 2, height / 2
    r = min(width, height) * .27
    lw = max(3, int(height * .04))
    _diamond(d, cx, cy, r, fill=(255, 255, 255, 64), outline=CYAN, width=lw)
    ray0, ray1 = r * 1.18, r * 1.48
    for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
        d.line((cx+dx*ray0, cy+dy*ray0, cx+dx*ray1, cy+dy*ray1), fill=AMBER, width=lw)
    _diamond(d, cx, cy, r * .16, fill=AMBER, outline=AMBER, width=1)
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
            icon = _faceted_action(w, h, 1)
        elif name == 'action_double.png':
            icon = _faceted_action(w, h, 2)
        elif name == 'action_triple.png':
            icon = _faceted_action(w, h, 3)
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
