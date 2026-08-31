#!/usr/bin/env python3
from pathlib import Path
import os,re
ROOT=Path(os.environ.get('JERKGRAM_SOURCE_ROOT',os.environ.get('GHOSTBASE_SOURCE_ROOT',str(Path.cwd())))).resolve()
SETTINGS=ROOT/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS=ROOT/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
APP=ROOT/'submodules/TelegramUI/Sources/AppDelegate.swift'
PROFILE=ROOT/'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift'
def req(v,m):
    if not v: raise SystemExit('[verify Build130 pre-Bazel] ERROR: '+m)
def block(t,token):
    s=t.find(token);req(s>=0,'missing '+token);b=t.find('{',s);d=0;ins=False;esc=False
    for i in range(b,len(t)):
        c=t[i]
        if ins:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':ins=False
            continue
        if c=='"':ins=True
        elif c=='{':d+=1
        elif c=='}':
            d-=1
            if d==0:return t[s:i+1]
    req(False,'unbalanced '+token)
def main():
    for p in (SETTINGS,STRINGS,APP,PROFILE):req(p.is_file(),'missing '+str(p))
    settings=SETTINGS.read_text();strings=STRINGS.read_text();app=APP.read_text();profile=PROFILE.read_text()
    req(profile.count('BUILD128_PROFILE_BIO_CORNER_OWNER1')==1,'triangle owner must survive exactly once')
    appearance=block(settings,'if page == .appearance {')
    req('strings.animatedBackgroundHint' not in appearance,'video-avatar explanatory row survived')
    req('strings.profileEffectDisabledHint' not in appearance,'profile-effect explanatory row survived')
    req('strings.hidePhoneHint' in appearance,'unrelated hide-phone hint was accidentally deleted')
    about=block(settings,'if page == .about {')
    for token in ('JerkgramApp','JerkgramCommunity','strings.jerkgramVersion','CFBundleShortVersionString','CFBundleVersion','strings.telegramBase','"12.9.2"','strings.anonymousAnalytics','strings.anonymousAnalyticsDescription'):
        req(token in about,'About invariant missing: '+token)
    req('Official Telegram 12.9.2' not in about,'legacy giant About footer survived')
    req(settings.count('case aboutValue(')==1 and settings.count('case telemetryToggle(')==1,'native About entry types missing or duplicated')
    for token in ('case let .aboutValue(section, _, _, _):','case let .telemetryToggle(section, _, _, _):','case let .aboutValue(section, index, _, _):','case let .telemetryToggle(section, index, _, _):','case let .aboutValue(ls, li, lt, lv):','case let .telemetryToggle(ls, li, lt, lv):','case let .aboutValue(_, _, title, value):','case let .telemetryToggle(_, _, title, value):'):
        req(token in settings,'new Settings enum case is not exhaustive: '+token)
    req('jerkgram.telemetry.anonymous.enabled' in settings,'global telemetry preference missing')
    req('Notification.Name("JerkgramTelemetryPreferenceChanged")' in settings,'OFF bridge missing')
    for token in ('BUILD130_RELEASE_STRINGS1','self.languageCode == "ru"','Анонимная аналитика','Anonymous Analytics','Помогайте улучшать Jerkgram','Help improve Jerkgram','Версия Jerkgram','Jerkgram Version'):
        req(token in strings,'localization invariant missing: '+token)
    req(re.search(r'[А-Яа-яЁё]',settings) is None,'hardcoded Cyrillic leaked into Settings owner')
    telemetry=app[app.find('// MARK: Jerkgram v1.2T BUILD130_TELEMETRY1'):app.find('@objc(AppDelegate) class AppDelegate')]
    req(telemetry,'telemetry owner missing')
    for token in ('https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity','"schema":1','class JerkgramTelemetry','SystemRandomNumberGenerator','randomBytes(32)','hmac(secret,String(format:"%04d-%02d-%02d"','hmac(secret,String(format:"%04d-W%02d"','hmac(secret,String(format:"%04d-%02d"','installReceiptId','minimumInterval: TimeInterval = 4 * 60 * 60','guard JerkgramTelemetryPreferences.isEnabled else { return }','request.timeoutInterval=8.0','queue.async','activeTask?.cancel()'):
        req(token in telemetry,'telemetry invariant missing: '+token)
    payload=telemetry[telemetry.find('var payload:'):telemetry.find('guard let body=')]
    req('secret' not in payload.lower(),'HMAC secret leaked into payload')
    req('installReceiptId' in payload and 'installReportedKey' in payload,'install receipt one-shot gate missing')
    success=telemetry[telemetry.find('let task=URLSession.shared.dataTask'):]
    req('(200..<300).contains(http.statusCode)' in success,'HTTP 2xx success gate missing')
    req('defaults.set(true,forKey:self.installReportedKey)' in success,'installReported is not set after success')
    req('defaults.removeObject(forKey:self.receiptKey)' in success,'receipt is not removed after first success')
    forbidden=('IDFA','IDFV','advertisingIdentifier','identifierForVendor','PeerId','MessageId','authKey','phoneNumber','accountPeerId','chatId','contact')
    for token in forbidden:req(token not in telemetry,'forbidden analytics identifier/data reference: '+token)
    req('Locale.current.regionCode' in telemetry,'device region must come from Locale')
    req('applicationDidBecomeActive()' in app and 'JerkgramTelemetry.shared.applicationDidBecomeActive()' in app,'safe foreground lifecycle hook missing')
    print('PRE-BUILD GATES: PASS')
    print('  PASS triangles final-owner survival')
    print('  PASS exact Appearance release-info removal + unrelated hint survival')
    print('  PASS About native version/privacy rows + exhaustive entry topology')
    print('  PASS EN/RU Telegram-language strings')
    print('  PASS telemetry endpoint/schema/HMAC rotation/rate-limit/OFF gate')
    print('  PASS telemetry forbidden-data hard gate')
    print('  PASS async foreground lifecycle wiring')
if __name__=='__main__':main()
