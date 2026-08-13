from __future__ import annotations

from manifest_patch import _find_manifest_pool, _iter_start_elements
from ownership_runtime_pass import _attr_value, _set_typed, TYPE_INT_BOOLEAN

CONFIG_PROVIDER = 'com.redrazors.pathbuilder2e.ConfigProvider'
ANDROID_VISIBLE = 0x01010194

DRAWER_HIDE_IDS = {
    0x7F09034E,  # legacy Full Access / remove_ads purchase
    0x7F09034F,  # legacy Report Bug / old GitLab route
}
OPEN_BY_ID_ROW = 0x7F0900D5
OPEN_JSON_ROW = 0x7F0900AF

# Short UI-shell terminology only. These are labels/headings, not PF2 rules,
# descriptions, item text, feat text or protected database content.
SAFE_UI_TRANSLATIONS = {
    'Ability Boosts': 'Повышения характеристик',
    'Ability Boosts and Flaws': 'Повышения и недостатки характеристик',
    'Heighten': 'Повысить',
    'Learn this spell': 'Выучить заклинание',
    'Roll': 'Бросок',
    'Skill Training': 'Обучение навыкам',
    'Actions': 'Действия',
    'Finished': 'Готово',
    'search': 'Поиск',
    'Languages': 'Языки',
    'Hit Points': 'Пункты здоровья',
    'Copy to Folder': 'Копировать в папку',
    'Campaign Management': 'Управление кампанией',
    'Export Character': 'Экспорт персонажа',
    'Remaster Information': 'О ремастере',
    'Consitution': 'Выносливость',
    'Attacks': 'Атака',
    'Class DC': 'Классовая СЛ',
    'Defenses': 'Защита',
    'Key Ability': 'Ключевая характеристика',
    'Perception': 'Внимание',
    'Saving Throws': 'Испытания',
    'Skills': 'Навыки',
    'Spells': 'Заклинания',
    'Size': 'Размер',
    'Special': 'Особое',
    'Speed': 'Скорость',
}

RELEASE_LAYOUT_PATHS = {
    'res/menu/activity_main_drawer.xml',
    'res/menu/activity_main_drawer_icons.xml',
    'res/layout/dialog_fragment_frontpage_more.xml',
    'res/layout/dialog_fragment_json.xml',
    'res/layout/button_boost.xml',
    'res/layout/button_heighten.xml',
    'res/layout/button_known.xml',
    'res/layout/button_roll_small.xml',
    'res/layout/button_skills.xml',
    'res/layout/dialog_fragment_actions.xml',
    'res/layout/dialog_fragment_boosts_level.xml',
    'res/layout/dialog_fragment_boosts_start.xml',
    'res/layout/dialog_fragment_campaign_management.xml',
    'res/layout/dialog_fragment_custom_feat_choice.xml',
    'res/layout/dialog_fragment_equipment.xml',
    'res/layout/dialog_fragment_equipment_pc.xml',
    'res/layout/dialog_fragment_export_pdf.xml',
    'res/layout/dialog_fragment_feats.xml',
    'res/layout/dialog_fragment_formula.xml',
    'res/layout/dialog_fragment_languages.xml',
    'res/layout/dialog_fragment_new_books_check.xml',
    'res/layout/dialog_fragment_optin_books.xml',
    'res/layout/dialog_fragment_proficiency_buffs.xml',
    'res/layout/dialog_fragment_rituals.xml',
    'res/layout/dialog_fragment_rulebooks.xml',
    'res/layout/dialog_fragment_spells.xml',
    'res/layout/dialog_fragment_universal_feat_browser.xml',
    'res/layout/layout_boost_set.xml',
    'res/layout/layout_flaw_set.xml',
    'res/layout/layout_move_copy.xml',
    'res/layout/listview_item_ancestries.xml',
    'res/layout/listview_item_classes.xml',
    'res/layout/listview_item_load.xml',
    'res/layout/table_buttons.xml',
}


def harden_release_manifest(blob: bytes) -> bytes:
    """Make the inherited ConfigProvider internal-only.

    RC1 QA confirmed that its exported /fetchDB query can return app-private
    database state. RuneSheet has no public provider API, so external access is
    closed without deleting the component or changing executable DEX.
    """
    pool = _find_manifest_pool(blob)
    strings = pool.strings
    out = bytearray(blob)
    found = False
    for _, tag, attrs in _iter_start_elements(bytes(out), strings):
        if tag != 'provider':
            continue
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if 'name' not in amap:
            continue
        _, raw, dtype, data = amap['name']
        if _attr_value(strings, raw, dtype, data) != CONFIG_PROVIDER:
            continue
        if 'exported' not in amap:
            raise ValueError('ConfigProvider exported attribute missing')
        _set_typed(out, amap['exported'][0], TYPE_INT_BOOLEAN, 0)
        found = True
    if not found:
        raise ValueError('ConfigProvider not found')
    return bytes(out)


def patch_release_layout(path: str, blob: bytes) -> bytes:
    # Keep CI/selftest import-light: the visual helpers depend on Pillow and are
    # loaded only during the actual APK resource transformation.
    from owned_shell_pass import _collapse_id_rows, _replace_xml_strings
    from sheet_dialog_pass import _add_android_attr

    out = _replace_xml_strings(blob, SAFE_UI_TRANSLATIONS)

    if path in ('res/menu/activity_main_drawer.xml', 'res/menu/activity_main_drawer_icons.xml'):
        for item_id in sorted(DRAWER_HIDE_IDS):
            out = _add_android_attr(
                out,
                target_tag='item',
                target_id=item_id,
                name='visible',
                attr_rid=ANDROID_VISIBLE,
                dtype=TYPE_INT_BOOLEAN,
                data=0,
            )
    elif path == 'res/layout/dialog_fragment_frontpage_more.xml':
        out = _collapse_id_rows(out, {OPEN_BY_ID_ROW})
    elif path == 'res/layout/dialog_fragment_json.xml':
        out = _collapse_id_rows(out, {OPEN_JSON_ROW})

    return out
