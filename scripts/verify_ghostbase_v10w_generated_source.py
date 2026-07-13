#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "work/swiftgram-src"

context = (
    source
    / "submodules/TelegramUI/Sources/"
      "ChatInterfaceStateContextMenus.swift"
).read_text()

voice = (
    source
    / "submodules/TelegramUI/Sources/Chat/"
      "ChatControllerMediaRecording.swift"
).read_text()

settings = (
    source
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
).read_text()

checks = {
    "direct ChatControllerImpl forwarding":
        "interfaceInteraction.chatController()" in context
        and "forceHideNames: true" in context,

    "invalid string-mode forwarding removed":
        '"forwardMessagesWithNoNames"' not in context[
            context.find(
                "GhostBase v1.0W forward without author action"
            ):
            context.find(
                "GhostBase v1.0W forward without author action"
            ) + 2500
        ],

    "voice cleanup":
        "GhostBase v1.0W scheduled voice post-enqueue cleanup"
        in voice,

    "native style page":
        "GhostBase v1.0W native send style page"
        in settings,

    "broken style opener removed":
        "GhostBase v1.0T compact send style menu"
        not in settings,
}

failed = [name for name, ok in checks.items() if not ok]

if failed:
    for name in failed:
        print(f"FAILED: {name}")
    raise SystemExit(1)

for name in checks:
    print(f"OK: {name}")
