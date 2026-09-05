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
APP_MARKER = "// BUILD132_TELEMETRY_V2"
ADDENDUM_MARKER = "// BUILD132_TELEMETRY_V2_1"
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"
IDENTITY_MARKER = "// BUILD132_RELEASE_IDENTITY1"

IDENTITY_SOURCE = f'''{IDENTITY_MARKER}
public enum JerkgramReleaseIdentity {{
    public static let version = "1.0.2-beta.1"
    public static let displayVersion = "1.0.2 Beta 1"
    public static let build = "132"
    public static let telegramBase = "12.9.2"

    // Telemetry uses the product release without the beta suffix.
    public static var releaseVersion: String {{
        return self.version.split(separator: "-").first.map(String.init) ?? self.version
    }}
}}
'''

EN_PRIVACY = (
    "Help improve Jerkgram by sharing anonymous usage statistics such as Jerkgram version, "
    "iOS version, device model and region, and the number of app opens. Telegram accounts, "
    "messages, usernames and phone numbers are never collected."
)
RU_PRIVACY = (
    "Помогайте улучшать Jerkgram, отправляя анонимную статистику использования: версию "
    "Jerkgram, версию iOS, модель и регион устройства, а также количество открытий приложения. "
    "Аккаунты Telegram, сообщения, имена пользователей и номера телефонов никогда не собираются."
)


def fail(message: str) -> "NoReturn":
    raise RuntimeError(f"[Build132 telemetry v2.1] {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing owner: {path}")
    return path.read_text(encoding="utf-8")


def write_if_changed(path: Path, text: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    state = "code"
    i = opening
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == '"':
                state = "string"
            elif ch == "/" and nxt == "/":
                state = "line"; i += 1
            elif ch == "/" and nxt == "*":
                state = "block"; i += 1
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        elif state == "string":
            if ch == "\\":
                i += 1
            elif ch == '"':
                state = "code"
        elif state == "line":
            if ch == "\n": state = "code"
        elif state == "block" and ch == "*" and nxt == "/":
            state = "code"; i += 1
        i += 1
    fail("unterminated Swift block")


def locate_telemetry(text: str) -> tuple[int, int]:
    matches = list(re.finditer(r"(?m)^[ \t]*private\s+final\s+class\s+JerkgramTelemetry\s*\{", text))
    if len(matches) != 1:
        fail(f"expected one legacy JerkgramTelemetry singleton, found {len(matches)}")
    opening = text.find("{", matches[0].start(), matches[0].end())
    return matches[0].start(), matching_brace(text, opening) + 1


def ensure_import(text: str, module: str) -> str:
    if re.search(rf"(?m)^import {re.escape(module)}\s*$", text):
        return text
    match = re.search(r"(?m)^import [A-Za-z_][A-Za-z0-9_.]*\s*$", text)
    if not match or match.start() > 2048:
        fail(f"bounded Swift import anchor missing for {module}")
    return text[:match.end()] + f"\nimport {module}" + text[match.end():]


def prepare_identity(root: Path, app: str, settings: str) -> tuple[str, str, Path, Path]:
    local = root / LOCAL_IDENTITY_OWNER
    if local.is_file() and IDENTITY_MARKER not in read(local):
        fail(f"refusing to remove non-Build132 identity: {LOCAL_IDENTITY_OWNER}")
    shared = root / SHARED_IDENTITY_OWNER
    if not shared.parent.is_dir():
        fail(f"shared identity parent missing: {SHARED_IDENTITY_OWNER.parent}")
    if shared.is_file() and IDENTITY_MARKER not in read(shared):
        fail(f"refusing to overwrite non-Build132 identity: {SHARED_IDENTITY_OWNER}")
    app = ensure_import(ensure_import(app, "TelegramCore"), "Darwin")
    settings = ensure_import(settings, "TelegramCore")
    return app, settings, local, shared


def require_legacy_contract(block: str) -> None:
    required = (
        f'URL(string: "{ENDPOINT}")!',
        'static let shared = JerkgramTelemetry()',
        'private let queue = DispatchQueue(label: "org.jerkgram.telemetry", qos: .utility)',
        'private let secretKey = "jerkgram.telemetry.secret.v1"',
        'private let firstDateKey = "jerkgram.telemetry.firstDate.v1"',
        'private let receiptKey = "jerkgram.telemetry.installReceipt.v1"',
        'private let installReportedKey = "jerkgram.telemetry.installReported.v1"',
        'private let lastSuccessKey = "jerkgram.telemetry.lastSuccess.v1"',
        'private let minimumInterval: TimeInterval = 4 * 60 * 60',
        'let dayId=hmac(secret,', 'let weekId=hmac(secret,', 'let monthId=hmac(secret,',
        'payload["installReceiptId"]=receipt',
        'private func localSecret(defaults:UserDefaults)->[UInt8]',
        'private func hmac(_ key:[UInt8],_ value:String)->String',
        'private func sha256(_ input:[UInt8])->[UInt8]',
        'request.timeoutInterval=8.0',
    )
    missing = [token for token in required if token not in block]
    if missing:
        fail(f"legacy telemetry contract drifted; missing {missing}")


def one_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"expected one {label} anchor, found {count}")
    return text.replace(old, new, 1)


def patch_telemetry_block(block: str) -> str:
    if ADDENDUM_MARKER in block:
        if block.count(ADDENDUM_MARKER) != 1 or APP_MARKER not in block:
            fail("partial/duplicated telemetry v2.1 marker")
        return block

    require_legacy_contract(block)

    fields_anchor = '    private let minimumInterval: TimeInterval = 4 * 60 * 60\n'
    fields = fields_anchor + f'''    {APP_MARKER}\n    {ADDENDUM_MARKER}\n    private let lastAttemptAtKey = "jerkgram.telemetry.lastAttempt.v2"\n    private let analyticsTimeZone = TimeZone(identifier: "Europe/Moscow")!\n    private let opensDayKey = "jerkgram.telemetry.opens.day"\n    private let opensCountKey = "jerkgram.telemetry.opens.count"\n    private let maximumOpenCount = 100000\n    private var hasSeenActive = false\n    private var enteredBackground = false\n'''
    block = one_replace(block, fields_anchor, fields, "telemetry v2.1 fields")

    old_active = '    func applicationDidBecomeActive() { queue.async { [weak self] in self?.submitIfNeeded() } }\n'
    new_active = '''    func applicationDidBecomeActive() {\n        let shouldCountOpen = !self.hasSeenActive || self.enteredBackground\n        self.hasSeenActive = true\n        self.enteredBackground = false\n        guard JerkgramTelemetryPreferences.isEnabled else { return }\n        guard shouldCountOpen else { return }\n        queue.async { [weak self] in\n            guard let self else { return }\n            guard JerkgramTelemetryPreferences.isEnabled else { return }\n            self.incrementOpenCountForCurrentAnalyticsDay()\n            self.submitIfNeeded()\n        }\n    }\n    func applicationDidEnterBackground() {\n        self.enteredBackground = true\n    }\n'''
    block = one_replace(block, old_active, new_active, "legacy foreground scheduler")

    old_interval = '        if let last = defaults.object(forKey: lastSuccessKey) as? Date, now.timeIntervalSince(last) < minimumInterval { return }\n'
    new_interval = '        if let last = defaults.object(forKey: lastAttemptAtKey) as? Date, now.timeIntervalSince(last) < minimumInterval { return }\n'
    block = one_replace(block, old_interval, new_interval, "rate-limit timestamp")

    old_version = '        let version=Bundle.main.object(forInfoDictionaryKey:"CFBundleShortVersionString") as? String ?? ""\n        let build=Bundle.main.object(forInfoDictionaryKey:"CFBundleVersion") as? String ?? ""\n'
    new_version = '        let version=JerkgramReleaseIdentity.releaseVersion\n        let build=JerkgramReleaseIdentity.build\n'
    block = one_replace(block, old_version, new_version, "Jerkgram release identity")

    old_payload = '        var payload:[String:Any]=["schema":1,"appVersion":version,"build":build,"iosVersion":os,"iosMajor":major,"deviceRegion":region,"installAgeDays":age,"dayId":dayId,"weekId":weekId,"monthId":monthId]\n'
    new_payload = '''        let model=hardwareModel()\n        var payload:[String:Any]=["schema":1,"appVersion":version,"build":build,"iosVersion":os,"iosMajor":major,"deviceRegion":region,"deviceModel":model,"installAgeDays":age,"dayId":dayId,"weekId":weekId,"monthId":monthId,"event":"app_active","ts":Int(now.timeIntervalSince1970)]\n        if let analytics=currentAnalyticsDayState(defaults:defaults,secret:secret){\n            payload["analyticsDay"]=analytics.day\n            payload["analyticsDayId"]=analytics.dayId\n            payload["openCountToday"]=analytics.openCountToday\n        }\n'''
    block = one_replace(block, old_payload, new_payload, "legacy payload")

    task_anchor = '        guard JerkgramTelemetryPreferences.isEnabled else{return}\n        let task=URLSession.shared.dataTask(with:request)'
    task_replacement = '        guard JerkgramTelemetryPreferences.isEnabled else{return}\n        defaults.set(now,forKey:lastAttemptAtKey)\n        let task=URLSession.shared.dataTask(with:request)'
    block = one_replace(block, task_anchor, task_replacement, "pre-network OFF gate")

    helper_anchor = '    private func localSecret(defaults:UserDefaults)->[UInt8]'
    helpers = '''    private struct AnalyticsDayState {\n        let day: String\n        let dayId: String\n        let openCountToday: Int\n    }\n    private func analyticsDayString(for date:Date=Date())->String{\n        var calendar=Calendar(identifier:.gregorian)\n        calendar.timeZone=analyticsTimeZone\n        let components=calendar.dateComponents([.year,.month,.day],from:date)\n        return String(format:"%04d-%02d-%02d",components.year ?? 0,components.month ?? 0,components.day ?? 0)\n    }\n    private func analyticsDayId(for day:String,secret:[UInt8])->String{\n        return hmac(secret,"jerkgram-msk-day-v1:"+day)\n    }\n    private func incrementOpenCountForCurrentAnalyticsDay(){\n        let defaults=UserDefaults.standard\n        let day=analyticsDayString()\n        let storedDay=defaults.string(forKey:opensDayKey)\n        let oldCount=storedDay == day ? defaults.integer(forKey:opensCountKey) : 0\n        let boundedOldCount=min(max(oldCount,0),maximumOpenCount)\n        let count=min(maximumOpenCount,boundedOldCount+1)\n        let secret=localSecret(defaults:defaults)\n        _=analyticsDayId(for:day,secret:secret)\n        defaults.set(day,forKey:opensDayKey)\n        defaults.set(count,forKey:opensCountKey)\n    }\n    private func currentAnalyticsDayState(defaults:UserDefaults,secret:[UInt8])->AnalyticsDayState?{\n        let day=analyticsDayString()\n        guard defaults.string(forKey:opensDayKey) == day else{return nil}\n        let count=min(max(defaults.integer(forKey:opensCountKey),1),maximumOpenCount)\n        return AnalyticsDayState(day:day,dayId:analyticsDayId(for:day,secret:secret),openCountToday:count)\n    }\n    private func hardwareModel()->String{\n        var info=utsname()\n        guard uname(&info) == 0 else{return "unknown"}\n        let capacity=MemoryLayout.size(ofValue:info.machine)\n        return withUnsafePointer(to:&info.machine){ pointer in\n            pointer.withMemoryRebound(to:CChar.self,capacity:capacity){ String(cString:$0) }\n        }\n    }\n'''
    block = one_replace(block, helper_anchor, helpers + helper_anchor, "legacy secret helper")
    return block


def patch_app_lifecycle(app: str) -> str:
    start, end = locate_telemetry(app)
    prefix, block, suffix = app[:start], app[start:end], app[end:]
    if 'JerkgramTelemetry.shared.applicationDidBecomeActive()' not in suffix:
        fail("AppDelegate foreground owner no longer calls telemetry singleton")
    if suffix.count('JerkgramTelemetry.shared.applicationDidBecomeActive()') != 1:
        fail("foreground telemetry call duplicated")

    background_signature = '    func applicationDidEnterBackground(_ application: UIApplication) {\n'
    if background_signature not in suffix:
        fail("AppDelegate background lifecycle owner missing")
    background_call = '        JerkgramTelemetry.shared.applicationDidEnterBackground()\n'
    if background_call not in suffix:
        suffix = suffix.replace(background_signature, background_signature + background_call, 1)
    elif suffix.count(background_call) != 1:
        fail("background telemetry call duplicated")

    if 'JerkgramTelemetry.didBecomeActive()' in suffix or 'JerkgramTelemetry.didEnterBackground()' in suffix:
        fail("static telemetry lifecycle API must not coexist with legacy singleton")
    return prefix + block + suffix


def patch_privacy_strings(text: str) -> str:
    if text.count(PRIVACY_MARKER) == 1 and EN_PRIVACY in text and RU_PRIVACY in text:
        return text
    if PRIVACY_MARKER in text:
        fail("privacy marker exists without canonical v2.1 text")
    matches = list(re.finditer(r"(?m)^(?P<indent>[ \t]*)var anonymousAnalyticsDescription: String \{", text))
    if len(matches) != 1:
        fail(f"expected one anonymousAnalyticsDescription owner, found {len(matches)}")
    match = matches[0]
    opening = text.find("{", match.start(), match.end())
    closing = matching_brace(text, opening)
    indent = match.group("indent")
    b = indent + "    "
    canonical = (
        f"{indent}{PRIVACY_MARKER}\n"
        f"{indent}var anonymousAnalyticsDescription: String {{\n"
        f"{b}if self.languageCode == \"ru\" {{\n"
        f"{b}    return \"{RU_PRIVACY}\"\n"
        f"{b}}} else {{\n"
        f"{b}    return \"{EN_PRIVACY}\"\n"
        f"{b}}}\n"
        f"{indent}}}"
    )
    return text[:match.start()] + canonical + text[closing + 1:]


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: apply_build132_telemetry_v2.py <materialized-source-root>")
    root = Path(sys.argv[1]).resolve()
    app_path = root / APP_OWNER
    settings_path = root / SETTINGS_OWNER
    strings_path = root / STRINGS_OWNER
    app = read(app_path)
    settings = read(settings_path)
    strings = read(strings_path)
    app, settings, local_identity, shared_identity = prepare_identity(root, app, settings)

    start, end = locate_telemetry(app)
    new_block = patch_telemetry_block(app[start:end])
    app = app[:start] + new_block + app[end:]
    app = patch_app_lifecycle(app)

    if '.info(3, strings.anonymousAnalyticsDescription)' not in settings:
        fail("Settings no longer renders semantic anonymousAnalyticsDescription")
    strings = patch_privacy_strings(strings)

    changed_identity = write_if_changed(shared_identity, IDENTITY_SOURCE)
    changed_app = write_if_changed(app_path, app)
    changed_settings = write_if_changed(settings_path, settings)
    changed_strings = write_if_changed(strings_path, strings)
    if local_identity.is_file():
        local_identity.unlink()
    print(f"[Build132 telemetry v2.1] AppDelegate={'updated' if changed_app else 'unchanged'}, Settings={'updated' if changed_settings else 'unchanged'}, Strings={'updated' if changed_strings else 'unchanged'}, shared identity={'updated' if changed_identity else 'unchanged'}")


if __name__ == "__main__":
    main()
