#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ENDPOINT = "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity"
APP_OWNER = Path("submodules/TelegramUI/Sources/AppDelegate.swift")
SETTINGS_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
STRINGS_OWNER = Path("submodules/TelegramPresentationData/Sources/JerkgramStrings.swift")
LOCAL_IDENTITY_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/JerkgramReleaseIdentity.swift")
SHARED_IDENTITY_OWNER = Path("submodules/TelegramCore/Sources/JerkgramReleaseIdentity.swift")
PATCHER = Path(__file__).resolve().parent / "apply_build132_telemetry_v2.py"
APP_MARKER = "// BUILD132_TELEMETRY_V2"
ADDENDUM_MARKER = "// BUILD132_TELEMETRY_V2_1"
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"
EN_PRIVACY = "Help improve Jerkgram by sharing anonymous usage statistics such as Jerkgram version, iOS version, device model and region, and the number of app opens. Telegram accounts, messages, usernames and phone numbers are never collected."
RU_PRIVACY = "Помогайте улучшать Jerkgram, отправляя анонимную статистику использования: версию Jerkgram, версию iOS, модель и регион устройства, а также количество открытий приложения. Аккаунты Telegram, сообщения, имена пользователей и номера телефонов никогда не собираются."


def fail(message: str) -> "NoReturn":
    raise RuntimeError(f"[Build132 telemetry verify] {message}")


def read(path: Path) -> str:
    if not path.is_file(): fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def matching_brace(text: str, opening: int) -> int:
    depth=0; state="code"; i=opening
    while i < len(text):
        ch=text[i]; nxt=text[i+1] if i+1<len(text) else ""
        if state=="code":
            if ch=='"': state="string"
            elif ch=="/" and nxt=="/": state="line"; i+=1
            elif ch=="/" and nxt=="*": state="block"; i+=1
            elif ch=="{": depth+=1
            elif ch=="}":
                depth-=1
                if depth==0: return i
        elif state=="string":
            if ch=="\\": i+=1
            elif ch=='"': state="code"
        elif state=="line" and ch=="\n": state="code"
        elif state=="block" and ch=="*" and nxt=="/": state="code"; i+=1
        i+=1
    fail("unterminated Swift block")


def telemetry_block(app: str) -> str:
    matches=list(re.finditer(r"(?m)^[ \t]*private\s+final\s+class\s+JerkgramTelemetry\s*\{",app))
    if len(matches)!=1: fail(f"expected one JerkgramTelemetry singleton, found {len(matches)}")
    opening=app.find("{",matches[0].start(),matches[0].end())
    return app[matches[0].start():matching_brace(app,opening)+1]


def method_body(block: str, signature: str) -> str:
    idx=block.find(signature)
    if idx<0: fail(f"missing method: {signature}")
    opening=block.find("{",idx+len(signature))
    if opening<0: fail(f"method opening brace missing: {signature}")
    return block[opening+1:matching_brace(block,opening)]


def main() -> None:
    if len(sys.argv)!=2: fail("usage: verify_build132_telemetry_v2.py <materialized-source-root>")
    root=Path(sys.argv[1]).resolve()
    app=read(root/APP_OWNER); settings=read(root/SETTINGS_OWNER); strings=read(root/STRINGS_OWNER)
    identity=read(root/SHARED_IDENTITY_OWNER); patcher=read(PATCHER)
    if (root/LOCAL_IDENTITY_OWNER).exists(): fail("SettingsUI-local release identity survived STEP2")

    for token in ('public enum JerkgramReleaseIdentity','public static let version = "1.0.2-beta.1"','public static let displayVersion = "1.0.2 Beta 1"','public static let build = "132"','public static let telegramBase = "12.9.2"','public static var releaseVersion: String'):
        if token not in identity: fail(f"release identity missing: {token}")
    for owner,text in ((APP_OWNER,app),(SETTINGS_OWNER,settings)):
        if "import TelegramCore" not in text: fail(f"{owner} missing TelegramCore import")
    if "import Darwin" not in app: fail("AppDelegate missing Darwin import for uname deviceModel")

    block=telemetry_block(app)
    lines=[line.strip() for line in block.splitlines()]
    if lines.count(APP_MARKER)!=1 or lines.count(ADDENDUM_MARKER)!=1: fail("telemetry v2/v2.1 markers must occur once")
    for token in (
        'static let shared = JerkgramTelemetry()', ENDPOINT, '"schema":1',
        '"appVersion":version', 'let version=JerkgramReleaseIdentity.releaseVersion',
        'let build=JerkgramReleaseIdentity.build', '"build":build',
        '"deviceModel":model', 'let model=hardwareModel()', 'uname(&info)',
        '"installAgeDays":age', '"installReceiptId"', '"dayId":dayId', '"weekId":weekId', '"monthId":monthId',
        'Calendar(identifier: .iso8601)', 'TimeZone(secondsFromGMT: 0)!',
        'private let minimumInterval: TimeInterval = 4 * 60 * 60', 'lastAttemptAtKey',
        'request.timeoutInterval=8.0',
    ):
        if token not in block: fail(f"required v2/legacy token missing: {token}")
    if block.count(ENDPOINT)!=1: fail("endpoint changed or duplicated")
    if 'CFBundleShortVersionString' in block or 'CFBundleVersion' in block: fail("Telegram/bundle version leaked into telemetry payload")

    for token in ('TimeZone(identifier: "Europe/Moscow")!','"jerkgram-msk-day-v1:"','"analyticsDay"','"analyticsDayId"','"openCountToday"','"jerkgram.telemetry.opens.day"','"jerkgram.telemetry.opens.count"','maximumOpenCount = 100000'):
        if token not in block: fail(f"v2.1 token missing: {token}")
    if 'TimeZone.current' in block: fail("analytics day must not use TimeZone.current")
    day_id_body=method_body(block,'private func analyticsDayId(for day:String,secret:[UInt8])->String')
    for token in ('hmac(secret,','"jerkgram-msk-day-v1:"+day'):
        if token not in day_id_body: fail(f"analyticsDayId does not reuse legacy secret/HMAC: {token}")
    if 'private func hmac(_ key:[UInt8],_ value:String)->String' not in block or 'private func sha256(_ input:[UInt8])->[UInt8]' not in block:
        fail("legacy HMAC-SHA256 implementation missing")

    trio=re.search(r'if let analytics=currentAnalyticsDayState\(defaults:defaults,secret:secret\)\{\s*payload\["analyticsDay"\]=analytics\.day\s*payload\["analyticsDayId"\]=analytics\.dayId\s*payload\["openCountToday"\]=analytics\.openCountToday\s*\}',block,re.DOTALL)
    if not trio: fail("Moscow analytics fields are not inserted together from one local state")

    active=method_body(block,'func applicationDidBecomeActive()')
    expected_active=(
        'let shouldCountOpen = !self.hasSeenActive || self.enteredBackground',
        'self.hasSeenActive = true','self.enteredBackground = false',
        'guard JerkgramTelemetryPreferences.isEnabled else { return }',
        'guard shouldCountOpen else { return }','queue.async',
        'self.incrementOpenCountForCurrentAnalyticsDay()','self.submitIfNeeded()'
    )
    for token in expected_active:
        if token not in active: fail(f"foreground lifecycle contract missing: {token}")
    ordered=(
        'let shouldCountOpen = !self.hasSeenActive || self.enteredBackground',
        'self.hasSeenActive = true',
        'self.enteredBackground = false',
        'guard JerkgramTelemetryPreferences.isEnabled else { return }',
        'guard shouldCountOpen else { return }',
        'queue.async',
        'self.incrementOpenCountForCurrentAnalyticsDay()',
        'self.submitIfNeeded()',
    )
    positions=[active.find(token) for token in ordered]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        fail("foreground lifecycle ordering regressed: consume lifecycle state before OFF gate, then schedule analytics")
    queue_pos=active.find('queue.async')
    second_gate=active.find('guard JerkgramTelemetryPreferences.isEnabled else { return }',queue_pos)
    if second_gate < queue_pos:
        fail("foreground analytics queue must re-check OFF before persisted counter/scheduler")
    increment_pos=active.find('self.incrementOpenCountForCurrentAnalyticsDay()',queue_pos)
    if second_gate > increment_pos:
        fail("persisted open counter can update after Analytics was disabled")
    for token in ('URL(', 'URLRequest(', 'URLSession', 'dataTask('):
        if token in active: fail(f"foreground open creates dedicated network request: {token}")

    background=method_body(block,'func applicationDidEnterBackground()')
    if 'self.enteredBackground = true' not in background:
        fail("background lifecycle must record a real background transition")
    if 'JerkgramTelemetryPreferences.isEnabled' in background:
        fail("background lifecycle bookkeeping must not depend on Analytics toggle")
    if 'queue.async' in background or 'submitIfNeeded' in background or 'URLSession' in background:
        fail("background transition must only update ephemeral lifecycle state")

    submit=method_body(block,'private func submitIfNeeded()')
    stripped=submit.lstrip()
    if not stripped.startswith('guard JerkgramTelemetryPreferences.isEnabled else { return }'):
        fail("submitIfNeeded OFF gate is not first telemetry work")
    url_pos=min([p for p in (submit.find('URLRequest('),submit.find('URLSession.shared')) if p>=0],default=-1)
    gate_pos=submit.find('guard JerkgramTelemetryPreferences.isEnabled else { return }')
    if url_pos>=0 and gate_pos>url_pos: fail("network construction occurs before OFF gate")
    if submit.find('defaults.set(now,forKey:lastAttemptAtKey)') > submit.find('URLSession.shared.dataTask'):
        fail("rate-limit attempt timestamp must be persisted before request starts")

    if app.count('JerkgramTelemetry.shared.applicationDidBecomeActive()')!=1: fail("AppDelegate must call singleton foreground lifecycle exactly once")
    if app.count('JerkgramTelemetry.shared.applicationDidEnterBackground()')!=1: fail("AppDelegate must call singleton background lifecycle exactly once")
    if 'JerkgramTelemetry.didBecomeActive()' in app or 'JerkgramTelemetry.didEnterBackground()' in app: fail("stale static telemetry lifecycle API survived")

    payload_start=block.find('var payload:[String:Any]=')
    payload_end=block.find('guard let body=try? JSONSerialization',payload_start)
    if payload_start<0 or payload_end<0: fail("payload construction window missing")
    payload=block[payload_start:payload_end]
    for token in ('secretKey','localSecret','receiptKey','authKey'):
        if token in payload: fail(f"local secret/storage key leaked into payload: {token}")
    response=block[block.find('let task=URLSession.shared.dataTask'):block.find('activeTask=task;task.resume()')]
    if 'openCountToday' in response or 'opensCountKey' in response: fail("server response mutates local open counter")

    forbidden=('identifierForVendor','ASIdentifierManager','advertisingIdentifier','IDFA','IDFV','PeerId','telegramUserId','telegramUsername','phoneNumber','authKey','serialNumber','messageText','chatText','contactsPayload')
    low=block.lower()
    for token in forbidden:
        if token.lower() in low: fail(f"forbidden identifier/data source in telemetry: {token}")
    for token in ('Timer.scheduledTimer','DispatchSource.makeTimerSource','while true','repeat {','event:"disabled"','event:"analytics_disabled"'):
        if token in block: fail(f"forbidden telemetry behavior: {token}")

    if '.info(3, strings.anonymousAnalyticsDescription)' not in settings: fail("Settings does not use semantic analytics description")
    if strings.count(PRIVACY_MARKER)!=1 or strings.count(EN_PRIVACY)!=1 or strings.count(RU_PRIVACY)!=1: fail("canonical RU/EN v2.1 privacy copy missing")
    if 'var anonymousAnalyticsDescription: String' not in strings or 'if self.languageCode == "ru"' not in strings: fail("privacy copy is not routed through JerkgramStrings language contract")

    if 'rglob(' in patcher or 'os.walk(' in patcher: fail("patcher performs broad source scan")
    for path in (APP_OWNER,SETTINGS_OWNER,STRINGS_OWNER,LOCAL_IDENTITY_OWNER,SHARED_IDENTITY_OWNER):
        if str(path) not in patcher: fail(f"patcher not bound to exact owner: {path}")

    print('[Build132 telemetry verify] PASS: legacy UTC/install contract + Jerkgram 1.0.2 identity + Moscow DAU/open counter + lifecycle-safe hard OFF + no per-open POST + semantic RU/EN privacy')

if __name__=='__main__': main()
