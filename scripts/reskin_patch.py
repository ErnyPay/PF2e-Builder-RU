from __future__ import annotations

import struct

from manifest_patch import (
    NO_INDEX,
    _find_manifest_pool,
    _iter_start_elements,
    _put_u32,
    _u32,
    build_string_pool,
)

TYPE_REFERENCE = 0x01
TYPE_COLOR = 0x1C
TYPE_DIMENSION = 0x05

# Stable resource IDs in the pinned polished 2.56 baseline.
ID_BUTTON_UPDATE = 0x7F09011D
ID_BUILD_LEVEL = 0x7F090456
ID_PLAY_LEVEL = 0x7F090510
ID_PLAY_SELECTED_TAB = 0x7F0902A7
COLOR_STANDARD_TEXT = 0x7F05031A

# Inherited top-navigation background resource IDs in the pinned baseline.
COLOR_BUILD_HEADER = 0x7F05008D
COLOR_PLAY_HEADER = 0x7F05008E

GRAPHITE = 0xFF172429
TEAL = 0xFF26958F
WHITE = 0xFFFFFFFF

FRONTPAGE_LAYOUTS = (
    "res/layout/activity_content_frontpage_plain.xml",
    "res/layout/activity_content_frontpage_parchment.xml",
    "res/layout/activity_content_frontpage_dark_horizontal.xml",
)


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


def _set_typed(out: bytearray, attr_offset: int, data_type: int, data: int) -> None:
    _put_u32(out, attr_offset + 8, NO_INDEX)
    struct.pack_into("<HBBI", out, attr_offset + 12, 8, 0, data_type, data)


def patch_frontpage_layout(blob: bytes) -> bytes:
    blob = _replace_xml_strings(
        blob,
        {
            "PATHBUILDER 2E": "RUNESHEET RU",
            "Because one character is never enough": "Персонаж • правила • сессия",
            "App Options": "Настройки",
            "New Character Button": "Создать персонажа",
            "Load Character Button": "Мои персонажи",
        },
    )
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if amap.get("id", (None, None, None, None))[3] == ID_BUTTON_UPDATE:
            # Hide the inherited version/update surface without touching its runtime code.
            for name in ("layout_height", "padding"):
                if name in amap:
                    _set_typed(out, amap[name][0], TYPE_DIMENSION, 0x00000001)  # 0dp
    return bytes(out)


def patch_level_layout(blob: bytes, *, play: bool) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    target = ID_PLAY_LEVEL if play else ID_BUILD_LEVEL
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != "TextView":
            continue
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if amap.get("id", (None, None, None, None))[3] != target:
            continue
        if "textColor" in amap:
            _set_typed(out, amap["textColor"][0], TYPE_COLOR, WHITE)
        if "textSize" in amap:
            _set_typed(out, amap["textSize"][0], TYPE_DIMENSION, 0x1001 if play else 0x1101)  # 16/17sp
    return bytes(out)


def patch_play_navigation(blob: bytes) -> bytes:
    """Patch only the play-mode top-navigation component.

    This deliberately avoids global resources.arsc palette changes because the
    inherited app reuses stateful colors across unrelated widgets.
    """
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        element_id = amap.get("id", (None, None, None, None))[3]
        if "background" in amap and amap["background"][3] == COLOR_PLAY_HEADER:
            _set_typed(out, amap["background"][0], TYPE_COLOR, GRAPHITE)
        if element_id == ID_PLAY_SELECTED_TAB:
            if "layout_height" in amap:
                _set_typed(out, amap["layout_height"][0], TYPE_DIMENSION, 0x2201)  # 34dp
            if "layout_marginTop" in amap:
                _set_typed(out, amap["layout_marginTop"][0], TYPE_DIMENSION, 0x0401)  # 4dp
            if "layout_marginBottom" in amap:
                _set_typed(out, amap["layout_marginBottom"][0], TYPE_DIMENSION, 0x0401)
    return bytes(out)


def patch_build_navigation(blob: bytes) -> bytes:
    """Patch only the build-mode top-navigation background."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if "background" in amap and amap["background"][3] == COLOR_BUILD_HEADER:
            _set_typed(out, amap["background"][0], TYPE_COLOR, GRAPHITE)
    return bytes(out)


def patch_topnav_slider(blob: bytes) -> bytes:
    """Give the selected top tab a restrained teal rounded indicator."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        if tag == "solid" and "color" in amap:
            _set_typed(out, amap["color"][0], TYPE_COLOR, TEAL)
        elif tag == "stroke":
            if "color" in amap:
                _set_typed(out, amap["color"][0], TYPE_COLOR, TEAL)
            if "width" in amap:
                _set_typed(out, amap["width"][0], TYPE_DIMENSION, 0x0101)  # 1dp
        elif tag == "corners" and "radius" in amap:
            _set_typed(out, amap["radius"][0], TYPE_DIMENSION, 0x0C01)  # 12dp
    return bytes(out)
