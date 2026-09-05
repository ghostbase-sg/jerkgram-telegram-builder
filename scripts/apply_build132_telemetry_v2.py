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
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"
IDENTITY_MARKER = "// BUILD132_RELEASE_IDENTITY1"

IDENTITY_SOURCE = f'''{IDENTITY_MARKER}
public enum JerkgramReleaseIdentity {{
    public static let version = "1.0.2-beta.1"
    public static let displayVersion = "1.0.2 Beta 1"
    public static let build = "132"
    public static let telegramBase = "12.9.2"
}}
'''

EN_PRIVACY = (
    "Sends Jerkgram version and build, iOS version, device region, hardware model "
    "(for example iPhone15,2), app lifecycle event and event time. It does not send "
    "Telegram account data, usernames, phone numbers, contacts, chats or message content. "
    "When disabled, Jerkgram makes no analytics network requests."
)
RU_PRIVACY = (
    "Отправляет версию и сборку Jerkgram, версию iOS, регион и модель устройства "
    "(например iPhone15,2), событие жизненного цикла приложения и время события. "
    "Не отправляет данные аккаунта Telegram, имя пользователя, номер телефона, контакты, "
    "чаты или содержимое сообщений. Когда аналитика выключена, Jerkgram не выполняет "
    "аналитические сетевые запросы."
)


def fail(message: str) -> "NoReturn":
    raise RuntimeError(f"[Build132 telemetry v2] {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing owner: {path}")
    return path.read_text(encoding="utf-8")


def write_if_changed(path: Path, text: str) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def matching_brace(text: str, open_index: int) -> int:
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
            if ch == "\n":
                state = "code"
        elif state == "block" and ch == "*" and nxt == "/":
            state = "code"
            i += 1
        i += 1
    fail("unterminated Swift declaration")


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


def extract_toggle_key(app: str, settings: str) -> str:
    candidates: list[str] = []
    for source in (app, settings):
        for pattern in (
            r'(?:static|private)\s+let\s+(?:enabledKey|jerkgramTelemetryEnabledKey)\s*=\s*"([^"]+)"',
            r'bool\s*\(\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
            r'object\s*\(\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
            r'set\s*\([^,\n]+,\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
        ):
            candidates += re.findall(pattern, source, flags=re.IGNORECASE)
    unique = list(dict.fromkeys(candidates))
    if len(unique) != 1:
        fail(f"expected one existing analytics UserDefaults key, found {unique}")
    return unique[0]


def canonical_telemetry(enabled_key: str) -> str:
    return f'''{APP_MARKER}
private enum JerkgramTelemetry {{
    private static let endpoint = "{ENDPOINT}"
    private static let schema = 1
    private static let enabledKey = "{enabled_key}"
    private static let minimumInterval: TimeInterval = 4.0 * 60.0 * 60.0
    private static let lastAttemptAtKey = "jerkgramAnonymousAnalyticsLastAttemptAt"

    static func start() {{
        guard isEnabled else {{ return }}
        send(event: "app_launch")
    }}

    static func send(event: String, properties: [String: Any] = [:]) {{
        // Hard OFF gate: no networking object exists before this guard.
        guard isEnabled else {{ return }}

        let now = Date()
        if let lastAttemptAt = UserDefaults.standard.object(forKey: lastAttemptAtKey) as? Date,
           now.timeIntervalSince(lastAttemptAt) < minimumInterval {{
            return
        }}
        UserDefaults.standard.set(now, forKey: lastAttemptAtKey)

        guard let url = URL(string: endpoint) else {{ return }}
        var payload: [String: Any] = [
            "schema": schema,
            "appVersion": JerkgramReleaseIdentity.version,
            "build": JerkgramReleaseIdentity.build,
            "iosVersion": UIDevice.current.systemVersion,
            "iosMajor": ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
            "deviceRegion": Locale.current.regionCode ?? "unknown",
            "deviceModel": hardwareModel(),
            "event": event,
            "ts": Int(now.timeIntervalSince1970)
        ]
        for (key, value) in properties where key == "source" {{
            payload[key] = value
        }}

        guard let body = try? JSONSerialization.data(withJSONObject: payload) else {{ return }}
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 8.0
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        URLSession.shared.dataTask(with: request).resume()
    }}

    static func track(event: String) {{
        guard isEnabled else {{ return }}
        send(event: event)
    }}

    static func record(event: String) {{
        guard isEnabled else {{ return }}
        send(event: event)
    }}

    private static var isEnabled: Bool {{
        UserDefaults.standard.bool(forKey: enabledKey)
    }}

    private static func hardwareModel() -> String {{
        var info = utsname()
        uname(&info)
        return withUnsafePointer(to: &info.machine) {{
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {{ String(cString: $0) }}
        }}
    }}
}}'''


def remove_duplicate_launch(text: str) -> str:
    pattern = re.compile(
        r'(?m)^[ \t]*JerkgramTelemetry\.send\(\s*event:\s*"app_launch"\s*,\s*properties:\s*\[[^\n]*\]\s*\)\s*\n?'
    )
    text, count = pattern.subn("", text)
    if count > 1:
        fail(f"unexpected external app_launch send count: {count}")
    return text


def patch_privacy_strings(text: str) -> str:
    if text.count(PRIVACY_MARKER) == 1 and EN_PRIVACY in text and RU_PRIVACY in text:
        return text
    if PRIVACY_MARKER in text:
        fail("privacy marker exists without canonical RU/EN text")

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

    updated = text[:match.start()] + canonical + text[closing + 1:]
    if updated.count(PRIVACY_MARKER) != 1:
        fail("privacy marker did not converge to exactly one owner")
    if updated.count(EN_PRIVACY) != 1 or updated.count(RU_PRIVACY) != 1:
        fail("canonical privacy strings did not converge exactly once")
    if "var anonymousAnalytics: String" not in updated:
        fail("analytics title localization disappeared while patching privacy copy")
    return updated


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

    if APP_MARKER not in app:
        start, end = locate_telemetry(app)
        key = extract_toggle_key(app, settings)
        app = app[:start] + canonical_telemetry(key) + app[end:]
        app = remove_duplicate_launch(app)

    start, end = locate_telemetry(app)
    block = app[start:end]
    if APP_MARKER not in app:
        fail("Build132 telemetry marker missing after patch")
    for forbidden in ("installReceiptId", "dayId", "weekId", "monthId"):
        if forbidden in block:
            fail(f"persistent telemetry identifier survived: {forbidden}")

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
        f"[Build132 telemetry v2] AppDelegate={'updated' if changed_app else 'unchanged'}, "
        f"Settings={'updated' if changed_settings else 'unchanged'}, "
        f"Strings={'updated' if changed_strings else 'unchanged'}, "
        f"shared identity={'updated' if changed_identity else 'unchanged'}"
    )


if __name__ == "__main__":
    main()
