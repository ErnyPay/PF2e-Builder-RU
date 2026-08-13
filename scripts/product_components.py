from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path
from PIL import Image

from manifest_patch import NO_INDEX, _find_manifest_pool, _iter_start_elements, _put_u32

TYPE_COLOR = 0x1C
TYPE_DIMENSION = 0x05
ADVIEW_ID = 0x7F090044

PANEL = 0xFFFFFFFF
PANEL_ALT = 0xFFEDF2F2
LINE = 0xFFD3DBDD
TEAL = 0xFF26958F
TEAL_RIPPLE = 0x3326958F
DARK_PANEL = 0xFF1F2D32
DARK_ALT = 0xFF2A393E
DARK_LINE = 0xFF46545A
DARK_RIPPLE = 0x3348BEB8
DISABLED = 0xFFE6EBEC
DISABLED_LINE = 0xFFC8D0D2
ERROR = 0xFFB83B3B

PATCH_MODES = {
    'res/drawable/background_ability_table_item.xml': 'ability',
    'res/drawable/background_drawdown.xml': 'drawdown',
    'res/drawable/background_drawdown_illegal.xml': 'drawdown_illegal',
    'res/drawable/border_dark.xml': 'border_dark',
    'res/drawable/border_dark_nofill.xml': 'border_dark',
    'res/drawable/border_filter_on.xml': 'filter_on',
    'res/drawable/custom_button_background.xml': 'light_button',
    'res/drawable/custom_button_background_cantrips_ornate.xml': 'light_button',
    'res/drawable/custom_button_background_cast.xml': 'light_button',
    'res/drawable/custom_button_background_cast_off.xml': 'light_off',
    'res/drawable/custom_button_background_dark.xml': 'dark_button',
    'res/drawable/custom_button_background_dark_off.xml': 'dark_off',
    'res/drawable/custom_button_background_dark_withpadding.xml': 'dark_button',
    'res/drawable/custom_button_background_disabled.xml': 'light_disabled',
    'res/drawable/custom_button_background_disabled_dark.xml': 'dark_off',
    'res/drawable/custom_button_background_heighten.xml': 'light_off',
    'res/drawable/custom_button_background_heighten_selected.xml': 'selected',
    'res/drawable/custom_button_background_nodecoration.xml': 'light_button',
    'res/drawable/custom_button_background_nodecoration_dark.xml': 'dark_button',
    'res/drawable/custom_button_background_nodecoration_off.xml': 'light_off',
    'res/drawable/custom_button_background_spellinfo.xml': 'light_button',
    'res/drawable/custom_button_background_spellinfo_off.xml': 'light_off',
    'res/drawable/dialog_menu_selected.xml': 'dialog_selected',
    'res/drawable/dialog_menu_selected_dark.xml': 'dialog_selected_dark',
    'res/drawable/rounded_rectangle.xml': 'rounded',
    'res/drawable/rounded_rectangle_darkmode_bordered.xml': 'rounded_dark',
    'res/drawable/rounded_rectangle_transparent_inside.xml': 'rounded_transparent',
    'res/drawable/rounded_rectangle_white_solid.xml': 'rounded_white',
    'res/drawable/theme_plain_background.xml': 'plain_bg',
    'res/drawable/custom_progress_bar.xml': 'progress',
    'res/drawable/custom_progress_bar_dark.xml': 'progress',
    'res/drawable/custom_progress_bar_plain.xml': 'progress',
}

ICON_NAMES = {
    'icon_ancestry.png','icon_ancestry_dark.png','icon_background.png','icon_background_dark.png',
    'icon_class.png','icon_class_dark.png','icon_general.png','icon_general_dark.png','icon_skill.png','icon_skill_dark.png',
    'icon_spellslot.png','icon_spellslot_dark.png','icon_spellslot_off.png','icon_spellslot_off_dark.png',
    'icon_known.png','icon_known_dark.png','icon_known_off.png','icon_known_off_dark.png',
    'icon_known_witch.png','icon_known_witch_dark.png','icon_known_witch_off.png','icon_known_witch_off_dark.png',
    'icon_d4.png','icon_d6.png','icon_d8.png','icon_d10.png','icon_d12.png','icon_d20.png',
    'icon_d4_dark.png','icon_d6_dark.png','icon_d8_dark.png','icon_d10_dark.png','icon_d12_dark.png','icon_d20_dark.png',
    'icon_trained.png','icon_expert.png','icon_master.png','icon_legendary.png',
    'icon_trained_dark.png','icon_expert_dark.png','icon_master_dark.png','icon_legendary_dark.png',
    'proficiency_untrained.png','proficiency_trained.png','proficiency_expert.png','proficiency_master.png','proficiency_legendary.png','proficiency_mythic.png',
    'proficiency_untrained_dark.png','proficiency_trained_dark.png','proficiency_expert_dark.png','proficiency_master_dark.png','proficiency_legendary_dark.png','proficiency_mythic_dark.png',
    'icon_cog.png','icon_boost.png','icon_flaw.png','icon_ability_boost.png','icon_ability_boost_ticked.png',
    'icon_add.png','icon_subtract.png','icon_cancel.png','icon_create.png','icon_open.png','icon_print.png',
}


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def patch_component_drawable(blob: bytes, mode: str) -> bytes:
    p = _find_manifest_pool(blob)
    out = bytearray(blob)
    solid_index = 0
    for _, tag, attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,data) for a,n,raw,dt,data in attrs}
        if tag == 'solid':
            solid_index += 1
            color = None
            if mode in ('light_button','rounded','ability','plain_bg'): color = PANEL
            elif mode == 'light_off': color = PANEL_ALT
            elif mode == 'light_disabled': color = DISABLED
            elif mode == 'dark_button': color = DARK_PANEL
            elif mode == 'dark_off': color = DARK_ALT
            elif mode == 'selected': color = TEAL
            elif mode == 'dialog_selected': color = PANEL if solid_index == 1 else TEAL
            elif mode == 'dialog_selected_dark': color = DARK_PANEL if solid_index == 1 else TEAL
            elif mode == 'drawdown': color = PANEL if solid_index == 1 else TEAL
            elif mode == 'drawdown_illegal': color = PANEL if solid_index == 1 else ERROR
            elif mode == 'border_dark': color = DARK_PANEL
            elif mode == 'filter_on': color = PANEL_ALT
            elif mode == 'rounded_dark': color = DARK_PANEL
            elif mode == 'rounded_white': color = PANEL
            if color is not None and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, color)
        elif tag == 'stroke':
            color = None
            if mode in ('light_button','rounded','ability','drawdown','rounded_white','rounded_transparent'): color = LINE
            elif mode in ('light_off','light_disabled'): color = DISABLED_LINE
            elif mode in ('dark_button','dark_off','border_dark','rounded_dark'): color = DARK_LINE
            elif mode in ('selected','filter_on'): color = TEAL
            elif mode == 'drawdown_illegal': color = ERROR
            if color is not None and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, color)
            if 'width' in amap and mode != 'border_dark': _set_typed(out, amap['width'][0], TYPE_DIMENSION, 0x101)
        elif tag == 'ripple' and 'color' in amap:
            _set_typed(out, amap['color'][0], TYPE_COLOR, DARK_RIPPLE if mode.startswith('dark') else TEAL_RIPPLE)
        elif tag == 'gradient':
            if 'startColor' in amap: _set_typed(out, amap['startColor'][0], TYPE_COLOR, TEAL)
            if 'endColor' in amap: _set_typed(out, amap['endColor'][0], TYPE_COLOR, 0x0026958F)
        elif tag == 'corners' and 'radius' in amap and mode not in ('drawdown','drawdown_illegal'):
            _set_typed(out, amap['radius'][0], TYPE_DIMENSION, 0xA01)
    return bytes(out)


def patch_activity_main(blob: bytes) -> bytes:
    p = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,data) for a,n,raw,dt,data in attrs}
        if amap.get('id',(None,None,None,None))[3] == ADVIEW_ID:
            for key in ('layout_width','layout_height'):
                if key in amap: _set_typed(out, amap[key][0], TYPE_DIMENSION, 0x00000001)
    return bytes(out)


def recolor_icon(data: bytes, dark_name: bool) -> bytes:
    im = Image.open(BytesIO(data)).convert('RGBA')
    px = im.load(); w,h = im.size
    teal = (72,190,184) if dark_name else (38,149,143)
    graphite = (29,39,44)
    for y in range(h):
        for x in range(w):
            r,g,b,a = px[x,y]
            if a == 0: continue
            mx=max(r,g,b); mn=min(r,g,b)
            if r >= 70 and r > g*1.35 and r > b*1.35 and g < 120 and b < 120:
                lum=max(.35,min(1.0,mx/125.0)); px[x,y]=(int(teal[0]*lum),int(teal[1]*lum),int(teal[2]*lum),a)
            elif not dark_name and mx < 55 and mn < 55:
                px[x,y]=(*graphite,a)
    out=BytesIO(); im.save(out,'PNG'); return out.getvalue()
