#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import plistlib
import zipfile

APP='Payload/Telegram.app/'

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def _primary_files(plist, key='CFBundleIcons'):
    icons=plist.get(key)
    if not isinstance(icons,dict): return []
    prim=icons.get('CFBundlePrimaryIcon')
    if not isinstance(prim,dict): return []
    files=prim.get('CFBundleIconFiles',[])
    return list(files) if isinstance(files,list) else []

def _declares_icon(plist):
    if plist.get('CFBundleIconName'):
        return True
    for key in ('CFBundleIcons','CFBundleIcons~ipad'):
        icons=plist.get(key)
        if isinstance(icons,dict) and isinstance(icons.get('CFBundlePrimaryIcon'),dict):
            prim=icons['CFBundlePrimaryIcon']
            if prim.get('CFBundleIconName') or prim.get('CFBundleIconFiles'):
                return True
    return False

def analyze_ipa(path):
    path=pathlib.Path(path)
    with zipfile.ZipFile(path,'r') as z:
        names=set(z.namelist())
        info=plistlib.loads(z.read(APP+'Info.plist'))
        root_files=sorted(n[len(APP):] for n in names if n.startswith(APP) and '/' not in n[len(APP):] and n != APP)
        notification_files=sorted(n for n in root_files if 'notification' in n.lower() and n.lower().endswith(('.png','.pdf','.webp')))
        jerkgram_icon_files=sorted(n for n in root_files if n.lower().startswith('jerkgram') and ('icon' in n.lower() or n.lower().endswith('.png')))
        telegram_icon_files=sorted(n for n in root_files if n.lower().startswith('telegram') and ('icon' in n.lower() or n.lower().endswith('.png')))
        assets_name=APP+'Assets.car'
        assets_present=assets_name in names
        extensions=[]
        for n in sorted(names):
            if not n.startswith(APP+'PlugIns/') or not n.endswith('/Info.plist'):
                continue
            ep=plistlib.loads(z.read(n))
            prefix=n[:-len('Info.plist')]
            exe=ep.get('CFBundleExecutable')
            exe_path=prefix+exe if exe and prefix+exe in names else None
            extensions.append({
                'path':prefix.rstrip('/'),
                'bundle_id':ep.get('CFBundleIdentifier'),
                'bundle_name':ep.get('CFBundleName'),
                'display_name':ep.get('CFBundleDisplayName'),
                'declares_app_icon':_declares_icon(ep),
                'cfbundle_icon_name':ep.get('CFBundleIconName'),
                'primary_icon_files':_primary_files(ep),
                'executable_sha256':sha256(z.read(exe_path)) if exe_path else None,
            })
        notif_ext=[e for e in extensions if e['bundle_id'] in {'ph.telegra.Telegraph.NotificationService','ph.telegra.Telegraph.NotificationContent'} or 'NotificationService' in e['path'] or 'NotificationContent' in e['path']]
        notif_declares=any(e['declares_app_icon'] for e in notif_ext)
        primary=_primary_files(info)
        modern_name=info.get('CFBundleIconName')
        legacy_override=(not modern_name and any(str(x).lower().startswith('jerkgram') for x in primary))
        if notif_declares:
            owner='ambiguous-extension-icon-declaration-present'
        elif legacy_override and assets_present:
            owner='main-app-icon-packaging-leading-evidence'
        else:
            owner='insufficient-evidence'
        return {
            'ipa_sha256':sha256(path.read_bytes()),
            'main':{
                'bundle_id':info.get('CFBundleIdentifier'),
                'bundle_name':info.get('CFBundleName'),
                'display_name':info.get('CFBundleDisplayName'),
                'cfbundle_icon_name':modern_name,
                'primary_icon_files':primary,
                'primary_icon_files_ipad':_primary_files(info,'CFBundleIcons~ipad'),
                'assets_car_present':assets_present,
                'assets_car_sha256':sha256(z.read(assets_name)) if assets_present else None,
                'jerkgram_root_icon_files':jerkgram_icon_files,
                'telegram_root_icon_files':telegram_icon_files,
                'notification_sized_root_files':notification_files,
            },
            'extensions':extensions,
            'evidence':{
                'legacy_primary_override_without_modern_icon_name':legacy_override,
                'notification_service_declares_app_icon':notif_declares,
                'small_badge_owner_classification':owner,
                'note':'Classification is bundle-level leading evidence only; Xcode Icon Composer probe is required before final root-cause closure.'
            }
        }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('ipa')
    ap.add_argument('-o','--output')
    ns=ap.parse_args()
    report=analyze_ipa(ns.ipa)
    text=json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)
    if ns.output:
        pathlib.Path(ns.output).write_text(text+'\n')
    else:
        print(text)

if __name__=='__main__': main()
