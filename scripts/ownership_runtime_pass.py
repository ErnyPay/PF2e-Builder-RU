from __future__ import annotations

import struct

from manifest_patch import (
    NO_INDEX,
    TYPE_STRING,
    _find_manifest_pool,
    _iter_start_elements,
    _put_u32,
    _u16,
    _u32,
)

TYPE_INT_BOOLEAN = 0x12
ANDROID_ENABLED = 0x0101000E

AD_COMPONENTS = {
    'com.google.android.gms.ads.MobileAdsInitProvider',
    'com.google.android.gms.ads.AdActivity',
    'com.google.android.gms.ads.OutOfContextTestingActivity',
    'com.google.android.gms.ads.NotificationHandlerActivity',
    'com.google.android.gms.ads.AdService',
}
INSTALL_REFERRER_PERMISSION = 'com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE'
ANALYTICS_CONNECTOR_META = 'com.google.firebase.components:com.google.firebase.analytics.connector.internal.AnalyticsConnectorRegistrar'


def _resource_map(blob: bytes) -> list[int]:
    pool = _find_manifest_pool(blob)
    offset = pool.offset + pool.size
    typ, _, size = struct.unpack_from('<HHI', blob, offset)
    if typ != 0x0180:
        raise ValueError('manifest has no resource map')
    return [_u32(blob, p) for p in range(offset + 8, offset + size, 4)]


def _attr_value(strings: list[str], raw: int, dtype: int, data: int):
    if dtype == TYPE_STRING and data != NO_INDEX and data < len(strings):
        return strings[data]
    if raw != NO_INDEX and raw < len(strings):
        return strings[raw]
    return data


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _set_string(out: bytearray, attr: int, index: int) -> None:
    _put_u32(out, attr + 8, index)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, TYPE_STRING, index)


def _disable_named_component(blob: bytes, target_name: str) -> bytes:
    pool = _find_manifest_pool(blob)
    strings = pool.strings
    ids = _resource_map(blob)
    out = bytearray(blob)
    if 'enabled' not in strings:
        raise ValueError('android enabled attribute missing from manifest string pool')

    target_chunk = None
    target_attrs = None
    for offset, tag, attrs in _iter_start_elements(bytes(out), strings):
        if tag not in ('activity', 'service', 'receiver', 'provider'):
            continue
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if 'name' not in amap:
            continue
        _, raw, dtype, data = amap['name']
        if _attr_value(strings, raw, dtype, data) == target_name:
            target_chunk, target_attrs = offset, attrs
            break
    if target_chunk is None or target_attrs is None:
        raise ValueError(f'component not found: {target_name}')

    amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in target_attrs}
    if 'enabled' in amap:
        _set_typed(out, amap['enabled'][0], TYPE_INT_BOOLEAN, 0)
        return bytes(out)

    uri_idx = strings.index('http://schemas.android.com/apk/res/android')
    name_idx = strings.index('enabled')
    resource_ids = []
    for a, _, _, _, _ in target_attrs:
        ni = _u32(out, a + 4)
        resource_ids.append(ids[ni] if ni < len(ids) else 0xFFFFFFFF)
    pos = next((i for i, rid in enumerate(resource_ids) if rid > ANDROID_ENABLED and rid != 0), len(resource_ids))

    attr_start = _u16(out, target_chunk + 24)
    attr_size = _u16(out, target_chunk + 26)
    attr_count = _u16(out, target_chunk + 28)
    if attr_size != 20:
        raise ValueError('unexpected manifest attribute size')
    base = target_chunk + 16 + attr_start
    insert_offset = base + pos * attr_size
    record = struct.pack('<IIIHBBI', uri_idx, name_idx, NO_INDEX, 8, 0, TYPE_INT_BOOLEAN, 0)
    out = out[:insert_offset] + bytearray(record) + out[insert_offset:]

    struct.pack_into('<I', out, target_chunk + 4, _u32(out, target_chunk + 4) + 20)
    struct.pack_into('<H', out, target_chunk + 28, attr_count + 1)
    inserted = pos + 1
    for field in (30, 32, 34):
        value = _u16(out, target_chunk + field)
        if value and value >= inserted:
            struct.pack_into('<H', out, target_chunk + field, value + 1)
    _put_u32(out, 4, _u32(out, 4) + 20)
    return bytes(out)


def harden_owned_runtime(blob: bytes, *, application_id: str) -> bytes:
    """Detach safe inherited telemetry/ads startup without touching billing or cloud auth/db.

    SDK classes remain packaged for binary compatibility. This pass only disables their
    automatic Android components and the Firebase AnalyticsConnector registrar.
    """
    pool = _find_manifest_pool(blob)
    strings = pool.strings
    noop_permission = application_id + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    if noop_permission not in strings:
        raise ValueError('expected app no-op permission missing')
    noop_idx = strings.index(noop_permission)

    out = bytearray(blob)
    for _, tag, attrs in _iter_start_elements(bytes(out), strings):
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if tag == 'uses-permission' and 'name' in amap:
            a, raw, dtype, data = amap['name']
            if _attr_value(strings, raw, dtype, data) == INSTALL_REFERRER_PERMISSION:
                _set_string(out, a, noop_idx)
        elif tag == 'meta-data' and 'name' in amap and 'value' in amap:
            _, raw, dtype, data = amap['name']
            if _attr_value(strings, raw, dtype, data) == ANALYTICS_CONNECTOR_META:
                _set_string(out, amap['value'][0], noop_idx)

    result = bytes(out)
    for component in sorted(AD_COMPONENTS):
        result = _disable_named_component(result, component)
    return result
