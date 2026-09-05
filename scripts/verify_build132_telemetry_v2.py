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
PATCHER = Path("scripts/apply_build132_telemetry_v2.py")
APP_MARKER = "// BUILD132_TELEMETRY_V2"
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"

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
    raise RuntimeError(f"[Build132 telemetry verify] {message}")


def read(path: Path) -> str:
    if not path.is_file(): fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def block_for(text: str) -> str:
    matches = list(re.finditer(r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b", text))
    if len(matches) != 1: fail(f"expected one JerkgramTelemetry declaration, found {len(matches)}")
    m = matches[0]; opening = text.find("{", m.end())
    depth = 0; i = opening; state = "code"
    while i < len(text):
        c = text[i]; n = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if c == '"': state = "string"
            elif c == "/" and n == "/": state = "line"; i += 1
            elif c == "/" and n == "*": state = "comment"; i += 1
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0: return text[m.start():i + 1]
        elif state == "string":
            if c == "\\": i += 1
            elif c == '"': state = "code"
        elif state == "line" and c == "\n": state = "code"
        elif state == "comment" and c == "*" and n == "/": state = "code"; i += 1
        i += 1
    fail("unterminated JerkgramTelemetry")


def require_gate(block: str, method: str) -> None:
    m = re.search(rf"static func {method}\b[^{{]*\{{", block)
    if not m: fail(f"{method}() missing")
    body = block[m.end():]
    gate = body.find("guard isEnabled else { return }")
    network = [p for token in ("URL(", "URLRequest(", "URLSession") if (p := body.find(token)) >= 0]
    if gate < 0: fail(f"{method}() missing hard OFF gate")
    if network and gate > min(network): fail(f"{method}() touches network before OFF gate")


def main() -> None:
    if len(sys.argv) != 2: fail("usage: verify_build132_telemetry_v2.py <materialized-source-root>")
    root = Path(sys.argv[1]).resolve()
    app, settings = read(root / APP_OWNER), read(root / SETTINGS_OWNER)
    patcher = read(root / PATCHER)
    identity = read(root / SHARED_IDENTITY_OWNER)
    if (root / LOCAL_IDENTITY_OWNER).exists(): fail("SettingsUI-local release identity must be removed after STEP2")

    for token in (
        "public enum JerkgramReleaseIdentity",
        'public static let version = "1.0.2-beta.1"',
        'public static let displayVersion = "1.0.2 Beta 1"',
        'public static let build = "132"',
        'public static let telegramBase = "12.9.2"',
    ):
        if token not in identity: fail(f"shared release identity missing: {token}")
    for owner, text in ((APP_OWNER, app), (SETTINGS_OWNER, settings)):
        if "import TelegramCore" not in text: fail(f"{owner} does not import shared release identity module")

    if app.count(APP_MARKER) != 1: fail("telemetry marker must occur once")
    block = block_for(app)
    for token in (
        ENDPOINT,
        "private static let schema = 1",
        '"schema": schema',
        '"appVersion": JerkgramReleaseIdentity.version',
        '"build": JerkgramReleaseIdentity.build',
        '"deviceModel": hardwareModel()',
        "request.timeoutInterval = 8.0",
        "private static let minimumInterval: TimeInterval = 4.0 * 60.0 * 60.0",
        "lastAttemptAtKey",
    ):
        if token not in block: fail(f"required telemetry token missing: {token}")
    if block.count(ENDPOINT) != 1: fail("endpoint changed or duplicated")
    if "CFBundleShortVersionString" in block or "CFBundleVersion" in block: fail("bundle/Telegram version leaked into telemetry")

    forbidden = (
        "identifierForVendor", "ASIdentifierManager", "advertisingIdentifier", "IDFA", "IDFV",
        "installReceiptId", "dayId", "weekId", "monthId", "CryptoKit", "HMAC<",
        "phoneNumber", "telegramUserId", "telegramUsername", "accountPeerId", "messageText", "chatText",
    )
    for token in forbidden:
        if token.lower() in block.lower(): fail(f"forbidden telemetry identifier/data source: {token}")
    for method in ("start", "send", "track", "record"): require_gate(block, method)
    if app.count('JerkgramTelemetry.send(event: "app_launch"') != 0: fail("duplicate external app_launch send survived")
    if any(x in block for x in ('event: "disabled"', 'event: "analytics_disabled"', 'event: "telemetry_disabled"')): fail("disabled-event request is forbidden")
    if any(x in block for x in ("Timer.scheduledTimer", "DispatchSource.makeTimerSource", "while true", "repeat {")): fail("timer/polling loop is forbidden")

    if settings.count(PRIVACY_MARKER) != 1 or EN_PRIVACY not in settings or RU_PRIVACY not in settings: fail("canonical EN/RU privacy copy missing")
    if "rglob(" in patcher or "os.walk(" in patcher: fail("patcher scans source tree")
    for path in (APP_OWNER, SETTINGS_OWNER, LOCAL_IDENTITY_OWNER, SHARED_IDENTITY_OWNER):
        if str(path) not in patcher: fail(f"patcher not bound to exact owner: {path}")

    print("[Build132 telemetry verify] PASS: schema=1 + shared release identity + device model + hard OFF + 4h attempt gate + privacy")


if __name__ == "__main__":
    main()
