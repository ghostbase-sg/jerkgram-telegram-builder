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

    // Telemetry reports the product release, not the beta suffix or Telegram base version.
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


def matching_delimiter(text: str, open_index: int, opening: str, closing: str) -> int:
    depth = 0
    i = open_index
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == '"':
                state = "string"
            elif ch == "/" and nxt == "/":
                state = "line"
                i += 1
            elif ch == "/" and nxt == "*":
                state = "block"
                i += 1
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return i
        elif state == "string":
            if ch == "\\":
                i += 1
            elif ch == '"':
                state = "code"
        elif state == "line":
            if ch == "\n":
                state = "code"
        elif state == "block" and ch == "*" and nxt == "/":
            state = "code"
            i += 1
        i += 1
    fail(f"unterminated Swift delimiter {opening}{closing}")


def matching_brace(text: str, open_index: int) -> int:
    return matching_delimiter(text, open_index, "{", "}")


def locate_telemetry(text: str) -> tuple[int, int]:
    matches = list(re.finditer(
        r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b",
        text,
    ))
    if len(matches) != 1:
        fail(f"expected exactly one JerkgramTelemetry declaration in {APP_OWNER}, found {len(matches)}")
    match = matches[0]
    opening = text.find("{", match.end())
    if opening < 0:
        fail("JerkgramTelemetry opening brace missing")
    return match.start(), matching_brace(text, opening) + 1


def ensure_import(text: str, module: str) -> str:
    if re.search(rf"(?m)^import {re.escape(module)}\s*$", text):
        return text
    anchor = re.search(r"(?m)^import [A-Za-z_][A-Za-z0-9_.]*\s*$", text)
    if not anchor:
        fail(f"top-level Swift import anchor missing while adding {module}")
    if anchor.start() > 2048:
        fail(f"first Swift import is outside bounded header while adding {module}")
    return text[:anchor.end()] + f"\nimport {module}" + text[anchor.end():]


def prepare_identity(root: Path, app: str, settings: str) -> tuple[str, str, Path, Path]:
    local = root / LOCAL_IDENTITY_OWNER
    if local.is_file() and IDENTITY_MARKER not in local.read_text(encoding="utf-8"):
        fail(f"refusing to remove non-Build132 identity owner: {LOCAL_IDENTITY_OWNER}")

    shared = root / SHARED_IDENTITY_OWNER
    if not shared.parent.is_dir():
        fail(f"shared identity parent missing: {SHARED_IDENTITY_OWNER.parent}")
    if shared.is_file() and IDENTITY_MARKER not in shared.read_text(encoding="utf-8"):
        fail(f"refusing to overwrite non-Build132 shared identity: {SHARED_IDENTITY_OWNER}")

    return ensure_import(app, "TelegramCore"), ensure_import(settings, "TelegramCore"), local, shared


def require_legacy_contract(block: str) -> None:
    required = (
        ENDPOINT,
        "schema",
        "installReceiptId",
        "dayId",
        "weekId",
        "monthId",
        "localSecret",
        "HMAC<SHA256>",
    )
    missing = [token for token in required if token not in block]
    if missing:
        fail(
            "refusing to synthesize/replace the legacy telemetry identity contract; "
            f"materialized JerkgramTelemetry is missing {missing}"
        )


def local_secret_shape(block: str) -> str:
    match = re.search(
        r"(?m)(?:private\s+)?static\s+func\s+localSecret\s*\([^)]*\)\s*->\s*(Data|SymmetricKey)(\?)?\s*\{",
        block,
    )
    if not match:
        fail("existing localSecret() must return Data/Data? or SymmetricKey/SymmetricKey? for bounded v2.1 HMAC reuse")
    return match.group(1) + (match.group(2) or "")


def analytics_helpers(secret_shape: str) -> str:
    if secret_shape == "Data":
        secret_lines = """        let secret = localSecret()\n        let key = SymmetricKey(data: secret)"""
    elif secret_shape == "Data?":
        secret_lines = """        guard let secret = localSecret() else { return nil }\n        let key = SymmetricKey(data: secret)"""
    elif secret_shape == "SymmetricKey":
        secret_lines = "        let key = localSecret()"
    elif secret_shape == "SymmetricKey?":
        secret_lines = "        guard let key = localSecret() else { return nil }"
    else:
        fail(f"unsupported localSecret() shape: {secret_shape}")

    return f'''
    {ADDENDUM_MARKER}
    private static let analyticsTimeZone = TimeZone(identifier: "Europe/Moscow")!
    private static let opensDayKey = "jerkgram.telemetry.opens.day"
    private static let opensCountKey = "jerkgram.telemetry.opens.count"
    private static let maximumOpenCount = 100000
    private static var hasSeenActive = false
    private static var enteredBackground = false

    private struct AnalyticsDayState {{
        let day: String
        let dayId: String
        let openCountToday: Int
    }}

    private static func analyticsDayString(for date: Date = Date()) -> String {{
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = analyticsTimeZone
        let components = calendar.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", components.year ?? 0, components.month ?? 0, components.day ?? 0)
    }}

    private static func analyticsDayId(for day: String) -> String? {{
{secret_lines}
        let input = Data(("jerkgram-msk-day-v1:" + day).utf8)
        let digest = HMAC<SHA256>.authenticationCode(for: input, using: key)
        return digest.map {{ String(format: "%02x", $0) }}.joined()
    }}

    @discardableResult
    private static func incrementOpenCountForCurrentAnalyticsDay() -> AnalyticsDayState? {{
        let defaults = UserDefaults.standard
        let day = analyticsDayString()
        let storedDay = defaults.string(forKey: opensDayKey)
        let oldCount = storedDay == day ? defaults.integer(forKey: opensCountKey) : 0
        let boundedOldCount = min(max(oldCount, 0), maximumOpenCount)
        let count = min(maximumOpenCount, boundedOldCount + 1)
        guard let dayId = analyticsDayId(for: day) else {{ return nil }}
        defaults.set(day, forKey: opensDayKey)
        defaults.set(count, forKey: opensCountKey)
        return AnalyticsDayState(day: day, dayId: dayId, openCountToday: count)
    }}

    private static func currentAnalyticsDayState() -> AnalyticsDayState? {{
        let defaults = UserDefaults.standard
        let day = analyticsDayString()
        guard defaults.string(forKey: opensDayKey) == day else {{ return nil }}
        let count = min(max(defaults.integer(forKey: opensCountKey), 1), maximumOpenCount)
        guard let dayId = analyticsDayId(for: day) else {{ return nil }}
        return AnalyticsDayState(day: day, dayId: dayId, openCountToday: count)
    }}

    static func didEnterBackground() {{
        enteredBackground = true
        guard isEnabled else {{ return }}
        record(event: "app_background")
    }}

    static func didBecomeActive() {{
        guard !hasSeenActive || enteredBackground else {{ return }}
        hasSeenActive = true
        enteredBackground = false
        guard isEnabled else {{ return }}
        _ = incrementOpenCountForCurrentAnalyticsDay()
        track(event: "app_active")
    }}
'''


def replace_app_version(block: str) -> str:
    pattern = re.compile(r'(?m)^(?P<indent>[ \t]*)"appVersion"\s*:\s*[^,\n]+,')
    matches = list(pattern.finditer(block))
    if len(matches) != 1:
        fail(f"expected exactly one appVersion payload field, found {len(matches)}")
    return pattern.sub(
        lambda m: f'{m.group("indent")}"appVersion": JerkgramReleaseIdentity.releaseVersion,',
        block,
        count=1,
    )


def inject_analytics_payload(block: str) -> str:
    if all(f'payload["{key}"]' in block for key in ("analyticsDay", "analyticsDayId", "openCountToday")):
        return block

    matches = list(re.finditer(r"\bvar\s+payload\s*:\s*\[String\s*:\s*Any\]\s*=\s*\[", block))
    if len(matches) != 1:
        fail(f"expected exactly one mutable telemetry payload dictionary, found {len(matches)}")
    opening = block.find("[", matches[0].end() - 1)
    closing = matching_delimiter(block, opening, "[", "]")
    injection = '''
        if let analytics = currentAnalyticsDayState() {
            payload["analyticsDay"] = analytics.day
            payload["analyticsDayId"] = analytics.dayId
            payload["openCountToday"] = analytics.openCountToday
        }
'''
    return block[:closing + 1] + injection + block[closing + 1:]


def neutralize_startup_open_send(block: str) -> str:
    match = re.search(r"(?m)^[ \t]*static\s+func\s+start\s*\([^)]*\)\s*\{", block)
    if not match:
        fail("JerkgramTelemetry.start() missing")
    opening = block.find("{", match.start(), match.end())
    closing = matching_brace(block, opening)
    method = block[match.start():closing + 1]
    method = re.sub(
        r'(?m)^[ \t]*(?:send|track|record)\(\s*event:\s*"app_launch"[^\n]*\)\s*\n?',
        "",
        method,
    )
    return block[:match.start()] + method + block[closing + 1:]


def patch_telemetry_block(block: str) -> str:
    if ADDENDUM_MARKER in block:
        if block.count(ADDENDUM_MARKER) != 1:
            fail("v2.1 marker duplicated")
        return block

    require_legacy_contract(block)
    secret_shape = local_secret_shape(block)
    block = replace_app_version(block)
    block = inject_analytics_payload(block)
    block = neutralize_startup_open_send(block)

    closing = block.rfind("}")
    if closing < 0:
        fail("telemetry closing brace missing")
    helpers = analytics_helpers(secret_shape)
    block = block[:closing] + helpers + block[closing:]
    if APP_MARKER not in block:
        block = APP_MARKER + "\n" + block
    return block


def replace_outside_telemetry(app: str, patterns: tuple[str, ...], replacement: str, label: str) -> str:
    start, end = locate_telemetry(app)
    prefix = app[:start]
    block = app[start:end]
    suffix = app[end:]
    if replacement in prefix or replacement in suffix:
        return app

    count = 0
    for pattern in patterns:
        prefix, prefix_count = re.subn(pattern, replacement, prefix, count=1)
        suffix, suffix_count = re.subn(pattern, replacement, suffix, count=1)
        count += prefix_count + suffix_count
    if count != 1:
        fail(f"expected exactly one existing {label} lifecycle call outside JerkgramTelemetry, replaced {count}")
    return prefix + block + suffix


def patch_lifecycle_calls(app: str) -> str:
    app = replace_outside_telemetry(
        app,
        (
            r'JerkgramTelemetry\.track\(\s*event:\s*"app_active"\s*\)',
            r'JerkgramTelemetry\.record\(\s*event:\s*"app_active"\s*\)',
        ),
        "JerkgramTelemetry.didBecomeActive()",
        "app_active",
    )
    app = replace_outside_telemetry(
        app,
        (
            r'JerkgramTelemetry\.record\(\s*event:\s*"app_background"\s*\)',
            r'JerkgramTelemetry\.track\(\s*event:\s*"app_background"\s*\)',
        ),
        "JerkgramTelemetry.didEnterBackground()",
        "app_background",
    )

    start, end = locate_telemetry(app)
    prefix = app[:start]
    block = app[start:end]
    suffix = app[end:]
    external_launch = re.compile(
        r'(?m)^[ \t]*JerkgramTelemetry\.(?:send|track|record)\(\s*event:\s*"app_launch"[^\n]*\)\s*\n?'
    )
    prefix, prefix_count = external_launch.subn("", prefix)
    suffix, suffix_count = external_launch.subn("", suffix)
    if prefix_count + suffix_count > 1:
        fail(f"unexpected external app_launch call count: {prefix_count + suffix_count}")
    return prefix + block + suffix


def patch_privacy_strings(text: str) -> str:
    if text.count(PRIVACY_MARKER) == 1 and EN_PRIVACY in text and RU_PRIVACY in text:
        return text
    if PRIVACY_MARKER in text:
        fail("privacy marker exists without canonical v2.1 RU/EN text")

    matches = list(re.finditer(
        r"(?m)^(?P<indent>[ \t]*)var anonymousAnalyticsDescription: String \{",
        text,
    ))
    if len(matches) != 1:
        fail(f"expected exactly one semantic anonymousAnalyticsDescription owner, found {len(matches)}")

    match = matches[0]
    opening = text.find("{", match.start(), match.end())
    closing = matching_brace(text, opening)
    indent = match.group("indent")
    body_indent = indent + "    "
    canonical = (
        f"{indent}{PRIVACY_MARKER}\n"
        f"{indent}var anonymousAnalyticsDescription: String {{\n"
        f"{body_indent}if self.languageCode == \"ru\" {{\n"
        f"{body_indent}    return \"{RU_PRIVACY}\"\n"
        f"{body_indent}}} else {{\n"
        f"{body_indent}    return \"{EN_PRIVACY}\"\n"
        f"{body_indent}}}\n"
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
    app = ensure_import(app, "Darwin")

    start, end = locate_telemetry(app)
    old_block = app[start:end]
    new_block = patch_telemetry_block(old_block)
    app = app[:start] + new_block + app[end:]
    app = patch_lifecycle_calls(app)

    if ".info(3, strings.anonymousAnalyticsDescription)" not in settings:
        fail("Settings no longer renders semantic anonymousAnalyticsDescription")
    strings = patch_privacy_strings(strings)

    changed_identity = write_if_changed(shared_identity, IDENTITY_SOURCE)
    changed_app = write_if_changed(app_path, app)
    changed_settings = write_if_changed(settings_path, settings)
    changed_strings = write_if_changed(strings_path, strings)
    if local_identity.is_file():
        local_identity.unlink()

    print(
        f"[Build132 telemetry v2.1] AppDelegate={'updated' if changed_app else 'unchanged'}, "
        f"Settings={'updated' if changed_settings else 'unchanged'}, "
        f"Strings={'updated' if changed_strings else 'unchanged'}, "
        f"shared identity={'updated' if changed_identity else 'unchanged'}"
    )


if __name__ == "__main__":
    main()
