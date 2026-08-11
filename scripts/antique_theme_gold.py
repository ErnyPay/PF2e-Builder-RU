from __future__ import annotations

import struct

import antique_theme as base
from antique_theme import recolor_icon_antique, restyle_generated_brand_antique
from manifest_patch import NO_INDEX, _find_manifest_pool, _iter_start_elements, _put_u32

TYPE_DIMENSION = 0x05
TYPE_INT_DEC = 0x10
TYPE_COLOR = 0x1C

# Brighter antique-book palette. Burgundy is intentionally absent.
INK = 0xFF2A2118
LEVEL_BLACK = 0xFF000000
BRASS = 0xFFB88A3F
BRASS_LIGHT = 0xFFE3C16F
BRASS_DARK = 0xFF8A6227
MENU_GOLD = 0xFFDDBB68
MENU_GOLD_DARK = 0xFFC99A45
TOPNAV_BRONZE = 0xFF805A2C
SELECTED_DARK = 0xFF4D351E
BADGE_FILL = 0xFFF0D48A

ID_BUILD_LEVEL = base.ID_BUILD_LEVEL
ID_PLAY_LEVEL = base.ID_PLAY_LEVEL
RID_LEVEL_BADGE = base.RID_LEVEL_BADGE


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def patch_level_layout_antique(blob: bytes, *, play: bool) -> bytes:
    """Keep Russian УРОВЕНЬ N readable: wrap_content, padding, black ink and badge."""
    target = ID_PLAY_LEVEL if play else ID_BUILD_LEVEL
    blob = base._add_background_attribute(blob, target, RID_LEVEL_BADGE)
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'TextView':
            continue
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if amap.get('id', (None, None, None, None))[3] != target:
            continue
        if 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, LEVEL_BLACK)
        if 'textSize' in amap:
            _set_typed(out, amap['textSize'][0], TYPE_DIMENSION, 0x1001)  # 16sp
        if 'padding' in amap:
            _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x801)  # 8dp
        if 'layout_width' in amap:
            _set_typed(out, amap['layout_width'][0], TYPE_INT_DEC, 0xFFFFFFFE)  # wrap_content
    return bytes(out)


def patch_shape_antique(blob: bytes, *, fill: int, stroke: int, radius_dp: int = 10) -> bytes:
    return base.patch_shape_antique(blob, fill=fill, stroke=stroke, radius_dp=radius_dp)


def patch_button_antique(blob: bytes) -> bytes:
    """Bright honey-gold menu surface and dark text are always patched together."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    surface = False
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if not surface and tag in ('LinearLayout', 'RelativeLayout', 'FrameLayout') and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, MENU_GOLD)
            surface = True
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, INK)
    if not surface:
        raise ValueError('button surface missing')
    return bytes(out)


def patch_nav_header_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if tag == 'LinearLayout' and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, MENU_GOLD_DARK)
        elif tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, INK)
    return bytes(out)


def patch_subheader_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, BRASS_DARK)
    return bytes(out)


def patch_topnav_antique(blob: bytes) -> bytes:
    """Brighten the main navigation strip while retaining contrast for inherited white labels."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if 'background' in amap and amap['background'][2] == TYPE_COLOR:
            if amap['background'][3] in (0xFF172429, 0xFF223238, base.WALNUT_DEEP):
                _set_typed(out, amap['background'][0], TYPE_COLOR, TOPNAV_BRONZE)
    return bytes(out)
