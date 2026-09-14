#!/usr/bin/env python3
import importlib.util
import pathlib
import tempfile
import plistlib
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
MOD=ROOT/'tools/m05r2/analyze_branding.py'
assert MOD.is_file(), f'missing analyzer: {MOD}'
spec=importlib.util.spec_from_file_location('analyze_branding', MOD)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def make_ipa(path, *, icon_name=None, primary_files=None, assets=b'TELEGRAM_ASSETS', ext_icons=False):
    info={
      'CFBundleIdentifier':'ph.telegra.Telegraph',
      'CFBundleName':'Jerkgram',
      'CFBundleIcons':{'CFBundlePrimaryIcon':{'CFBundleIconFiles':primary_files or ['Telegram60x60']}},
    }
    if icon_name is not None:
      info['CFBundleIconName']=icon_name
    ext={'CFBundleIdentifier':'ph.telegra.Telegraph.NotificationService','CFBundleName':'Telegram'}
    if ext_icons:
      ext['CFBundleIcons']={'CFBundlePrimaryIcon':{'CFBundleIconFiles':['ExtensionIcon']}}
    with zipfile.ZipFile(path,'w') as z:
      z.writestr('Payload/Telegram.app/Info.plist', plistlib.dumps(info))
      z.writestr('Payload/Telegram.app/Assets.car', assets)
      z.writestr('Payload/Telegram.app/Jerkgram60x60@2x.png', b'JG')
      z.writestr('Payload/Telegram.app/Telegram60x60@2x.png', b'TG')
      z.writestr('Payload/Telegram.app/BlueNotificationIcon@3x.png', b'ALT')
      z.writestr('Payload/Telegram.app/PlugIns/NotificationServiceExtensionv1.appex/Info.plist', plistlib.dumps(ext))
      z.writestr('Payload/Telegram.app/PlugIns/NotificationServiceExtensionv1.appex/NotificationServiceExtensionv1', b'EXE')

with tempfile.TemporaryDirectory() as td:
    td=pathlib.Path(td)
    m05=td/'m05.ipa'; make_ipa(m05, primary_files=['Jerkgram60x60'])
    report=mod.analyze_ipa(m05)
    assert report['main']['bundle_id']=='ph.telegra.Telegraph'
    assert report['main']['primary_icon_files']==['Jerkgram60x60']
    assert report['main']['cfbundle_icon_name'] is None
    assert report['main']['assets_car_present'] is True
    assert report['evidence']['legacy_primary_override_without_modern_icon_name'] is True
    assert report['evidence']['notification_service_declares_app_icon'] is False
    assert report['evidence']['small_badge_owner_classification']=='main-app-icon-packaging-leading-evidence'

    ext=td/'ext.ipa'; make_ipa(ext, primary_files=['Jerkgram60x60'], ext_icons=True)
    report2=mod.analyze_ipa(ext)
    assert report2['evidence']['notification_service_declares_app_icon'] is True
    assert report2['evidence']['small_badge_owner_classification']=='ambiguous-extension-icon-declaration-present'

print('M05R2_BRANDING_ROOT_CAUSE_TEST_PASS')
