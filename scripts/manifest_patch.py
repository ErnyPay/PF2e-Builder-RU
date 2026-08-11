from __future__ import annotations
import struct
from dataclasses import dataclass

RES_STRING_POOL_TYPE = 0x0001
RES_XML_START_ELEMENT_TYPE = 0x0102
TYPE_STRING = 0x03
TYPE_INT_DEC = 0x10
NO_INDEX = 0xFFFFFFFF
UTF8_FLAG = 0x100


def _u16(d: bytes | bytearray, o: int) -> int:
    return struct.unpack_from('<H', d, o)[0]

def _u32(d: bytes | bytearray, o: int) -> int:
    return struct.unpack_from('<I', d, o)[0]

def _put_u32(d: bytearray, o: int, v: int) -> None:
    struct.pack_into('<I', d, o, v)

def _read_len8(d: bytes, o: int):
    x = d[o]; o += 1
    if x & 0x80:
        return ((x & 0x7f) << 8) | d[o], o + 1
    return x, o

def _read_len16(d: bytes, o: int):
    x = struct.unpack_from('<H', d, o)[0]; o += 2
    if x & 0x8000:
        y = struct.unpack_from('<H', d, o)[0]; o += 2
        return ((x & 0x7fff) << 16) | y, o
    return x, o

def _enc_len8(n: int) -> bytes:
    if n > 0x7FFF:
        raise ValueError('UTF-8 manifest string too long')
    return bytes([(n >> 8) | 0x80, n & 0xff]) if n > 0x7f else bytes([n])

def _enc_len16(n: int) -> bytes:
    if n > 0x7FFFFFFF:
        raise ValueError('UTF-16 manifest string too long')
    if n > 0x7fff:
        return struct.pack('<HH', (n >> 16) | 0x8000, n & 0xffff)
    return struct.pack('<H', n)

@dataclass
class StringPool:
    offset: int
    header_size: int
    size: int
    flags: int
    strings: list[str]

    @property
    def utf8(self) -> bool:
        return bool(self.flags & UTF8_FLAG)


def parse_string_pool(blob: bytes, off: int) -> StringPool:
    typ, hs, size = struct.unpack_from('<HHI', blob, off)
    if typ != RES_STRING_POOL_TYPE:
        raise ValueError('not a string pool')
    sc, style_count, flags, strings_start, styles_start = struct.unpack_from('<IIIII', blob, off + 8)
    if style_count:
        raise ValueError('styled manifest string pools are not supported')
    offsets = [struct.unpack_from('<I', blob, off + hs + 4*i)[0] for i in range(sc)]
    base = off + strings_start
    out = []
    for rel in offsets:
        q = base + rel
        if flags & UTF8_FLAG:
            _, q = _read_len8(blob, q)
            byte_len, q = _read_len8(blob, q)
            out.append(blob[q:q+byte_len].decode('utf-8'))
        else:
            char_len, q = _read_len16(blob, q)
            out.append(blob[q:q+char_len*2].decode('utf-16le'))
    return StringPool(off, hs, size, flags, out)


def build_string_pool(strings: list[str], flags: int) -> bytes:
    utf8 = bool(flags & UTF8_FLAG)
    encoded = []
    offsets = []
    cur = 0
    for s in strings:
        offsets.append(cur)
        if utf8:
            raw = s.encode('utf-8')
            utf16_len = len(s.encode('utf-16le')) // 2
            item = _enc_len8(utf16_len) + _enc_len8(len(raw)) + raw + b'\0'
        else:
            raw = s.encode('utf-16le')
            utf16_len = len(raw) // 2
            item = _enc_len16(utf16_len) + raw + b'\0\0'
        encoded.append(item); cur += len(item)
    header_size = 28
    strings_start = header_size + 4*len(strings)
    body = b''.join(encoded)
    while len(body) % 4:
        body += b'\0'
    size = strings_start + len(body)
    head = struct.pack('<HHI', RES_STRING_POOL_TYPE, header_size, size)
    head += struct.pack('<IIIII', len(strings), 0, flags, strings_start, 0)
    head += b''.join(struct.pack('<I', x) for x in offsets)
    return head + body


def _find_manifest_pool(blob: bytes) -> StringPool:
    root_hs = _u16(blob, 2)
    typ = _u16(blob, root_hs)
    if typ != RES_STRING_POOL_TYPE:
        raise ValueError('unexpected binary AndroidManifest layout')
    return parse_string_pool(blob, root_hs)


def _iter_start_elements(blob: bytes, strings: list[str]):
    total = _u32(blob, 4)
    o = _u16(blob, 2)
    while o < total:
        typ, hs, size = struct.unpack_from('<HHI', blob, o)
        if size <= 0:
            raise ValueError(f'bad chunk size at {o:#x}')
        if typ == RES_XML_START_ELEMENT_TYPE:
            name_idx = _u32(blob, o + 20)
            tag = strings[name_idx]
            attr_start = _u16(blob, o + 24)
            attr_size = _u16(blob, o + 26)
            attr_count = _u16(blob, o + 28)
            base = o + 16 + attr_start
            attrs = []
            for i in range(attr_count):
                a = base + i*attr_size
                name_i = _u32(blob, a + 4)
                raw_i = _u32(blob, a + 8)
                dtype = blob[a + 15]
                data = _u32(blob, a + 16)
                attrs.append((a, strings[name_i], raw_i, dtype, data))
            yield o, tag, attrs
        o += size


def patch_manifest(blob: bytes, *, app_name: str, application_id: str, version_name: str,
                   version_code: int, file_provider_authority: str,
                   old_application_id: str = 'com.redrazors.pathbuilder2e') -> bytes:
    pool = _find_manifest_pool(blob)
    strings = list(pool.strings)

    # First discover every new literal we will need.
    needed = {app_name, application_id, version_name, file_provider_authority,
              application_id + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'}
    for _, tag, attrs in _iter_start_elements(blob, strings):
        for _, name, raw, dtype, data in attrs:
            val = strings[data] if dtype == TYPE_STRING and data != NO_INDEX else (strings[raw] if raw != NO_INDEX else None)
            if tag == 'provider' and name == 'authorities' and val and val.startswith(old_application_id):
                if val == old_application_id + '.provider':
                    needed.add(file_provider_authority)
                elif val.endswith('.ConfigProvider'):
                    needed.add(application_id + '.config')
                else:
                    needed.add(application_id + val[len(old_application_id):])

    idx = {s: i for i, s in enumerate(strings)}
    for s in sorted(needed):
        if s not in idx:
            idx[s] = len(strings); strings.append(s)

    new_pool = build_string_pool(strings, pool.flags)
    delta = len(new_pool) - pool.size
    out = bytearray(blob[:pool.offset] + new_pool + blob[pool.offset + pool.size:])
    _put_u32(out, 4, _u32(blob, 4) + delta)

    def set_string(a: int, text: str):
        i = idx[text]
        _put_u32(out, a + 8, i)      # rawValue
        struct.pack_into('<HBBI', out, a + 12, 8, 0, TYPE_STRING, i)

    dynamic_old = old_application_id + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
    dynamic_new = application_id + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'

    for _, tag, attrs in _iter_start_elements(bytes(out), strings):
        for a, name, raw, dtype, data in attrs:
            val = strings[data] if dtype == TYPE_STRING and data != NO_INDEX else (strings[raw] if raw != NO_INDEX else None)
            if tag == 'manifest' and name == 'package':
                set_string(a, application_id)
            elif tag == 'manifest' and name == 'versionName':
                set_string(a, version_name)
            elif tag == 'manifest' and name == 'versionCode':
                _put_u32(out, a + 8, NO_INDEX)
                struct.pack_into('<HBBI', out, a + 12, 8, 0, TYPE_INT_DEC, version_code)
            elif tag == 'application' and name == 'label':
                set_string(a, app_name)
            elif name == 'name' and tag in ('permission', 'uses-permission') and val == dynamic_old:
                set_string(a, dynamic_new)
            elif tag == 'provider' and name == 'authorities' and val and val.startswith(old_application_id):
                if val == old_application_id + '.provider':
                    nv = file_provider_authority
                elif val.endswith('.ConfigProvider'):
                    nv = application_id + '.config'
                else:
                    nv = application_id + val[len(old_application_id):]
                set_string(a, nv)
    return bytes(out)
