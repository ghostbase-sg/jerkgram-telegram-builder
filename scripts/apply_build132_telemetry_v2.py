#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ENDPOINT = "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity"
SCHEMA = 1

APP_OWNER = Path("submodules/TelegramUI/Sources/AppDelegate.swift")
SETTINGS_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")

APP_MARKER = "// BUILD132_TELEMETRY_V2"
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"

EN_TITLE = "Anonymous Analytics"
RU_TITLE = "Анонимная аналитика"
EN_PRIVACY = (
    "Sends Jerkgram version, build, iOS version, device region and hardware model "
    "(for example iPhone15,2). It does not send Telegram account data, usernames, "
    "phone numbers, contacts, chats or message content. When disabled, Jerkgram "
    "makes no analytics network requests."
)
RU_PRIVACY = (
    "Отправляет версию и сборку Jerkgram, версию iOS, регион устройства и модель "
    "устройства (например iPhone15,2). Не отправляет данные аккаунта Telegram, "
    "имя пользователя, номер телефона, контакты, чаты или содержимое сообщений. "
    "Когда аналитика выключена, Jerkgram не выполняет аналитические сетевые запросы."
)

FORBIDDEN_OLD_KEYS = (
    "installReceiptId",
    "dayId",
    "weekId",
    "monthId",
)


def die(message: str) -> "NoReturn":
    raise RuntimeError(f"[Build132 telemetry v2] {message}")


def read(path: Path) -> str:
    if not path.is_file():
        die(f"missing owner: {path}")
    return path.read_text(encoding="utf-8")


def write_if_changed(path: Path, text: str) -> bool:
    old = path.read_text(encoding="utf-8")
    if old == text:
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
        elif state == "block":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 1
        i += 1
    die("unterminated JerkgramTelemetry declaration")


def locate_telemetry_type(text: str) -> tuple[int, int]:
    matches = list(re.finditer(
        r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b",
        text,
    ))
    if len(matches) != 1:
        die(f"expected exactly one JerkgramTelemetry declaration in {APP_OWNER}, found {len(matches)}")
    start = matches[0].start()
    open_index = text.find("{", matches[0].end())
    if open_index < 0:
        die("JerkgramTelemetry opening brace missing")
    end = matching_brace(text, open_index) + 1
    return start, end


def extract_toggle_key(telemetry_block: str, settings_text: str) -> str:
    candidates: list[str] = []
    patterns = (
        r'bool\s*\(\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
        r'object\s*\(\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
        r'set\s*\([^,\n]+,\s*forKey:\s*"([^"]*(?:analytic|telemetr)[^"]*)"\s*\)',
    )
    for source in (telemetry_block, settings_text):
        for pattern in patterns:
            candidates += re.findall(pattern, source, flags=re.IGNORECASE)
    unique = list(dict.fromkeys(candidates))
    if len(unique) == 1:
        return unique[0]
    if len(unique) > 1:
        die(f"ambiguous analytics UserDefaults keys: {unique}")
    return "jerkgramAnonymousAnalyticsEnabled"


def canonical_telemetry(toggle_key: str) -> str:
    return f'''{APP_MARKER}
private enum JerkgramTelemetry {{
    private static let endpoint = "{ENDPOINT}"
    private static let schema = {SCHEMA}
    private static let enabledKey = "{toggle_key}"
    private static let minimumInterval: TimeInterval = 4.0 * 60.0 * 60.0
    private static let lastSentAtKey = "jerkgramAnonymousAnalyticsLastSentAt"

    static func start() {{
        guard isEnabled else {{ return }}
        send(event: "app_launch")
    }}

    static func send(event: String, properties: [String: Any] = [:]) {{
        // OFF must be a hard network gate: do not construct URL/request/session first.
        guard isEnabled else {{ return }}

        let now = Date()
        if event != "app_launch",
           let lastSentAt = UserDefaults.standard.object(forKey: lastSentAtKey) as? Date,
           now.timeIntervalSince(lastSentAt) < minimumInterval {{
            return
        }}

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
        for (key, value) in properties {{
            guard isAllowedProperty(key) else {{ continue }}
            payload[key] = value
        }}

        guard let body = try? JSONSerialization.data(withJSONObject: payload) else {{ return }}
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 8.0
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body

        URLSession.shared.dataTask(with: request) {{ _, response, _ in
            guard let http = response as? HTTPURLResponse,
                  (200 ... 299).contains(http.statusCode) else {{
                return
            }}
            UserDefaults.standard.set(Date(), forKey: lastSentAtKey)
        }}.resume()
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
        let defaults = UserDefaults.standard
        if defaults.object(forKey: enabledKey) == nil {{
            return false
        }}
        return defaults.bool(forKey: enabledKey)
    }}

    private static func hardwareModel() -> String {{
        var systemInfo = utsname()
        uname(&systemInfo)
        return withUnsafePointer(to: &systemInfo.machine) {{
            $0.withMemoryRebound(to: CChar.self, capacity: 1) {{
                String(cString: $0)
            }}
        }}
    }}

    private static func isAllowedProperty(_ key: String) -> Bool {{
        switch key {{
        case "source":
            return true
        default:
            return false
        }}
    }}
}}'''


def ensure_imports(text: str) -> str:
    if "import Darwin" in text:
        return text
    m = re.search(r"(?m)^import Foundation\s*$", text)
    if not m:
        die("Foundation import anchor missing in AppDelegate.swift")
    return text[:m.end()] + "\nimport Darwin" + text[m.end():]


def patch_launch_calls(text: str) -> str:
    duplicate = re.compile(
        r'(?m)^[ \t]*JerkgramTelemetry\.send\(\s*event:\s*"app_launch"\s*,\s*properties:\s*\[[^\n]*\]\s*\)\s*\n?'
    )
    text, count = duplicate.subn("", text)
    if count > 1:
        die(f"unexpected duplicate app_launch call count: {count}")
    return text


def replace_description_near_title(text: str, title: str, replacement: str) -> tuple[str, bool]:
    title_pos = text.find(title)
    if title_pos < 0:
        return text, False
    lo = max(0, title_pos - 1200)
    hi = min(len(text), title_pos + 2200)
    region = text[lo:hi]
    quoted = list(re.finditer(r'"((?:\\.|[^"\\])*)"', region))
    title_local = title_pos - lo
    after = [m for m in quoted if m.start() > title_local]
    keywords = ("analytic", "telemetr", "anonymous", "аноним", "аналит", "статист")
    target = None
    for m in after[:8]:
        value = m.group(1).lower()
        if any(k in value for k in keywords) and value != title.lower():
            target = m
            break
    if target is None:
        return text, False
    escaped = replacement.replace("\\", "\\\\").replace('"', '\\"')
    region = region[:target.start()] + f'"{escaped}"' + region[target.end():]
    return text[:lo] + region + text[hi:], True


def patch_privacy(settings_text: str) -> str:
    if PRIVACY_MARKER in settings_text and EN_PRIVACY in settings_text and RU_PRIVACY in settings_text:
        return settings_text
    out = settings_text
    out, en_changed = replace_description_near_title(out, EN_TITLE, EN_PRIVACY)
    out, ru_changed = replace_description_near_title(out, RU_TITLE, RU_PRIVACY)
    if not (en_changed and ru_changed):
        die("could not bind both EN/RU Anonymous Analytics descriptions in exact settings owner")
    pos = out.find(EN_TITLE)
    if pos < 0:
        die("EN analytics title disappeared while patching")
    line_start = out.rfind("\n", 0, pos) + 1
    out = out[:line_start] + PRIVACY_MARKER + "\n" + out[line_start:]
    return out


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    app_path = root / APP_OWNER
    settings_path = root / SETTINGS_OWNER
    app_text = read(app_path)
    settings_text = read(settings_path)

    if APP_MARKER not in app_text:
        telemetry_start, telemetry_end = locate_telemetry_type(app_text)
        old_block = app_text[telemetry_start:telemetry_end]
        toggle_key = extract_toggle_key(old_block, settings_text)
        app_text = app_text[:telemetry_start] + canonical_telemetry(toggle_key) + app_text[telemetry_end:]
        app_text = ensure_imports(app_text)
        app_text = patch_launch_calls(app_text)

    telemetry_start, telemetry_end = locate_telemetry_type(app_text)
    block = app_text[telemetry_start:telemetry_end]
    if APP_MARKER not in block:
        die("Build132 telemetry marker missing after patch")
    for forbidden in FORBIDDEN_OLD_KEYS:
        if forbidden in block:
            die(f"persistent telemetry identifier survived migration: {forbidden}")

    settings_text = patch_privacy(settings_text)

    changed_app = write_if_changed(app_path, app_text)
    changed_settings = write_if_changed(settings_path, settings_text)
    print(
        "[Build132 telemetry v2] "
        f"AppDelegate={'updated' if changed_app else 'unchanged'}, "
        f"Settings={'updated' if changed_settings else 'unchanged'}"
    )


if __name__ == "__main__":
    main()
