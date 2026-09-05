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
    raise RuntimeError(f"[Build132 telemetry verify] {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def block_for(text: str) -> str:
    matches = list(re.finditer(
        r"(?m)^[ \t]*(?:(?:private|fileprivate|internal|public|final)\s+)*(?:final\s+)?(?:class|enum|struct)\s+JerkgramTelemetry\b",
        text,
    ))
    if len(matches) != 1:
        fail(f"expected one JerkgramTelemetry declaration, found {len(matches)}")
    match = matches[0]
    opening = text.find("{", match.end())
    if opening < 0:
        fail("JerkgramTelemetry opening brace missing")
    depth = 0
    i = opening
    state = "code"
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "/" and nxt == "/":
                state = "line"
                i += 1
            elif char == "/" and nxt == "*":
                state = "comment"
                i += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[match.start():i + 1]
        elif state == "string":
            if char == "\\":
                i += 1
            elif char == '"':
                state = "code"
        elif state == "line" and char == "\n":
            state = "code"
        elif state == "comment" and char == "*" and nxt == "/":
            state = "code"
            i += 1
        i += 1
    fail("unterminated JerkgramTelemetry")


def require_method_gate(block: str, method: str) -> None:
    match = re.search(rf"static func {re.escape(method)}\b[^{{]*\{{", block)
    if not match:
        fail(f"{method}() missing")
    body = block[match.end():]
    gate = body.find("guard isEnabled else { return }")
    network = [
        position
        for token in ("URL(", "URLRequest(", "URLSession")
        if (position := body.find(token)) >= 0
    ]
    if gate < 0:
        fail(f"{method}() missing hard OFF gate")
    if network and gate > min(network):
        fail(f"{method}() touches network before OFF gate")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_build132_telemetry_v2.py <materialized-source-root>")

    root = Path(sys.argv[1]).resolve()
    app = read(root / APP_OWNER)
    settings = read(root / SETTINGS_OWNER)
    strings = read(root / STRINGS_OWNER)
    patcher = read(PATCHER)
    identity = read(root / SHARED_IDENTITY_OWNER)

    if (root / LOCAL_IDENTITY_OWNER).exists():
        fail("SettingsUI-local release identity must be removed after STEP2")

    for token in (
        "public enum JerkgramReleaseIdentity",
        'public static let version = "1.0.2-beta.1"',
        'public static let displayVersion = "1.0.2 Beta 1"',
        'public static let build = "132"',
        'public static let telegramBase = "12.9.2"',
        "public static var releaseVersion: String",
    ):
        if token not in identity:
            fail(f"shared release identity missing: {token}")

    for owner, text in ((APP_OWNER, app), (SETTINGS_OWNER, settings)):
        if "import TelegramCore" not in text:
            fail(f"{owner} does not import shared release identity module")

    if app.count(APP_MARKER) != 1:
        fail("telemetry v2 marker must occur once")
    if app.count(ADDENDUM_MARKER) != 1:
        fail("telemetry v2.1 marker must occur once")
    block = block_for(app)

    # Compatibility contract: endpoint/schema and legacy UTC identifiers survive unchanged in v2.1.
    for token in (
        ENDPOINT,
        "private static let schema = 1",
        '"schema": schema',
        '"appVersion": JerkgramReleaseIdentity.releaseVersion',
        '"build": JerkgramReleaseIdentity.build',
        '"deviceModel": hardwareModel()',
        '"installReceiptId"',
        '"dayId"',
        '"weekId"',
        '"monthId"',
        "request.timeoutInterval = 8.0",
        "private static let minimumInterval: TimeInterval = 4.0 * 60.0 * 60.0",
        "lastAttemptAtKey",
    ):
        if token not in block:
            fail(f"required telemetry token missing: {token}")
    if block.count(ENDPOINT) != 1:
        fail("endpoint changed or duplicated")
    if "CFBundleShortVersionString" in block or "CFBundleVersion" in block:
        fail("bundle/Telegram version leaked into telemetry")

    # New Moscow-day trio must be generated as one local state and inserted together.
    for token in (
        'TimeZone(identifier: "Europe/Moscow")',
        '"jerkgram-msk-day-v1:"',
        '"analyticsDay"',
        '"analyticsDayId"',
        '"openCountToday"',
        '"jerkgram.telemetry.opens.day"',
        '"jerkgram.telemetry.opens.count"',
        "HMAC<SHA256>",
        "100000",
    ):
        if token not in block:
            fail(f"v2.1 telemetry token missing: {token}")
    trio_assignment = re.search(
        r'payload\["analyticsDay"\]\s*=\s*analytics\.day.*?'
        r'payload\["analyticsDayId"\]\s*=\s*analytics\.dayId.*?'
        r'payload\["openCountToday"\]\s*=\s*analytics\.openCountToday',
        block,
        flags=re.DOTALL,
    )
    if not trio_assignment:
        fail("analyticsDay/analyticsDayId/openCountToday are not inserted together from one local state")

    # HMAC must be day-scoped and use the same local secret used by legacy period IDs.
    hmac_window = re.search(r"private static func analyticsDayId\b.*?\n\s*}", block, flags=re.DOTALL)
    if not hmac_window:
        fail("analyticsDayId helper missing")
    hmac_body = hmac_window.group(0)
    for token in ("localSecret()", '"jerkgram-msk-day-v1:"', "HMAC<SHA256>"):
        if token not in hmac_body:
            fail(f"analyticsDayId is not derived from existing local secret + Moscow day: {token}")

    # Lifecycle semantics: first active counts; later inactive->active does not unless background occurred.
    for token in (
        "private static var hasSeenActive = false",
        "private static var enteredBackground = false",
        "static func didEnterBackground()",
        "static func didBecomeActive()",
        "guard !hasSeenActive || enteredBackground else {",
        "incrementOpenCountForCurrentAnalyticsDay()",
    ):
        if token not in block:
            fail(f"foreground lifecycle guard missing: {token}")
    active_match = re.search(r"static func didBecomeActive\(\)\s*\{(?P<body>.*?)\n\s*}\n", block, flags=re.DOTALL)
    if not active_match:
        fail("didBecomeActive() body missing")
    active_body = active_match.group("body")
    gate_pos = active_body.find("guard isEnabled else { return }")
    increment_pos = active_body.find("incrementOpenCountForCurrentAnalyticsDay()")
    send_pos = active_body.find("send(event:")
    if gate_pos < 0 or increment_pos < 0 or gate_pos > increment_pos:
        fail("OFF gate must precede local open-counter work")
    if send_pos >= 0 and increment_pos > send_pos:
        fail("open count must update before normal scheduler/send path")

    # No per-open networking bypass: lifecycle can only call the existing rate-limited send().
    lifecycle_window = re.search(
        r"static func didBecomeActive\(\).*?private static var isEnabled",
        block,
        flags=re.DOTALL,
    )
    if not lifecycle_window:
        fail("cannot isolate lifecycle window")
    lifecycle = lifecycle_window.group(0)
    for token in ("URL(", "URLRequest(", "URLSession", "dataTask("):
        if token in lifecycle:
            fail(f"foreground lifecycle creates a dedicated network request: {token}")

    for method in ("start", "send", "track", "record", "didEnterBackground", "didBecomeActive"):
        require_method_gate(block, method)
    if app.count('JerkgramTelemetry.send(event: "app_launch"') != 0:
        fail("duplicate external app_launch send survived")
    if any(x in block for x in ('event: "disabled"', 'event: "analytics_disabled"', 'event: "telemetry_disabled"')):
        fail("disabled-event request is forbidden")
    if any(x in block for x in ("Timer.scheduledTimer", "DispatchSource.makeTimerSource", "while true", "repeat {")):
        fail("timer/polling loop is forbidden")

    # Secret must never be serialized/logged, and response must never mutate the open counter.
    payload_window = re.search(r"var payload: \[String: Any\] = \[.*?JSONSerialization", block, flags=re.DOTALL)
    if not payload_window:
        fail("payload construction window missing")
    payload_body = payload_window.group(0)
    for token in ("localSecret", "secretKey", "authKey"):
        if token in payload_body:
            fail(f"local secret leaked into payload construction: {token}")
    response_windows = re.findall(r"dataTask\(with: request\).*?\.resume\(\)", block, flags=re.DOTALL)
    for response_body in response_windows:
        if "openCountToday" in response_body or "opensCountKey" in response_body:
            fail("server response is allowed to affect openCountToday")

    forbidden = (
        "identifierForVendor", "ASIdentifierManager", "advertisingIdentifier", "IDFA", "IDFV",
        "PeerId", "telegramUserId", "telegramUsername", "phoneNumber", "authKey", "serialNumber",
        "messageText", "chatText", "contactsPayload",
    )
    for token in forbidden:
        if token.lower() in block.lower():
            fail(f"forbidden telemetry identifier/data source: {token}")

    if ".info(3, strings.anonymousAnalyticsDescription)" not in settings:
        fail("Settings no longer renders semantic anonymousAnalyticsDescription")
    if strings.count(PRIVACY_MARKER) != 1:
        fail("semantic privacy marker must occur once in JerkgramStrings")
    if strings.count(EN_PRIVACY) != 1 or strings.count(RU_PRIVACY) != 1:
        fail("canonical v2.1 EN/RU privacy copy missing from JerkgramStrings")
    for token in (
        "var anonymousAnalyticsDescription: String",
        'if self.languageCode == "ru"',
    ):
        if token not in strings:
            fail(f"semantic privacy localization missing: {token}")

    if "rglob(" in patcher or "os.walk(" in patcher:
        fail("patcher scans source tree")
    for path in (APP_OWNER, SETTINGS_OWNER, STRINGS_OWNER, LOCAL_IDENTITY_OWNER, SHARED_IDENTITY_OWNER):
        if str(path) not in patcher:
            fail(f"patcher not bound to exact owner: {path}")

    print(
        "[Build132 telemetry verify] PASS: v2.1 preserves schema/legacy UTC IDs + Moscow DAU ID + "
        "guarded open counter + hard OFF + rate-limited send + semantic RU/EN privacy"
    )


if __name__ == "__main__":
    main()
