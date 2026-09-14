#!/usr/bin/env python3
import argparse, collections, copy, hashlib, json, pathlib, plistlib, subprocess, tempfile, zipfile
APP='Payload/Telegram.app/'
BASE_IPA_SHA='d266cd250a40efaf400724edde8a10853cc7b8b159763ed4417bbbac1aadaac9'
MAIN_SHA='5f23143d29373905d95577310242479e2db922bc50891d6cd5bc89d3b4d212f1'
PRODUCT_SHA='dbea7cd08cb0ebf4762333e67c7a3e0d2c223d6b4c18d34c82fa06ca4bbbfa64'
COMPAT_SHA='a347679d04e0506841a623ce1383cf3c69a20fe0124c8ec9d7a9fb8f607e066a'
PROBE_CAR_SHA='14686d8e0332ca4bf5e4e3d6b61e6d21a3bdf555089af286d9395f6422959c95'
FALLBACKS={APP+'JerkgramGlassReveal60x60@2x.png':'df82726a2a40f884d77e9b2212c4cac37aa497df158b1d6ec4a89f38d2344432',APP+'JerkgramGlassReveal76x76@2x~ipad.png':'bfcf63cc8430871b74c0a980e8457fefc116f1a3819c306ff5c33a7969fe2df6'}
OLD_FLAT={APP+'Jerkgram60x60@2x.png',APP+'Jerkgram60x60@3x.png',APP+'Jerkgram76x76.png',APP+'Jerkgram76x76@2x.png',APP+'Jerkgram83.5x83.5@2x.png'}
ALLOWED_CHANGED={APP+'Info.plist',APP+'Assets.car'}
def sha(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return sha(pathlib.Path(p).read_bytes())
def zmap(p):
    with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist() if not n.endswith('/')}
def strip_primary_icon(pl):
    d=copy.deepcopy(pl)
    for k in ('CFBundleIcons','CFBundleIcons~ipad'):
        if isinstance(d.get(k),dict):d[k].pop('CFBundlePrimaryIcon',None)
    return d
def _decompile_raw(scar,car,out):
    subprocess.run([scar,'decompile',str(car),'--out',str(out),'--raw'],check=True,stdout=subprocess.DEVNULL);return json.loads((out/'manifest.json').read_text())
def _sig(r):
    c=r['content'];return (tuple(sorted(r['key'].items())),r['name'],r['layout'],r['flags'],r['pixel_format'],r['color_space_id'],r['width'],r['height'],r['scale'],r['modified'],tuple(sorted(r['composition'].items())),r['bitmap_info'],c['type'],c.get('kind'))
def _payload(root,r):
    f=r['content'].get('file');return b'' if not f else (root/f).read_bytes()
def _rmap(root,m):
    out=collections.defaultdict(list)
    for r in m['renditions']:out[_sig(r)].append(sha(_payload(root,r)))
    for v in out.values():v.sort()
    return out
def _assert_subset(label,small_root,small,merged_root,merged):
    sm=_rmap(small_root,small);mm=_rmap(merged_root,merged)
    for sig,hashes in sm.items():
        got=list(mm.get(sig,[]))
        for h in hashes:
            assert h in got,f'{label} rendition/raw payload missing or changed: {sig[:4]}';got.remove(h)
    assert all(f in merged['facets'] for f in small['facets']),f'{label} facets not preserved'
    assert all(merged['bitmap_keys'].get(k)==v for k,v in small['bitmap_keys'].items()),f'{label} bitmap keys not preserved'
def main(base,target,scar,probe):
    base=pathlib.Path(base);target=pathlib.Path(target);probe=pathlib.Path(probe)
    assert sha_file(base)==BASE_IPA_SHA,'wrong M0.5 base IPA';assert sha_file(probe/'JGIconProbe.app/Assets.car')==PROBE_CAR_SHA
    b=zmap(base);t=zmap(target);bs,ts=set(b),set(t);changed={n for n in bs&ts if sha(b[n])!=sha(t[n])};added=ts-bs;removed=bs-ts
    assert changed==ALLOWED_CHANGED,f'changed scope mismatch: {sorted(changed)}';assert added==set(FALLBACKS),f'added scope mismatch: {sorted(added)}';assert removed==OLD_FLAT,f'removed scope mismatch: {sorted(removed)}'
    assert sha(t[APP+'Telegram'])==MAIN_SHA;assert sha(t[APP+'Jerkgram.dylib'])==PRODUCT_SHA
    compats=[n for n in t if n.endswith('JerkgramCompatibility.dylib')];assert len(compats)==6 and all(sha(t[n])==COMPAT_SHA for n in compats)
    bp=plistlib.loads(b[APP+'Info.plist']);tp=plistlib.loads(t[APP+'Info.plist']);assert tp['CFBundleIdentifier']=='ph.telegra.Telegraph';assert tp.get('CFBundleName')=='Jerkgram' and tp.get('CFBundleDisplayName')=='Jerkgram';assert strip_primary_icon(bp)==strip_primary_icon(tp)
    assert tp['CFBundleIcons']['CFBundlePrimaryIcon']=={'CFBundleIconFiles':['JerkgramGlassReveal60x60'],'CFBundleIconName':'JerkgramGlassReveal'}
    assert tp['CFBundleIcons~ipad']['CFBundlePrimaryIcon']=={'CFBundleIconFiles':['JerkgramGlassReveal60x60','JerkgramGlassReveal76x76'],'CFBundleIconName':'JerkgramGlassReveal'}
    for n,h in FALLBACKS.items():assert sha(t[n])==h
    for n in OLD_FLAT:assert n not in t
    assert all(n not in changed and n not in added and n not in removed for n in t if '/PlugIns/Notification' in n)
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td);(td/'tg.car').write_bytes(b[APP+'Assets.car']);(td/'merged.car').write_bytes(t[APP+'Assets.car'])
        tm=_decompile_raw(scar,td/'tg.car',td/'tg');jm=_decompile_raw(scar,probe/'JGIconProbe.app/Assets.car',td/'jg');mm=_decompile_raw(scar,td/'merged.car',td/'merged')
        assert (len(tm['renditions']),len(tm['facets']))==(5408,1365);assert (len(jm['renditions']),len(jm['facets']))==(30,16);assert (len(mm['renditions']),len(mm['facets']))==(5438,1381);assert tm['appearances']==jm['appearances']==mm['appearances'];assert set(jm['car']['key_format']).issubset(set(mm['car']['key_format']))
        _assert_subset('Telegram',td/'tg',tm,td/'merged',mm);_assert_subset('Jerkgram Icon Composer',td/'jg',jm,td/'merged',mm)
        assert any(f['name']=='JerkgramGlassReveal' for f in mm['facets']);icon=[r for r in mm['renditions'] if r['name']=='JerkgramGlassReveal.iconstack'];assert len(icon)==3 and {r['key'].get('appearance',0) for r in icon}=={1,4,10};assert sum(1 for r in mm['renditions'] if r['layout']==12 and r['key'].get('identifier')==62444)==8
    print('M0_5_R2_BRANDING_VERIFIER_PASS');print('changed=',sorted(changed));print('added=',sorted(added));print('removed=',sorted(removed));print('main_sha=',MAIN_SHA);print('product_sha=',PRODUCT_SHA);print('compat_sha=',COMPAT_SHA);print('merged_assets_car_sha=',sha(t[APP+'Assets.car']))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('base');ap.add_argument('target');ap.add_argument('--scar',required=True);ap.add_argument('--probe',required=True);a=ap.parse_args();main(a.base,a.target,a.scar,a.probe)
