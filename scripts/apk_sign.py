from __future__ import annotations
from pathlib import Path
import hashlib, os, shutil, struct, subprocess, zipfile
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


def is_signature_entry(name:str)->bool:
    u=name.upper()
    return u=='META-INF/MANIFEST.MF' or (u.startswith('META-INF/') and (u.endswith('.SF') or u.endswith('.RSA') or u.endswith('.DSA') or u.endswith('.EC') or '/SIG-' in u))

def clone_info(src, extra=None):
    zi=zipfile.ZipInfo(src.filename, src.date_time)
    zi.compress_type=src.compress_type; zi.comment=src.comment; zi.extra=src.extra if extra is None else extra
    zi.create_system=src.create_system; zi.create_version=src.create_version; zi.extract_version=src.extract_version
    zi.flag_bits=src.flag_bits & ~0x08; zi.volume=src.volume; zi.internal_attr=src.internal_attr; zi.external_attr=src.external_attr
    return zi

def build_with_overrides(source:Path,dest:Path,overrides:dict[str,bytes],*,strip_signatures=True,align=False):
    with zipfile.ZipFile(source,'r') as zin, zipfile.ZipFile(dest,'w',allowZip64=True) as zout:
        seen=set()
        for src in zin.infolist():
            n=src.filename
            if n in seen: raise RuntimeError(f'duplicate zip entry: {n}')
            seen.add(n)
            if strip_signatures and is_signature_entry(n): continue
            data=overrides.get(n, zin.read(src))
            extra=src.extra
            if align and src.compress_type==zipfile.ZIP_STORED:
                alignment=4096 if n.endswith('.so') else 4
                cur=zout.fp.tell(); base=cur+30+len(n.encode('utf-8'))+len(extra)
                need=(-base)%alignment; add=need if need>=4 else need+alignment
                extra=extra+struct.pack('<HH',0xFFFF,add-4)+b'\0'*(add-4)
            zout.writestr(clone_info(src,extra),data,compress_type=src.compress_type)
        zout.comment=zin.comment

def zip_data_offset(fp,info):
    fp.seek(info.header_offset); h=fp.read(30); nl,el=struct.unpack_from('<HH',h,26); return info.header_offset+30+nl+el

def check_alignment(path:Path):
    bad=[]
    with zipfile.ZipFile(path) as z, open(path,'rb') as f:
        for i in z.infolist():
            if i.compress_type!=zipfile.ZIP_STORED: continue
            o=zip_data_offset(f,i); a=4096 if i.filename.endswith('.so') else 4
            if o%a: bad.append((i.filename,o,a,o%a))
    return bad

def _lp(b): return struct.pack('<I',len(b))+b

def _find_eocd(d:bytes):
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

def _load_key_cert(keystore:Path,password:bytes):
    key,cert,_=pkcs12.load_key_and_certificates(keystore.read_bytes(),password)
    if key is None or cert is None: raise RuntimeError('PKCS12 has no key/certificate')
    return key,cert

def v2_sign(src:Path,dst:Path,keystore:Path,password:bytes):
    d=src.read_bytes(); e=_find_eocd(d); cd_size,cd_off=struct.unpack_from('<II',d,e+12)
    if cd_off+cd_size!=e: raise RuntimeError('central directory layout unsupported')
    before=d[:cd_off]; cd=d[cd_off:e]; eocd=d[e:]; dig=_content_digest([before,cd,eocd]); alg=0x0103
    digest_rec=_lp(struct.pack('<I',alg)+_lp(dig)); digests=_lp(digest_rec)
    key,cert=_load_key_cert(keystore,password); cert_der=cert.public_bytes(Encoding.DER); certs=_lp(_lp(cert_der)); attrs=_lp(b'')
    signed_data=digests+certs+attrs; sig=key.sign(signed_data,padding.PKCS1v15(),hashes.SHA256())
    sigs=_lp(_lp(struct.pack('<I',alg)+_lp(sig))); pub=key.public_key().public_bytes(Encoding.DER,PublicFormat.SubjectPublicKeyInfo)
    signer=_lp(signed_data)+sigs+_lp(pub); v2val=_lp(_lp(signer)); pair=struct.pack('<Q',4+len(v2val))+struct.pack('<I',0x7109871a)+v2val
    size=len(pair)+24; block=struct.pack('<Q',size)+pair+struct.pack('<Q',size)+b'APK Sig Block 42'
    ne=bytearray(eocd); struct.pack_into('<I',ne,16,cd_off+len(block)); dst.write_bytes(before+block+cd+ne)
    return cert.fingerprint(hashes.SHA256()).hex()

def sign_apk(unsigned:Path, final:Path, keystore:Path, password:str, workdir:Path):
    workdir.mkdir(parents=True,exist_ok=True); v1=workdir/'v1.apk'; aligned=workdir/'v1_aligned.apk'
    shutil.copy2(unsigned,v1)
    cmd=['jarsigner','-keystore',str(keystore),'-storetype','PKCS12','-storepass',password,'-keypass',password,'-sigalg','SHA256withRSA','-digestalg','SHA-256','-sigfile','PF2ERU',str(v1),'pbfix']
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    build_with_overrides(v1,aligned,{},strip_signatures=False,align=True)
    bad=check_alignment(aligned)
    if bad: raise RuntimeError(f'alignment failure: {bad[:3]}')
    vr=subprocess.run(['jarsigner','-verify',str(aligned)],capture_output=True,text=True)
    if vr.returncode!=0 or 'jar verified' not in vr.stdout.lower(): raise RuntimeError('v1 signature verify failed')
    cert=v2_sign(aligned,final,keystore,password.encode())
    vr=subprocess.run(['jarsigner','-verify',str(final)],capture_output=True,text=True)
    if vr.returncode!=0 or 'jar verified' not in vr.stdout.lower(): raise RuntimeError('final v1 verify failed')
    if check_alignment(final): raise RuntimeError('final alignment failure')
    with zipfile.ZipFile(final) as z:
        if z.testzip(): raise RuntimeError('zip CRC failure')
    return cert
