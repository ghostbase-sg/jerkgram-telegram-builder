#!/usr/bin/env python3
import argparse, copy, hashlib, json, pathlib, plistlib, shutil, subprocess, tempfile, zipfile

APP='Payload/Telegram.app/'
EXPECTED_BASE='d266cd250a40efaf400724edde8a10853cc7b8b159763ed4417bbbac1aadaac9'
PLANE_SHA='9dc83c22a01878aac9f8494c509a7862fdd1679d7e7f7f0026afc367d3a7e304'
PROBE_CAR_SHA='14686d8e0332ca4bf5e4e3d6b61e6d21a3bdf555089af286d9395f6422959c95'
OLD_FLAT={APP+'Jerkgram60x60@2x.png',APP+'Jerkgram60x60@3x.png',APP+'Jerkgram76x76.png',APP+'Jerkgram76x76@2x.png',APP+'Jerkgram83.5x83.5@2x.png'}

def sha_file(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def clone_info(info,name=None):
    z=zipfile.ZipInfo(name or info.filename,date_time=info.date_time)
    for a in ('compress_type','comment','extra','internal_attr','external_attr','create_system','create_version','extract_version','flag_bits','volume'):
        if hasattr(info,a): setattr(z,a,getattr(info,a))
    return z
def new_info(name,template_time):
    z=zipfile.ZipInfo(name,date_time=template_time); z.compress_type=zipfile.ZIP_DEFLATED; z.create_system=3; z.external_attr=(0o100644<<16); return z
def run(*args,stdout=None): subprocess.run(list(args),check=True,stdout=stdout)

def merge_cars(base_car,probe_car,scar,out_car,work_root):
    tg=work_root/'tg'; jg=work_root/'jg'; merged=work_root/'merged'
    run(scar,'decompile',str(base_car),'--out',str(tg),'--raw',stdout=subprocess.DEVNULL)
    run(scar,'decompile',str(probe_car),'--out',str(jg),'--raw',stdout=subprocess.DEVNULL)
    shutil.copytree(tg,merged)
    T=json.loads((merged/'manifest.json').read_text()); J=json.loads((jg/'manifest.json').read_text())
    assert T['car']['coreui_version']==J['car']['coreui_version']==975
    assert T['car']['storage_version']==J['car']['storage_version']==17
    assert T['car']['schema_version']==J['car']['schema_version']==2
    assert T['appearances']==J['appearances']
    assert set(J['car']['key_format']).issubset(set(T['car']['key_format']))
    tids={f['attributes'].get('identifier') for f in T['facets']}|{r['key'].get('identifier') for r in T['renditions']}; tids.discard(None)
    jids={f['attributes'].get('identifier') for f in J['facets']}|{r['key'].get('identifier') for r in J['renditions']}; jids.discard(None)
    assert not (tids&jids),f'identifier collision: {sorted(tids&jids)}'
    assert not ({f['name'] for f in T['facets']}&{f['name'] for f in J['facets']}),'facet name collision'
    assert not (set(T['bitmap_keys'])&set(J['bitmap_keys'])),'bitmap key collision'
    payload_dir=merged/'rawpayload_jg'; payload_dir.mkdir()
    for src_r in J['renditions']:
        r=copy.deepcopy(src_r); content=r.get('content',{}); f=content.get('file')
        if f:
            src=jg/f; dst=payload_dir/src.name; shutil.copy2(src,dst); content['file']=str(pathlib.Path('rawpayload_jg')/src.name)
        T['renditions'].append(r)
    T['facets'].extend(copy.deepcopy(J['facets'])); T['bitmap_keys'].update(copy.deepcopy(J['bitmap_keys']))
    (merged/'manifest.json').write_text(json.dumps(T,indent=2,sort_keys=True)+'\n')
    run(scar,'compile',str(merged),'--out',str(out_car),stdout=subprocess.DEVNULL)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('base_ipa'); ap.add_argument('output_ipa'); ap.add_argument('--probe',required=True); ap.add_argument('--scar',required=True); ns=ap.parse_args()
    base=pathlib.Path(ns.base_ipa); out=pathlib.Path(ns.output_ipa); probe=pathlib.Path(ns.probe); scar=str(pathlib.Path(ns.scar))
    assert sha_file(base)==EXPECTED_BASE,'input is not accepted M0.5 IPA'
    plane=probe/'source/JerkgramGlassIconComposerPackages/JerkgramGlassReveal.icon/Assets/Plane.svg'; probe_car=probe/'JGIconProbe.app/Assets.car'; probe_app=probe/'JGIconProbe.app'
    assert sha_file(plane)==PLANE_SHA,'wrong canonical Plane.svg'; assert sha_file(probe_car)==PROBE_CAR_SHA,'wrong Xcode probe Assets.car'
    with tempfile.TemporaryDirectory() as td:
        td=pathlib.Path(td); base_car=td/'base.car'; merged_car=td/'merged.car'
        with zipfile.ZipFile(base) as zin: base_car.write_bytes(zin.read(APP+'Assets.car'))
        merge_cars(base_car,probe_car,scar,merged_car,td/'mergework'); merged_bytes=merged_car.read_bytes()
        with zipfile.ZipFile(base,'r') as zin,zipfile.ZipFile(out,'w',allowZip64=True) as zout:
            info_map={i.filename:i for i in zin.infolist()}; template_time=info_map[APP+'Info.plist'].date_time
            pl=plistlib.loads(zin.read(APP+'Info.plist')); assert pl['CFBundleIdentifier']=='ph.telegra.Telegraph'
            pl['CFBundleIcons']['CFBundlePrimaryIcon']={'CFBundleIconFiles':['JerkgramGlassReveal60x60'],'CFBundleIconName':'JerkgramGlassReveal'}
            pl['CFBundleIcons~ipad']['CFBundlePrimaryIcon']={'CFBundleIconFiles':['JerkgramGlassReveal60x60','JerkgramGlassReveal76x76'],'CFBundleIconName':'JerkgramGlassReveal'}
            replacements={APP+'Info.plist':plistlib.dumps(pl,fmt=plistlib.FMT_BINARY,sort_keys=False),APP+'Assets.car':merged_bytes}
            for info in zin.infolist():
                if info.filename in OLD_FLAT: continue
                zout.writestr(clone_info(info),replacements.get(info.filename,zin.read(info.filename)))
            additions={APP+'JerkgramGlassReveal60x60@2x.png':(probe_app/'JerkgramGlassReveal60x60@2x.png').read_bytes(),APP+'JerkgramGlassReveal76x76@2x~ipad.png':(probe_app/'JerkgramGlassReveal76x76@2x~ipad.png').read_bytes()}
            for name,data in additions.items(): assert name not in info_map; zout.writestr(new_info(name,template_time),data)
    print(out); print('sha256',sha_file(out)); print('merged_assets_car_sha256',hashlib.sha256(merged_bytes).hexdigest())
if __name__=='__main__': main()
