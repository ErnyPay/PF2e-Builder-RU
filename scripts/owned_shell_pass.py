from __future__ import annotations

import struct

from manifest_patch import _find_manifest_pool, _iter_start_elements, _u32, _put_u32, build_string_pool
from sheet_dialog_pass import _add_android_attr, patch_root_background

UTF8_FLAG = 0x100
TYPE_REFERENCE = 0x01
TYPE_DIMENSION = 0x05
TYPE_INT_BOOLEAN = 0x12
TYPE_INT_DEC = 0x10
NO_INDEX = 0xFFFFFFFF
ABOUT_SLOT_ID = 0x7F090119  # inherited theme row, reused as safe RuneSheet About entry
NAV_PATRON_ID = 0x7F090349
ANDROID_VISIBLE = 0x01010194
LEGACY_PROMO_IDS = {
    0x7F090114, # Starbuilder cross-promo
    0x7F0900D6, # Pathbuilder 1e cross-promo
}
THEME_DIALOG_COLLAPSE_IDS = {
    0x7F09011C, # parchment row
    0x7F09011A, # classic row
    0x7F09011B, # dark row
    0x7F0900FC, # select-theme action
}
DRAWER_MENUS = {
    'res/menu/activity_main_drawer.xml',
    'res/menu/activity_main_drawer_icons.xml',
}

# Non-gameplay shells that should visually belong to RuneSheet as a coherent
# service layer. Rules browsers/content dialogs are intentionally not included.
SERVICE_SURFACES = {
    'res/layout/dialog_fragment_frontpage_more.xml',
    'res/layout/dialog_fragment_options.xml',
    'res/layout/dialog_fragment_database_management.xml',
    'res/layout/dialog_fragment_custom_pack.xml',
    'res/layout/dialog_fragment_upgrade.xml',
    'res/layout/dialog_fragment_report_bug.xml',
    'res/layout/dialog_fragment_report_bug_actual.xml',
    'res/layout/dialog_fragment_open_by_id.xml',
    'res/layout/dialog_fragment_firebase_connect.xml',
    'res/layout/dialog_fragment_json.xml',
    'res/layout/dialog_fragment_theme.xml',
    'res/layout/dialog_fragment_new_save.xml',
    'res/layout/dialog_fragment_save.xml',
    'res/layout/dialog_fragment_load_new.xml',
    'res/layout/dialog_fragment_liences.xml',
    'res/layout/dialog_fragment_export_pdf.xml',
    'res/layout/dialog_fragment_export_stat_block.xml',
    'res/layout/dialog_fragment_campaign_management.xml',
    'res/layout/dialog_fragment_move_folder.xml',
}

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
    'If you have just reinstalled the app, have previously bought the full unlock and the app is not unlocking, there may be an error with the Play Store on your device. Try the following to fix:\n\n 1) If you have multiple accounts on your device, make sure you definitely logged into your device and playstore with the account that you bought the app on. \n\n2) Uninstall the app (export the database if you have local files first). \n\n3) Go to settings -> Apps -> Google Play Store -> Storage and Cache -> Clear Storage and Clear Cache. \n\n4) Reboot the device \n\n5) Reinstall the app. (import the database if you had local files). The play store cache can sometimes take up to 24 hours to populate on a new device, so please give it some time to resolve.\n\n\nIf you continue to have issues please use Report Bug and open a new issue.':
        'Полный доступ пока проверяется через унаследованный Google Play Billing. Если ранее приобретённый доступ не восстановился, убедитесь, что на устройстве выбран тот же Google-аккаунт. Перед переустановкой обязательно экспортируйте локальную базу персонажей. После очистки кэша Google Play и перезагрузки восстановление покупки может занять некоторое время. Если проблема сохраняется, используйте «Отправить отчёт».',
    OLD_AD_APP_ID: TEST_AD_APP_ID,
    OLD_BANNER_ID: TEST_BANNER_ID,
}

DRAWER_REPLACEMENTS = {
    'About Creator': '',
    'Character Options': 'Настройки персонажа',
    'Character is remastered!': 'Ремастер включён',
    'Connect to GM': 'GM-связь (совместимость)',
    'Convert to Remaster Rules': 'Перейти на ремастер',
    'Custom Ability Increases': 'Настройка характеристик',
    'Custom Feat Choices': 'Настройка черт',
    'Custom Skill Increases': 'Настройка навыков',
    'Exit to Start Page': 'На стартовый экран',
    'Export Character': 'Экспорт персонажа',
    'Feat Browser': 'Каталог черт',
    'Open Character': 'Открыть персонажа',
    'Remaster Information': 'О ремастере',
    'Report Bug': 'Отправить отчёт',
    'Save': 'Сохранить',
    'Upgrade and Remove Adverts': 'Полный доступ RuneSheet',
}

LAYOUT_REPLACEMENTS = {
    'res/layout/dialog_fragment_frontpage_more.xml': {
        'App Options': 'Настройки RuneSheet', 'Custom Packs': 'Пользовательские наборы',
        'Database Management': 'Данные персонажей', 'Manage Campaigns': 'Кампании',
        'Open Character by ID': 'Открыть по ID (совместимость)', 'Set App Theme': 'О RuneSheet',
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
    'res/layout/dialog_fragment_report_bug.xml': {},
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
    'res/layout/dialog_fragment_theme.xml': {
        'Set App Theme': 'RuneSheet RU',
        'App Theme can be set at any time via the App Options button on the front page. Classic or Dark may give a better experience on low end devices.': 'RuneSheet RU — лист и конструктор персонажа PF2e. В приложении используется единый фиксированный стиль; сетевые функции совместимости отмечены отдельно.',
        'Select Theme': '',
        'Parchment': '', 'Classic': '', 'Dark': '',
    },
    'res/layout/dialog_fragment_new_save.xml': {
        'First Save': 'Первое сохранение',
        'Local Folder': 'Локальная папка',
        'Save to GDrive': 'Облако (совместимость)',
        'Save to Local Folder': 'Сохранить локально',
        'Warning: cloud storage will use mobile data allowances where wifi is not available.': 'Облачное сохранение может использовать мобильный интернет при отсутствии Wi-Fi.',
    },
    'res/layout/dialog_fragment_save.xml': {
        'Make a new copy': 'Создать копию',
        'Warning: cloud storage will use mobile data allowances where wifi is not available.': 'Облачное сохранение может использовать мобильный интернет при отсутствии Wi-Fi.',
    },
    'res/layout/dialog_fragment_move_folder.xml': {
        'Copy Character': 'Копировать персонажа',
        'Warning: cloud storage will use mobile data allowances where wifi is not available.': 'Облачное сохранение может использовать мобильный интернет при отсутствии Wi-Fi.',
    },
    'res/layout/dialog_fragment_load_new.xml': {},
    'res/layout/dialog_fragment_liences.xml': {},
    'res/layout/dialog_fragment_export_pdf.xml': {
        'Export Character': 'Экспорт персонажа',
        'Export Character Sheet': 'Лист персонажа (PDF)',
        'Export JSON file': 'Файл JSON',
        'Export Spellbook': 'Книга заклинаний',
        'Export Stat Block': 'Статблок',
        'Share character by link': 'Поделиться ссылкой (совместимость)',
        'Dual Class is not supported on the PDF Character Sheet': 'Двойной класс пока не поддерживается в PDF-листе персонажа',
    },
    'res/layout/dialog_fragment_export_stat_block.xml': {
        'Export PDF': 'Экспорт PDF',
        'Export Statblock': 'Экспорт статблока',
        'Hide all action descriptions': 'Скрыть все описания действий',
        'Hide common action descriptions (Shield Block etc)': 'Скрыть описания обычных действий (Shield Block и т. п.)',
    },
    'res/layout/dialog_fragment_campaign_management.xml': {
        'Campaign Management': 'Кампании',
        'Add Campaign': 'Добавить кампанию',
        'Import Campaign': 'Импорт кампании',
        'You can create, export and import Campaigns here to ensure that character creation uses specific options and sources.': 'Здесь можно создавать, экспортировать и импортировать кампании с нужными настройками и источниками.',
    },
    'res/layout/listview_item_load.xml': {'Copy to Folder': 'Копировать в папку'},
    'res/menu/activity_main_drawer.xml': DRAWER_REPLACEMENTS,
    'res/menu/activity_main_drawer_icons.xml': DRAWER_REPLACEMENTS,
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


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _collapse_id_rows(blob: bytes, target_ids: set[int]) -> bytes:
    pool = _find_manifest_pool(blob)
    out = bytearray(blob)
    found=set()
    for _, _, attrs in _iter_start_elements(bytes(out), pool.strings):
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        ident = amap.get('id')
        if not ident or ident[2] != TYPE_REFERENCE or ident[3] not in target_ids:
            continue
        for name in ('layout_height', 'padding', 'layout_marginTop', 'layout_marginBottom'):
            if name in amap:
                _set_typed(out, amap[name][0], TYPE_DIMENSION, 0x00000001)  # 0dp
        found.add(ident[3])
    missing=target_ids-found
    if missing:
        raise ValueError(f'collapsible rows not found: {[hex(x) for x in sorted(missing)]}')
    return bytes(out)


def _relax_service_text(blob: bytes) -> bytes:
    """Allow long service-shell labels to wrap without touching game content."""
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
    return bytes(out)


def _hide_frontpage_legacy_rows(blob: bytes) -> bytes:
    """Keep inherited promo view IDs/listener wiring but remove obsolete products.

    The former theme row is intentionally NOT hidden anymore: it is reused as
    an in-app `О RuneSheet` entry. DialogTheme still exists for binary safety,
    but all theme-choice rows inside it remain collapsed.
    """
    return _collapse_id_rows(blob,LEGACY_PROMO_IDS)


def _hide_creator_menu_item(blob: bytes) -> bytes:
    # Keep nav_patron ID so NavigationControl remains binary-compatible, but the
    # old creator/Patreon item is not part of the RuneSheet product navigation.
    return _add_android_attr(
        blob,target_tag='item',target_id=NAV_PATRON_ID,name='visible',
        attr_rid=ANDROID_VISIBLE,dtype=TYPE_INT_BOOLEAN,data=0,
    )


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
    out = _replace_xml_strings(blob, replacements) if replacements else blob
    if path in SERVICE_SURFACES:
        out = patch_root_background(out)
        out = _relax_service_text(out)
    if path == 'res/layout/dialog_fragment_frontpage_more.xml':
        out = _hide_frontpage_legacy_rows(out)
    elif path == 'res/layout/dialog_fragment_theme.xml':
        out = _collapse_id_rows(out,THEME_DIALOG_COLLAPSE_IDS)
    elif path in DRAWER_MENUS:
        out = _hide_creator_menu_item(out)
    return out
