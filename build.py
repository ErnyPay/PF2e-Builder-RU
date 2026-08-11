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
from product_components import patch_activity_main
from milestone_components import (
    BUTTON_LAYOUTS,
    ICON_NAMES,
    harden_manifest_privacy,
    patch_button_layout,
    patch_nav_header,
    patch_subheader,
    recolor_icon,
)
from antique_theme_gold import (
    BADGE_FILL,
    BRASS_DARK,
    BRASS_LIGHT,
    SELECTED_DARK,
    patch_button_antique,
    patch_level_layout_antique,
    patch_nav_header_antique,
    patch_shape_antique,
    patch_subheader_antique,
    patch_topnav_antique,
    recolor_icon_antique,
    restyle_generated_brand_antique,
)
from reskin_patch import (
    FRONTPAGE_LAYOUTS,
    patch_frontpage_layout,
    patch_level_layout,
    patch_play_navigation,
    patch_build_navigation,
    patch_topnav_slider,
)
from apk_sign import build_with_overrides,sign_apk
from verify_apk import verify

ROOT=Path(__file__).resolve().parent

def sha256(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    cfg=json.loads((ROOT/'config/brand.json').read_text(encoding='utf8'))
    default_out=ROOT/f"dist/RuneSheet-RU-{cfg['version_name']}.apk"
    ap=argparse.ArgumentParser(description='Build RuneSheet RU transition APK from a locally supplied compatible base APK.')
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--keystore',type=Path,default=ROOT/'.local/pf2e-builder-ru-signing.p12')
    ap.add_argument('--out',type=Path,default=default_out)
    ap.add_argument('--allow-base-mismatch',action='store_true')
    args=ap.parse_args()
    got=sha256(args.base)
    if got!=cfg['base_apk_sha256'] and not args.allow_base_mismatch:
        raise SystemExit(f'Base APK SHA-256 mismatch. Expected {cfg["base_apk_sha256"]}, got {got}')
    pw=os.environ.get('PF2E_KEYSTORE_PASSWORD')
    if not pw: raise SystemExit('Set PF2E_KEYSTORE_PASSWORD; the signing key/password are intentionally not stored in Git.')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    work=ROOT/'work'; work.mkdir(exist_ok=True)
    brand=work/'branding'
    if brand.exists():
        import shutil; shutil.rmtree(brand)
    generate_brand_assets(brand)
    generate_action_assets(brand)
    # Warm antique-book identity; generated product art only, never rule/content images.
    restyle_generated_brand_antique(brand)

    with zipfile.ZipFile(args.base) as z:
        names=set(z.namelist())
        manifest=z.read('AndroidManifest.xml'); arsc=z.read('resources.arsc'); c2=z.read('classes2.dex')
        resource_overrides={}
        for path in FRONTPAGE_LAYOUTS:
            if path in names: resource_overrides[path]=patch_frontpage_layout(z.read(path))
        if 'res/layout/layout_level_navigation.xml' in names:
            resource_overrides['res/layout/layout_level_navigation.xml']=patch_level_layout(z.read('res/layout/layout_level_navigation.xml'),play=False)
        if 'res/layout/layout_level_navigation_play.xml' in names:
            resource_overrides['res/layout/layout_level_navigation_play.xml']=patch_level_layout(z.read('res/layout/layout_level_navigation_play.xml'),play=True)
        if 'res/layout/activity_content_play_mode.xml' in names:
            resource_overrides['res/layout/activity_content_play_mode.xml']=patch_play_navigation(z.read('res/layout/activity_content_play_mode.xml'))
        if 'res/layout/totalfragment_build_navigation.xml' in names:
            resource_overrides['res/layout/totalfragment_build_navigation.xml']=patch_build_navigation(z.read('res/layout/totalfragment_build_navigation.xml'))
        if 'res/drawable/background_topnav_slider.xml' in names:
            resource_overrides['res/drawable/background_topnav_slider.xml']=patch_topnav_slider(z.read('res/drawable/background_topnav_slider.xml'))
        if 'res/layout/activity_main.xml' in names:
            resource_overrides['res/layout/activity_main.xml']=patch_activity_main(z.read('res/layout/activity_main.xml'))

        # Surface + every label are migrated together to prevent invisible text.
        for path in sorted(BUTTON_LAYOUTS):
            if path in names:
                resource_overrides[path]=patch_button_layout(z.read(path))
        if 'res/layout/nav_header_main.xml' in names:
            resource_overrides['res/layout/nav_header_main.xml']=patch_nav_header(z.read('res/layout/nav_header_main.xml'))
        if 'res/layout/text_view_subheader.xml' in names:
            resource_overrides['res/layout/text_view_subheader.xml']=patch_subheader(z.read('res/layout/text_view_subheader.xml'))
        for name in sorted(ICON_NAMES):
            path='res/drawable/'+name
            if path in names:
                resource_overrides[path]=recolor_icon(z.read(path),'_dark' in name)

        # Bright antique overlay: no burgundy. Honey-gold menu surfaces with dark ink.
        for path in sorted(BUTTON_LAYOUTS):
            if path in resource_overrides:
                resource_overrides[path]=patch_button_antique(resource_overrides[path])
        if 'res/layout/nav_header_main.xml' in resource_overrides:
            resource_overrides['res/layout/nav_header_main.xml']=patch_nav_header_antique(resource_overrides['res/layout/nav_header_main.xml'])
        if 'res/layout/text_view_subheader.xml' in resource_overrides:
            resource_overrides['res/layout/text_view_subheader.xml']=patch_subheader_antique(resource_overrides['res/layout/text_view_subheader.xml'])
        for path in ('res/layout/activity_content_play_mode.xml','res/layout/totalfragment_build_navigation.xml'):
            if path in resource_overrides:
                resource_overrides[path]=patch_topnav_antique(resource_overrides[path])
        for name in sorted(ICON_NAMES):
            path='res/drawable/'+name
            if path in resource_overrides:
                resource_overrides[path]=recolor_icon_antique(resource_overrides[path])

        # Russian УРОВЕНЬ N: wrap_content + padding + direct black text + framed badge.
        if 'res/layout/layout_level_navigation.xml' in resource_overrides:
            resource_overrides['res/layout/layout_level_navigation.xml']=patch_level_layout_antique(resource_overrides['res/layout/layout_level_navigation.xml'],play=False)
        if 'res/layout/layout_level_navigation_play.xml' in resource_overrides:
            resource_overrides['res/layout/layout_level_navigation_play.xml']=patch_level_layout_antique(resource_overrides['res/layout/layout_level_navigation_play.xml'],play=True)
        if 'res/drawable/background_topnav_slider.xml' in resource_overrides:
            base_slider=z.read('res/drawable/background_topnav_slider.xml')
            resource_overrides['res/drawable/background_topnav_slider.xml']=patch_shape_antique(base_slider,fill=SELECTED_DARK,stroke=BRASS_LIGHT,radius_dp=10)
            resource_overrides['res/drawable/test_level_drawable.xml']=patch_shape_antique(base_slider,fill=BADGE_FILL,stroke=BRASS_DARK,radius_dp=8)

    manifest=patch_manifest(manifest, app_name=cfg['app_name'], application_id=cfg['application_id'], version_name=cfg['version_name'], version_code=cfg['version_code'], file_provider_authority=cfg['file_provider_authority'])
    manifest=harden_manifest_privacy(manifest,application_id=cfg['application_id'])

    arsc=patch_utf8_pool_literal(arsc,'Pathbuilder2e RU',cfg['app_name'])
    old='com.redrazors.pathbuilder2e'; new=cfg['application_id']
    repl={
        old:new,
        f'/data/data/{old}/databases/':f'/data/data/{new}/databases/',
        old+'.provider':cfg['file_provider_authority'],
    }
    c2=patch_exact_strings(c2,repl)
    overrides={'AndroidManifest.xml':manifest,'resources.arsc':arsc,'classes2.dex':c2}
    overrides.update(resource_overrides)
    for p in brand.rglob('*'):
        if p.is_file(): overrides[str(p.relative_to(brand)).replace(os.sep,'/')]=p.read_bytes()
    unsigned=work/'unsigned.apk'; build_with_overrides(args.base,unsigned,overrides,strip_signatures=True,align=False)
    cert=sign_apk(unsigned,args.out,args.keystore,pw,work/'sign')
    result=verify(args.out); result['cert_sha256']=cert; result['application_id']=cfg['application_id']; result['app_name']=cfg['app_name']
    (args.out.with_suffix('.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
