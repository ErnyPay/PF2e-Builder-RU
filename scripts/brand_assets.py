from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
]
FONT_REGULAR = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
]

def _font(size:int, bold=True):
    candidates = FONT_CANDIDATES if bold else FONT_REGULAR
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def _palette(dark=True):
    if dark:
        return {
            'bg': (12, 20, 28, 255),
            'panel': (23, 35, 45, 255),
            'panel2': (31, 49, 61, 255),
            'cyan': (83, 213, 208, 255),
            'amber': (244, 180, 74, 255),
            'text': (239, 245, 247, 255),
            'muted': (157, 176, 184, 255),
        }
    return {
        'bg': (242, 246, 245, 255),
        'panel': (255, 255, 255, 255),
        'panel2': (225, 235, 233, 255),
        'cyan': (28, 132, 133, 255),
        'amber': (188, 120, 33, 255),
        'text': (25, 38, 44, 255),
        'muted': (92, 112, 119, 255),
    }

def _draw_sigil(size:int, *, transparent=False, dark=True):
    c=_palette(dark)
    im=Image.new('RGBA',(size,size),(0,0,0,0) if transparent else c['bg'])
    d=ImageDraw.Draw(im)
    cx=cy=size/2
    r=size*.31
    # Original rune/compass mark: concentric broken ring + four directional strokes.
    lw=max(2,size//32)
    d.rounded_rectangle((size*.12,size*.12,size*.88,size*.88), radius=size*.18,
                        fill=c['panel'], outline=c['panel2'], width=lw)
    box=(cx-r,cy-r,cx+r,cy+r)
    d.arc(box,18,150,fill=c['cyan'],width=lw*2)
    d.arc(box,198,330,fill=c['amber'],width=lw*2)
    inner=r*.50
    points=[]
    for k in range(8):
        a=math.radians(k*45-90)
        rr=inner*(1.0 if k%2==0 else .62)
        points.append((cx+math.cos(a)*rr,cy+math.sin(a)*rr))
    d.polygon(points,fill=None,outline=c['text'])
    d.line((cx,cy-inner*.95,cx,cy+inner*.95),fill=c['text'],width=lw)
    d.line((cx-inner*.95,cy,cx+inner*.95,cy),fill=c['text'],width=lw)
    dot=size*.035
    d.ellipse((cx-dot,cy-dot,cx+dot,cy+dot),fill=c['cyan'])
    return im

def _fit_text(draw,text,font,max_width):
    while font.size>10 and draw.textbbox((0,0),text,font=font)[2] > max_width:
        font=_font(font.size-2, bold=True)
    return font

def _gradient(size, top, bottom):
    w,h=size
    im=Image.new('RGB',size,top[:3])
    px=im.load()
    for y in range(h):
        t=y/max(1,h-1)
        row=tuple(round(top[i]*(1-t)+bottom[i]*t) for i in range(3))
        for x in range(w): px[x,y]=row
    return im

def _grid_overlay(im, accent, spacing=64, alpha=24):
    ov=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    w,h=im.size
    col=accent[:3]+(alpha,)
    for x in range(-h,w+h,spacing): d.line((x,0,x-h,h),fill=col,width=1)
    for x in range(0,w+h,spacing): d.line((x,0,x-h,h),fill=col,width=1)
    return Image.alpha_composite(im.convert('RGBA'),ov)

def _front_card(w,h,title,subtitle,kind='new',dark=False):
    c=_palette(True if dark else False)
    top = (13,28,36,255) if dark else (229,240,238,255)
    bottom = (27,48,58,255) if dark else (248,250,249,255)
    im=_gradient((w,h),top,bottom).convert('RGBA')
    im=_grid_overlay(im,c['cyan'],spacing=max(40,w//14),alpha=28 if dark else 18)
    d=ImageDraw.Draw(im)
    sig=_draw_sigil(int(h*.72),transparent=True,dark=dark)
    im.alpha_composite(sig,(int(w*.07),int(h*.14)))
    x=int(w*.43)
    d.line((x,int(h*.14),x,int(h*.86)),fill=c['cyan'],width=max(2,w//320))
    f=_fit_text(d,title,_font(int(h*.105)),int(w*.49))
    f2=_font(int(h*.045),bold=False)
    d.text((x+int(w*.045),int(h*.30)),title,font=f,fill=c['text'])
    d.text((x+int(w*.045),int(h*.52)),subtitle,font=f2,fill=c['muted'])
    pill='СОЗДАТЬ' if kind=='new' else 'ОТКРЫТЬ'
    fp=_font(int(h*.036))
    bx=x+int(w*.045); by=int(h*.68)
    tb=d.textbbox((0,0),pill,font=fp); tw=tb[2]-tb[0]; th=tb[3]-tb[1]
    d.rounded_rectangle((bx,by,bx+tw+36,by+th+22),radius=16,fill=c['cyan'])
    d.text((bx+18,by+7),pill,font=fp,fill=(9,24,28,255))
    return im

def _portrait_card(w,h,title,kind='new'):
    c=_palette(False)
    im=_gradient((w,h),(235,243,241,255),(250,251,249,255)).convert('RGBA')
    im=_grid_overlay(im,c['cyan'],spacing=44,alpha=15)
    d=ImageDraw.Draw(im)
    sig=_draw_sigil(int(w*.68),transparent=True,dark=False)
    im.alpha_composite(sig,(int(w*.16),int(h*.12)))
    f=_fit_text(d,title,_font(int(w*.12)),int(w*.82))
    box=d.textbbox((0,0),title,font=f); tw=box[2]-box[0]
    d.text(((w-tw)/2,int(h*.68)),title,font=f,fill=c['text'])
    sub='СОЗДАТЬ' if kind=='new' else 'ОТКРЫТЬ'
    fs=_font(int(w*.07),bold=False); box=d.textbbox((0,0),sub,font=fs); tw=box[2]-box[0]
    d.text(((w-tw)/2,int(h*.82)),sub,font=fs,fill=c['cyan'])
    return im

def _paper_background(w,h):
    im=_gradient((w,h),(247,249,248,255),(233,240,238,255)).convert('RGBA')
    d=ImageDraw.Draw(im)
    col=(47,130,130,18)
    step=96
    for y in range(0,h,step):
        for x in range(0,w,step):
            d.ellipse((x-2,y-2,x+2,y+2),fill=col)
    return im

def _blank_portrait(w,h):
    c=_palette(False); im=_paper_background(w,h); d=ImageDraw.Draw(im)
    cx=w/2
    d.ellipse((cx-w*.12,h*.18,cx+w*.12,h*.42),fill=(168,186,187,255))
    d.rounded_rectangle((w*.22,h*.43,w*.78,h*.86),radius=w*.18,fill=(168,186,187,255))
    sig=_draw_sigil(int(w*.22),transparent=True,dark=False); im.alpha_composite(sig,(int(w*.39),int(h*.62)))
    return im

def _action_icon(size,label,dark=False):
    c=_palette(dark); im=Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(im)
    pad=size*.10
    d.rounded_rectangle((pad,pad,size-pad,size-pad),radius=size*.25,fill=c['panel'],outline=c['cyan'],width=max(2,size//18))
    f=_font(int(size*.42)); box=d.textbbox((0,0),label,font=f); tw=box[2]-box[0]; th=box[3]-box[1]
    d.text(((size-tw)/2,(size-th)/2-size*.05),label,font=f,fill=c['text'])
    return im

def generate_brand_assets(out_dir: Path):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    densities={'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
    adaptive={'mdpi':108,'hdpi':162,'xhdpi':216,'xxhdpi':324,'xxxhdpi':432}
    files={}
    def save(rel,im,fmt=None,**kw):
        p=out_dir/rel; p.parent.mkdir(parents=True,exist_ok=True)
        if fmt is None: fmt=Path(rel).suffix.lstrip('.').upper()
        if fmt=='JPG': fmt='JPEG'
        if fmt=='WEBP' and im.mode=='RGBA': im.save(p,fmt,lossless=True,**kw)
        else: im.convert('RGB' if fmt in ('JPEG','WEBP') else im.mode).save(p,fmt,**kw)
        files[str(p.relative_to(out_dir))]=p
    for den,size in densities.items():
        save(f'res/mipmap-{den}-v4/ic_launcher.webp',_draw_sigil(size), 'WEBP')
        mark=_draw_sigil(size,transparent=True,dark=True)
        circ=Image.new('L',(size,size),0); ImageDraw.Draw(circ).ellipse((0,0,size-1,size-1),fill=255)
        bg=Image.new('RGBA',(size,size),_palette(True)['bg']); bg.alpha_composite(mark); bg.putalpha(circ)
        save(f'res/mipmap-{den}-v4/ic_launcher_round.webp',bg,'WEBP')
    for den,size in adaptive.items():
        save(f'res/mipmap-{den}-v4/ic_launcher_background.webp',Image.new('RGBA',(size,size),_palette(True)['bg']),'WEBP')
        save(f'res/mipmap-{den}-v4/ic_launcher_foreground.webp',_draw_sigil(size,transparent=True,dark=True),'WEBP')
    for name,dark in [('logo.png',False),('logo_dark.png',True),('logo_white.png',True)]:
        save(f'res/drawable/{name}',_draw_sigil(256,transparent=True,dark=dark),'PNG')

    W,H=1000,200; c=_palette(True); im=_gradient((W,H),(10,18,26,255),(21,36,44,255)); im=_grid_overlay(im,c['cyan'],76,18); d=ImageDraw.Draw(im)
    mark=_draw_sigil(160,transparent=True,dark=True); im.alpha_composite(mark,(24,20))
    title='RuneSheet RU'; f=_font(70); d.text((215,34),title,font=f,fill=c['text'])
    sub='Персонаж • правила • сессия'; f2=_font(27,bold=False); d.text((219,120),sub,font=f2,fill=c['muted'])
    save('res/drawable/logo_red.jpg',im,'JPEG',quality=94)

    for dark,suf in [(False,''),(True,'_dark')]:
        save(f'res/drawable-xxhdpi-v4/frontpage_new_character{suf}_horizontal.png',_front_card(1280,548,'НОВЫЙ ПЕРСОНАЖ','Начать сборку героя','new',dark),'PNG')
        save(f'res/drawable-xxhdpi-v4/frontpage_load_character{suf}_horizontal.png',_front_card(1280,548,'МОИ ПЕРСОНАЖИ','Продолжить или импортировать','load',dark),'PNG')
    save('res/drawable/img_new.jpg',_portrait_card(300,500,'НОВЫЙ','new'),'JPEG',quality=94)
    save('res/drawable/img_load.jpg',_portrait_card(300,500,'ПЕРСОНАЖИ','load'),'JPEG',quality=94)

    save('res/drawable-xxhdpi-v4/parchment.jpg',_paper_background(1280,1920),'JPEG',quality=92)
    save('res/drawable/portrait_blank.jpg',_blank_portrait(208,312),'JPEG',quality=92)
    save('assets/portrait_blank.jpg',_blank_portrait(208,312),'JPEG',quality=92)

    def brace(w,h,side='top'):
        im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im); c=_palette(False)
        lw=max(2,min(w,h)//22); col=c['cyan']; col2=c['amber']
        if side=='top':
            y=int(h*.72); d.line((int(w*.08),y,int(w*.92),y),fill=col,width=lw)
            d.line((int(w*.18),y-int(h*.08),int(w*.82),y-int(h*.08)),fill=col2,width=max(1,lw//2))
            for x in (int(w*.08),int(w*.92)):
                d.ellipse((x-lw*2,y-lw*2,x+lw*2,y+lw*2),fill=col)
        elif side=='tl':
            d.line((w*.18,h*.82,w*.18,h*.28,w*.72,h*.28),fill=col,width=lw)
            d.line((w*.30,h*.70,w*.30,h*.42,w*.58,h*.42),fill=col2,width=max(1,lw//2))
        elif side=='tr':
            d.line((w*.82,h*.82,w*.82,h*.28,w*.28,h*.28),fill=col,width=lw)
            d.line((w*.70,h*.70,w*.70,h*.42,w*.42,h*.42),fill=col2,width=max(1,lw//2))
        elif side=='bl':
            d.line((w*.18,h*.18,w*.18,h*.72,w*.72,h*.72),fill=col,width=lw)
            d.line((w*.30,h*.30,w*.30,h*.58,w*.58,h*.58),fill=col2,width=max(1,lw//2))
        else:
            d.line((w*.82,h*.18,w*.82,h*.72,w*.28,h*.72),fill=col,width=lw)
            d.line((w*.70,h*.30,w*.70,h*.58,w*.42,h*.58),fill=col2,width=max(1,lw//2))
        return im
    save('res/drawable/brace_top.png',brace(451,160,'top'),'PNG')
    save('res/drawable/brace_top_left.png',brace(133,100,'tl'),'PNG')
    save('res/drawable/brace_top_right.png',brace(133,100,'tr'),'PNG')
    save('res/drawable/brace_bottom_left.png',brace(133,100,'bl'),'PNG')
    save('res/drawable/brace_bottom_right.png',brace(133,100,'br'),'PNG')
    strip=Image.new('RGBA',(512,135),(246,249,248,238)); sd=ImageDraw.Draw(strip); cc=_palette(False)
    sd.rounded_rectangle((4,4,507,130),radius=18,outline=cc['cyan'],width=3)
    sd.line((28,20,484,20),fill=cc['amber'],width=2)
    save('res/drawable/scroll_background.png',strip,'PNG')

    prev=_paper_background(400,300); pd=ImageDraw.Draw(prev); pc=_palette(False)
    for y,label in [(42,'Имя персонажа'),(105,'Народ'),(168,'Класс')]:
        pd.rounded_rectangle((28,y,372,y+48),radius=12,fill=pc['panel'],outline=pc['cyan'],width=2)
        pd.text((48,y+12),label,font=_font(18,bold=False),fill=pc['text'])
    pd.rounded_rectangle((28,238,372,278),radius=12,fill=pc['panel2'])
    pd.text((150,247),'УРОВЕНЬ 1',font=_font(16),fill=pc['text'])
    save('res/drawable/theme_picture_ornate.jpg',prev,'JPEG',quality=92)

    for rel,label,dark in [
        ('res/drawable/action_single.png','1',False),('res/drawable/action_double.png','2',False),
        ('res/drawable/action_triple.png','3',False),('res/drawable/action_reaction.png','R',False),
        ('res/drawable/action_free.png','F',False),
        ('assets/Images/Actions/action_single.png','1',False),('assets/Images/Actions/action_double.png','2',False),
        ('assets/Images/Actions/action_triple.png','3',False),('assets/Images/Actions/action_reaction.png','R',False),
        ('assets/Images/Actions/action_free.png','F',False),
    ]:
        dims={'action_single.png':(200,200),'action_double.png':(286,200),'action_triple.png':(375,200),'action_reaction.png':(200,200),'action_free.png':(200,200)}
        name=Path(rel).name; w,h=dims[name]
        icon=_action_icon(min(w,h),label,dark)
        canvas=Image.new('RGBA',(w,h),(0,0,0,0)); canvas.alpha_composite(icon,((w-icon.width)//2,(h-icon.height)//2))
        save(rel,canvas,'PNG')
    return files
