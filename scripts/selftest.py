from pathlib import Path
import json,re

from dex_patch import PRODUCT_SHELL_REPLACEMENTS, PROTECTED_GAMEPLAY_DEX_LITERALS, _item
from storage_boundary import load_storage_boundary, _pairs
from storage_save_runtime import OWNED_TYPE_RENAMES

ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
storage_cfg=load_storage_boundary()
old='com.redrazors.pathbuilder2e'

# The transition product has one stable Android identity. Do not create another
# side-by-side package as a shortcut for signing or manifest problems.
assert cfg['application_id']=='com.pf2ebuilder.ru.producty', 'RuneSheet update package is locked'
assert cfg['file_provider_authority']=='com.runesheet.producty.file.provider', 'RuneSheet FileProvider authority is locked'
assert len(cfg['application_id'].encode('ascii')) == len(old.encode('ascii')), 'application_id must preserve current DEX slot size'
assert len(cfg['file_provider_authority'].encode('ascii')) == len((old+'.provider').encode('ascii')), 'FileProvider authority must preserve current DEX slot size'
assert cfg['application_id'] > 'com.itextpdf.typography.shaping.TypographyApplier'
assert cfg['application_id'] < 'com.redrazors.pathbuilder2e.backend.data.CharacterData'
assert cfg['file_provider_authority'] > 'com.redrazors.pathbuilder2e.backend.export.json.ExportDataFactory.ExportedJson'
assert cfg['file_provider_authority'] < 'com/google/firebase/FirebaseKt$coroutineDispatcher$1'

cert=cfg.get('expected_signing_cert_sha256','')
assert re.fullmatch(r'[0-9a-f]{64}',cert), 'expected_signing_cert_sha256 must be lowercase SHA-256'
assert cert=='e8e86e8c2beb58db4ca242a65ac9b970f0c9f736321ed1057814d64f7dfa7c90', 'update certificate is locked to the accepted RuneSheet line'
assert cfg.get('fixed_theme')=='runesheet_antique', 'RuneSheet uses one fixed product theme'
assert cfg.get('theme_switching_enabled') is False, 'theme switching must stay disabled'
assert cfg.get('cloud_storage_enabled') is False, 'cloud storage must stay disabled until explicitly reintroduced'
assert cfg.get('dex_product_shell_enabled') is False, 'experimental DEX shell branding stays launch-safe/off'
assert cfg.get('dex_fixed_theme_enabled') is False, 'experimental DEX theme bytecode stays launch-safe/off'
assert cfg.get('storage_owned_save_policy_enabled') is True, 'owned local-save policy must stay enabled'
assert cfg.get('storage_owned_backend_enabled') is False, 'legacy persistence backend is not yet replaced'
assert cfg.get('native_library_alignment')==16384, 'stored native libraries must use 16K alignment'

# Runtime shell strings stay inside their original string_data slots. Shorter
# values are safe because dex_patch zero-fills the unused tail without moving
# any offsets; longer values are forbidden. The experiment remains available
# for targeted smoke-tests but is not part of the default product build.
for old_text,new_text in PRODUCT_SHELL_REPLACEMENTS.items():
    assert len(_item(new_text))<=len(_item(old_text)), f'DEX shell replacement exceeds slot: {old_text!r}'

# Product ownership work must never rewrite gameplay/rules messages.
assert not (set(PRODUCT_SHELL_REPLACEMENTS) & set(PROTECTED_GAMEPLAY_DEX_LITERALS)), 'gameplay literal leaked into product shell replacements'

# Local persistence now has an explicit RuneSheet-owned API. The transition APK
# still delegates SQL/serialization to the pinned compatibility backend, but
# save policy itself is RuneSheet-owned and cloud operations are inert.
assert storage_cfg['cloud_storage_enabled'] is False
assert storage_cfg['cloud_storage_enabled'] == cfg['cloud_storage_enabled']
assert storage_cfg['owned_contract'] == 'com.runesheet.storage.CharacterStorage'
contract_file=ROOT/'native/storage-core/src/main/java/com/runesheet/storage/CharacterStorage.java'
assert contract_file.exists(), 'RuneSheet storage-core contract missing'
contract_text=contract_file.read_text(encoding='utf8')
assert 'package com.runesheet.storage;' in contract_text
assert 'interface CharacterStorage' in contract_text

owned_save=storage_cfg.get('owned_transition',{}).get('save_policy',{})
assert owned_save.get('enabled') is True
assert owned_save.get('backend_replaced') is False
assert owned_save.get('policy') == 'local-only'
assert set(owned_save.get('runtime_types',[])) <= set(OWNED_TYPE_RENAMES.values())
assert (ROOT/'scripts/storage_save_runtime.py').exists(), 'hardened owned save pass missing'
assert (ROOT/'build_runesheet.py').exists(), 'primary RuneSheet build entrypoint missing'

local_pairs=set()
for section in ('save','load','folders','state'):
    local_pairs |= _pairs(storage_cfg['legacy_transition'][section])
cloud_pairs=_pairs(storage_cfg['isolated_cloud_runtime'])
assert local_pairs, 'legacy local storage seam is empty'
assert cloud_pairs, 'cloud isolation seam is empty'
assert not (local_pairs & cloud_pairs), 'cloud/local storage seam overlap'
assert all('CloudStorageHelper' not in cls for cls,_ in local_pairs), 'cloud helper leaked into local seam'

print('configuration, release-line, no-cloud, launch-safe DEX, gameplay and owned-save storage guards: OK')
