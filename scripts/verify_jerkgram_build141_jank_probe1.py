#!/usr/bin/env python3
from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ACCOUNT = ROOT / "submodules/TelegramCore/Sources/Account/Account.swift"
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
CHAT_INPUT = ROOT / "submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift"
PROFILE_BG = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build141 jank verifier] " + message)


def read(path: Path) -> str:
    require(path.is_file(), "source owner missing: " + str(path))
    return path.read_text(encoding="utf-8")


def main() -> None:
    account = read(ACCOUNT)
    app = read(APP_DELEGATE)
    settings = read(SETTINGS)
    chat = read(CHAT_INPUT)
    profile = read(PROFILE_BG)

    for token in (
        "// MARK: Jerkgram Build141 JANK_PROBE_CORE1",
        "public static let hitchCapacity = 64",
        "public static let regionCapacity = 256",
        "public func recordFrameGap(",
        "public func makeTextReport() -> String",
    ):
        require(account.count(token) == 1, "core token count: " + token)

    core = account[account.index("// MARK: Jerkgram Build141 JANK_PROBE_CORE1"):account.index("public final class Account")]
    for forbidden in ("UserDefaults", "FileManager", "JSONEncoder", "JSONDecoder", "Data.write"):
        require(forbidden not in core, "hot probe must stay memory-only: " + forbidden)

    require(app.count("// MARK: Jerkgram Build141 JANK_DISPLAY_LINK1") == 1, "display marker count")
    require(app.count("CADisplayLink(target:") == 1, "display link count")
    require(app.count("JerkgramJankDisplayLink.shared.start()") == 1, "display start count")
    require("durationMs >= 33.0" in app, "33ms threshold missing")
    require("durationMs >= 100.0" in app and "durationMs >= 250.0" in app, "severity thresholds missing")

    require(settings.count("// MARK: Jerkgram Build141 JANK_SETTINGS1") == 1, "settings marker count")
    require(settings.count("JerkgramJankProbe.shared.begin(.settingsUpdate)") == 1, "settings region count")
    require(settings.count("UIPasteboard.general.string = JerkgramJankProbe.shared.makeTextReport()") == 1, "report copy action count")
    require(settings.count("case let .aboutValue(_, index, title, value):") == 1, "About Version action owner missing")

    require(chat.count("// MARK: Jerkgram Build141 JANK_CHAT_INPUT1") == 1, "chat marker count")
    require(chat.count("JerkgramJankProbe.shared.begin(.chatTextInput)") == 1, "chat region count")
    require(chat.count("JerkgramJankProbe.shared.noteTyping(true)") == 1, "typing activity marker count")
    require(chat.count("self.chatInputTextNodeDidUpdateText()") >= 1, "native typing call disappeared")

    require(profile.count("// MARK: Jerkgram Build141 JANK_PROFILE1") == 1, "profile marker count")
    require(profile.count("JerkgramJankProbe.shared.begin(.profileBackground)") == 1, "profile region count")
    require(profile.count("JerkgramJankProbe.shared.noteAnimatedAvatar(true)") == 1, "animated-avatar activity marker count")
    require("synchronousLoad: true" in profile, "Build120 synchronous avatar behavior changed")
    require("completeOnly: true" in profile, "Build123 complete-only avatar behavior changed")

    print("[Build141 jank verifier] GREEN")
    print("[Build141 jank verifier] memory-only bounded recorder / one display link / Settings + profile + typing owners present")


if __name__ == "__main__":
    main()
