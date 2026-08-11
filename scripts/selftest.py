from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
old='com.redrazors.pathbuilder2e'
assert len(cfg['application_id'].encode('ascii')) == len(old.encode('ascii')), 'application_id must preserve current DEX slot size'
assert len(cfg['file_provider_authority'].encode('ascii')) == len((old+'.provider').encode('ascii')), 'FileProvider authority must preserve current DEX slot size'
assert cfg['application_id'] > 'com.itextpdf.typography.shaping.TypographyApplier'
assert cfg['application_id'] < 'com.redrazors.pathbuilder2e.backend.data.CharacterData'
assert cfg['file_provider_authority'] > 'com.redrazors.pathbuilder2e.backend.export.json.ExportDataFactory.ExportedJson'
assert cfg['file_provider_authority'] < 'com/google/firebase/FirebaseKt$coroutineDispatcher$1'
print('configuration invariants: OK')
