#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'scripts'))
from manifest_patch import patch_manifest
from dex_patch import patch_exact_strings
from arsc_patch import patch_utf8_pool_literal
from brand_assets import generate_brand_assets
from action_icons import generate_action_assets
from apk_sign import build_with_overrides,sign_apk
from verify_apk import verify

ROOT=Path(__file__).resolve().parent

def sha256(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description='Build RuneSheet RU transition APK from a locally supplied compatible base APK.')
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--keystore',type=Path,default=ROOT/'.local/pf2e-builder-ru-signing.p12')
    ap.add_argument('--out',type=Path,default=ROOT/'dist/RuneSheet-RU-0.3.0-alpha.3.apk')
    ap.add_argument('--allow-base-mismatch',action='store_true')
    args=ap.parse_args(); cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
    got=sha256(args.base)
    if got!=cfg['base_apk_sha256'] and not args.allow_base_mismatch:
        raise SystemExit(f'Base APK SHA-256 mismatch. Expected {cfg["base_apk_sha256"]}, got {got}')
    pw=os.environ.get('PF2E_KEYSTORE_PASSWORD')
    if not pw: raise SystemExit('Set PF2E_KEYSTORE_PASSWORD; the signing key/password are intentionally not stored in Git.')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    work=ROOT/'work'; work.mkdir(exist_ok=True)
    brand=work/'branding';
    if brand.exists():
        import shutil; shutil.rmtree(brand)
    generate_brand_assets(brand)
    # Overwrite the legacy numeric badges with project-owned action glyphs.
    generate_action_assets(brand)

    with zipfile.ZipFile(args.base) as z:
        manifest=z.read('AndroidManifest.xml'); arsc=z.read('resources.arsc'); c2=z.read('classes2.dex')
    manifest=patch_manifest(manifest, app_name=cfg['app_name'], application_id=cfg['application_id'], version_name=cfg['version_name'], version_code=cfg['version_code'], file_provider_authority=cfg['file_provider_authority'])
    arsc=patch_utf8_pool_literal(arsc,'Pathbuilder2e RU',cfg['app_name'])
    old='com.redrazors.pathbuilder2e'; new=cfg['application_id']
    repl={
        old:new,
        f'/data/data/{old}/databases/':f'/data/data/{new}/databases/',
        old+'.provider':cfg['file_provider_authority'],
    }
    c2=patch_exact_strings(c2,repl)
    overrides={'AndroidManifest.xml':manifest,'resources.arsc':arsc,'classes2.dex':c2}
    for p in brand.rglob('*'):
        if p.is_file(): overrides[str(p.relative_to(brand)).replace(os.sep,'/')]=p.read_bytes()
    unsigned=work/'unsigned.apk'; build_with_overrides(args.base,unsigned,overrides,strip_signatures=True,align=False)
    cert=sign_apk(unsigned,args.out,args.keystore,pw,work/'sign')
    result=verify(args.out); result['cert_sha256']=cert; result['application_id']=cfg['application_id']; result['app_name']=cfg['app_name']
    (args.out.with_suffix('.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
