from __future__ import annotations
import hashlib, struct, zlib


# User-visible shell/runtime literals that still live directly in classes2.dex.
# These replacements are deliberately exact-size so string_data offsets and all
# method/class references remain unchanged. Real compatibility backend URLs and
# inherited class descriptors are intentionally NOT rewritten here.
PRODUCT_SHELL_REPLACEMENTS = {
    'https://gitlab.com/doctor.unspeakable/pathbuilder-2e/-/issues':
        'https://github.com/ErnyPay/PF2e-Builder-RU/issues/new?x=12345',
    '«Воспитанный верой» недоступен в Pathbuilder 2e':
        '«Воспитанный верой» недоступен в RuneSheet RU  ',
    'Нажмите «Назад», чтобы вернуться в Pathbuilder':
        'Нажмите «Назад», чтобы вернуться в RuneSheet  ',
    'Удалить старое изображение портрета из папки Pathbuilder2e? Внимание: оно будет удалено у всех персонажей, использующих этот портрет!':
        'Удалить старое изображение портрета из папки RuneSheet RU ? Внимание: оно будет удалено у всех персонажей, использующих этот портрет!',
    'Файл не распознан как база данных Pathbuilder 2e!':
        'Файл не распознан как база данных RuneSheet RU  !',
}


def _uleb(d: bytes | bytearray, o: int):
    v = s = 0
    start = o
    while True:
        b = d[o]; o += 1; v |= (b & 0x7f) << s
        if b < 0x80:
            return v, o, o-start
        s += 7


def _enc_uleb(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7f; n >>= 7
        if n: b |= 0x80
        out.append(b)
        if not n: return bytes(out)


def _item(s: str) -> bytes:
    return _enc_uleb(len(s.encode('utf-16le'))//2) + s.encode('utf-8') + b'\0'


def strings_with_meta(d: bytes):
    u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    ss, so = u32(0x38), u32(0x3c)
    out = []
    for i in range(ss):
        off = u32(so + 4*i)
        _, q, _ = _uleb(d, off)
        e = d.index(0, q)
        s = d[q:e].decode('utf-8','replace')
        # DEX string_data_items are contiguous in this file; physical capacity is next string offset where sorted ids are physical order too.
        out.append((i, off, e+1-off, s))
    return ss, so, out


def patch_exact_strings(dex: bytes, replacements: dict[str, str]) -> bytes:
    # Every product build gets the safe shell cleanup in addition to the explicit
    # package/data-path replacements supplied by build.py.
    replacements = {**PRODUCT_SHELL_REPLACEMENTS, **replacements}

    d = bytearray(dex)
    ss, so, meta = strings_with_meta(dex)
    by_text = {s:(i,off,cap) for i,off,cap,s in meta}
    for old,new in replacements.items():
        if old not in by_text:
            raise KeyError(f'DEX string not found: {old}')
        i,off,cap = by_text[old]
        old_item, new_item = _item(old), _item(new)
        if len(old_item) != cap:
            raise ValueError(f'unexpected DEX item size for {old!r}')
        if len(new_item) != cap:
            raise ValueError(f'replacement must preserve exact DEX item size: {old!r} ({cap}) -> {new!r} ({len(new_item)})')
        d[off:off+cap] = new_item

    # Re-parse raw MUTF-8 and ensure string_ids remain strictly sorted as required by ART.
    def mutf8_units(raw: bytes):
        out=[]; i=0
        while i < len(raw):
            b=raw[i]
            if b < 0x80:
                out.append(b); i += 1
            elif b & 0xe0 == 0xc0:
                out.append(((b & 31) << 6) | (raw[i+1] & 63)); i += 2
            elif b & 0xf0 == 0xe0:
                out.append(((b & 15) << 12) | ((raw[i+1] & 63) << 6) | (raw[i+2] & 63)); i += 3
            else:
                raise ValueError(f'unsupported MUTF-8 lead byte {b:#x}')
        return tuple(out)
    u32=lambda o:struct.unpack_from('<I',d,o)[0]
    vals=[]
    for i in range(ss):
        off=u32(so+4*i); _,q,_=_uleb(d,off); e=d.index(0,q); vals.append(mutf8_units(bytes(d[q:e])))
    bad=[(i,vals[i-1],vals[i]) for i in range(1,len(vals)) if vals[i-1] >= vals[i]]
    if bad:
        raise ValueError(f'DEX string_ids ordering broken at {bad[0][0]}')

    d[12:32] = hashlib.sha1(d[32:]).digest()
    struct.pack_into('<I', d, 8, zlib.adler32(d[12:]) & 0xffffffff)
    return bytes(d)
