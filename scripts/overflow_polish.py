from __future__ import annotations

from manifest_patch import _find_manifest_pool, _iter_start_elements, _put_u32, build_string_pool
from sheet_dialog_pass import (
    TYPE_DIMENSION, TYPE_REFERENCE, TYPE_INT_DEC, _add_android_attr, _set_typed,
)

TYPE_INT_BOOLEAN = 0x12
ANDROID_PADDING = 0x010100D5
ANDROID_MIN_HEIGHT = 0x01010140
ANDROID_MAX_LINES = 0x01010153
ANDROID_SINGLE_LINE = 0x0101015D
ANDROID_INCLUDE_FONT_PADDING = 0x0101015F
RID_HEADER_PILL = 0x7F0700D2
RID_SURFACE = 0x7F0701DD

TEXT_LIST_LAYOUTS = {
    'res/layout/list_item_small.xml',
    'res/layout/list_item_small_white.xml',
    'res/layout/list_item_standard.xml',
    'res/layout/list_item_standard_boxed.xml',
    'res/layout/list_item_standard_centered.xml',
    'res/layout/layout_user_added_bonus_feat.xml',
    'res/layout/listview_item_weapons.xml',
    'res/layout/list_item_folder.xml',
    'res/layout/list_item_folder_white.xml',
}

PRODUCT_LITERAL_REPLACEMENTS = {
    'Pathbuilder 2e JSON ID': 'RuneSheet RU JSON ID',
    'The following book containing remastered character options have been added to Pathbuilder. Would you like to enable it?':
        'The following book containing remastered character options has been added to RuneSheet RU. Would you like to enable it?',
}

COMPATIBILITY_LITERAL_REPLACEMENTS = {
    'GM Mode is currently only available on Pathbuilder Web.':
        'GM-режим пока использует унаследованный веб-сервис Pathbuilder (режим совместимости).',
    "A shared character's build ID is found at the end of its sharable link, eg 106893 for pathbuilder2e.com/launch.html?build=106983":
        'ID общего персонажа берётся из ссылки режима совместимости Pathbuilder; это число в конце параметра build.',
}


def _root(blob: bytes):
    pool = _find_manifest_pool(blob)
    return next(_iter_start_elements(blob, pool.strings))


def patch_root_padding(blob: bytes, padding_dp: int) -> bytes:
    _, tag, attrs = _root(blob)
    amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
    encoded = (padding_dp << 8) | 1
    if 'padding' in amap:
        out = bytearray(blob)
        _set_typed(out, amap['padding'][0], TYPE_DIMENSION, encoded)
        return bytes(out)
    return _add_android_attr(blob,target_tag=tag,target_id=None,name='padding',attr_rid=ANDROID_PADDING,dtype=TYPE_DIMENSION,data=encoded)


def _attrs_for_id(blob: bytes, target_id: int):
    pool = _find_manifest_pool(blob)
    for _, tag, attrs in _iter_start_elements(blob, pool.strings):
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if tag == 'TextView' and amap.get('id',(None,None,None,None))[3] == target_id:
            return amap
    return None


def patch_header_text_fit(blob: bytes, target_id: int) -> bytes:
    """Allow long Russian sheet headers to grow inside rounded pills."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    found = False
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'TextView':
            continue
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if amap.get('id',(None,None,None,None))[3] != target_id:
            continue
        found = True
        if 'padding' in amap:
            _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x0E01)  # 14dp
        if 'layout_height' in amap:
            _set_typed(out, amap['layout_height'][0], TYPE_INT_DEC, 0xFFFFFFFE)  # wrap_content
        if 'minHeight' in amap:
            _set_typed(out, amap['minHeight'][0], TYPE_DIMENSION, 0x3001)  # 48dp
        if 'maxLines' in amap:
            _set_typed(out, amap['maxLines'][0], TYPE_INT_DEC, 2)
        if 'singleLine' in amap:
            _set_typed(out, amap['singleLine'][0], TYPE_INT_BOOLEAN, 0)
        if 'includeFontPadding' in amap:
            _set_typed(out, amap['includeFontPadding'][0], TYPE_INT_BOOLEAN, 1)
        blob = bytes(out)
        break
    if not found:
        return blob

    amap = _attrs_for_id(blob, target_id)
    if 'minHeight' not in amap:
        blob = _add_android_attr(blob,target_tag='TextView',target_id=target_id,name='minHeight',attr_rid=ANDROID_MIN_HEIGHT,dtype=TYPE_DIMENSION,data=0x3001)
    amap = _attrs_for_id(blob, target_id)
    if 'maxLines' not in amap:
        blob = _add_android_attr(blob,target_tag='TextView',target_id=target_id,name='maxLines',attr_rid=ANDROID_MAX_LINES,dtype=TYPE_INT_DEC,data=2)
    amap = _attrs_for_id(blob, target_id)
    if 'singleLine' not in amap:
        blob = _add_android_attr(blob,target_tag='TextView',target_id=target_id,name='singleLine',attr_rid=ANDROID_SINGLE_LINE,dtype=TYPE_INT_BOOLEAN,data=0)
    amap = _attrs_for_id(blob, target_id)
    if 'includeFontPadding' not in amap:
        blob = _add_android_attr(blob,target_tag='TextView',target_id=target_id,name='includeFontPadding',attr_rid=ANDROID_INCLUDE_FONT_PADDING,dtype=TYPE_INT_BOOLEAN,data=1)
    return blob


def patch_existing_text_fit(blob: bytes) -> bytes:
    """Relax existing one-line constraints without touching compact numeric cells."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag not in ('TextView', 'CheckedTextView'):
            continue
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        width = amap.get('layout_width')
        if width and width[2] == TYPE_DIMENSION and 0 < (width[3] >> 8) <= 44:
            continue
        if 'singleLine' in amap:
            _set_typed(out, amap['singleLine'][0], TYPE_INT_BOOLEAN, 0)
        if 'maxLines' in amap and amap['maxLines'][3] <= 1:
            _set_typed(out, amap['maxLines'][0], TYPE_INT_DEC, 2)
        if 'lines' in amap and amap['lines'][3] <= 1:
            _set_typed(out, amap['lines'][0], TYPE_INT_DEC, 2)
        bg = amap.get('background')
        if bg and bg[2] == TYPE_REFERENCE and bg[3] in (RID_HEADER_PILL, RID_SURFACE):
            if 'layout_height' in amap:
                _set_typed(out, amap['layout_height'][0], TYPE_INT_DEC, 0xFFFFFFFE)
            if 'padding' in amap:
                _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x0C01)
            if 'includeFontPadding' in amap:
                _set_typed(out, amap['includeFontPadding'][0], TYPE_INT_BOOLEAN, 1)
    return bytes(out)


def patch_existing_rounded_text_padding(blob: bytes) -> bytes:
    """Compatibility wrapper retained for older build scripts."""
    return patch_existing_text_fit(blob)


def _replace_literals(blob: bytes, replacements: dict[str, str]) -> bytes:
    pool = _find_manifest_pool(blob)
    strings = list(pool.strings)
    changed = False
    for i, value in enumerate(strings):
        replacement = replacements.get(value)
        if replacement is not None:
            strings[i] = replacement
            changed = True
    if not changed:
        return blob
    new_pool = build_string_pool(strings, pool.flags)
    delta = len(new_pool) - pool.size
    out = bytearray(blob[:pool.offset] + new_pool + blob[pool.offset + pool.size:])
    _put_u32(out, 4, int.from_bytes(blob[4:8], 'little') + delta)
    return bytes(out)


def replace_product_shell_literals(blob: bytes) -> bytes:
    return _replace_literals(blob, PRODUCT_LITERAL_REPLACEMENTS)


def replace_compatibility_shell_literals(blob: bytes) -> bytes:
    return _replace_literals(blob, COMPATIBILITY_LITERAL_REPLACEMENTS)
