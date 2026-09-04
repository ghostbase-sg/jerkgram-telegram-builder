#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ENDPOINT = "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity"
APP_OWNER = Path("submodules/TelegramUI/Sources/AppDelegate.swift")
SETTINGS_OWNER = Path("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
PATCHER = Path("scripts/apply_build132_telemetry_v2.py")
APP_MARKER = "// BUILD132_TELEMETRY_V2"
PRIVACY_MARKER = "// BUILD132_TELEMETRY_PRIVACY_V2"

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

FORBIDDEN = (
    "identifierForVendor",
    "ASIdentifierManager",
    "advertisingIdentifier",
    "IDFA",
    "IDFV",
    "installReceiptId",
    "dayId",
    "weekId",
    "monthId",
    "CryptoKit",
    "HMAC<",
    "phoneNumber",
    "telegramUserId",
    "telegramUsername",
    "accountPeerId",
    "messageText",
    "chatText",
)


def fail(message: str) -> "NoReturn":
    raise RuntimeError(f"[Build132 telemetry verify] {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


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
            if ch == "\n":
                state = "code"
        elif state == "block":
            if ch == "*" and nxt == "/":
                state = "code"; i += 1
        i += 1
    fail("unterminated JerkgramTelemetry declaration")


def telemetry_block(text: str) -> str:
    matches = list(re.finditer(
        r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b",
        text,
    ))
    if len(matches) != 1:
        fail(f"expected one JerkgramTelemetry declaration, found {len(matches)}")
    m = matches[0]
    open_index = text.find("{", m.end())
    if open_index < 0:
        fail("JerkgramTelemetry opening brace missing")
    return text[m.start():matching_brace(text, open_index) + 1]


def require_gate_before_network(block: str, method: str) -> None:
    m = re.search(rf"static func {method}\b[^{{]*\{{", block)
    if not m:
        fail(f"{method}() missing")
    body = block[m.end():]
    gate = body.find("guard isEnabled else { return }")
    if gate < 0:
        fail(f"{method}() has no hard OFF gate")
    network_positions = [p for token in ("URL(", "URLRequest(", "URLSession") if (p := body.find(token)) >= 0]
    if network_positions and gate > min(network_positions):
        fail(f"{method}() touches network before OFF gate")


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    app = read(root / APP_OWNER)
    settings = read(root / SETTINGS_OWNER)
    patcher = read(root / PATCHER)

    if app.count(APP_MARKER) != 1:
        fail("Build132 telemetry marker must occur exactly once")
    block = telemetry_block(app)

    required = (
        ENDPOINT,
        'private static let schema = 1',
        '"schema": schema',
        '"appVersion": JerkgramReleaseIdentity.version',
        '"build": JerkgramReleaseIdentity.build',
        '"deviceModel": hardwareModel()',
        'request.timeoutInterval = 8.0',
        'private static let minimumInterval: TimeInterval = 4.0 * 60.0 * 60.0',
    )
    for token in required:
        if token not in block:
            fail(f"required telemetry token missing: {token}")

    if block.count(ENDPOINT) != 1:
        fail("endpoint changed or duplicated")
    if "CFBundleShortVersionString" in block or "CFBundleVersion" in block:
        fail("telemetry still reads Telegram/bundle version")

    for token in FORBIDDEN:
        if token.lower() in block.lower():
            fail(f"forbidden identifier/data source in telemetry: {token}")

    for method in ("start", "send", "track", "record"):
        require_gate_before_network(block, method)

    if 'send(event: "app_launch")' not in block:
        fail("start() must own app_launch")
    if app.count('JerkgramTelemetry.send(event: "app_launch"') != 0:
        fail("duplicate external app_launch send survived")

    disabled_patterns = (
        'event: "disabled"',
        'event: "analytics_disabled"',
        'event: "telemetry_disabled"',
    )
    if any(token in block for token in disabled_patterns):
        fail("disabled-state network event is forbidden")

    loop_tokens = ("Timer.scheduledTimer", "DispatchSource.makeTimerSource", "while true", "repeat {")
    if any(token in block for token in loop_tokens):
        fail("recurring telemetry polling/timer is forbidden")

    if settings.count(PRIVACY_MARKER) != 1:
        fail("privacy marker must occur exactly once")
    if EN_PRIVACY not in settings or RU_PRIVACY not in settings:
        fail("EN/RU privacy copy is not canonical")

    if "rglob(" in patcher or "os.walk(" in patcher:
        fail("patcher must not scan the source tree")
    for path in (str(APP_OWNER), str(SETTINGS_OWNER)):
        if path not in patcher:
            fail(f"patcher is not bound to exact owner: {path}")

    print("[Build132 telemetry verify] PASS: schema=1 + release identity + model + hard OFF gate + privacy")


if __name__ == "__main__":
    main()
