from __future__ import annotations

from manifest_patch import _find_manifest_pool, _iter_start_elements, _put_u32, build_string_pool
from sheet_dialog_pass import TYPE_DIMENSION, TYPE_REFERENCE, _add_android_attr, _set_typed

ANDROID_PADDING = 0x010100D5
RID_HEADER_PILL = 0x7F0700D2
RID_SURFACE = 0x7F0701DD

PRODUCT_LITERAL_REPLACEMENTS = {
    'Pathbuilder 2e JSON ID': 'RuneSheet RU JSON ID',
    'The following book containing remastered character options have been added to Pathbuilder. Would you like to enable it?':
        'The following book containing remastered character options has been added to RuneSheet RU. Would you like to enable it?',
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


def patch_existing_rounded_text_padding(blob: bytes) -> bytes:
    """Increase insets only where a TextView already owns a RuneSheet rounded surface."""
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), pool.strings):
        if tag != 'TextView':
            continue
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        bg = amap.get('background')
        if not bg or bg[2] != TYPE_REFERENCE or bg[3] not in (RID_HEADER_PILL, RID_SURFACE):
            continue
        if 'padding' in amap:
            dp = 12 if bg[3] == RID_HEADER_PILL else 10
            _set_typed(out, amap['padding'][0], TYPE_DIMENSION, (dp << 8) | 1)
    return bytes(out)


def replace_product_shell_literals(blob: bytes) -> bytes:
    """Replace only product-shell literals; rules/content strings are never passed here."""
    pool = _find_manifest_pool(blob)
    strings = list(pool.strings)
    changed = False
    for i, value in enumerate(strings):
        replacement = PRODUCT_LITERAL_REPLACEMENTS.get(value)
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
