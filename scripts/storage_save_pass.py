from __future__ import annotations

import hashlib
import struct
import zlib

from dex_patch import _item, _uleb, strings_with_meta
from storage_boundary import verify_storage_boundary

# First transition-runtime ownership slice.  We keep the proven character
# serialization / SQL schema, but RuneSheet owns the save policy: cloud storage
# is inert and local persistence is exposed through RuneSheet-named adapters.
OWNED_TYPE_RENAMES = {
    'Lcom/redrazors/pathbuilder2e/filemanagement/CombinedHelper$1;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/CoreRuneSheet$1;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/CombinedHelper;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/CoreRuneSheet;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/SavedStateFile;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/RuneSheetState;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/filecomponents/FileManagementCharacter;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/CharacterStore;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/filecomponents/FileManagementCustom;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/CustomStore;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/filecomponents/FileManagementCustomBackgrounds;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/CustomStoreBackgrounds;',
    'Lcom/redrazors/pathbuilder2e/filemanagement/filecomponents/FileManagementFolders;':
        'Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/FolderStore;',
}

CLOUD_HELPER = 'Lcom/redrazors/pathbuilder2e/filemanagement/CloudStorageHelper;'
CLOUD_VOID_METHODS = (
    'access$200', 'checkInternet', 'copyFileFromCloudToCloud', 'copyFileToLocal',
    'createFile', 'deleteFile', 'fetchFileMetadata', 'getFileContents',
    'saveFile', 'updateFile', 'updateFileMetadata',
)
CLOUD_UI_VOID_METHODS = (
    ('Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogNewSave;', 'doGDriveSave'),
    ('Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogMoveFolder;', 'copyToCloud'),
    ('Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogLoadNew;', 'setCloudFiles'),
)


def _u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from('<I', data, off)[0]


def _u16(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from('<H', data, off)[0]


def _index(dex: bytes):
    strings = [s for _, _, _, s in strings_with_meta(dex)[2]]
    type_size, type_off = _u32(dex, 0x40), _u32(dex, 0x44)
    type_ids = [_u32(dex, type_off + 4*i) for i in range(type_size)]
    types = [strings[i] for i in type_ids]

    proto_size, proto_off = _u32(dex, 0x48), _u32(dex, 0x4C)
    protos = []
    for i in range(proto_size):
        ret = _u32(dex, proto_off + 12*i + 4)
        params_off = _u32(dex, proto_off + 12*i + 8)
        params = []
        if params_off:
            count = _u32(dex, params_off)
            params = [types[_u16(dex, params_off + 4 + 2*j)] for j in range(count)]
        protos.append((types[ret], params))

    method_size, method_off = _u32(dex, 0x58), _u32(dex, 0x5C)
    methods = []
    for i in range(method_size):
        class_idx, proto_idx, name_idx = struct.unpack_from('<HHI', dex, method_off + 8*i)
        methods.append((types[class_idx], strings[name_idx], proto_idx))

    code = {}
    class_size, class_off = _u32(dex, 0x60), _u32(dex, 0x64)
    for c in range(class_size):
        class_data = _u32(dex, class_off + 32*c + 24)
        if not class_data:
            continue
        p = class_data
        sf, p, _ = _uleb(dex, p); inf, p, _ = _uleb(dex, p)
        direct, p, _ = _uleb(dex, p); virtual, p, _ = _uleb(dex, p)
        for count in (sf, inf):
            index = 0
            for _ in range(count):
                diff, p, _ = _uleb(dex, p); _, p, _ = _uleb(dex, p); index += diff
        for count in (direct, virtual):
            index = 0
            for _ in range(count):
                diff, p, _ = _uleb(dex, p); _, p, _ = _uleb(dex, p)
                code_off, p, _ = _uleb(dex, p); index += diff
                if code_off:
                    code[index] = code_off
    return strings, protos, methods, code


def _find_method(protos, methods, cls: str, name: str, params=None, ret='V') -> int:
    found = []
    for i, (owner, method, proto_idx) in enumerate(methods):
        if owner != cls or method != name:
            continue
        actual_ret, actual_params = protos[proto_idx]
        if ret is not None and actual_ret != ret:
            continue
        if params is not None and actual_params != params:
            continue
        found.append(i)
    if len(found) != 1:
        raise ValueError(f'expected one method {cls}->{name}, got {found!r}')
    return found[0]


def _set_code_unit(data: bytearray, code_off: int, unit: int, value: int) -> None:
    insns_size = _u32(data, code_off + 12)
    if not (0 <= unit < insns_size):
        raise ValueError(f'code unit outside method: {unit}/{insns_size}')
    struct.pack_into('<H', data, code_off + 16 + 2*unit, value)


def _mutf8_units(raw: bytes):
    out = []
    i = 0
    while i < len(raw):
        b = raw[i]
        if b < 0x80:
            out.append(b); i += 1
        elif b & 0xE0 == 0xC0:
            out.append(((b & 31) << 6) | (raw[i+1] & 63)); i += 2
        elif b & 0xF0 == 0xE0:
            out.append(((b & 15) << 12) | ((raw[i+1] & 63) << 6) | (raw[i+2] & 63)); i += 3
        else:
            raise ValueError(f'unsupported MUTF-8 lead byte {b:#x}')
    return tuple(out)


def _verify_string_order(data: bytes) -> None:
    size, table = _u32(data, 0x38), _u32(data, 0x3C)
    values = []
    for i in range(size):
        off = _u32(data, table + 4*i)
        _, payload, _ = _uleb(data, off)
        end = data.index(0, payload)
        values.append(_mutf8_units(data[payload:end]))
    bad = [i for i in range(1, len(values)) if values[i-1] >= values[i]]
    if bad:
        raise ValueError(f'DEX string_ids ordering broken at {bad[0]}')


def verify_owned_local_save(dex: bytes) -> dict:
    strings, protos, methods, code = _index(dex)
    string_set = set(strings)
    old_left = sorted(set(OWNED_TYPE_RENAMES) & string_set)
    missing_new = sorted(set(OWNED_TYPE_RENAMES.values()) - string_set)
    if old_left or missing_new:
        raise ValueError(f'owned storage type migration incomplete: old={old_left!r} new_missing={missing_new!r}')

    # MainActivity.saveFile(boolean): move-result v4 from isCloudStorage is replaced
    # by const/4 v4,#0, making the following if-eqz always take the local path.
    main_save = _find_method(protos, methods,
        'Lcom/redrazors/pathbuilder2e/MainActivity;', 'saveFile', ['Z'])
    main_code = code[main_save]
    if _u16(dex, main_code + 16 + 2*0x59) != 0x0412:
        raise ValueError('MainActivity.saveFile(Z) is not forced to local storage')

    # DialogSave copy path: cloud sentinel branch is replaced with goto/16 local.
    dialog_save = _find_method(protos, methods,
        'Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogSave;', 'simplerSaferSave', ['Z'])
    dialog_code = code[dialog_save]
    if (_u16(dex, dialog_code + 16 + 2*6), _u16(dex, dialog_code + 16 + 2*7)) != (0x0029, 0x0013):
        raise ValueError('DialogSave cloud-copy branch is still reachable')

    inert = []
    for cls, name in CLOUD_UI_VOID_METHODS:
        mid = _find_method(protos, methods, cls, name, None, 'V')
        if _u16(dex, code[mid] + 16) != 0x000E:
            raise ValueError(f'cloud UI method still active: {cls}->{name}')
        inert.append(f'{cls}->{name}')
    for name in CLOUD_VOID_METHODS:
        mid = _find_method(protos, methods, CLOUD_HELPER, name, None, 'V')
        if _u16(dex, code[mid] + 16) != 0x000E:
            raise ValueError(f'cloud helper method still active: {name}')
        inert.append(f'{CLOUD_HELPER}->{name}')

    # Prove that the local persistence calls now resolve through RuneSheet-named
    # runtime types while the underlying character format remains untouched.
    required = (
        ('Lcom/redrazors/pathbuilder2e/filemanagement/CoreRuneSheet;', 'saveFile'),
        ('Lcom/redrazors/pathbuilder2e/filemanagement/CoreRuneSheet;', 'saveNewCharacterAndAddToFolder'),
        ('Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/CharacterStore;', 'saveFile'),
        ('Lcom/redrazors/pathbuilder2e/filemanagement/runesheet/FolderStore;', 'addCharacterToFolder'),
    )
    for cls, name in required:
        if not any(owner == cls and method == name for owner, method, _ in methods):
            raise ValueError(f'owned local-save runtime method missing: {cls}->{name}')

    _verify_string_order(dex)
    sig_ok = dex[12:32] == hashlib.sha1(dex[32:]).digest()
    checksum_ok = _u32(dex, 8) == (zlib.adler32(dex[12:]) & 0xFFFFFFFF)
    if not sig_ok or not checksum_ok:
        raise ValueError('owned local-save DEX checksum/signature invalid')
    return {
        'ok': True,
        'policy': 'local-only',
        'owned_runtime_types': sorted(OWNED_TYPE_RENAMES.values()),
        'inert_cloud_methods': len(inert),
        'legacy_format_preserved': True,
    }


def patch_owned_local_save(dex: bytes) -> bytes:
    verify_storage_boundary(dex)
    strings, protos, methods, code = _index(dex)
    by_text = {s: (off, cap) for _, off, cap, s in strings_with_meta(dex)[2]}
    out = bytearray(dex)

    for old, new in OWNED_TYPE_RENAMES.items():
        if old not in by_text:
            raise KeyError(f'owned storage type missing: {old}')
        off, cap = by_text[old]
        encoded = _item(new)
        if len(encoded) > cap:
            raise ValueError(f'owned storage type exceeds DEX slot: {old!r} -> {new!r}')
        out[off:off+cap] = encoded + b'\0' * (cap-len(encoded))

    main_save = _find_method(protos, methods,
        'Lcom/redrazors/pathbuilder2e/MainActivity;', 'saveFile', ['Z'])
    main_code = code[main_save]
    if _u16(out, main_code + 16 + 2*0x59) != 0x040A:
        raise ValueError('unexpected MainActivity.saveFile(Z) baseline')
    _set_code_unit(out, main_code, 0x59, 0x0412)

    dialog_save = _find_method(protos, methods,
        'Lcom/redrazors/pathbuilder2e/navigation/views/dialogs/DialogSave;', 'simplerSaferSave', ['Z'])
    dialog_code = code[dialog_save]
    if (_u16(out, dialog_code + 16 + 2*6), _u16(out, dialog_code + 16 + 2*7)) != (0x0333, 0x0013):
        raise ValueError('unexpected DialogSave.simplerSaferSave baseline')
    _set_code_unit(out, dialog_code, 6, 0x0029)  # goto/16
    _set_code_unit(out, dialog_code, 7, 0x0013)  # local target (+19 code units)

    for cls, name in CLOUD_UI_VOID_METHODS:
        mid = _find_method(protos, methods, cls, name, None, 'V')
        _set_code_unit(out, code[mid], 0, 0x000E)
    for name in CLOUD_VOID_METHODS:
        mid = _find_method(protos, methods, CLOUD_HELPER, name, None, 'V')
        _set_code_unit(out, code[mid], 0, 0x000E)

    out[12:32] = hashlib.sha1(out[32:]).digest()
    struct.pack_into('<I', out, 8, zlib.adler32(out[12:]) & 0xFFFFFFFF)
    result = bytes(out)
    verify_owned_local_save(result)
    return result
