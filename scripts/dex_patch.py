from __future__ import annotations
import hashlib, struct, zlib


# User-visible shell/runtime literals that still live directly in classes2.dex.
# Replacements stay inside the existing string_data slot, so string offsets and
# all method/class references remain unchanged. Real compatibility backend URLs,
# inherited class descriptors and gameplay/rules messages are intentionally NOT
# rewritten here.
PRODUCT_SHELL_REPLACEMENTS = {
    'Share Pathbuilder 2e Character':
        'Share RuneSheet RU Character',
    '.  To view this build you need to open it on an android device with version 256+ Pathbuilder 2e installed. ':
        '.  To view this build, open it on Android with RuneSheet RU installed. ',
    'https://gitlab.com/doctor.unspeakable/pathbuilder-2e/-/issues':
        'https://github.com/ErnyPay/PF2e-Builder-RU/issues',
    'Нажмите «Назад», чтобы вернуться в Pathbuilder':
        'Нажмите «Назад» для возврата в RuneSheet RU',
    'Удалить старое изображение портрета из папки Pathbuilder2e? Внимание: оно будет удалено у всех персонажей, использующих этот портрет!':
        'Удалить старое изображение портрета из папки RuneSheet RU? Внимание: оно будет удалено у всех персонажей, использующих этот портрет!',
    'Файл не распознан как база данных Pathbuilder 2e!':
        'Файл не распознан как база данных RuneSheet RU!',
}

# This is gameplay-facing behavior, not product shell. Keep it as an explicit
# negative guard so future ownership passes do not silently rewrite it again.
PROTECTED_GAMEPLAY_DEX_LITERALS = {
    '«Воспитанный верой» недоступен в Pathbuilder 2e',
}

FIXED_THEME_TARGET_METHODS = {
    ('Lcom/redrazors/pathbuilder2e/MainActivity;', 'onCreate'),
    ('Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogTheme;', 'setTheme'),
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
        # Pinned baseline string_data items are contiguous. The original item
        # size is therefore a safe maximum slot size for shorter shell strings.
        out.append((i, off, e+1-off, s))
    return ss, so, out


def _force_fixed_theme_refs(d: bytearray, strings: list[str]) -> None:
    """Map all inherited Classic/Dark style choices to the RuneSheet AppTheme.

    This preserves SharedPreferences and old dialog IDs for binary compatibility,
    but a previously saved Classic/Dark preference can no longer change the
    visual theme. Only the two pinned theme-selection methods are modified.
    """
    u32=lambda o:struct.unpack_from('<I',d,o)[0]
    type_size,type_off=u32(0x40),u32(0x44)
    type_ids=[u32(type_off+4*i) for i in range(type_size)]

    field_size,field_off=u32(0x50),u32(0x54)
    style_fields={}
    for i in range(field_size):
        class_idx,_,name_idx=struct.unpack_from('<HHI',d,field_off+8*i)
        if strings[type_ids[class_idx]] != 'Lcom/redrazors/pathbuilder2e/R$style;':
            continue
        name=strings[name_idx]
        if name in ('AppTheme','AppThemeDark','AppThemePlain'):
            style_fields[name]=i
    if set(style_fields) != {'AppTheme','AppThemeDark','AppThemePlain'}:
        raise ValueError(f'expected style fields missing: {style_fields}')

    method_size,method_off=u32(0x58),u32(0x5c)
    methods=[]
    for i in range(method_size):
        class_idx,_,name_idx=struct.unpack_from('<HHI',d,method_off+8*i)
        methods.append((strings[type_ids[class_idx]],strings[name_idx]))

    class_size,class_off=u32(0x60),u32(0x64)
    code_by_method={}
    for c in range(class_size):
        off=class_off+32*c
        class_data_off=u32(off+24)
        if not class_data_off:
            continue
        p=class_data_off
        static_fields,p,_=_uleb(d,p); instance_fields,p,_=_uleb(d,p)
        direct_methods,p,_=_uleb(d,p); virtual_methods,p,_=_uleb(d,p)
        for count in (static_fields,instance_fields):
            idx=0
            for _ in range(count):
                diff,p,_=_uleb(d,p); _,p,_=_uleb(d,p); idx += diff
        for count in (direct_methods,virtual_methods):
            idx=0
            for _ in range(count):
                diff,p,_=_uleb(d,p); _,p,_=_uleb(d,p); code_off,p,_=_uleb(d,p); idx += diff
                if code_off:
                    code_by_method[idx]=code_off

    wanted={i for i,m in enumerate(methods) if m in FIXED_THEME_TARGET_METHODS}
    if len(wanted) != len(FIXED_THEME_TARGET_METHODS):
        raise ValueError(f'fixed-theme target methods missing: {wanted}')

    old_fields={style_fields['AppThemeDark'],style_fields['AppThemePlain']}
    new_field=style_fields['AppTheme']
    patched=0
    per_method={}
    for method_idx in wanted:
        code_off=code_by_method.get(method_idx)
        if not code_off:
            raise ValueError(f'fixed-theme method has no code: {methods[method_idx]}')
        insns_size=u32(code_off+12)
        base=code_off+16
        hits=0
        # sget is format 21c: first code unit opcode/register, second unit field@BBBB.
        for unit in range(insns_size-1):
            first=struct.unpack_from('<H',d,base+2*unit)[0]
            if (first & 0xff) != 0x60:
                continue
            field_idx=struct.unpack_from('<H',d,base+2*(unit+1))[0]
            if field_idx in old_fields:
                struct.pack_into('<H',d,base+2*(unit+1),new_field)
                patched += 1; hits += 1
        per_method[methods[method_idx]]=hits

    # Pinned 2.56 baseline: MainActivity has two refs and DialogTheme has two.
    if patched != 4 or any(v != 2 for v in per_method.values()):
        raise ValueError(f'unexpected fixed-theme patch count: total={patched}, per_method={per_method}')


def patch_exact_strings(dex: bytes, replacements: dict[str, str]) -> bytes:
    """Patch pinned DEX strings without moving any string_data offsets.

    The historical function name is kept because build.py already imports it.
    New values may be shorter than their original slots; unused bytes are zeroed.
    """
    replacements = {**PRODUCT_SHELL_REPLACEMENTS, **replacements}

    d = bytearray(dex)
    ss, so, meta = strings_with_meta(dex)
    by_text = {s:(i,off,cap) for i,off,cap,s in meta}
    for old,new in replacements.items():
        if old not in by_text:
            raise KeyError(f'DEX string not found: {old}')
        _,off,cap = by_text[old]
        old_item, new_item = _item(old), _item(new)
        if len(old_item) != cap:
            raise ValueError(f'unexpected DEX item size for {old!r}')
        if len(new_item) > cap:
            raise ValueError(f'replacement exceeds DEX string slot: {old!r} ({cap}) -> {new!r} ({len(new_item)})')
        d[off:off+cap] = new_item + b'\0'*(cap-len(new_item))

    strings=[s for _,_,_,s in strings_with_meta(bytes(d))[2]]
    string_set=set(strings)
    old_shell=set(PRODUCT_SHELL_REPLACEMENTS)
    new_shell=set(PRODUCT_SHELL_REPLACEMENTS.values())
    remaining=old_shell & string_set
    missing_new=new_shell - string_set
    missing_gameplay=set(PROTECTED_GAMEPLAY_DEX_LITERALS) - string_set
    if remaining:
        raise ValueError(f'legacy product shell DEX strings remain: {sorted(remaining)!r}')
    if missing_new:
        raise ValueError(f'RuneSheet product shell DEX strings missing: {sorted(missing_new)!r}')
    if missing_gameplay:
        raise ValueError(f'protected gameplay DEX strings changed or missing: {sorted(missing_gameplay)!r}')

    _force_fixed_theme_refs(d,strings)

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
