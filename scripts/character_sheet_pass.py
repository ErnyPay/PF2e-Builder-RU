from __future__ import annotations

from manifest_patch import _find_manifest_pool, _iter_start_elements
from sheet_dialog_pass import (
    TYPE_DIMENSION, TYPE_REFERENCE, RID_SURFACE, _add_android_attr, _set_typed,
)

RID_MINI_CARD = 0x7F07008C          # background_drawdown
RID_HEADER_PILL = 0x7F0700D2        # dialog_menu_selected
RID_STANDARD_TEXT = 0x7F05031A      # standard_text = black
ANDROID_BACKGROUND = 0x010100D4
ANDROID_PADDING = 0x010100D5
ANDROID_TEXT_COLOR = 0x01010098

# Runtime-inflated play-sheet templates. Styling these is more robust than only
# changing the fragment shells because new weapons/spellcasters reuse them too.
SHEET_CARD_ROOTS = {
    'res/layout/layout_hp_standard.xml','res/layout/layout_stamina_hp.xml',
    'res/layout/layout_player_weapon.xml','res/layout/layout_player_armor.xml',
    'res/layout/layout_player_shield.xml','res/layout/layout_player_siege_weapon.xml',
    'res/layout/layout_spellcaster.xml','res/layout/layout_spell_casting.xml',
    'res/layout/layout_spells.xml','res/layout/layout_spells_impulses.xml',
    'res/layout/layout_action.xml','res/layout/layout_custom_action.xml',
}

MINI_CARD_ROOTS = {
    'res/layout/layout_build_proficiency_linear.xml','res/layout/layout_build_proficiency_roller.xml',
    'res/layout/layout_active_generic.xml','res/layout/layout_active_pet.xml',
    'res/layout/layout_active_familiar.xml','res/layout/layout_active_construct.xml',
}

HEADER_IDS = {
    'res/layout/playfragment_defenses.xml':[0x7F0904F1],
    'res/layout/playfragment_attacks.xml':[0x7F0904BF],
    'res/layout/layout_player_weapon.xml':[0x7F09051A],
    'res/layout/layout_player_armor.xml':[0x7F0904D9],
    'res/layout/layout_player_shield.xml':[0x7F0904F9],
    'res/layout/layout_player_siege_weapon.xml':[0x7F09051A,0x7F0904A8],
    'res/layout/layout_spellcaster.xml':[0x7F090505],
}

SHEET_FRAGMENTS = {
    'res/layout/playfragment_defenses.xml','res/layout/playfragment_attacks.xml',
    'res/layout/playfragment_spells.xml','res/layout/playfragment_gear.xml',
}


def _root(blob: bytes):
    p = _find_manifest_pool(blob)
    return next(_iter_start_elements(blob, p.strings))


def patch_root_card(blob: bytes, *, mini: bool = False) -> bytes:
    _, tag, attrs = _root(blob)
    amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
    rid = RID_MINI_CARD if mini else RID_SURFACE
    padding = 0x0801 if mini else 0x0C01
    out = blob
    if 'background' in amap:
        b = bytearray(out); _set_typed(b, amap['background'][0], TYPE_REFERENCE, rid); out = bytes(b)
    else:
        out = _add_android_attr(out,target_tag=tag,target_id=None,name='background',attr_rid=ANDROID_BACKGROUND,dtype=TYPE_REFERENCE,data=rid)
    _, tag, attrs = _root(out)
    amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
    if 'padding' in amap:
        b = bytearray(out); _set_typed(b, amap['padding'][0], TYPE_DIMENSION, padding); out = bytes(b)
    else:
        out = _add_android_attr(out,target_tag=tag,target_id=None,name='padding',attr_rid=ANDROID_PADDING,dtype=TYPE_DIMENSION,data=padding)
    return out


def patch_sheet_section_spacing(blob: bytes) -> bytes:
    p = _find_manifest_pool(blob); out = bytearray(blob)
    for _,_,attrs in _iter_start_elements(bytes(out), p.strings):
        amap = {name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        bg = amap.get('background')
        if not bg or bg[2] != TYPE_REFERENCE or bg[3] != RID_SURFACE:
            continue
        if 'padding' in amap: _set_typed(out, amap['padding'][0], TYPE_DIMENSION, 0x0C01)
        if 'layout_marginTop' in amap: _set_typed(out, amap['layout_marginTop'][0], TYPE_DIMENSION, 0x0801)
        if 'layout_marginBottom' in amap: _set_typed(out, amap['layout_marginBottom'][0], TYPE_DIMENSION, 0x0801)
    return bytes(out)


def patch_header_pill(blob: bytes, target_id: int) -> bytes:
    out = _add_android_attr(blob,target_tag='TextView',target_id=target_id,name='background',attr_rid=ANDROID_BACKGROUND,dtype=TYPE_REFERENCE,data=RID_HEADER_PILL)
    out = _add_android_attr(out,target_tag='TextView',target_id=target_id,name='textColor',attr_rid=ANDROID_TEXT_COLOR,dtype=TYPE_REFERENCE,data=RID_STANDARD_TEXT)
    return _add_android_attr(out,target_tag='TextView',target_id=target_id,name='padding',attr_rid=ANDROID_PADDING,dtype=TYPE_DIMENSION,data=0x0801)
