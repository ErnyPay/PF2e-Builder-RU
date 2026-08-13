from pathlib import Path
import json,re

from dex_patch import PRODUCT_SHELL_REPLACEMENTS, PROTECTED_GAMEPLAY_DEX_LITERALS, _item
from storage_boundary import load_storage_boundary, _pairs
from release_hardening import CONFIG_PROVIDER, DRAWER_HIDE_IDS, OPEN_BY_ID_ROW, OPEN_JSON_ROW, RELEASE_LAYOUT_PATHS

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
storage_cfg=load_storage_boundary()
release_baseline=json.loads((ROOT/'config/release_baseline.json').read_text(encoding='utf8'))
content_beta=json.loads((ROOT/'config/content_release_1_0_1_beta1.json').read_text(encoding='utf8'))
old='com.redrazors.pathbuilder2e'

assert cfg['application_id']=='com.pf2ebuilder.ru.producty', 'RuneSheet update package is locked'
assert cfg['file_provider_authority']=='com.runesheet.producty.file.provider', 'RuneSheet FileProvider authority is locked'
assert len(cfg['application_id'].encode('ascii')) == len(old.encode('ascii'))
assert len(cfg['file_provider_authority'].encode('ascii')) == len((old+'.provider').encode('ascii'))
assert cfg.get('version_name')=='1.0.0'
assert cfg.get('version_code')==1002

cert=cfg.get('expected_signing_cert_sha256','')
assert re.fullmatch(r'[0-9a-f]{64}',cert)
assert cert=='0b780e6e9b38b3c05ad0e0af780b77a13700cfdfb767af2724942db4cf0b29f7', 'RuneSheet release certificate is permanently locked'
assert cfg.get('release_key_promoted_from_preview') is True
assert cfg.get('release_baseline')=='0.6.0-preview.5-dex-rollback'
assert release_baseline['signing_cert_sha256']==cert
assert release_baseline['application_id']==cfg['application_id']
assert release_baseline['source_version']=='0.6.0-preview.5'
assert len(release_baseline['dex_sha256'])==5
assert all(re.fullmatch(r'[0-9a-f]{64}',x) for x in release_baseline['dex_sha256'].values())

assert cfg.get('fixed_theme')=='runesheet_antique'
assert cfg.get('theme_switching_enabled') is False
assert cfg.get('cloud_storage_enabled') is False
assert cfg.get('legacy_external_actions_enabled') is False
assert cfg.get('dex_product_shell_enabled') is False
assert cfg.get('dex_fixed_theme_enabled') is False
assert cfg.get('storage_owned_save_policy_enabled') is False, 'owned-save runtime is quarantined after device launch regression'
assert cfg.get('storage_owned_backend_enabled') is False
assert cfg.get('native_library_alignment')==16384

for old_text,new_text in PRODUCT_SHELL_REPLACEMENTS.items():
    assert len(_item(new_text))<=len(_item(old_text))
assert not (set(PRODUCT_SHELL_REPLACEMENTS) & set(PROTECTED_GAMEPLAY_DEX_LITERALS))

# Final 1.0 keeps the RC2 release hardening exactly as device-tested.
assert CONFIG_PROVIDER == 'com.redrazors.pathbuilder2e.ConfigProvider'
assert DRAWER_HIDE_IDS == {0x7F09034E, 0x7F09034F}
assert OPEN_BY_ID_ROW == 0x7F0900D5
assert OPEN_JSON_ROW == 0x7F0900AF
assert 'res/menu/activity_main_drawer.xml' in RELEASE_LAYOUT_PATHS
assert 'res/menu/activity_main_drawer_icons.xml' in RELEASE_LAYOUT_PATHS
assert (ROOT/'scripts/release_hardening.py').exists()
assert (ROOT/'build_runesheet.py').exists()

# Translation work is a separate content-only beta line. Stable brand/release
# identity remains 1.0.0 while this manifest records the guarded DB patch.
assert content_beta['release']=='1.0.1-beta1'
assert content_beta['stable_parent']=='1.0.0'
assert content_beta['content_only'] is True
assert content_beta['expected_changed_cells']==45
assert content_beta['master_changed_cells']==37
assert content_beta['remaster_changed_cells']==8
assert content_beta['categories']=={
    'misbound_class_feature_descriptions':34,
    'mixed_en_ru_energy_resistant_runes':8,
    'mixed_en_ru_magentic_suit':3,
}
assert content_beta['source_databases']['master_encrypted_sha256']=='06f09830b2e578dd1ab01730537ec76b9b05e37a68902fe744a9f6c37b889b81'
assert content_beta['source_databases']['remaster_encrypted_sha256']=='8485608ddf46b3b5437bd8b051b2d47fa6118b0bfaa5187a59bdd3f831289f1d'
assert re.fullmatch(r'[0-9a-f]{64}',content_beta['source_databases']['master_plaintext_sha256'])
assert re.fullmatch(r'[0-9a-f]{64}',content_beta['source_databases']['remaster_plaintext_sha256'])
assert content_beta['runtime_policy']['dex_must_match_stable_1_0_0'] is True
assert content_beta['runtime_policy']['resources_must_match_stable_1_0_0'] is True
assert content_beta['runtime_policy']['gameplay_ids_names_levels_traits_unchanged'] is True
assert (ROOT/'scripts/content_patch_1_0_1_beta1.py').exists()

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

local_pairs=set()
for section in ('save','load','folders','state'):
    local_pairs |= _pairs(storage_cfg['legacy_transition'][section])
cloud_pairs=_pairs(storage_cfg['isolated_cloud_runtime'])
assert local_pairs
assert cloud_pairs
assert not (local_pairs & cloud_pairs)
assert all('CloudStorageHelper' not in cls for cls,_ in local_pairs)

print('1.0.0 identity, permanent signing key, RC2 hardening, no-cloud, launch-safe DEX, storage guards and 1.0.1 beta1 content patch manifest: OK')
