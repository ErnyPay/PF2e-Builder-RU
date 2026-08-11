from __future__ import annotations

import struct
import zipfile

from manifest_patch import (
    NO_INDEX,
    RES_XML_START_ELEMENT_TYPE,
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

# Stable resource IDs in the pinned polished 2.56 baseline.
ID_BUTTON_UPDATE = 0x7F09011D
ID_BUILD_LEVEL = 0x7F090456
ID_PLAY_LEVEL = 0x7F090510
COLOR_STANDARD_TEXT = 0x7F05031A

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
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name: (offset, raw, dtype, data) for offset, name, raw, dtype, data in attrs}
        element_id = amap.get("id", (None, None, None, None))[3]
        if element_id == ID_BUTTON_UPDATE:
            # Keep the inherited update/version code intact, but remove its product UI surface.
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
            _set_typed(out, amap["textColor"][0], TYPE_REFERENCE, COLOR_STANDARD_TEXT)
        if "textSize" in amap:
            _set_typed(out, amap["textSize"][0], TYPE_DIMENSION, 0x1001 if play else 0x1201)  # 16sp / 18sp
    return bytes(out)


def _read_pool(blob: bytes | bytearray, off: int) -> tuple[list[str], int]:
    typ, hs, size = struct.unpack_from("<HHI", blob, off)
    if typ != 0x0001:
        raise ValueError("not a resource string pool")
    sc, _, flags, strings_start, _ = struct.unpack_from("<IIIII", blob, off + 8)
    offsets = [struct.unpack_from("<I", blob, off + hs + 4 * i)[0] for i in range(sc)]
    base = off + strings_start
    strings: list[str] = []
    for rel in offsets:
        q = base + rel
        if flags & 0x100:
            x = blob[q]; q += 1
            if x & 0x80:
                q += 1
            x = blob[q]; q += 1
            if x & 0x80:
                byte_len = ((x & 0x7F) << 8) | blob[q]; q += 1
            else:
                byte_len = x
            strings.append(bytes(blob[q:q + byte_len]).decode("utf-8", "replace"))
        else:
            x = struct.unpack_from("<H", blob, q)[0]; q += 2
            if x & 0x8000:
                y = struct.unpack_from("<H", blob, q)[0]; q += 2
                char_len = ((x & 0x7FFF) << 16) | y
            else:
                char_len = x
            strings.append(bytes(blob[q:q + char_len * 2]).decode("utf-16le", "replace"))
    return strings, size


def patch_product_palette(blob: bytes) -> bytes:
    out = bytearray(blob)
    root_type, root_hs, root_size = struct.unpack_from("<HHI", out, 0)
    if root_type != 0x0002:
        raise ValueError("unexpected resources.arsc root")
    off = root_hs
    _, global_pool_size = _read_pool(out, off)
    off += global_pool_size

    desired = {
        "colorAccent": 0xFF228A89,
        "colorAccentFade": 0xFFDCECEB,
        "colorPrimary": 0xFF228A89,
        "colorPrimaryDark": 0xFF102F35,
        "colorPrimaryFifty": 0xFF67B8B4,
        "colorPrimaryNotAsDark": 0xFF185E63,
        "colorPrimaryVeryFaded": 0xFFB8DAD7,
    }
    patched: set[str] = set()

    while off < root_size:
        chunk_type, header_size, chunk_size = struct.unpack_from("<HHI", out, off)
        if chunk_type == 0x0200:
            type_strings_off = struct.unpack_from("<I", out, off + 268)[0]
            key_strings_off = struct.unpack_from("<I", out, off + 276)[0]
            types, _ = _read_pool(out, off + type_strings_off)
            keys, _ = _read_pool(out, off + key_strings_off)
            q = off + header_size
            while q < off + chunk_size:
                child_type, child_header, child_size = struct.unpack_from("<HHI", out, q)
                if child_type == 0x0201:
                    type_id = out[q + 8]
                    entry_count = struct.unpack_from("<I", out, q + 12)[0]
                    entries_start = struct.unpack_from("<I", out, q + 16)[0]
                    type_name = types[type_id - 1] if 0 < type_id <= len(types) else ""
                    if type_name == "color":
                        for i in range(entry_count):
                            rel = struct.unpack_from("<I", out, q + child_header + 4 * i)[0]
                            if rel == 0xFFFFFFFF:
                                continue
                            entry = q + entries_start + rel
                            entry_size, flags, key_index = struct.unpack_from("<HHI", out, entry)
                            if flags & 1 or key_index >= len(keys):
                                continue
                            name = keys[key_index]
                            if name not in desired:
                                continue
                            value_off = entry + entry_size
                            dtype = out[value_off + 3]
                            if not 0x1C <= dtype <= 0x1F:
                                raise ValueError(f"{name} is not a direct color")
                            struct.pack_into("<I", out, value_off + 4, desired[name])
                            patched.add(name)
                q += child_size
        off += chunk_size

    missing = set(desired) - patched
    if missing:
        raise ValueError(f"missing palette resources: {sorted(missing)}")
    return bytes(out)


def generate_reskin_overrides(apk: zipfile.ZipFile) -> dict[str, bytes]:
    overrides: dict[str, bytes] = {"resources.arsc": patch_product_palette(apk.read("resources.arsc"))}
    names = set(apk.namelist())
    for path in FRONTPAGE_LAYOUTS:
        if path in names:
            overrides[path] = patch_frontpage_layout(apk.read(path))
    if "res/layout/layout_level_navigation.xml" in names:
        overrides["res/layout/layout_level_navigation.xml"] = patch_level_layout(
            apk.read("res/layout/layout_level_navigation.xml"), play=False
        )
    if "res/layout/layout_level_navigation_play.xml" in names:
        overrides["res/layout/layout_level_navigation_play.xml"] = patch_level_layout(
            apk.read("res/layout/layout_level_navigation_play.xml"), play=True
        )
    return overrides
