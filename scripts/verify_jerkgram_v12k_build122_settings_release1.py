#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STARS = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramStarsEditorController.swift"
DATA = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift"
FLOW = ROOT / "submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift"
TRANSACTION = ROOT / "submodules/JerkgramCore/Sources/JerkgramArchiveTransaction.swift"
TIME_MACHINE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build122 settings verify] " + message)


def main() -> None:
    settings = SETTINGS.read_text(encoding="utf-8")
    stars = STARS.read_text(encoding="utf-8")
    data = DATA.read_text(encoding="utf-8")
    flow = FLOW.read_text(encoding="utf-8")
    transaction = TRANSACTION.read_text(encoding="utf-8")
    time_machine = TIME_MACHINE.read_text(encoding="utf-8")

    require("BUILD122_SETTINGS_RELEASE1" in settings, "Settings marker missing")
    root = settings[settings.index("if page == .root {"):settings.index("if page == .home {")]
    require(root.count(".disclosure(") == 9, "root destination count changed")
    require('"Jerkgram",' not in root, "root Jerkgram hero survived")
    require("strings.debugResearch" in root, "Debug destination missing")

    require("BUILD122_STARS_DRAFT_EDITOR1" in stars, "Stars draft editor missing")
    require("Common_Cancel" in stars and "Common_Save" in stars, "localized Stars navigation missing")
    require("jerkgramCommitStarsDraft" in stars, "Stars commit owner missing")
    require("textUpdated: { arguments.setAmount" in stars, "Stars local draft owner missing")
    require("textUpdated: { _ in }" in settings, "legacy input neutralization missing")
    require("UserDefaults.standard.set(ghostBaseSanitizeStarsAmount(updatedText)" not in settings, "per-keystroke Stars persistence survived")
    require("case let .input(_, _, key, title, text):" not in settings, "unused legacy Stars key binding survived")
    require("case let .input(_, _, _, title, text):" in settings, "warning-clean legacy Stars input binding missing")

    require("ItemListActionItem" in data, "Data action buttons missing")
    require('action == "perChat" ? .arrow : .none' in data, "Data disclosure semantics missing")
    require("BUILD122_TIME_MACHINE_POLISH1" in time_machine, "Time Machine visual semantics missing")
    require("ItemListActionItem" in time_machine, "Time Machine load-more button missing")

    require("BUILD122_ARCHIVE_EXACT_ACCOUNTS1" in transaction, "archive transaction marker missing")
    require("retentionRollback" in transaction, "retentionRollback missing")
    require("BUILD122_ARCHIVE_RESULT_FEEDBACK1" in flow, "import result feedback missing")
    require("try? JerkgramArchiveTransaction.apply" not in flow, "import transaction errors are swallowed")
    require("selectedAccountPeerIds.isSubset(of: availableAccountPeerIds)" in transaction, "exact available-account gate missing")
    require("activeAccountContexts" in flow, "connected account source missing")
    require("matchingAccounts" in flow and "disconnected" in flow, "account import preview missing")
    require("incomingRetention" in flow, "retention transaction input missing")
    require("availableAccountPeerIds: [context.account.peerId.toInt64()]" not in flow, "single-account import hardcode survived")

    print("[Build122 settings verify] GREEN")
    print("[Build122 settings verify] root Jerkgram hero absent; Stars Save/Cancel draft; exact connected-account import with retention rollback; visual action owners verified")


if __name__ == "__main__":
    main()
