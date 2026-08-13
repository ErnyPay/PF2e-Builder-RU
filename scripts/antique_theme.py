from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path
from PIL import Image

from manifest_patch import (
    NO_INDEX,
    TYPE_STRING,
    _find_manifest_pool,
    _iter_start_elements,
    _put_u32,
    _u16,
    _u32,
    build_string_pool,
)

TYPE_REFERENCE = 0x01
TYPE_DIMENSION = 0x05
TYPE_INT_DEC = 0x10
TYPE_COLOR = 0x1C

# Warm antique-book palette: parchment, walnut, oxblood and aged brass.
PARCHMENT_TEXT = 0xFFF4E8C8
WALNUT = 0xFF3A2A22
WALNUT_DEEP = 0xFF2A1E19
OXBLOOD = 0xFF582B2D
OXBLOOD_DARK = 0xFF3D2021
BRASS = 0xFFB38A52
BRASS_LIGHT = 0xFFD2AD6D
BRASS_DARK = 0xFF8B6637
BADGE_FILL = 0xAA3A2A22

ID_BUILD_LEVEL = 0x7F090456
ID_PLAY_LEVEL = 0x7F090510
RID_LEVEL_BADGE = 0x7F0701E3  # existing unused test_level_drawable
ANDROID_BACKGROUND = 0x010100D4


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _bump_string_index(out: bytearray, offset: int, inserted_at: int) -> None:
    value = _u32(out, offset)
    if value != NO_INDEX and value >= inserted_at:
        _put_u32(out, offset, value + 1)


def _resource_map(blob: bytes) -> list[int]:
    pool = _find_manifest_pool(blob)
    offset = pool.offset + pool.size
    typ, _, size = struct.unpack_from('<HHI', blob, offset)
    if typ != 0x0180:
        raise ValueError('binary XML has no resource map')
    return [_u32(blob, p) for p in range(offset + 8, offset + size, 4)]


def _insert_resource_name(blob: bytes, name: str, resource_id: int) -> bytes:
    pool = _find_manifest_pool(blob)
    if name in pool.strings:
        return blob

    map_offset = pool.offset + pool.size
    typ, _, map_size = struct.unpack_from('<HHI', blob, map_offset)
    if typ != 0x0180:
        raise ValueError('binary XML has no resource map')
    old_ids = [_u32(blob, p) for p in range(map_offset + 8, map_offset + map_size, 4)]
    insert_at = next((i for i, rid in enumerate(old_ids) if rid > resource_id), len(old_ids))

    strings = list(pool.strings)
    strings.insert(insert_at, name)
    new_pool = build_string_pool(strings, pool.flags)
    tmp = bytearray(blob[:pool.offset] + new_pool + blob[pool.offset + pool.size:])
    _put_u32(tmp, 4, _u32(blob, 4) + len(new_pool) - pool.size)

    map_offset = pool.offset + len(new_pool)
    _, _, map_size = struct.unpack_from('<HHI', tmp, map_offset)
    ids = [_u32(tmp, p) for p in range(map_offset + 8, map_offset + map_size, 4)]
    ids.insert(insert_at, resource_id)
    new_map = struct.pack('<HHI', 0x0180, 8, 8 + 4 * len(ids)) + b''.join(struct.pack('<I', x) for x in ids)
    out = bytearray(tmp[:map_offset] + new_map + tmp[map_offset + map_size:])
    _put_u32(out, 4, _u32(tmp, 4) + 4)

    # Every compiled XML string index at/after the inserted resource name shifts by one.
    offset = map_offset + len(new_map)
    total = _u32(out, 4)
    while offset < total:
        typ, _, size = struct.unpack_from('<HHI', out, offset)
        if typ in (0x0100, 0x0101):
            _bump_string_index(out, offset + 16, insert_at)
            _bump_string_index(out, offset + 20, insert_at)
        elif typ == 0x0102:
            _bump_string_index(out, offset + 16, insert_at)
            _bump_string_index(out, offset + 20, insert_at)
            attr_start = _u16(out, offset + 24)
            attr_size = _u16(out, offset + 26)
            attr_count = _u16(out, offset + 28)
            base = offset + 16 + attr_start
            for i in range(attr_count):
                a = base + i * attr_size
                _bump_string_index(out, a, insert_at)
                _bump_string_index(out, a + 4, insert_at)
                _bump_string_index(out, a + 8, insert_at)
                if out[a + 15] == TYPE_STRING:
                    _bump_string_index(out, a + 16, insert_at)
        elif typ == 0x0103:
            _bump_string_index(out, offset + 16, insert_at)
            _bump_string_index(out, offset + 20, insert_at)
        offset += size
    return bytes(out)


def _add_background_attribute(blob: bytes, target_id: int, background_resource: int) -> bytes:
    blob = _insert_resource_name(blob, 'background', ANDROID_BACKGROUND)
    pool = _find_manifest_pool(blob)
    strings = pool.strings
    ids = _resource_map(blob)
    out = bytearray(blob)

    target_chunk = None
    target_attrs = None
    for offset, tag, attrs in _iter_start_elements(bytes(out), strings):
        if tag != 'TextView':
            continue
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if amap.get('id', (None, None, None, None))[3] == target_id:
            target_chunk, target_attrs = offset, attrs
            break
    if target_chunk is None or target_attrs is None:
        raise ValueError('level navigation TextView not found')
    if any(name == 'background' for _, name, _, _, _ in target_attrs):
        return bytes(out)

    uri_index = strings.index('http://schemas.android.com/apk/res/android')
    name_index = strings.index('background')
    resource_ids = []
    for a, _, _, _, _ in target_attrs:
        ni = _u32(out, a + 4)
        resource_ids.append(ids[ni] if ni < len(ids) else 0xFFFFFFFF)
    insert_position = next((i for i, rid in enumerate(resource_ids) if rid > ANDROID_BACKGROUND and rid != 0), len(resource_ids))

    attr_start = _u16(out, target_chunk + 24)
    attr_size = _u16(out, target_chunk + 26)
    attr_count = _u16(out, target_chunk + 28)
    if attr_size != 20:
        raise ValueError('unexpected binary XML attribute size')
    base = target_chunk + 16 + attr_start
    insert_offset = base + insert_position * attr_size
    record = struct.pack('<IIIHBBI', uri_index, name_index, NO_INDEX, 8, 0, TYPE_REFERENCE, background_resource)
    out = out[:insert_offset] + bytearray(record) + out[insert_offset:]

    struct.pack_into('<I', out, target_chunk + 4, _u32(out, target_chunk + 4) + 20)
    struct.pack_into('<H', out, target_chunk + 28, attr_count + 1)
    inserted_one_based = insert_position + 1
    for field in (30, 32, 34):
        value = _u16(out, target_chunk + field)
        if value and value >= inserted_one_based:
            struct.pack_into('<H', out, target_chunk + field, value + 1)
    _put_u32(out, 4, _u32(out, 4) + 20)
    return bytes(out)


def patch_level_layout_antique(blob: bytes, *, play: bool) -> bytes:
    """Make Russian УРОВЕНЬ N labels impossible to clip or disappear.

    The inherited layouts used fixed widths (50/70dp), which are too narrow for
    Russian labels. Use wrap_content, explicit padding/text color and a dedicated
    framed background instead.
    """
    target = ID_PLAY_LEVEL if play else ID_BUILD_LEVEL
    blob = _add_background_attribute(blob, target, RID_LEVEL_BADGE)
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'TextView':
            continue
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if amap.get('id', (None, None, None, None))[3] != target:
            continue
        if 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, PARCHMENT_TEXT)
        if 'textSize' in amap:
            _set_typed(out, amap['textSize'][0], TYPE_DIMENSION, 0x1001)  # 16sp
        if 'padding' in amap:
            _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x801)  # 8dp
        if 'layout_width' in amap:
            _set_typed(out, amap['layout_width'][0], TYPE_INT_DEC, 0xFFFFFFFE)  # wrap_content
    return bytes(out)


def patch_shape_antique(blob: bytes, *, fill: int, stroke: int, radius_dp: int = 10) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if tag == 'solid' and 'color' in amap:
            _set_typed(out, amap['color'][0], TYPE_COLOR, fill)
        elif tag == 'stroke':
            if 'color' in amap:
                _set_typed(out, amap['color'][0], TYPE_COLOR, stroke)
            if 'width' in amap:
                _set_typed(out, amap['width'][0], TYPE_DIMENSION, 0x101)
        elif tag == 'corners' and 'radius' in amap:
            _set_typed(out, amap['radius'][0], TYPE_DIMENSION, (radius_dp << 8) | 1)
    return bytes(out)


def patch_button_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    surface = False
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if not surface and tag in ('LinearLayout', 'RelativeLayout', 'FrameLayout') and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, WALNUT)
            surface = True
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, PARCHMENT_TEXT)
    return bytes(out)


def patch_nav_header_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if tag == 'LinearLayout' and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, OXBLOOD_DARK)
        elif tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, PARCHMENT_TEXT)
    return bytes(out)


def patch_subheader_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, OXBLOOD)
    return bytes(out)


def patch_topnav_antique(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (a, raw, dtype, data) for a, name, raw, dtype, data in attrs}
        if 'background' in amap and amap['background'][2] == TYPE_COLOR and amap['background'][3] in (0xFF172429, 0xFF223238):
            _set_typed(out, amap['background'][0], TYPE_COLOR, WALNUT_DEEP)
    return bytes(out)


def recolor_icon_antique(data: bytes) -> bytes:
    im = Image.open(BytesIO(data)).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            # Owned teal -> aged brass.
            if g > r * 1.18 and g > b * 1.05 and g > 75:
                lum = max(.38, min(1.0, max(r, g, b) / 190.0))
                px[x, y] = (int(179 * lum), int(138 * lum), int(82 * lum), a)
            # Cold neutral graphite -> warm ink/walnut.
            elif max(r, g, b) < 85 and abs(r - g) < 25 and abs(g - b) < 25:
                lum = max(.5, min(1.2, max(r, g, b) / 55.0))
                px[x, y] = (min(255, int(45 * lum)), min(255, int(36 * lum)), min(255, int(29 * lum)), a)
    out = BytesIO()
    im.save(out, 'PNG')
    return out.getvalue()


def _warm_image(path: Path) -> None:
    im = Image.open(path).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            # teal/cyan accents -> brass
            if g > r * 1.12 and g > b * 1.03 and g > 75:
                lum = max(.45, min(1.15, mx / 190.0))
                px[x, y] = (min(255, int(179 * lum)), min(255, int(138 * lum)), min(255, int(82 * lum)), a)
                continue
            # neutral/cool surfaces -> warm paper/sepia scale
            if mx - mn < 34:
                l = (r + g + b) / 3.0
                if l > 205:
                    t = (l - 205) / 50.0
                    c0, c1 = (232, 216, 178), (250, 239, 210)
                elif l > 105:
                    t = (l - 105) / 100.0
                    c0, c1 = (92, 69, 52), (232, 216, 178)
                else:
                    t = l / 105.0
                    c0, c1 = (42, 30, 25), (92, 69, 52)
                px[x, y] = tuple(int(c0[i] * (1 - t) + c1[i] * t) for i in range(3)) + (a,)
    suffix = path.suffix.lower()
    if suffix in ('.jpg', '.jpeg'):
        im.convert('RGB').save(path, 'JPEG', quality=94)
    elif suffix == '.webp':
        im.save(path, 'WEBP', lossless=True)
    else:
        im.save(path, 'PNG')


def restyle_generated_brand_antique(root: Path) -> None:
    """Warm the generated RuneSheet identity without touching game-content images."""
    root = Path(root)
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
            _warm_image(path)
