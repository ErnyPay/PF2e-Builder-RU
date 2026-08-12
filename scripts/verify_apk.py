from __future__ import annotations
from pathlib import Path
import hashlib,json,struct,subprocess,zipfile

from manifest_patch import _find_manifest_pool,_iter_start_elements,NO_INDEX,TYPE_STRING,TYPE_INT_DEC
from apk_sign import zip_data_offset

ROOT=Path(__file__).resolve().parents[1]
OLD_AD_IDS=(
    b'ca-app-pub-8849615353397054~3022553003',
    b'ca-app-pub-8849615353397054/1681551174',
)
THEME_OPTION_ID=0x7F090119
TYPE_REFERENCE=0x01
TYPE_DIMENSION=0x05

# Polished round5 content is a product baseline, not a migration source.
# Branding/code changes must not mutate these assets unless a dedicated
# content-change task explicitly updates the baseline hashes.
PROTECTED_ASSET_SHA256={
    'assets/master.db':'06f09830b2e578dd1ab01730537ec76b9b05e37a68902fe744a9f6c37b889b81',
    'assets/remaster.db':'8485608ddf46b3b5437bd8b051b2d47fa6118b0bfaa5187a59bdd3f831289f1d',
}


def _config():
    p=ROOT/'config/brand.json'
    return json.loads(p.read_text(encoding='utf8')) if p.exists() else {}

def _xml_attr_value(strings,raw,dtype,data):
    if dtype==TYPE_STRING and data!=NO_INDEX and data<len(strings): return strings[data]
    if raw!=NO_INDEX and raw<len(strings): return strings[raw]
    return data

def inspect_manifest(blob:bytes):
    p=_find_manifest_pool(blob); strings=p.strings
    out={'package':None,'version_name':None,'version_code':None,'application_label':None,'provider_authorities':[]}
    for _,tag,attrs in _iter_start_elements(blob,strings):
        amap={name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        if tag=='manifest':
            if 'package' in amap: out['package']=_xml_attr_value(strings,*amap['package'][1:])
            if 'versionName' in amap: out['version_name']=_xml_attr_value(strings,*amap['versionName'][1:])
            if 'versionCode' in amap:
                _,raw,dtype,data=amap['versionCode']; out['version_code']=data if dtype==TYPE_INT_DEC else _xml_attr_value(strings,raw,dtype,data)
        elif tag=='application' and 'label' in amap:
            out['application_label']=_xml_attr_value(strings,*amap['label'][1:])
        elif tag=='provider' and 'authorities' in amap:
            out['provider_authorities'].append(_xml_attr_value(strings,*amap['authorities'][1:]))
    return out

def verify_fixed_theme(blob:bytes):
    p=_find_manifest_pool(blob); strings=p.strings
    hidden=False
    for _,tag,attrs in _iter_start_elements(blob,strings):
        if tag!='LinearLayout': continue
        amap={name:(a,raw,dtype,data) for a,name,raw,dtype,data in attrs}
        ident=amap.get('id')
        if not ident or ident[2]!=TYPE_REFERENCE or ident[3]!=THEME_OPTION_ID: continue
        h=amap.get('layout_height')
        hidden=bool(h and h[2]==TYPE_DIMENSION and (h[3]>>8)==0)
        break
    if not hidden: raise RuntimeError('theme selector is not collapsed')
    if 'Set App Theme' in strings or 'Оформление' in strings: raise RuntimeError('theme selector wording is still user-visible')
    return {'ok':True,'theme_option_id':hex(THEME_OPTION_ID),'collapsed':True}

def verify_alignment(apk:Path,alignment:int):
    checked=[]; bad=[]
    with zipfile.ZipFile(apk) as z,open(apk,'rb') as f:
        for info in z.infolist():
            if info.compress_type!=zipfile.ZIP_STORED or not info.filename.endswith('.so'): continue
            off=zip_data_offset(f,info); row={'name':info.filename,'offset':off,'alignment':alignment,'remainder':off%alignment}
            checked.append(row)
            if off%alignment: bad.append(row)
    if bad: raise RuntimeError(f'native library alignment failed: {bad[:3]}')
    return {'ok':True,'alignment':alignment,'libraries':checked}


def dex_units(d:bytes):
    u32=lambda o:struct.unpack_from('<I',d,o)[0]
    ss,so=u32(0x38),u32(0x3c)
    def uleb(o):
        v=s=0
        while True:
            b=d[o];o+=1;v|=(b&127)<<s
            if b<128:return v,o
            s+=7
    def mutf8_units(raw):
        out=[];i=0
        while i<len(raw):
            b=raw[i]
            if b<0x80:out.append(b);i+=1
            elif b&0xe0==0xc0:out.append(((b&31)<<6)|(raw[i+1]&63));i+=2
            elif b&0xf0==0xe0:out.append(((b&15)<<12)|((raw[i+1]&63)<<6)|(raw[i+2]&63));i+=3
            else:raise ValueError(hex(b))
        return tuple(out)
    vals=[]
    for i in range(ss):
        o=u32(so+4*i);_,q=uleb(o);e=d.index(0,q);vals.append(mutf8_units(d[q:e]))
    return vals

def verify_dex(d:bytes):
    import zlib
    sig_ok=d[12:32]==hashlib.sha1(d[32:]).digest()
    chk_ok=struct.unpack_from('<I',d,8)[0]==(zlib.adler32(d[12:])&0xffffffff)
    vals=dex_units(d); sorted_ok=all(vals[i-1] < vals[i] for i in range(1,len(vals)))
    return sig_ok and chk_ok and sorted_ok, {'sha1':sig_ok,'adler32':chk_ok,'sorted_strings':sorted_ok,'strings':len(vals)}


def _verify_protected_assets(z:zipfile.ZipFile, expected):
    result={}
    for name,want in expected.items():
        try:
            data=z.read(name)
        except KeyError as exc:
            raise RuntimeError(f'Protected content asset missing: {name}') from exc
        got=hashlib.sha256(data).hexdigest()
        ok=got==want
        result[name]={'ok':ok,'sha256':got,'expected_sha256':want,'bytes':len(data)}
        if not ok:
            raise RuntimeError(f'Protected content asset changed: {name}; expected {want}, got {got}')
    return result


def verify(apk:Path, expected_package_strings=None, protected_assets=PROTECTED_ASSET_SHA256):
    cfg=_config(); out={'apk':str(apk),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'dex':{}}
    with zipfile.ZipFile(apk) as z:
        bad=z.testzip(); out['zip_ok']=bad is None
        if protected_assets:
            out['protected_assets']=_verify_protected_assets(z,protected_assets)
        manifest=z.read('AndroidManifest.xml'); out['manifest']=inspect_manifest(manifest)
        if cfg:
            checks=(
                ('package',cfg.get('application_id')),
                ('version_name',cfg.get('version_name')),
                ('version_code',cfg.get('version_code')),
                ('application_label',cfg.get('app_name')),
            )
            for key,want in checks:
                if want is not None and out['manifest'].get(key)!=want:
                    raise RuntimeError(f'manifest {key} mismatch: expected {want!r}, got {out["manifest"].get(key)!r}')
            old_auth=[a for a in out['manifest']['provider_authorities'] if isinstance(a,str) and a.startswith('com.redrazors.pathbuilder2e')]
            if old_auth: raise RuntimeError(f'old provider authorities remain: {old_auth}')
            if cfg.get('theme_switching_enabled') is False:
                out['fixed_theme']=verify_fixed_theme(z.read('res/layout/dialog_fragment_frontpage_more.xml'))
        scan=manifest+z.read('resources.arsc')
        leaked=[x.decode() for x in OLD_AD_IDS if x in scan]
        if leaked: raise RuntimeError(f'production AdMob IDs remain: {leaked}')
        out['production_ad_ids_absent']=True
        for n in z.namelist():
            if n.startswith('classes') and n.endswith('.dex'):
                ok,detail=verify_dex(z.read(n)); out['dex'][n]=detail
                if not ok: raise RuntimeError(f'DEX verify failed: {n} {detail}')
    alignment=int(cfg.get('native_library_alignment',16384)) if cfg else 16384
    out['native_alignment']=verify_alignment(apk,alignment)
    r=subprocess.run(['jarsigner','-verify',str(apk)],capture_output=True,text=True); out['v1_ok']=r.returncode==0 and 'jar verified' in r.stdout.lower()
    out['v2']=verify_v2(apk)
    expected_cert=str(cfg.get('expected_signing_cert_sha256','')).lower() if cfg else ''
    if expected_cert and out['v2']['cert_sha256'].lower()!=expected_cert:
        raise RuntimeError(f'wrong signing certificate: expected {expected_cert}, got {out["v2"]["cert_sha256"].lower()}')
    if not out['zip_ok'] or not out['v1_ok'] or not out['v2']['ok']: raise RuntimeError(out)
    return out

# APK Signature Scheme v2 verifier for the simple RSA/SHA-256 signing block produced by apk_sign.py.
def _parse_lp(buf,off=0):
    n=struct.unpack_from('<I',buf,off)[0]; off+=4; return buf[off:off+n],off+n

def _find_eocd(d):
    i=d.rfind(b'PK\x05\x06',max(0,len(d)-65557))
    if i<0: raise RuntimeError('EOCD not found')
    comlen=struct.unpack_from('<H',d,i+20)[0]
    if i+22+comlen!=len(d): raise RuntimeError('bad EOCD/comment')
    return i

def _content_digest(parts):
    ds=[]
    for sec in parts:
        for o in range(0,len(sec),1024*1024):
            ch=sec[o:o+1024*1024]
            ds.append(hashlib.sha256(b'\xa5'+struct.pack('<I',len(ch))+ch).digest())
    return hashlib.sha256(b'\x5a'+struct.pack('<I',len(ds))+b''.join(ds)).digest()

def verify_v2(apk:Path):
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
    d=Path(apk).read_bytes(); e=_find_eocd(d); cd_size,cd_off=struct.unpack_from('<II',d,e+12)
    magicpos=cd_off-16
    if d[magicpos:cd_off]!=b'APK Sig Block 42': raise RuntimeError('v2 magic missing')
    size2=struct.unpack_from('<Q',d,magicpos-8)[0]; start=cd_off-(size2+8); size1=struct.unpack_from('<Q',d,start)[0]
    if size1!=size2: raise RuntimeError('v2 size mismatch')
    pos=start+8; pairs_end=magicpos-8; v2=None
    while pos<pairs_end:
        l=struct.unpack_from('<Q',d,pos)[0]; pos+=8; ident=struct.unpack_from('<I',d,pos)[0]; val=d[pos+4:pos+l]; pos+=l
        if ident==0x7109871a: v2=val
    if v2 is None: raise RuntimeError('v2 pair missing')
    signers,_=_parse_lp(v2); signer,_=_parse_lp(signers); signed_data,q=_parse_lp(signer); sigs,q=_parse_lp(signer,q); pub,q=_parse_lp(signer,q)
    dgseq,r=_parse_lp(signed_data); certseq,r=_parse_lp(signed_data,r); attrs,r=_parse_lp(signed_data,r)
    drec,_=_parse_lp(dgseq); alg=struct.unpack_from('<I',drec,0)[0]; recorded,_=_parse_lp(drec,4)
    certder,_=_parse_lp(certseq); srec,_=_parse_lp(sigs); salg=struct.unpack_from('<I',srec,0)[0]; sig,_=_parse_lp(srec,4)
    if alg!=0x0103 or salg!=0x0103: raise RuntimeError('unsupported v2 algorithm')
    cert=x509.load_der_x509_certificate(certder); cert.public_key().verify(sig,signed_data,padding.PKCS1v15(),hashes.SHA256())
    eocd=bytearray(d[e:]); struct.pack_into('<I',eocd,16,start); comp=_content_digest([d[:start],d[cd_off:e],bytes(eocd)])
    if comp!=recorded: raise RuntimeError('v2 content digest mismatch')
    if cert.public_key().public_bytes(Encoding.DER,PublicFormat.SubjectPublicKeyInfo)!=pub: raise RuntimeError('v2 public key mismatch')
    return {'ok':True,'cert_sha256':cert.fingerprint(hashes.SHA256()).hex(),'digest':comp.hex()}
