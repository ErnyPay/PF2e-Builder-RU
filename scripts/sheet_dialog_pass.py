from __future__ import annotations

import struct

import antique_theme as antique_base
from manifest_patch import NO_INDEX, TYPE_STRING, _find_manifest_pool, _iter_start_elements, _put_u32, _u16, _u32

TYPE_REFERENCE = 0x01
TYPE_DIMENSION = 0x05
TYPE_INT_DEC = 0x10
TYPE_COLOR = 0x1C

INK = 0xFF241B12
HONEY = 0xFFE3BF69
HONEY_LIGHT = 0xFFF1D58D
BRONZE = 0xFF9A6F2F
BRONZE_DARK = 0xFF5B3F20
PARCHMENT = 0xFFF7E8BD
PARCHMENT_SOFT = 0xFFF3DFAD
PARCHMENT_EDGE = 0xFFC49A51

RID_SURFACE = 0x7F0701DD
RID_BUTTON = 0x7F0700B4
RID_BACKGROUND_HEADER = 0x7F07008E
RID_STANDARD_TEXT = 0x7F05031A
ID_HEADER_TEXT = 0x7F090221
ANDROID_BACKGROUND = 0x010100D4
ANDROID_TEXT_COLOR = 0x01010098

LIST_ROWS = {
    'res/layout/listview_item_ancestries.xml','res/layout/listview_item_armor.xml','res/layout/listview_item_backgrounds.xml',
    'res/layout/listview_item_classes.xml','res/layout/listview_item_conditions.xml','res/layout/listview_item_custom_buffs.xml',
    'res/layout/listview_item_equipment.xml','res/layout/listview_item_equipment_multibuy.xml','res/layout/listview_item_feats.xml',
    'res/layout/listview_item_load.xml','res/layout/listview_item_multiuse_actions.xml','res/layout/listview_item_rituals.xml',
    'res/layout/listview_item_runes.xml','res/layout/listview_item_shields.xml','res/layout/listview_item_skills.xml',
    'res/layout/listview_item_specials.xml','res/layout/listview_item_specials_with_label.xml','res/layout/listview_item_spells.xml',
    'res/layout/listview_item_weapons.xml','res/layout/list_item_standard_boxed.xml',
}

DIALOGS = {
    'res/layout/dialog_fragment_actions.xml','res/layout/dialog_fragment_ancestry.xml','res/layout/dialog_fragment_armor.xml',
    'res/layout/dialog_fragment_background.xml','res/layout/dialog_fragment_background_custom.xml','res/layout/dialog_fragment_class.xml',
    'res/layout/dialog_fragment_custom.xml','res/layout/dialog_fragment_custom_buff.xml','res/layout/dialog_fragment_custom_feat_choice.xml',
    'res/layout/dialog_fragment_custom_skill_increase.xml','res/layout/dialog_fragment_custom_spell_item.xml','res/layout/dialog_fragment_equipment.xml',
    'res/layout/dialog_fragment_equipment_pc.xml','res/layout/dialog_fragment_export_stat_block.xml','res/layout/dialog_fragment_feats.xml',
    'res/layout/dialog_fragment_formula.xml','res/layout/dialog_fragment_fundamental_runes.xml','res/layout/dialog_fragment_languages.xml',
    'res/layout/dialog_fragment_liences.xml','res/layout/dialog_fragment_listview.xml','res/layout/dialog_fragment_load_new.xml',
    'res/layout/dialog_fragment_materials.xml','res/layout/dialog_fragment_new_books_check.xml','res/layout/dialog_fragment_optin_books.xml',
    'res/layout/dialog_fragment_options.xml','res/layout/dialog_fragment_pet_animal_companions.xml','res/layout/dialog_fragment_pet_armor.xml',
    'res/layout/dialog_fragment_pet_familiar_abilities.xml','res/layout/dialog_fragment_pet_follower.xml','res/layout/dialog_fragment_rituals.xml',
    'res/layout/dialog_fragment_runes.xml','res/layout/dialog_fragment_spell_bonus_slots.xml','res/layout/dialog_fragment_spell_bonus_slots_new.xml',
    'res/layout/dialog_fragment_spells.xml','res/layout/dialog_fragment_universal_feat_browser.xml','res/layout/dialog_fragment_weapons.xml',
}

ROUND_RADII = {
    'res/drawable/background_ability_table_item.xml':28,'res/drawable/background_drawdown.xml':32,
    'res/drawable/background_drawdown_illegal.xml':32,'res/drawable/background_topnav_slider.xml':38,
    'res/drawable/border_filter_on.xml':30,'res/drawable/custom_button_background.xml':38,
    'res/drawable/custom_button_background_cantrips_ornate.xml':36,'res/drawable/custom_button_background_cast.xml':36,
    'res/drawable/custom_button_background_cast_off.xml':36,'res/drawable/custom_button_background_dark.xml':36,
    'res/drawable/custom_button_background_dark_off.xml':36,'res/drawable/custom_button_background_dark_withpadding.xml':36,
    'res/drawable/custom_button_background_disabled.xml':36,'res/drawable/custom_button_background_disabled_dark.xml':36,
    'res/drawable/custom_button_background_heighten.xml':34,'res/drawable/custom_button_background_heighten_selected.xml':34,
    'res/drawable/custom_button_background_nodecoration_off.xml':36,'res/drawable/custom_button_background_spellinfo.xml':36,
    'res/drawable/custom_button_background_spellinfo_off.xml':36,'res/drawable/rounded_rectangle.xml':32,
    'res/drawable/rounded_rectangle_darkmode_bordered.xml':32,'res/drawable/rounded_rectangle_transparent_inside.xml':32,
    'res/drawable/rounded_rectangle_white_solid.xml':32,'res/drawable/test_level_drawable.xml':40,
    'res/drawable/tooltip_frame_dark.xml':28,'res/drawable/tooltip_frame_light.xml':28,
}


def _set_typed(out: bytearray, attr: int, dtype: int, data: int) -> None:
    _put_u32(out, attr + 8, NO_INDEX)
    struct.pack_into('<HBBI', out, attr + 12, 8, 0, dtype, data)


def _add_android_attr(blob: bytes, *, target_tag: str, target_id: int | None, name: str, attr_rid: int, dtype: int, data: int) -> bytes:
    blob = antique_base._insert_resource_name(blob, name, attr_rid)
    p = _find_manifest_pool(blob); strings = p.strings; ids = antique_base._resource_map(blob); out = bytearray(blob)
    target_chunk = None; target_attrs = None
    for offset, tag, attrs in _iter_start_elements(bytes(out), strings):
        if tag != target_tag: continue
        amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
        if target_id is not None and amap.get('id',(None,None,None,None))[3] != target_id: continue
        target_chunk, target_attrs = offset, attrs; break
    if target_chunk is None or target_attrs is None: raise ValueError(f'target missing: {target_tag}/{target_id}')
    amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in target_attrs}
    if name in amap:
        _set_typed(out, amap[name][0], dtype, data); return bytes(out)
    uri_idx = strings.index('http://schemas.android.com/apk/res/android'); name_idx = strings.index(name)
    attr_res = []
    for a,_,_,_,_ in target_attrs:
        ni = _u32(out, a + 4); attr_res.append(ids[ni] if ni < len(ids) else 0xFFFFFFFF)
    pos = next((i for i,rid in enumerate(attr_res) if rid > attr_rid and rid != 0), len(attr_res))
    attr_start = _u16(out, target_chunk + 24); attr_size = _u16(out, target_chunk + 26); attr_count = _u16(out, target_chunk + 28)
    if attr_size != 20: raise ValueError('unexpected binary XML attribute size')
    base = target_chunk + 16 + attr_start; insert_offset = base + pos * attr_size
    record = struct.pack('<IIIHBBI', uri_idx, name_idx, NO_INDEX, 8, 0, dtype, data)
    out = out[:insert_offset] + bytearray(record) + out[insert_offset:]
    struct.pack_into('<I', out, target_chunk + 4, _u32(out, target_chunk + 4) + 20)
    struct.pack_into('<H', out, target_chunk + 28, attr_count + 1)
    inserted = pos + 1
    for field in (30,32,34):
        value = _u16(out, target_chunk + field)
        if value and value >= inserted: struct.pack_into('<H', out, target_chunk + field, value + 1)
    _put_u32(out, 4, _u32(out, 4) + 20)
    return bytes(out)


def patch_root_background(blob: bytes, rid: int = RID_SURFACE) -> bytes:
    p = _find_manifest_pool(blob); first = next(_iter_start_elements(blob, p.strings)); _, tag, attrs = first
    amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
    if 'background' in amap:
        out = bytearray(blob); _set_typed(out, amap['background'][0], TYPE_REFERENCE, rid); return bytes(out)
    return _add_android_attr(blob,target_tag=tag,target_id=None,name='background',attr_rid=ANDROID_BACKGROUND,dtype=TYPE_REFERENCE,data=rid)


def patch_dynamic_level_header(blob: bytes) -> bytes:
    blob = _add_android_attr(blob,target_tag='RelativeLayout',target_id=None,name='background',attr_rid=ANDROID_BACKGROUND,dtype=TYPE_REFERENCE,data=RID_BACKGROUND_HEADER)
    return _add_android_attr(blob,target_tag='TextView',target_id=ID_HEADER_TEXT,name='textColor',attr_rid=ANDROID_TEXT_COLOR,dtype=TYPE_REFERENCE,data=RID_STANDARD_TEXT)


def patch_dialog_menu_item(blob: bytes) -> bytes:
    blob = patch_root_background(blob, RID_BUTTON)
    p = _find_manifest_pool(blob); out = bytearray(blob)
    for _,tag,attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
        if tag == 'TextView':
            if 'textColor' in amap: _set_typed(out, amap['textColor'][0], TYPE_COLOR, INK)
            if 'padding' in amap: _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x801)
            if 'layout_margin' in amap: _set_typed(out, amap['layout_margin'][0], TYPE_DIMENSION, 0x401)
    return bytes(out)


def patch_surface_shape(blob: bytes) -> bytes:
    p = _find_manifest_pool(blob); out = bytearray(blob); solid_i = 0
    for _,tag,attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
        if tag == 'solid' and 'color' in amap:
            solid_i += 1; _set_typed(out, amap['color'][0], TYPE_COLOR, PARCHMENT if solid_i == 1 else HONEY_LIGHT)
        elif tag == 'stroke' and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, PARCHMENT_EDGE)
        elif tag == 'corners':
            for n,(a,_,_,_) in amap.items():
                if n == 'radius' or n.endswith('Radius'): _set_typed(out,a,TYPE_DIMENSION,0x2001)
    return bytes(out)


def patch_drawdown(blob: bytes) -> bytes:
    p = _find_manifest_pool(blob); out = bytearray(blob); solid_i = 0
    for _,tag,attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
        if tag == 'solid' and 'color' in amap:
            solid_i += 1; _set_typed(out, amap['color'][0], TYPE_COLOR, PARCHMENT_SOFT if solid_i == 1 else HONEY)
        elif tag == 'stroke' and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, BRONZE)
        elif tag == 'corners':
            for n,(a,_,_,_) in amap.items():
                if n == 'radius' or n.endswith('Radius'): _set_typed(out,a,TYPE_DIMENSION,0x2001)
    return bytes(out)


def patch_selected_pill(button_blob: bytes, dark: bool = False) -> bytes:
    p = _find_manifest_pool(button_blob); out = bytearray(button_blob)
    for _,tag,attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {n:(a,raw,dt,val) for a,n,raw,dt,val in attrs}
        if tag == 'solid' and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, BRONZE_DARK if dark else HONEY)
        elif tag == 'stroke' and 'color' in amap: _set_typed(out, amap['color'][0], TYPE_COLOR, HONEY_LIGHT if dark else BRONZE_DARK)
        elif tag == 'corners':
            for n,(a,_,_,_) in amap.items():
                if n == 'radius' or n.endswith('Radius'): _set_typed(out,a,TYPE_DIMENSION,0x2401)
    return bytes(out)
