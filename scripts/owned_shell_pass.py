from __future__ import annotations

import struct

from manifest_patch import _find_manifest_pool, _u32, _put_u32, build_string_pool

UTF8_FLAG = 0x100
OLD_AD_APP_ID = 'ca-app-pub-8849615353397054~3022553003'
OLD_BANNER_ID = 'ca-app-pub-8849615353397054/1681551174'
TEST_AD_APP_ID = 'ca-app-pub-3940256099942544~3347511713'
TEST_BANNER_ID = 'ca-app-pub-3940256099942544/6300978111'

ARSC_REPLACEMENTS = {
    'Инструкция\n\n1) Введите имя игрока, чтобы мастер мог вас определить.\n2) Введите ID мастера и пароль группы ниже (их выдаёт мастер в режиме GM на сайте Pathbuilder).\n\nВнимание: мастер получит полный доступ к вашему персонажу, включая право редактирования.':
        'Инструкция\n\n1) Введите имя игрока.\n2) Введите ID мастера и пароль группы из веб-режима совместимости.\n\nВнимание: мастер получит полный доступ к персонажу, включая редактирование.',
    'Пользовательские наборы — это пакеты стороннего контента, созданные через инструмент веб-версии. Pathbuilder не отвечает за содержимое таких наборов; используйте их на свой риск.':
        'Пользовательские наборы — сторонний контент из веб-инструмента совместимости. RuneSheet RU не проверяет содержимое таких наборов; используйте их на свой риск.',
    'Животные-компаньоны, эйдолоны, конструкты и фамильяры доступны только в полной версии Pathbuilder 2e.\n\nЕздовые животные в Pathbuilder 2e недоступны.':
        'Животные-компаньоны, эйдолоны, конструкты и фамильяры доступны при полном доступе.\n\nЕздовые животные пока недоступны.',
    'Pathbuilder2e хочет создать SQL-базу персонажей во внешнем хранилище. Если не дать разрешение, база будет создана во внутреннем хранилище приложения и удалится при удалении приложения.':
        'RuneSheet RU может создать SQL-базу персонажей во внешнем хранилище. Без разрешения база останется во внутреннем хранилище и удалится вместе с приложением.',
    'Обновитесь до полной версии Pathbuilder 2e для Android, чтобы убрать рекламу. Также станут доступны животные-компаньоны, фамильяры, облачное хранилище и дополнительные настройки, включая выбор способностей, навыков, доспехов, оружия и снаряжения.\n\nВерсии для Android и Web являются отдельными продуктами и приобретаются отдельно.':
        'Полный доступ открывает дополнительные функции персонажа и облачное хранение. Лицензия и часть сетевых функций пока работают через унаследованный слой совместимости.\n\nРекламные компоненты в RuneSheet RU отключены.',
    OLD_AD_APP_ID: TEST_AD_APP_ID,
    OLD_BANNER_ID: TEST_BANNER_ID,
}

LAYOUT_REPLACEMENTS = {
    'res/layout/dialog_fragment_frontpage_more.xml': {
        'App Options': 'Настройки RuneSheet', 'Custom Packs': 'Пользовательские наборы',
        'Database Management': 'Данные персонажей', 'Manage Campaigns': 'Кампании',
        'Open Character by ID': 'Открыть по ID (совместимость)', 'Set App Theme': 'Оформление',
    },
    'res/layout/dialog_fragment_options.xml': {
        'Options': 'Настройки RuneSheet', 'Standard Options': 'Основные', 'Advanced Options': 'Расширенные',
        'Remaster Options': 'Ремастер', 'Manage Available Rulebooks': 'Доступные книги',
    },
    'res/layout/dialog_fragment_database_management.xml': {
        'Database Management': 'Данные персонажей', 'Export': 'Экспорт', 'Export Local Database': 'Экспорт базы',
        'Export your local database if you wish to transfer your characters to a new device or create a back-up.': 'Экспортируйте локальную базу для переноса персонажей или резервной копии.',
        'Import': 'Импорт', 'Import Local Database': 'Импорт базы',
        'Warning - this will overwrite your current local database!': 'Внимание: текущая локальная база будет перезаписана!',
    },
    'res/layout/dialog_fragment_custom_pack.xml': {
        'Custom Packs': 'Пользовательские наборы', 'Import': 'Импорт', 'Import Custom Pack': 'Импорт набора',
    },
    'res/layout/dialog_fragment_upgrade.xml': {'Upgrade App': 'Полный доступ RuneSheet'},
    'res/layout/dialog_fragment_report_bug_actual.xml': {
        'Submit Bug': 'Отправить отчёт', 'Your bug': 'Описание ошибки', 'Optional email address': 'Email (необязательно)',
        'By including an email address you give permission to receive emails regarding this bug.  Your email address will not be visible to other users.': 'Email нужен только для ответа по отчёту и не показывается другим пользователям.',
    },
    'res/layout/dialog_fragment_open_by_id.xml': {
        'Open Character by ID': 'Открыть по ID (совместимость)', 'Character ID': 'ID персонажа',
        'ID общего персонажа берётся из ссылки режима совместимости Pathbuilder; это число в конце параметра build.': 'ID общего персонажа берётся из ссылки веб-режима совместимости; это число в конце параметра build.',
    },
    'res/layout/dialog_fragment_firebase_connect.xml': {
        'GM Connect': 'GM-связь (совместимость)', 'Connect': 'Подключить', 'Disconnect': 'Отключить',
        'Your name': 'Имя игрока', 'GM ID (Given to you by your GM)': 'ID мастера',
        'Group Password (Given to you by your GM)': 'Пароль группы', 'Remember Password?': 'Запомнить пароль?',
        'GM-режим пока использует унаследованный веб-сервис Pathbuilder (режим совместимости).': 'GM-режим пока использует унаследованный веб-сервис (режим совместимости).',
    },
    'res/layout/dialog_fragment_json.xml': {'Export JSON': 'Экспорт JSON', 'View JSON file': 'Открыть JSON'},
}


def _read_len8(blob: bytes | bytearray, p: int):
    x = blob[p]; p += 1
    if x & 0x80:
        return ((x & 0x7f) << 8) | blob[p], p + 1, 2
    return x, p, 1


def _enc_len8_fixed(n: int, width: int) -> bytes:
    if width == 1:
        if n > 0x7f: raise ValueError('length no longer fits one-byte prefix')
        return bytes([n])
    if n > 0x7fff: raise ValueError('length too large')
    return bytes([0x80 | ((n >> 8) & 0x7f), n & 0xff])


def patch_arsc_owned_shell(blob: bytes) -> bytes:
    """Patch only global product-shell strings in-place; resource indexes never move."""
    d = bytearray(blob)
    root_hs = struct.unpack_from('<H', d, 2)[0]
    off = root_hs
    typ, hs, _ = struct.unpack_from('<HHI', d, off)
    if typ != 1: raise ValueError('global string pool missing')
    count, _, flags, strings_start, _ = struct.unpack_from('<IIIII', d, off + 8)
    if not flags & UTF8_FLAG: raise ValueError('expected UTF-8 global pool')
    base = off + strings_start
    found = {k: 0 for k in ARSC_REPLACEMENTS}
    for i in range(count):
        rel = struct.unpack_from('<I', d, off + hs + 4*i)[0]
        p = base + rel
        old_u16, p1, w1 = _read_len8(d, p)
        old_b, p2, w2 = _read_len8(d, p1)
        s = bytes(d[p2:p2+old_b]).decode('utf-8', 'replace')
        if s not in ARSC_REPLACEMENTS: continue
        new = ARSC_REPLACEMENTS[s]
        raw = new.encode('utf-8'); units = len(new.encode('utf-16le')) // 2
        if len(raw) > old_b or units > old_u16:
            raise ValueError(f'owned-shell replacement too long: {s!r}')
        d[p:p+w1] = _enc_len8_fixed(units, w1)
        d[p1:p1+w2] = _enc_len8_fixed(len(raw), w2)
        d[p2:p2+len(raw)] = raw
        d[p2+len(raw)] = 0
        for q in range(p2+len(raw)+1, p2+old_b+1): d[q] = 0
        found[s] += 1
    bad = [(k,v) for k,v in found.items() if v != 1]
    if bad: raise ValueError(f'owned-shell ARSC hits: {bad}')
    return bytes(d)


def _replace_xml_strings(blob: bytes, replacements: dict[str, str]) -> bytes:
    pool = _find_manifest_pool(blob)
    strings = list(pool.strings)
    changed = False
    for i, value in enumerate(strings):
        if value in replacements:
            strings[i] = replacements[value]; changed = True
    if not changed: return blob
    new_pool = build_string_pool(strings, pool.flags)
    delta = len(new_pool) - pool.size
    out = bytearray(blob[:pool.offset] + new_pool + blob[pool.offset + pool.size:])
    _put_u32(out, 4, _u32(blob, 4) + delta)
    return bytes(out)


def patch_manifest_owned_shell(blob: bytes) -> bytes:
    return _replace_xml_strings(blob, {OLD_AD_APP_ID: TEST_AD_APP_ID})


def patch_owned_shell_layout(path: str, blob: bytes) -> bytes:
    replacements = LAYOUT_REPLACEMENTS.get(path)
    return _replace_xml_strings(blob, replacements) if replacements else blob
