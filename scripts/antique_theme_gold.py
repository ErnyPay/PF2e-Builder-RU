from __future__ import annotations

import struct

import antique_theme as base
from antique_theme import recolor_icon_antique, restyle_generated_brand_antique
from manifest_patch import NO_INDEX, _find_manifest_pool, _iter_start_elements, _put_u32

TYPE_NULL = 0x00
TYPE_REFERENCE = 0x01
TYPE_DIMENSION = 0x05
TYPE_INT_DEC = 0x10
TYPE_COLOR = 0x1C

# Brighter antique palette. Product burgundy is intentionally absent.
INK = 0xFF1D1812
PRIMARY_BRONZE = 0xFF8C672F
PRIMARY_DARK = 0xFF4A3520
PRIMARY_MID = 0xFF6D4E25
PRIMARY_FIFTY = 0xFFB99458
ACCENT_GOLD = 0xFFD6A84C
ACCENT_FADE = 0xFFF3E8CF
FADED = 0xFFE7D5AC
BRASS = ACCENT_GOLD
BRASS_LIGHT = 0xFFE3C16F
BRASS_DARK = PRIMARY_BRONZE
MENU_GOLD = 0xFFDDBB68
MENU_GOLD_DARK = 0xFFC99A45
TOPNAV_BRONZE = PRIMARY_BRONZE
SELECTED_DARK = ACCENT_GOLD
BADGE_FILL = 0xFFF4DFAA
LEVEL_TEXT_RESOURCE = 0x7F05031A  # standard_text = black in pinned polished baseline

ID_BUILD_LEVEL = base.ID_BUILD_LEVEL
ID_PLAY_LEVEL = base.ID_PLAY_LEVEL
RID_LEVEL_BADGE = base.RID_LEVEL_BADGE

PRODUCT_COLORS = {
    'colorAccent': ACCENT_GOLD,
    'colorAccentFade': ACCENT_FADE,
    'colorPrimary': PRIMARY_BRONZE,
    'colorPrimaryDark': PRIMARY_DARK,
    'colorPrimaryFifty': PRIMARY_FIFTY,
    'colorPrimaryNotAsDark': PRIMARY_MID,
    'colorPrimaryVeryFaded': FADED,
    'colorBrace': 0x80D6A84C,
    'header_build': PRIMARY_BRONZE,
    'header_play': PRIMARY_BRONZE,
    'ic_launcher_background': PRIMARY_BRONZE,
    'traitColor': PRIMARY_MID,
}

LEGACY_DIRECT_COLORS = {
    0xFF500000: ACCENT_GOLD,
    0xFF2F0000: PRIMARY_MID,
    0xFF140000: PRIMARY_DARK,
    0xFF794F4F: PRIMARY_FIFTY,
    0xFFB89F95: FADED,
    0x80500000: 0x80D6A84C,
}

APP_ROUND_DRAWABLES = {
    'res/drawable/background_ability_table_item.xml': 14,
    'res/drawable/background_drawdown.xml': 14,
    'res/drawable/background_drawdown_illegal.xml': 14,
    'res/drawable/background_topnav_slider.xml': 18,
    'res/drawable/border_filter_on.xml': 14,
    'res/drawable/custom_button_background.xml': 18,
    'res/drawable/custom_button_background_cantrips_ornate.xml': 18,
    'res/drawable/custom_button_background_cast.xml': 18,
    'res/drawable/custom_button_background_cast_off.xml': 18,
    'res/drawable/custom_button_background_dark.xml': 18,
    'res/drawable/custom_button_background_dark_off.xml': 18,
    'res/drawable/custom_button_background_dark_withpadding.xml': 18,
    'res/drawable/custom_button_background_disabled.xml': 18,
    'res/drawable/custom_button_background_disabled_dark.xml': 18,
    'res/drawable/custom_button_background_heighten.xml': 16,
    'res/drawable/custom_button_background_heighten_selected.xml': 16,
    'res/drawable/custom_button_background_nodecoration_off.xml': 18,
    'res/drawable/custom_button_background_spellinfo.xml': 18,
    'res/drawable/custom_button_background_spellinfo_off.xml': 18,
    'res/drawable/rounded_rectangle.xml': 16,
    'res/drawable/rounded_rectangle_darkmode_bordered.xml': 16,
    'res/drawable/rounded_rectangle_transparent_inside.xml': 16,
    'res/drawable/rounded_rectangle_white_solid.xml': 16,
    'res/drawable/test_level_drawable.xml': 22,
}


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _read_pool(blob: bytes | bytearray, off: int) -> tuple[list[str], int]:
    typ, hs, size = struct.unpack_from('<HHI', blob, off)
    if typ != 0x0001:
        raise ValueError('not a resource string pool')
    sc, _, flags, strings_start, _ = struct.unpack_from('<IIIII', blob, off + 8)
    offsets = [struct.unpack_from('<I', blob, off + hs + 4 * i)[0] for i in range(sc)]
    base = off + strings_start
    strings: list[str] = []
    for rel in offsets:
        q = base + rel
        if flags & 0x100:
            x = blob[q]; q += 1
            if x & 0x80: q += 1
            x = blob[q]; q += 1
            if x & 0x80:
                byte_len = ((x & 0x7F) << 8) | blob[q]; q += 1
            else:
                byte_len = x
            strings.append(bytes(blob[q:q + byte_len]).decode('utf-8', 'replace'))
        else:
            x = struct.unpack_from('<H', blob, q)[0]; q += 2
            if x & 0x8000:
                y = struct.unpack_from('<H', blob, q)[0]; q += 2
                char_len = ((x & 0x7FFF) << 16) | y
            else:
                char_len = x
            strings.append(bytes(blob[q:q + char_len * 2]).decode('utf-16le', 'replace'))
    return strings, size


def patch_product_color_table(blob: bytes) -> bytes:
    """Patch only RuneSheet/Pathbuilder product colors, not the whole Material palette."""
    out = bytearray(blob)
    root_type, root_hs, root_size = struct.unpack_from('<HHI', out, 0)
    if root_type != 0x0002:
        raise ValueError('unexpected resources.arsc root')
    off = root_hs
    _, global_pool_size = _read_pool(out, off)
    off += global_pool_size
    patched: set[str] = set()
    while off < root_size:
        chunk_type, header_size, chunk_size = struct.unpack_from('<HHI', out, off)
        if chunk_type == 0x0200:
            type_strings_off = struct.unpack_from('<I', out, off + 268)[0]
            key_strings_off = struct.unpack_from('<I', out, off + 276)[0]
            types, _ = _read_pool(out, off + type_strings_off)
            keys, _ = _read_pool(out, off + key_strings_off)
            q = off + header_size
            while q < off + chunk_size:
                child_type, child_header, child_size = struct.unpack_from('<HHI', out, q)
                if child_type == 0x0201:
                    type_id = out[q + 8]
                    entry_count = struct.unpack_from('<I', out, q + 12)[0]
                    entries_start = struct.unpack_from('<I', out, q + 16)[0]
                    type_name = types[type_id - 1] if 0 < type_id <= len(types) else ''
                    if type_name == 'color':
                        for i in range(entry_count):
                            rel = struct.unpack_from('<I', out, q + child_header + 4 * i)[0]
                            if rel == 0xFFFFFFFF:
                                continue
                            entry = q + entries_start + rel
                            entry_size, flags, key_index = struct.unpack_from('<HHI', out, entry)
                            if flags & 1 or key_index >= len(keys):
                                continue
                            name = keys[key_index]
                            if name not in PRODUCT_COLORS:
                                continue
                            value_off = entry + entry_size
                            dtype = out[value_off + 3]
                            if 0x1C <= dtype <= 0x1F:
                                struct.pack_into('<I', out, value_off + 4, PRODUCT_COLORS[name])
                                patched.add(name)
                q += child_size
        off += chunk_size
    missing = set(PRODUCT_COLORS) - patched
    if missing:
        raise ValueError(f'missing product color resources: {sorted(missing)}')
    return bytes(out)


def patch_direct_legacy_product_colors(blob: bytes) -> bytes:
    """Replace only exact old product reds compiled directly into app XML."""
    try:
        pool = _find_manifest_pool(blob)
    except Exception:
        return blob
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        for attr, _, _, dtype, data in attrs:
            if 0x1C <= dtype <= 0x1F and data in LEGACY_DIRECT_COLORS:
                _set_typed(out, attr, TYPE_COLOR, LEGACY_DIRECT_COLORS[data])
    return bytes(out)


def patch_rounding(blob: bytes, radius_dp: int) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    value = (radius_dp << 8) | 1
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'corners':
            continue
        for attr, name, _, _, _ in attrs:
            if name == 'radius' or name.endswith('Radius'):
                _set_typed(out, attr, TYPE_DIMENSION, value)
    return bytes(out)


def patch_level_layout_antique(blob: bytes, *, play: bool) -> bytes:
    """Hard override for Russian УРОВЕНЬ N chips.

    Use a known-black color resource, remove the inherited play style, use
    wrap_content in both dimensions, and keep a rounded badge.
    """
    target = ID_PLAY_LEVEL if play else ID_BUILD_LEVEL
    blob = base._add_background_attribute(blob, target, RID_LEVEL_BADGE)
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    found = False
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'TextView':
            continue
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if amap.get('id', (None, None, None, None))[3] != target:
            continue
        found = True
        if 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_REFERENCE, LEVEL_TEXT_RESOURCE)
        if 'style' in amap:
            _set_typed(out, amap['style'][0], TYPE_NULL, 0)
        if 'textSize' in amap:
            _set_typed(out, amap['textSize'][0], TYPE_DIMENSION, 0x1101)  # 17sp
        if 'padding' in amap:
            _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x0A01)  # 10dp
        if 'layout_width' in amap:
            _set_typed(out, amap['layout_width'][0], TYPE_INT_DEC, 0xFFFFFFFE)
        if 'layout_height' in amap:
            _set_typed(out, amap['layout_height'][0], TYPE_INT_DEC, 0xFFFFFFFE)
    if not found:
        raise ValueError('level navigation TextView not found')
    return bytes(out)


def patch_shape_antique(blob: bytes, *, fill: int, stroke: int, radius_dp: int = 18) -> bytes:
    return base.patch_shape_antique(blob, fill=fill, stroke=stroke, radius_dp=radius_dp)


def patch_button_antique(blob: bytes) -> bytes:
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
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, PRIMARY_BRONZE)
    return bytes(out)


def patch_topnav_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if 'background' in amap and amap['background'][2] == TYPE_COLOR:
            if amap['background'][3] in (0xFF172429, 0xFF223238, base.WALNUT_DEEP, 0xFF805A2C):
                _set_typed(out, amap['background'][0], TYPE_COLOR, TOPNAV_BRONZE)
    return bytes(out)
