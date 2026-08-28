#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_SENSITIVE_SETTINGS_SYNC1"


OLD = '''private func jerkgramPersistChangedSettings(
    accountPeerId: Int64,
    previous: GhostBaseSettingsState?,
    current: GhostBaseSettingsState
) {
    let oldValues = previous.map(jerkgramStateValues) ?? [:]
    let newValues = jerkgramStateValues(current)
    let changes = newValues.filter { oldValues[$0.key] != $0.value }
    guard !changes.isEmpty else { return }

    JerkgramSettingsCommitQueue.enqueue {
        let defaults = UserDefaults.standard
        for (key, value) in changes {
            value.write(to: defaults, key: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key))
            // Legacy Telegram and extension consumers use this active-account projection.
            value.write(to: defaults, key: key)
            if key == GhostBaseKey.scheduledSend {
                value.write(to: UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? defaults, key: key)
            }
        }
    }
}'''


NEW = '''private func jerkgramPersistChangedSettings(
    accountPeerId: Int64,
    previous: GhostBaseSettingsState?,
    current: GhostBaseSettingsState
) {
    let oldValues = previous.map(jerkgramStateValues) ?? [:]
    let newValues = jerkgramStateValues(current)
    let changes = newValues.filter { oldValues[$0.key] != $0.value }
    guard !changes.isEmpty else { return }

    // MARK: Jerkgram v1.2M BUILD124_SENSITIVE_SETTINGS_SYNC1
    // These values are consumed synchronously outside Settings immediately
    // before user-visible side effects. Leaving them behind the utility queue
    // creates a real stale-state window: Scheduled Send can remain active after
    // OFF, and protected one-time media can be replaced with expired content
    // immediately after One-Time Save was switched ON.
    //
    // UserDefaults.set updates the in-process defaults domain; deliberately
    // avoid any forced defaults/filesystem synchronization here.
    let jerkgramSynchronousRuntimeSettingKeys: Set<String> = [
        GhostBaseKey.scheduledSend,
        GhostBaseKey.protectedEnabled,
        GhostBaseKey.oneTimeSave,
    ]
    let defaults = UserDefaults.standard
    for key in jerkgramSynchronousRuntimeSettingKeys {
        guard let value = changes[key] else { continue }
        value.write(
            to: defaults,
            key: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key)
        )
        // Legacy Telegram/Jerkgram runtime owners consume the active-account
        // projection directly from UserDefaults.standard.
        value.write(to: defaults, key: key)
        if key == GhostBaseKey.scheduledSend {
            let sharedDefaults = UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? defaults
            value.write(to: sharedDefaults, key: key)
        }
    }

    let deferredChanges = changes.filter {
        !jerkgramSynchronousRuntimeSettingKeys.contains($0.key)
    }
    guard !deferredChanges.isEmpty else { return }

    JerkgramSettingsCommitQueue.enqueue {
        let defaults = UserDefaults.standard
        for (key, value) in deferredChanges {
            value.write(to: defaults, key: jerkgramScopedSettingsKey(accountPeerId: accountPeerId, key: key))
            // Non-critical compatibility projections stay off the caller thread.
            value.write(to: defaults, key: key)
        }
    }
}'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 sensitive settings] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    require(
        "BUILD123_ACCOUNT_SETTINGS_OWNER1" in text or text.lstrip().startswith("private func jerkgramPersistChangedSettings("),
        "Build123 settings persistence owner missing",
    )
    require(text.count(OLD) == 1, f"expected one Build123 persistence owner, found {text.count(OLD)}")
    updated = text.replace(OLD, NEW, 1)
    require(MARKER in updated, "marker missing after patch")
    require("synchronize()" not in updated, "forced UserDefaults synchronize must not be introduced")
    return updated


def main() -> None:
    require(SETTINGS.is_file(), f"materialized settings owner missing: {SETTINGS}")
    original = SETTINGS.read_text(encoding="utf-8")
    updated = patch_text(original)
    SETTINGS.write_text(updated, encoding="utf-8")
    print("[Build124 sensitive settings] GREEN")
    print("[Build124 sensitive settings] Scheduled Send, Protected Enabled and One-Time Save project before deferred settings commits")
    print("[Build124 sensitive settings] no forced UserDefaults disk synchronization added")


if __name__ == "__main__":
    main()
