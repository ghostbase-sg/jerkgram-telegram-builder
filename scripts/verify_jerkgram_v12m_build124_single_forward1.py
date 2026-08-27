#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MENU = ROOT / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 single forward verify] " + message)


def main() -> None:
    settings = SETTINGS.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")

    require("BUILD124_FORWARD_SETTING_OWNER1" in settings, "forward setting account owner missing")
    require("GhostBaseKey.forwardWithoutAuthor: .bool(state.forwardWithoutAuthor)" in settings, "forward setting omitted from Build123 persisted values")

    require("BUILD124_SINGLE_FORWARD_ACCOUNT_SCOPE1" in menu, "single context account resolver missing")
    require("context.account.peerId.toInt64()" in menu, "single context setting is not account scoped")
    require("scopedForwardWithoutAuthorKey" in menu and "legacyForwardWithoutAuthorKey" in menu, "scoped + legacy resolution missing")
    require("BUILD123_PORTABLE_MENU_RESTRICTIONS1" in menu, "portable single-message capability gate missing")

    marker = menu.index("BUILD124_SINGLE_FORWARD_ACCOUNT_SCOPE1")
    gate_end = menu.index("actions.append(.action(ContextMenuActionItem(", marker)
    gate = menu[marker:gate_end]
    sentinel = "// data.messageActions.options.contains(.forward) survived portable gate"
    gate_without_sentinel = gate.replace(sentinel, "")
    require("data.messageActions.options.contains(.forward)" not in gate_without_sentinel, "single action is still gated by Telegram's forward permission")
    require("Namespaces.Peer.SecretChat" in gate and "TelegramMediaPaidContent" in gate, "single action safety restrictions were weakened")

    print("[Build124 single forward verify] GREEN")
    print("[Build124 single forward verify] single long-press follows current-account toggle and portable capability gate")


if __name__ == "__main__":
    main()
