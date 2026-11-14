#!/usr/bin/env python3
"""Static contract check for the materialized Profile Observer v1."""
from pathlib import Path
import os

ROOT = Path(os.environ.get(
    "JERKGRAM_SOURCE_ROOT",
    os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
)).resolve()

CORE = ROOT / "submodules/TelegramCore/Sources/JerkgramProfileObserver.swift"
BUILD = ROOT / "submodules/TelegramCore/BUILD"
UPDATE_PEERS = ROOT / "submodules/TelegramCore/Sources/UpdatePeers.swift"
FULL_USER = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Peers/UpdateCachedPeerData.swift"
PROFILE_UI = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift"


def check(condition, message):
    if not condition:
        raise RuntimeError("[verify Profile observer v1] " + message)


def main():
    core = CORE.read_text(encoding="utf-8")
    build = BUILD.read_text(encoding="utf-8")
    peers = UPDATE_PEERS.read_text(encoding="utf-8")
    full = FULL_USER.read_text(encoding="utf-8")
    ui = PROFILE_UI.read_text(encoding="utf-8")

    for marker in (
        "PROFILE_TIME_MACHINE_OBSERVER_V1",
        "qos: .utility",
        "CREATE TABLE IF NOT EXISTS watched",
        "CREATE TABLE IF NOT EXISTS snapshots",
        "CREATE INDEX IF NOT EXISTS snapshots_peer_time",
        "BEGIN IMMEDIATE",
        "COMMIT",
        "ROLLBACK",
        "profileColor",
        "profileBackgroundEmojiId",
        "aboutObserved",
        "func jerkgramProfileObserverBegin(",
        "func jerkgramProfileObserverUpdatedPeers(",
        "func jerkgramProfileObserverFullUser(",
    ):
        check(marker in core, "missing core contract: " + marker)
    for forbidden in ("UserDefaults.standard", "Timer.scheduledTimer", "DispatchQueue.main",
                      "BGAppRefreshTask", "updateUserStatus", "maximumEvents"):
        check(forbidden not in core, "unexpected hot-path or presence mechanism: " + forbidden)

    check('"//submodules/sqlcipher:sqlcipher"' in build, "missing database module")
    check(peers.count("PROFILE_OBSERVER_PEER_UPDATES_V1") == 1, "peer updates hook missing")
    check("jerkgramObserverExcludingPeerId: PeerId? = nil" in peers, "full-user exclusion missing")
    check(full.count("PROFILE_OBSERVER_FULL_USER_V1") == 1, "BIO refresh hook missing")
    check("jerkgramObserverExcludingPeerId: peerId" in full, "same-response double capture")
    check(ui.count("PROFILE_OBSERVER_FIRST_OPEN_V1") == 1, "first-open enrollment missing")
    print("[verify Profile observer v1] GREEN: no polling, no presence snapshots, account-scoped SQLite")


if __name__ == "__main__":
    main()
