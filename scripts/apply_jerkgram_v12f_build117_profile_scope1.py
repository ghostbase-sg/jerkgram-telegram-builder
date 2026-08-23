#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

PROFILE = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/"
    "Sources/PeerInfoData.swift"
)


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 profile scope] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_settings_constructors(text):
    start = text.find("func peerInfoScreenSettingsData(")
    end = text.find("\nfunc peerInfoScreenData(", start)
    require(start >= 0 and end > start, "Settings data function boundary missing")

    region = text[start:end]
    pattern = re.compile(
        r"(?m)^([ \t]*)(businessConnectedBot:\s*[^,\n\)]+)(\n[ \t]*\))"
    )
    matches = list(pattern.finditer(region))
    require(matches, "Settings PeerInfoScreenData constructors missing")
    existing_flags = region.count("isSettings: true")

    def add_flag(match):
        return (
            match.group(1)
            + match.group(2)
            + ",\n"
            + match.group(1)
            + "isSettings: true"
            + match.group(3)
        )

    patched_region = pattern.sub(add_flag, region)
    require(
        patched_region.count("isSettings: true")
        == existing_flags + len(matches),
        "not every Settings constructor received the route flag",
    )
    return text[:start] + patched_region + text[end:]


def patch_profile_scope(text):
    old_helper = '''// MARK: Jerkgram v1.2E BUILD116_PROFILE_SCOPE1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    guard let peer, case .user = peer else {
        return availablePanes
    }

    var result = availablePanes
    for key in [
        PeerInfoPaneKey.ghostBaseProfileHistory,
        PeerInfoPaneKey.ghostBasePresence,
        PeerInfoPaneKey.ghostBaseGiftHistory
    ] where !result.contains(key) {
        result.append(key)
    }

    if personalChannel != nil,
       !result.contains(.ghostBasePersonalChannel) {
        result.append(.ghostBasePersonalChannel)
    }

    return result
}'''
    new_helper = '''// MARK: Jerkgram v1.2F BUILD117_SETTINGS_PROFILE_SCOPE1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?,
    isSettings: Bool
) -> [PeerInfoPaneKey] {
    if isSettings {
        return availablePanes
    }

    guard let peer, case .user = peer else {
        return availablePanes
    }

    var result = availablePanes
    for key in [
        PeerInfoPaneKey.ghostBaseProfileHistory,
        PeerInfoPaneKey.ghostBasePresence,
        PeerInfoPaneKey.ghostBaseGiftHistory
    ] where !result.contains(key) {
        result.append(key)
    }

    if personalChannel != nil,
       !result.contains(.ghostBasePersonalChannel) {
        result.append(.ghostBasePersonalChannel)
    }

    return result
}'''
    text = replace_once(text, old_helper, new_helper, "Build116 profile helper")

    init_parameter = "        businessConnectedBot: EnginePeer?\n    ) {"
    text = replace_once(
        text,
        init_parameter,
        "        businessConnectedBot: EnginePeer?,\n"
        "        isSettings: Bool = false\n"
        "    ) {",
        "PeerInfoScreenData route parameter",
    )

    helper_call = '''            availablePanes,
            peer: peer,
            personalChannel: personalChannel
        )'''
    text = replace_once(
        text,
        helper_call,
        '''            availablePanes,
            peer: peer,
            personalChannel: personalChannel,
            isSettings: isSettings
        )''',
        "profile helper route call",
    )

    return patch_settings_constructors(text)


def main():
    require(PROFILE.is_file(), "source owner missing: " + str(PROFILE))
    PROFILE.write_text(
        patch_profile_scope(PROFILE.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print("[Build117 profile scope] Settings profile uses stock panes")
    print("[Build117 profile scope] ordinary user history panes preserved")


if __name__ == "__main__":
    main()
