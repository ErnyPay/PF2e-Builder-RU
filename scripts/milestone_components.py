from __future__ import annotations

import struct
from io import BytesIO
from PIL import Image

from manifest_patch import (
    NO_INDEX,
    TYPE_STRING,
    _find_manifest_pool,
    _iter_start_elements,
    _put_u32,
    _u32,
    build_string_pool,
)

TYPE_INT_BOOLEAN = 0x12
TYPE_COLOR = 0x1C

GRAPHITE = 0xFF223238
GRAPHITE_DEEP = 0xFF172429
WHITE = 0xFFF5F8F8
TEAL = 0xFF26958F

BUTTON_LAYOUTS = {
    'res/layout/button_boost.xml',
    'res/layout/button_heighten.xml',
    'res/layout/button_known.xml',
    'res/layout/button_roll_small.xml',
    'res/layout/button_single.xml',
    'res/layout/button_single_nodecoration.xml',
    'res/layout/button_single_small.xml',
    'res/layout/button_single_small_left_align.xml',
    'res/layout/button_single_small_nodecoration.xml',
    'res/layout/button_skills.xml',
    'res/layout/button_spells.xml',
    'res/layout/button_standard.xml',
    'res/layout/button_standard_no_image.xml',
    'res/layout/button_standard_nodecoration.xml',
}

# Only identity / utility icons. Semantic warning, cancel/flaw, rarity and
# proficiency-rank colors deliberately stay untouched.
ICON_NAMES = {
    'icon_ancestry.png', 'icon_ancestry_dark.png',
    'icon_background.png', 'icon_background_dark.png',
    'icon_class.png', 'icon_class_dark.png',
    'icon_general.png', 'icon_general_dark.png',
    'icon_skill.png', 'icon_skill_dark.png',
    'icon_spellslot.png', 'icon_spellslot_dark.png',
    'icon_spellslot_off.png', 'icon_spellslot_off_dark.png',
    'icon_known.png', 'icon_known_dark.png',
    'icon_known_off.png', 'icon_known_off_dark.png',
    'icon_known_witch.png', 'icon_known_witch_dark.png',
    'icon_known_witch_off.png', 'icon_known_witch_off_dark.png',
    'icon_d4.png', 'icon_d6.png', 'icon_d8.png', 'icon_d10.png', 'icon_d12.png', 'icon_d20.png',
    'icon_d4_dark.png', 'icon_d6_dark.png', 'icon_d8_dark.png', 'icon_d10_dark.png', 'icon_d12_dark.png', 'icon_d20_dark.png',
    'icon_cog.png', 'icon_boost.png',
    'icon_ability_boost.png', 'icon_ability_boost_ticked.png',
    'icon_add.png', 'icon_subtract.png', 'icon_create.png', 'icon_open.png', 'icon_print.png',
}

AD_TRACKING_PERMISSIONS = {
    'com.google.android.gms.permission.AD_ID',
    'android.permission.ACCESS_ADSERVICES_AD_ID',
    'android.permission.ACCESS_ADSERVICES_ATTRIBUTION',
    'android.permission.ACCESS_ADSERVICES_TOPICS',
}

DISABLE_COMPONENTS = {
    'com.google.android.gms.ads.AdService',
    'com.google.android.gms.measurement.AppMeasurementReceiver',
    'com.google.android.gms.measurement.AppMeasurementService',
    'com.google.android.gms.measurement.AppMeasurementJobService',
}


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _replace_xml_strings(blob: bytes, replacements: dict[str, str]) -> bytes:
    pool = _find_manifest_pool(blob)
    strings = list(pool.strings)
    changed = False
    for i, value in enumerate(strings):
        if value in replacements:
            strings[i] = replacements[value]
            changed = True
    if not changed:
        return blob
    new_pool = build_string_pool(strings, pool.flags)
    delta = len(new_pool) - pool.size
    out = bytearray(blob[:pool.offset] + new_pool + blob[pool.offset + pool.size:])
    _put_u32(out, 4, _u32(blob, 4) + delta)
    return bytes(out)


def patch_button_layout(blob: bytes) -> bytes:
    """Patch a contained button surface and every label inside it as one unit.

    This rule intentionally prevents the alpha.12 failure mode where a light
    background was changed without changing inherited white text.
    """
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    first_surface_done = False
    label_count = 0
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if not first_surface_done and tag in ('LinearLayout', 'RelativeLayout', 'FrameLayout') and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, GRAPHITE)
            first_surface_done = True
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, WHITE)
            label_count += 1
    if not first_surface_done or not label_count:
        raise ValueError('button layout is not a safe contained surface')
    return bytes(out)


def patch_nav_header(blob: bytes) -> bytes:
    blob = _replace_xml_strings(blob, {'PATHBUILDER 2E': 'RUNESHEET RU'})
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if tag == 'LinearLayout' and 'background' in amap:
            _set_typed(out, amap['background'][0], TYPE_COLOR, GRAPHITE_DEEP)
        elif tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, WHITE)
    return bytes(out)


def patch_subheader(blob: bytes) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if tag == 'TextView' and 'textColor' in amap:
            _set_typed(out, amap['textColor'][0], TYPE_COLOR, TEAL)
    return bytes(out)


def recolor_icon(data: bytes, dark_name: bool) -> bytes:
    im = Image.open(BytesIO(data)).convert('RGBA')
    px = im.load()
    w, h = im.size
    teal = (72, 190, 184) if dark_name else (38, 149, 143)
    graphite = (29, 39, 44)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            mx = max(r, g, b)
            mn = min(r, g, b)
            # Legacy burgundy/red-brown product-identity pixels only; vivid red
            # status/error pixels are excluded by the upper red bound.
            if 70 <= r < 165 and r > g * 1.35 and r > b * 1.35 and g < 105 and b < 105:
                lum = max(.40, min(1.0, mx / 125.0))
                px[x, y] = (int(teal[0] * lum), int(teal[1] * lum), int(teal[2] * lum), a)
            elif not dark_name and mx < 48 and mn < 48:
                px[x, y] = (*graphite, a)
    out = BytesIO()
    im.save(out, 'PNG')
    return out.getvalue()


def harden_manifest_privacy(blob: bytes, *, application_id: str) -> bytes:
    """Disable ad/measurement tracking without touching billing or Firebase auth/db."""
    pool = _find_manifest_pool(blob)
    strings = pool.strings
    idx = {s: i for i, s in enumerate(strings)}
    noop_permission = application_id + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    if noop_permission not in idx:
        raise ValueError('expected app dynamic permission is missing')

    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}

        if tag == 'uses-permission' and 'name' in amap:
            a, raw, dtype, data = amap['name']
            value = strings[data] if dtype == TYPE_STRING and data != NO_INDEX and data < len(strings) else None
            if value in AD_TRACKING_PERMISSIONS:
                _put_u32(out, a + 8, idx[noop_permission])
                struct.pack_into('<HBBI', out, a + 12, 8, 0, TYPE_STRING, idx[noop_permission])

        elif tag in ('service', 'receiver') and 'name' in amap:
            _, _, dtype, data = amap['name']
            value = strings[data] if dtype == TYPE_STRING and data != NO_INDEX and data < len(strings) else None
            if value in DISABLE_COMPONENTS:
                if 'enabled' not in amap:
                    raise ValueError(f'cannot safely disable {value}: missing enabled attribute')
                _set_typed(out, amap['enabled'][0], TYPE_INT_BOOLEAN, 0)

    # Second layer: detach inherited ads startup, install-referrer and Firebase
    # AnalyticsConnector while deliberately keeping Billing and Firebase Auth/DB.
    from ownership_runtime_pass import harden_owned_runtime
    return harden_owned_runtime(bytes(out), application_id=application_id)
