#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ENDPOINT = "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity"
APP_OWNER = Path("submodules/TelegramUI/Sources/AppDelegate.swift")
SETTINGS_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
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

EN_TITLE = "Anonymous Analytics"
RU_TITLE = "Анонимная аналитика"
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
            if ch == '"': state = "string"
            elif ch == "/" and nxt == "/": state = "line"; i += 1
            elif ch == "/" and nxt == "*": state = "block"; i += 1
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return i
        elif state == "string":
            if ch == "\\": i += 1
            elif ch == '"': state = "code"
        elif state == "line":
            if ch == "\n": state = "code"
        elif state == "block" and ch == "*" and nxt == "/":
            state = "code"; i += 1
        i += 1
    fail("unterminated JerkgramTelemetry declaration")


def locate_telemetry(text: str) -> tuple[int, int]:
    matches = list(re.finditer(
        r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b",
        text,
    ))
    if len(matches) != 1:
        fail(f"expected exactly one JerkgramTelemetry declaration in {APP_OWNER}, found {len(matches)}")
    m = matches[0]
    opening = text.find("{", m.end())
    if opening < 0: fail("JerkgramTelemetry opening brace missing")
    return m.start(), matching_brace(text, opening) + 1


def ensure_import(text: str, module: str) -> str:
    if re.search(rf"(?m)^import {re.escape(module)}\s*$", text):
        return text
    anchor = re.search(r"(?m)^import Foundation\s*$", text)
    if not anchor: fail(f"Foundation import anchor missing while adding {module}")
    return text[:anchor.end()] + f"\nimport {module}" + text[anchor.end():]


def prepare_identity(root: Path, app: str, settings: str) -> tuple[str, str, Path, Path]:
    local = root / LOCAL_IDENTITY_OWNER
    if local.is_file():
        old = local.read_text(encoding="utf-8")
        if IDENTITY_MARKER not in old:
            fail(f"refusing to remove non-Build132 identity owner: {LOCAL_IDENTITY_OWNER}")
    shared = root / SHARED_IDENTITY_OWNER
    if not shared.parent.is_dir():
        fail(f"shared identity parent missing: {SHARED_IDENTITY_OWNER.parent}")
    if shared.is_file() and IDENTITY_MARKER not in shared.read_text(encoding="utf-8"):
        fail(f"refusing to overwrite non-Build132 shared identity: {SHARED_IDENTITY_OWNER}")
    return ensure_import(app, "TelegramCore"), ensure_import(settings, "TelegramCore"), local, shared


def extract_toggle_key(block: str, settings: str) -> str:
    candidates: list[str] = []
    for source in (block, settings):
        for pattern in (
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
    if count > 1: fail(f"unexpected external app_launch send count: {count}")
    return text


def replace_description(text: str, title: str, replacement: str) -> tuple[str, bool]:
    title_pos = text.find(title)
    if title_pos < 0: return text, False
    lo, hi = max(0, title_pos - 1500), min(len(text), title_pos + 6500)
    region = text[lo:hi]
    title_local = title_pos - lo
    strings = list(re.finditer(r'"((?:\\.|[^"\\])*)"', region))
    keywords = ("analytic", "telemetr", "anonymous", "аноним", "аналит", "статист")
    target = next((m for m in strings if m.start() > title_local and any(k in m.group(1).lower() for k in keywords) and m.group(1) != title), None)
    if target is None: return text, False
    escaped = replacement.replace("\\", "\\\\").replace('"', '\\"')
    region = region[:target.start()] + f'"{escaped}"' + region[target.end():]
    return text[:lo] + region + text[hi:], True


def patch_privacy(text: str) -> str:
    if PRIVACY_MARKER in text and EN_PRIVACY in text and RU_PRIVACY in text: return text
    text, en = replace_description(text, EN_TITLE, EN_PRIVACY)
    text, ru = replace_description(text, RU_TITLE, RU_PRIVACY)
    if not (en and ru): fail("could not bind both EN/RU Anonymous Analytics descriptions")
    pos = text.find(EN_TITLE)
    line = text.rfind("\n", 0, pos) + 1
    return text[:line] + PRIVACY_MARKER + "\n" + text[line:]


def main() -> None:
    if len(sys.argv) != 2: fail("usage: apply_build132_telemetry_v2.py <materialized-source-root>")
    root = Path(sys.argv[1]).resolve()
    app_path, settings_path = root / APP_OWNER, root / SETTINGS_OWNER
    app, settings = read(app_path), read(settings_path)
    app, settings, local_identity, shared_identity = prepare_identity(root, app, settings)
    app = ensure_import(app, "Darwin")

    if APP_MARKER not in app:
        start, end = locate_telemetry(app)
        key = extract_toggle_key(app[start:end], settings)
        app = app[:start] + canonical_telemetry(key) + app[end:]
        app = remove_duplicate_launch(app)

    start, end = locate_telemetry(app)
    block = app[start:end]
    if APP_MARKER not in app: fail("Build132 telemetry marker missing after patch")
    for forbidden in ("installReceiptId", "dayId", "weekId", "monthId"):
        if forbidden in block: fail(f"persistent telemetry identifier survived: {forbidden}")

    settings = patch_privacy(settings)
    changed_identity = write_if_changed(shared_identity, IDENTITY_SOURCE)
    changed_app = write_if_changed(app_path, app)
    changed_settings = write_if_changed(settings_path, settings)
    if local_identity.is_file():
        local_identity.unlink()
    print(f"[Build132 telemetry v2] AppDelegate={'updated' if changed_app else 'unchanged'}, Settings={'updated' if changed_settings else 'unchanged'}, shared identity={'updated' if changed_identity else 'unchanged'}")


if __name__ == "__main__":
    main()
