#!/usr/bin/env python3
"""Materialize the first event-driven Profile Time Machine observer.

Runs after Build137 performance and before Bazel. Only the isolated dev branch
wires this installer. The base Telegram checkout stays pinned to 12.9.2.
"""
from pathlib import Path
import os

REPO = Path(__file__).resolve().parent.parent
ROOT = Path(os.environ.get(
    "JERKGRAM_SOURCE_ROOT",
    os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
)).resolve()

PAYLOAD = REPO / "scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileObserver.swift"
CORE = ROOT / "submodules/TelegramCore/Sources/JerkgramProfileObserver.swift"
BUILD = ROOT / "submodules/TelegramCore/BUILD"
UPDATE_PEERS = ROOT / "submodules/TelegramCore/Sources/UpdatePeers.swift"
FULL_USER = ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Peers/UpdateCachedPeerData.swift"
PROFILE_UI = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift"

MARKER = "// MARK: Jerkgram PROFILE_TIME_MACHINE_OBSERVER_V1"
UI_MARKER = "// MARK: Jerkgram PROFILE_OBSERVER_FIRST_OPEN_V1"
PEERS_MARKER = "// MARK: Jerkgram PROFILE_OBSERVER_PEER_UPDATES_V1"
FULL_MARKER = "// MARK: Jerkgram PROFILE_OBSERVER_FULL_USER_V1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Profile observer v1] " + message)


def replace_once(source: str, old: str, new: str, description: str) -> str:
    require(source.count(old) == 1, f"{description}: anchor count {source.count(old)}")
    return source.replace(old, new, 1)


def patch_core_build(source: str) -> str:
    library = '"//submodules/sqlcipher:sqlcipher",'
    if library in source:
        return source
    anchor = '        "//submodules/Postbox:Postbox",\n'
    return replace_once(source, anchor, anchor + '        ' + library + '\n', "TelegramCore sqlcipher dep")


def patch_update_peers(source: str) -> str:
    if PEERS_MARKER in source:
        require(source.count(PEERS_MARKER) == 1, "duplicate peer hook")
        return source
    old_signature = "func updatePeers(transaction: Transaction, accountPeerId: PeerId, peers: AccumulatedPeers) {"
    new_signature = (
        "func updatePeers(transaction: Transaction, accountPeerId: PeerId, "
        "peers: AccumulatedPeers, jerkgramObserverExcludingPeerId: PeerId? = nil) {"
    )
    source = replace_once(source, old_signature, new_signature, "updatePeers signature")
    old = "    updatePeersCustom(transaction: transaction, peers: parsedPeers, update: { _, updated in updated })\n"
    new = (
        old + "    " + PEERS_MARKER + "\n"
        + "    jerkgramProfileObserverUpdatedPeers(\n"
        + "        accountPeerId: accountPeerId,\n"
        + "        peers: parsedPeers,\n"
        + "        excludingPeerId: jerkgramObserverExcludingPeerId\n"
        + "    )\n"
    )
    return replace_once(source, old, new, "identity event owner")


def patch_full_user(source: str) -> str:
    if FULL_MARKER in source:
        require(source.count(FULL_MARKER) == 1, "duplicate full-user hook")
        return source
    old = (
        "                                let userFullNotifySettings = userFullData.notifySettings\n"
        "                                updatePeers(transaction: transaction, accountPeerId: accountPeerId, peers: parsedPeers)\n"
    )
    new = (
        "                                let userFullNotifySettings = userFullData.notifySettings\n"
        "                                // " + FULL_MARKER.removeprefix("// ") + "\n"
        "                                // Capture the full user once, including BIO, without a separate\n"
        "                                // identity-only snapshot from the same full-user response.\n"
        "                                updatePeers(\n"
        "                                    transaction: transaction,\n"
        "                                    accountPeerId: accountPeerId,\n"
        "                                    peers: parsedPeers,\n"
        "                                    jerkgramObserverExcludingPeerId: peerId\n"
        "                                )\n"
        "                                if let observedUser = transaction.getPeer(peerId) as? TelegramUser {\n"
        "                                    jerkgramProfileObserverFullUser(\n"
        "                                        accountPeerId: accountPeerId,\n"
        "                                        user: observedUser,\n"
        "                                        about: userFullData.about\n"
        "                                    )\n"
        "                                }\n"
    )
    return replace_once(source, old, new, "full-user BIO refresh")


def patch_profile_ui(source: str) -> str:
    if UI_MARKER in source:
        require(source.count(UI_MARKER) == 1, "duplicate UI hook")
        return source
    old = (
        "            ghostBaseRecordObservedProfileV11G(\n"
        "                accountPeerId: self.context.account.peerId,\n"
        "                peer: peer,\n"
        "                cachedData: data.cachedData\n"
        "            )\n"
    )
    new = (
        old
        + "            " + UI_MARKER + "\n"
        + "            jerkgramProfileObserverBegin(\n"
        + "                accountPeerId: self.context.account.peerId,\n"
        + "                peer: peer,\n"
        + "                cachedData: data.cachedData\n"
        + "            )\n"
    )
    return replace_once(source, old, new, "profile first-open observation")


def main() -> None:
    require(PAYLOAD.is_file(), "missing Swift payload")
    require(MARKER in PAYLOAD.read_text(encoding="utf-8"), "payload marker missing")
    for source in (BUILD, UPDATE_PEERS, FULL_USER, PROFILE_UI):
        require(source.is_file(), "source missing: " + str(source))

    CORE.write_text(PAYLOAD.read_text(encoding="utf-8"), encoding="utf-8")
    BUILD.write_text(patch_core_build(BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    UPDATE_PEERS.write_text(
        patch_update_peers(UPDATE_PEERS.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    FULL_USER.write_text(
        patch_full_user(FULL_USER.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    PROFILE_UI.write_text(
        patch_profile_ui(PROFILE_UI.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print("[Profile observer v1] materialized: first-open enrollment + event-driven updates + SQLite")


if __name__ == "__main__":
    main()
