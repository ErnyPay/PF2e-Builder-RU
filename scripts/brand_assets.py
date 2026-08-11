from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
]

def _font(size:int):
    for p in FONT_CANDIDATES:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def _palette():
    return {
        'bg': (18, 24, 38, 255),
        'panel': (32, 43, 64, 255),
        'accent': (89, 214, 193, 255),
        'accent2': (121, 126, 255, 255),
        'text': (244, 247, 252, 255),
    }

def _draw_mark(size:int, *, transparent=False):
    c=_palette(); im=Image.new('RGBA',(size,size),(0,0,0,0) if transparent else c['bg'])
    d=ImageDraw.Draw(im)
    m=size*0.15; cx=cy=size/2; r=size*0.34
    pts=[(cx,cy-r),(cx+r*0.95,cy-r*0.28),(cx+r*0.59,cy+r*0.85),(cx-r*0.59,cy+r*0.85),(cx-r*0.95,cy-r*0.28)]
    d.polygon(pts, fill=c['panel'], outline=c['accent'], width=max(2,size//32))
    # Facets: generic polyhedral/d20-inspired geometry, intentionally original.
    center=(cx,cy+size*0.03)
    for p in pts: d.line([center,p], fill=c['accent2'], width=max(1,size//64))
    f=_font(max(12,int(size*0.23)))
    text='P2'
    box=d.textbbox((0,0),text,font=f); tw=box[2]-box[0]; th=box[3]-box[1]
    d.text((cx-tw/2,cy-th/2-size*0.04),text,font=f,fill=c['text'])
    fr=_font(max(8,int(size*0.10)))
    ru='RU'; box=d.textbbox((0,0),ru,font=fr); tw=box[2]-box[0]
    d.rounded_rectangle((cx-tw/2-size*.04,cy+size*.14,cx+tw/2+size*.04,cy+size*.26),radius=size*.03,fill=c['accent'])
    d.text((cx-tw/2,cy+size*.145),ru,font=fr,fill=c['bg'])
    return im

def generate_brand_assets(out_dir: Path):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    densities={'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
    adaptive={'mdpi':108,'hdpi':162,'xhdpi':216,'xxhdpi':324,'xxxhdpi':432}
    files={}
    for den,size in densities.items():
        im=_draw_mark(size)
        p=out_dir/f'res/mipmap-{den}-v4/ic_launcher.webp'; p.parent.mkdir(parents=True,exist_ok=True); im.convert('RGB').save(p,'WEBP',lossless=True); files[str(p.relative_to(out_dir))]=p
        mask=Image.new('RGBA',(size,size),(0,0,0,0)); mark=_draw_mark(size,transparent=True)
        # circular icon variant
        circ=Image.new('L',(size,size),0); ImageDraw.Draw(circ).ellipse((0,0,size-1,size-1),fill=255)
        bg=Image.new('RGBA',(size,size),_palette()['bg']); bg.alpha_composite(mark); bg.putalpha(circ)
        p=out_dir/f'res/mipmap-{den}-v4/ic_launcher_round.webp'; p.parent.mkdir(parents=True,exist_ok=True); bg.save(p,'WEBP',lossless=True); files[str(p.relative_to(out_dir))]=p
    for den,size in adaptive.items():
        bg=Image.new('RGBA',(size,size),_palette()['bg'])
        p=out_dir/f'res/mipmap-{den}-v4/ic_launcher_background.webp'; p.parent.mkdir(parents=True,exist_ok=True); bg.save(p,'WEBP',lossless=True); files[str(p.relative_to(out_dir))]=p
        fg=_draw_mark(size,transparent=True)
        p=out_dir/f'res/mipmap-{den}-v4/ic_launcher_foreground.webp'; p.parent.mkdir(parents=True,exist_ok=True); fg.save(p,'WEBP',lossless=True); files[str(p.relative_to(out_dir))]=p
    for name in ['logo.png','logo_dark.png','logo_white.png']:
        p=out_dir/f'res/drawable/{name}'; p.parent.mkdir(parents=True,exist_ok=True); _draw_mark(256,transparent=(name!='logo_dark.png')).save(p,'PNG'); files[str(p.relative_to(out_dir))]=p

    # Wide banner used by the legacy UI.
    W,H=1000,200; c=_palette(); im=Image.new('RGB',(W,H),c['bg'][:3]); d=ImageDraw.Draw(im)
    mark=_draw_mark(180,transparent=True); im.paste(mark,(20,10),mark)
    title='PF2e Builder RU'; f=_font(70); d.text((220,38),title,font=f,fill=c['text'][:3])
    sub='Конструктор персонажей'; f2=_font(30); d.text((224,122),sub,font=f2,fill=c['accent'][:3])
    p=out_dir/'res/drawable/logo_red.jpg'; p.parent.mkdir(parents=True,exist_ok=True); im.save(p,'JPEG',quality=92); files[str(p.relative_to(out_dir))]=p
    return files
