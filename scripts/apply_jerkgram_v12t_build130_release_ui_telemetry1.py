#!/usr/bin/env python3
from pathlib import Path
import os, re
ROOT=Path(os.environ.get('JERKGRAM_SOURCE_ROOT',os.environ.get('GHOSTBASE_SOURCE_ROOT',str(Path.cwd())))).resolve()
SETTINGS=ROOT/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STRINGS=ROOT/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
APP=ROOT/'submodules/TelegramUI/Sources/AppDelegate.swift'
PROFILE=ROOT/'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift'
MARK='// MARK: Jerkgram v1.2T BUILD130_RELEASE_UI_TELEMETRY1'

def req(v,m):
    if not v: raise RuntimeError('[Build130 release] '+m)
def bounds(t, token):
    s=t.find(token); req(s>=0,'missing owner '+token); b=t.find('{',s); req(b>=0,'missing brace '+token)
    d=0; ins=False; esc=False
    for i in range(b,len(t)):
        c=t[i]
        if ins:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': ins=False
            continue
        if c=='"': ins=True
        elif c=='{': d+=1
        elif c=='}':
            d-=1
            if d==0:return s,i+1
    raise RuntimeError('[Build130 release] unbalanced '+token)
def bracket(t,start):
    b=t.find('[',start); req(b>=0,'array missing'); d=0; ins=False; esc=False
    for i in range(b,len(t)):
        c=t[i]
        if ins:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c=='"':ins=False
            continue
        if c=='"':ins=True
        elif c=='[':d+=1
        elif c==']':
            d-=1
            if d==0:return b,i+1
    raise RuntimeError('[Build130 release] unbalanced array')

def patch_settings(t):
    if MARK in t:return t
    s,e=bounds(t,'if page == .appearance {'); block=t[s:e]
    infos=list(re.finditer(r'(?m)^\s*\.info\([^\n]+\),?\s*\n?',block))
    req(len(infos)==2,f'Appearance expected exactly 2 info rows, found {len(infos)}')
    for m in reversed(infos): block=block[:m.start()]+block[m.end():]
    t=t[:s]+block+t[e:]
    bridge='''private let jerkgramTelemetryEnabledKey = "jerkgram.telemetry.anonymous.enabled"\nprivate func jerkgramTelemetryEnabled() -> Bool {\n    let defaults = UserDefaults.standard\n    return defaults.object(forKey: jerkgramTelemetryEnabledKey) == nil ? true : defaults.bool(forKey: jerkgramTelemetryEnabledKey)\n}\nprivate func jerkgramSetTelemetryEnabled(_ enabled: Bool) {\n    UserDefaults.standard.set(enabled, forKey: jerkgramTelemetryEnabledKey)\n    NotificationCenter.default.post(name: Notification.Name("JerkgramTelemetryPreferenceChanged"), object: nil)\n}\n\n'''
    owner='private enum GhostBaseSettingsEntry: ItemListNodeEntry {'
    bi=t.find(owner); req(bi>=0,'settings entry enum missing')
    t=t[:bi]+bridge+t[bi:]
    enum='private enum GhostBaseSettingsEntry: ItemListNodeEntry {'
    es=t.find(enum); req(es>=0,'settings entry enum missing')
    insert=t.find('\n',es)+1
    t=t[:insert]+'    case aboutValue(Int32, Int32, String, String)\n    case telemetryToggle(Int32, Int32, String, Bool)\n'+t[insert:]
    t=t.replace('case let .toggle(section, _, _, _, _):', 'case let .aboutValue(section, _, _, _), let .telemetryToggle(section, _, _, _): return section\n        case let .toggle(section, _, _, _, _):',1)
    t=t.replace('case let .toggle(_, id, _, _, _):', 'case let .aboutValue(_, id, _, _), let .telemetryToggle(_, id, _, _): return id\n        case let .toggle(_, id, _, _, _):',1)
    req('case let .aboutValue(section' in t and 'case let .aboutValue(_, id' in t,'entry topology anchors missing')
    anchor='        case let .toggle('
    ri=t.find(anchor,es); req(ri>=0,'toggle renderer missing')
    render='''        case let .aboutValue(_, _, title, value):\n            return ItemListDisclosureItem(\n                presentationData: presentationData, systemStyle: .glass,\n                title: title, label: value, labelStyle: .text,\n                sectionId: self.section, style: .blocks, disclosureStyle: .none, action: nil\n            )\n        case let .telemetryToggle(_, _, title, value):\n            return ItemListSwitchItem(\n                presentationData: presentationData, systemStyle: .glass, title: title, value: value,\n                sectionId: self.section, style: .blocks,\n                updated: { enabled in jerkgramSetTelemetryEnabled(enabled) }\n            )\n'''
    t=t[:ri]+render+t[ri:]
    s,e=bounds(t,'if page == .about {'); block=t[s:e]
    ret=block.find('return ['); req(ret>=0,'About return array missing'); a,z=bracket(block,ret)
    arr='''[\n            .header(0, strings.about),\n            channelEntry(index: 1, username: "JerkgramApp", state: aboutChannelState),\n            channelEntry(index: 2, username: "JerkgramCommunity", state: aboutCommunityState),\n            .header(1, strings.version),\n            .aboutValue(1, 1, strings.jerkgramVersion, Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"),\n            .aboutValue(1, 2, strings.build, Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "—"),\n            .aboutValue(1, 3, strings.telegramBase, "12.9.2"),\n            .header(2, strings.privacy),\n            .telemetryToggle(2, 1, strings.anonymousAnalytics, jerkgramTelemetryEnabled()),\n            .info(3, strings.anonymousAnalyticsDescription)\n        ]'''
    block=block[:a]+arr+block[z:]
    t=t[:s]+block+t[e:]
    owner='private func ghostBaseSettingsEntries('
    oi=t.find(owner); req(oi>=0,'settings entries owner missing')
    t=t[:oi]+MARK+'\n'+t[oi:]
    return t

STR_EXT=r'''

// MARK: Jerkgram v1.2T BUILD130_RELEASE_STRINGS1
public extension JerkgramStrings {
    var version: String { self.languageCode == "ru" ? "ВЕРСИЯ" : "VERSION" }
    var privacy: String { self.languageCode == "ru" ? "КОНФИДЕНЦИАЛЬНОСТЬ" : "PRIVACY" }
    var jerkgramVersion: String { self.languageCode == "ru" ? "Версия Jerkgram" : "Jerkgram Version" }
    var build: String { self.languageCode == "ru" ? "Сборка" : "Build" }
    var telegramBase: String { self.languageCode == "ru" ? "База Telegram" : "Telegram Base" }
    var anonymousAnalytics: String { self.languageCode == "ru" ? "Анонимная аналитика" : "Anonymous Analytics" }
    var anonymousAnalyticsDescription: String {
        if self.languageCode == "ru" {
            return "Помогайте улучшать Jerkgram, отправляя анонимную статистику использования: версию Jerkgram, версию iOS и регион устройства. Аккаунты Telegram, сообщения, имена пользователей и номера телефонов никогда не собираются."
        } else {
            return "Help improve Jerkgram by sharing anonymous usage statistics such as Jerkgram version, iOS version and device region. Telegram accounts, messages, usernames and phone numbers are never collected."
        }
    }
}
'''

def patch_strings(t):
    return t if 'BUILD130_RELEASE_STRINGS1' in t else t+STR_EXT

TELEMETRY=r'''

// MARK: Jerkgram v1.2T BUILD130_TELEMETRY1
private extension Notification.Name {
    static let jerkgramTelemetryPreferenceChanged = Notification.Name("JerkgramTelemetryPreferenceChanged")
}
private enum JerkgramTelemetryPreferences {
    static let enabledKey = "jerkgram.telemetry.anonymous.enabled"
    static var isEnabled: Bool {
        get { let d = UserDefaults.standard; return d.object(forKey: enabledKey) == nil ? true : d.bool(forKey: enabledKey) }
        set { UserDefaults.standard.set(newValue, forKey: enabledKey) }
    }
}
private final class JerkgramTelemetry {
    static let shared = JerkgramTelemetry()
    private let queue = DispatchQueue(label: "org.jerkgram.telemetry", qos: .utility)
    private var activeTask: URLSessionDataTask?
    private var observer: NSObjectProtocol?
    private let endpoint = URL(string: "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity")!
    private let secretKey = "jerkgram.telemetry.secret.v1"
    private let firstDateKey = "jerkgram.telemetry.firstDate.v1"
    private let receiptKey = "jerkgram.telemetry.installReceipt.v1"
    private let installReportedKey = "jerkgram.telemetry.installReported.v1"
    private let lastSuccessKey = "jerkgram.telemetry.lastSuccess.v1"
    private let minimumInterval: TimeInterval = 4 * 60 * 60
    private init() {
        observer = NotificationCenter.default.addObserver(forName: .jerkgramTelemetryPreferenceChanged, object: nil, queue: nil) { [weak self] _ in
            guard let self else { return }; self.queue.async { if !JerkgramTelemetryPreferences.isEnabled { self.activeTask?.cancel(); self.activeTask = nil } }
        }
    }
    func applicationDidBecomeActive() { queue.async { [weak self] in self?.submitIfNeeded() } }
    private func submitIfNeeded() {
        guard JerkgramTelemetryPreferences.isEnabled else { return }
        let defaults = UserDefaults.standard; let now = Date()
        if let last = defaults.object(forKey: lastSuccessKey) as? Date, now.timeIntervalSince(last) < minimumInterval { return }
        guard activeTask == nil else { return }
        let secret = localSecret(defaults: defaults)
        let firstDate: Date
        if let stored = defaults.object(forKey: firstDateKey) as? Date { firstDate = stored } else { firstDate = now; defaults.set(now, forKey: firstDateKey) }
        var c = Calendar(identifier: .iso8601); c.timeZone = TimeZone(secondsFromGMT: 0)!
        let year=c.component(.year,from:now), month=c.component(.month,from:now), day=c.component(.day,from:now)
        let weekYear=c.component(.yearForWeekOfYear,from:now), week=c.component(.weekOfYear,from:now)
        let dayId=hmac(secret,String(format:"%04d-%02d-%02d",year,month,day))
        let weekId=hmac(secret,String(format:"%04d-W%02d",weekYear,week))
        let monthId=hmac(secret,String(format:"%04d-%02d",year,month))
        let receipt: String
        if let existing=defaults.string(forKey:receiptKey){receipt=existing}else{receipt=randomBytes(16).map{String(format:"%02x",$0)}.joined();defaults.set(receipt,forKey:receiptKey)}
        let version=Bundle.main.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? ""
        let build=Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? ""
        let os=UIDevice.current.systemVersion; let major=Int(os.split(separator:".").first ?? "0") ?? 0
        let region=Locale.current.regionCode ?? "ZZ"
        let age=max(0,c.dateComponents([.day],from:c.startOfDay(for:firstDate),to:c.startOfDay(for:now)).day ?? 0)
        var payload:[String:Any]=["schema":1,"appVersion":version,"build":build,"iosVersion":os,"iosMajor":major,"deviceRegion":region,"installAgeDays":age,"dayId":dayId,"weekId":weekId,"monthId":monthId]
        if !defaults.bool(forKey:installReportedKey){payload["installReceiptId"]=receipt}
        guard let body=try? JSONSerialization.data(withJSONObject:payload) else{return}
        var request=URLRequest(url:endpoint);request.httpMethod="POST";request.httpBody=body;request.timeoutInterval=8.0;request.setValue("application/json",forHTTPHeaderField:"Content-Type")
        guard JerkgramTelemetryPreferences.isEnabled else{return}
        let task=URLSession.shared.dataTask(with:request){[weak self] _,response,_ in guard let self else{return};self.queue.async{defer{self.activeTask=nil};guard JerkgramTelemetryPreferences.isEnabled,let http=response as? HTTPURLResponse,(200..<300).contains(http.statusCode) else{return};defaults.set(Date(),forKey:self.lastSuccessKey);if !defaults.bool(forKey:self.installReportedKey){defaults.set(true,forKey:self.installReportedKey);defaults.removeObject(forKey:self.receiptKey)}}}
        activeTask=task;task.resume()
    }
    private func localSecret(defaults:UserDefaults)->[UInt8]{if let data=defaults.data(forKey:secretKey),data.count==32{return Array(data)};let bytes=randomBytes(32);defaults.set(Data(bytes),forKey:secretKey);return bytes}
    private func randomBytes(_ count:Int)->[UInt8]{var generator=SystemRandomNumberGenerator();return(0..<count).map{_ in UInt8.random(in:UInt8.min...UInt8.max,using:&generator)}}
    private func hmac(_ key:[UInt8],_ value:String)->String{let block=64;var k=key;if k.count>block{k=sha256(k)};if k.count<block{k += [UInt8](repeating:0,count:block-k.count)};let inner=sha256(zip(k,[UInt8](repeating:0x36,count:block)).map{$0.0 ^ $0.1}+Array(value.utf8));let out=sha256(zip(k,[UInt8](repeating:0x5c,count:block)).map{$0.0 ^ $0.1}+inner);return out.map{String(format:"%02x",$0)}.joined()}
    private func sha256(_ input:[UInt8])->[UInt8]{let constants:[UInt32]=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];var m=input;let bits=UInt64(m.count)*8;m.append(0x80);while m.count%64 != 56{m.append(0)};for s in stride(from:56,through:0,by:-8){m.append(UInt8((bits>>UInt64(s))&0xff))};var h:[UInt32]=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];for off in stride(from:0,to:m.count,by:64){var w=[UInt32](repeating:0,count:64);for i in 0..<16{let j=off+i*4;w[i]=UInt32(m[j])<<24|UInt32(m[j+1])<<16|UInt32(m[j+2])<<8|UInt32(m[j+3])};for i in 16..<64{let a=w[i-15],b=w[i-2];let s0=(a>>7|a<<25)^(a>>18|a<<14)^(a>>3);let s1=(b>>17|b<<15)^(b>>19|b<<13)^(b>>10);w[i]=w[i-16]&+s0&+w[i-7]&+s1};var a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],x=h[7];for i in 0..<64{let s1=(e>>6|e<<26)^(e>>11|e<<21)^(e>>25|e<<7);let ch=(e&f)^((~e)&g);let t1=x&+s1&+ch&+constants[i]&+w[i];let s0=(a>>2|a<<30)^(a>>13|a<<19)^(a>>22|a<<10);let maj=(a&b)^(a&c)^(b&c);let t2=s0&+maj;x=g;g=f;f=e;e=d&+t1;d=c;c=b;b=a;a=t1&+t2};for i in 0..<8{h[i]=h[i]&+[a,b,c,d,e,f,g,x][i]}};return h.flatMap{v in[UInt8(v>>24),UInt8((v>>16)&255),UInt8((v>>8)&255),UInt8(v&255)]}}
}
'''
def patch_app(t):
    if 'BUILD130_TELEMETRY1' in t:return t
    owner='@objc(AppDelegate) class AppDelegate';i=t.find(owner);req(i>=0,'AppDelegate owner missing');t=t[:i]+TELEMETRY+'\n'+t[i:]
    sig='func applicationDidBecomeActive(_ application: UIApplication)';s=t.find(sig);req(s>=0,'applicationDidBecomeActive lifecycle owner missing');b=t.find('{',s);req(b>=0,'active lifecycle brace missing')
    return t[:b+1]+'\n        JerkgramTelemetry.shared.applicationDidBecomeActive()'+t[b+1:]
def main():
    for p in (SETTINGS,STRINGS,APP,PROFILE):req(p.is_file(),'missing '+str(p))
    profile=PROFILE.read_text();req('BUILD128_PROFILE_BIO_CORNER_OWNER1' in profile,'Build128 triangle owner did not survive materialization')
    SETTINGS.write_text(patch_settings(SETTINGS.read_text()),encoding='utf-8');STRINGS.write_text(patch_strings(STRINGS.read_text()),encoding='utf-8');APP.write_text(patch_app(APP.read_text()),encoding='utf-8')
    print('[Build130 release] UI + telemetry applied')
if __name__=='__main__':main()
