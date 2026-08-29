#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
CONSUME = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
AUTOREMOVE = ROOT / "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift"
FORWARD = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
STANDALONE = ROOT / "submodules/TelegramCore/Sources/PendingMessages/StandaloneSendMessage.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_SENSITIVE_SETTINGS_SYNC1"


def fail(message: str) -> None:
    raise SystemExit("[verify Build124 sensitive settings] ERROR: " + message)


def require(value: bool, message: str) -> None:
    if not value:
        fail(message)


def main() -> None:
    for path in (SETTINGS, CONSUME, AUTOREMOVE, FORWARD, STANDALONE):
        require(path.is_file(), f"materialized owner missing: {path}")

    settings = SETTINGS.read_text(encoding="utf-8")
    consume = CONSUME.read_text(encoding="utf-8")
    autoremove = AUTOREMOVE.read_text(encoding="utf-8")
    forward = FORWARD.read_text(encoding="utf-8")
    standalone = STANDALONE.read_text(encoding="utf-8")

    require(settings.count(MARKER) == 1, "sensitive-setting marker must exist exactly once")
    for key in (
        "GhostBaseKey.scheduledSend",
        "GhostBaseKey.protectedEnabled",
        "GhostBaseKey.oneTimeSave",
    ):
        require(key in settings, f"synchronous runtime key missing: {key}")

    sync_loop = settings.index("for key in jerkgramSynchronousRuntimeSettingKeys")
    queue_owner = settings.index("JerkgramSettingsCommitQueue.enqueue", sync_loop)
    require(sync_loop < queue_owner, "runtime-sensitive projection must precede deferred queue")
    before_queue = settings[sync_loop:queue_owner]
    require("jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)" in before_queue, "scoped synchronous projection missing")
    require("value.write(to: defaults, key: key)" in before_queue, "active synchronous projection missing")
    require('UserDefaults(suiteName: "group.4a348a9b186b700c.1")' in before_queue, "Scheduled Send shared-suite projection missing")

    queue_block = settings[queue_owner:]
    require("for (key, value) in deferredChanges" in queue_block, "deferred settings loop missing")
    require("for (key, value) in changes" not in queue_block, "runtime-sensitive values can still enter async batch")
    require("!jerkgramSynchronousRuntimeSettingKeys.contains($0.key)" in settings, "sensitive-key exclusion filter missing")
    require("synchronize()" not in settings, "forced UserDefaults disk synchronize must not exist")

    protected_key = '"jerkgram.ProtectedContent.Enabled"'
    one_time_key = '"jerkgram.ProtectedContent.OneTimeSave"'
    require(protected_key in consume and one_time_key in consume, "consume owner no longer reads protected one-time runtime state")
    require(protected_key in autoremove and one_time_key in autoremove, "autoremove owner no longer reads protected one-time runtime state")

    scheduled_key = '"jerkgram.GhostMode.ScheduledSend"'
    require(scheduled_key in forward, "forward Scheduled Send consumer missing")
    require(scheduled_key in standalone, "standalone Scheduled Send consumer missing")

    print("[verify Build124 sensitive settings] SOURCE VERIFIED")
    print("[verify Build124 sensitive settings] synchronous consumers receive Scheduled Send / Protected Enabled / One-Time Save before deferred settings work")
    print("[verify Build124 sensitive settings] unrelated settings remain deferred; no UserDefaults synchronize() introduced")


if __name__ == "__main__":
    main()
