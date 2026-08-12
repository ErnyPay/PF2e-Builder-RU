from pathlib import Path
import json,re

from dex_patch import PRODUCT_SHELL_REPLACEMENTS, PROTECTED_GAMEPLAY_DEX_LITERALS, _item
from storage_boundary import load_storage_boundary, _pairs

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
storage_cfg=load_storage_boundary()
old='com.redrazors.pathbuilder2e'

assert cfg['application_id']=='com.pf2ebuilder.ru.producty', 'RuneSheet update package is locked'
assert cfg['file_provider_authority']=='com.runesheet.producty.file.provider', 'RuneSheet FileProvider authority is locked'
assert len(cfg['application_id'].encode('ascii')) == len(old.encode('ascii'))
assert len(cfg['file_provider_authority'].encode('ascii')) == len((old+'.provider').encode('ascii'))

cert=cfg.get('expected_signing_cert_sha256','')
assert re.fullmatch(r'[0-9a-f]{64}',cert)
assert cert=='e8e86e8c2beb58db4ca242a65ac9b970f0c9f736321ed1057814d64f7dfa7c90'
assert cfg.get('fixed_theme')=='runesheet_antique'
assert cfg.get('theme_switching_enabled') is False
assert cfg.get('cloud_storage_enabled') is False
assert cfg.get('dex_product_shell_enabled') is False
assert cfg.get('dex_fixed_theme_enabled') is False
assert cfg.get('storage_owned_save_policy_enabled') is False, 'owned-save runtime is quarantined after device launch regression'
assert cfg.get('storage_owned_backend_enabled') is False
assert cfg.get('native_library_alignment')==16384

for old_text,new_text in PRODUCT_SHELL_REPLACEMENTS.items():
    assert len(_item(new_text))<=len(_item(old_text))
assert not (set(PRODUCT_SHELL_REPLACEMENTS) & set(PROTECTED_GAMEPLAY_DEX_LITERALS))

assert storage_cfg['cloud_storage_enabled'] is False
assert storage_cfg['cloud_storage_enabled'] == cfg['cloud_storage_enabled']
assert storage_cfg['owned_contract'] == 'com.runesheet.storage.CharacterStorage'
contract_file=ROOT/'native/storage-core/src/main/java/com/runesheet/storage/CharacterStorage.java'
assert contract_file.exists()
contract_text=contract_file.read_text(encoding='utf8')
assert 'package com.runesheet.storage;' in contract_text
assert 'interface CharacterStorage' in contract_text

owned_save=storage_cfg.get('owned_transition',{}).get('save_policy',{})
assert owned_save.get('enabled') is False
assert owned_save.get('backend_replaced') is False
assert owned_save.get('status') == 'quarantined-after-device-launch-regression'
assert owned_save.get('runtime_types') == []
assert (ROOT/'build_runesheet.py').exists()

local_pairs=set()
for section in ('save','load','folders','state'):
    local_pairs |= _pairs(storage_cfg['legacy_transition'][section])
cloud_pairs=_pairs(storage_cfg['isolated_cloud_runtime'])
assert local_pairs
assert cloud_pairs
assert not (local_pairs & cloud_pairs)
assert all('CloudStorageHelper' not in cls for cls,_ in local_pairs)

print('release-line, no-cloud, launch-safe DEX, gameplay and quarantined-storage guards: OK')
