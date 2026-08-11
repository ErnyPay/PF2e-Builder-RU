from __future__ import annotations
from pathlib import Path
import hashlib,struct,subprocess,zipfile


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

def verify(apk:Path, expected_package_strings=None):
    out={'apk':str(apk),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'dex':{}}
    with zipfile.ZipFile(apk) as z:
        bad=z.testzip(); out['zip_ok']=bad is None
        for n in z.namelist():
            if n.startswith('classes') and n.endswith('.dex'):
                ok,detail=verify_dex(z.read(n)); out['dex'][n]=detail
                if not ok: raise RuntimeError(f'DEX verify failed: {n} {detail}')
    r=subprocess.run(['jarsigner','-verify',str(apk)],capture_output=True,text=True); out['v1_ok']=r.returncode==0 and 'jar verified' in r.stdout.lower()
    out['v2']=verify_v2(apk)
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
