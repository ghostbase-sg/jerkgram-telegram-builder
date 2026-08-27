#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 release verify] " + message)


def read(relative: str) -> str:
    path = ROOT / relative
    require(path.is_file(), "missing source: " + relative)
    return path.read_text(encoding="utf-8")


def main() -> None:
    settings = read("submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift")
    require("BUILD123_ACCOUNT_SETTINGS_OWNER1" in settings, "account settings owner missing")
    require("JerkgramSettingsCommitQueue" in settings, "serial commit owner missing")
    require("jerkgramPersistChangedSettings" in settings, "targeted settings commit missing")
    require("jerkgramProjectActiveSettings" in settings, "active projection missing")
    require("dictionaryRepresentation()" not in settings, "bulk defaults scan remains")
    require("jerkgramMirrorSettingsToAccount" not in settings, "reverse mirror remains")
    require("BUILD123_SETTINGS_SYSTEM1" in settings, "shared Settings UI missing")
    require("BUILD123_SETTINGS_TOGGLE_ICONS1" in settings and "icon: jerkgramSettingsToggleIcon(key)" in settings, "Settings category icons missing")

    attribute = read("submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift")
    require("editHistoryEntities" in attribute and "originalEntities" in attribute, "entity snapshots missing")
    require("entity-only edits" in attribute, "entity-only history contract missing")
    state = read("submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift")
    require("BUILD123_ENTITY_HISTORY_CAPTURE1" in state and "entities: previousEntities" in state, "entity capture missing")
    require("BUILD123_DELETED_ENTITY_SNAPSHOT1" in state and "originalEntities: currentMessage.textEntitiesAttribute?.entities ?? []" in state, "deleted message entities missing")
    deleted = read("submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift")
    require("BUILD123_DELETED_ENTITY_SNAPSHOT1" in deleted and "originalEntities: currentMessage.textEntitiesAttribute?.entities ?? []" in deleted, "interactive deletion entities missing")
    history = read("submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift")
    require("BUILD123_HISTORY_ENTITIES1" in history, "history entity renderer missing")
    require("EmbeddedMediaStickersMessageAttribute" in history, "premium emoji media bridge missing")
    require("data.messageActions.options.contains(.forward) survived portable gate" in history, "portable menu regression sentinel missing")
    require("BUILD123_PORTABLE_MENU_RESTRICTIONS1" in history and "$0 is TelegramMediaPaidContent" in history and "$0 is TelegramMediaAction" in history, "portable menu restrictions missing")
    forward = read("submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift")
    require("BUILD123_PORTABLE_FORWARD1" in forward, "portable forward builder missing")
    require("messages.contains(where: { $0.isCopyProtected() })" in forward, "protected forward fallback missing")
    require("canUsePortableCopy" in forward and "$0 is TelegramMediaPaidContent" in forward, "portable forwarding restrictions missing")

    links = read("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift")
    require("BUILD123_LINKS_INTRINSIC_GLASS1" in links, "Links intrinsic owner missing")
    require("&& !self.jerkgramLinksReadabilityEnabled" in links, "Links still receives viewport plate")
    groups = read("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift")
    require("BUILD123_COMMON_GROUPS_SURFACE1" in groups, "Common Groups surface missing")
    description = read("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/ListItems/PeerInfoScreenLabeledValueItem.swift")
    require("BUILD123_DESCRIPTION_EXPAND_GLASS1" in description, "description expansion glass missing")
    phone = read("submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift")
    require("BUILD123_SAFE_LOGIN_ALL_ACCOUNTS1" in phone, "Safe Login add-account visibility missing")
    require("ghostBaseSafeLoginNode.isHidden = true" not in phone, "Safe Login remains hidden")
    profile_items = read("submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift")
    require("BUILD123_REMOVE_PRIVATE_LINK_PROBE1" in profile_items, "private link probe removal missing")
    require("id: 9871001" not in profile_items, "experimental Get Link action remains")
    time_machine = read("submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift")
    require("BUILD123_TIME_MACHINE_UI1" in time_machine and "event.observedAtMs" in time_machine, "dated Time Machine UI missing")

    print("[Build123 release verify] GREEN")


if __name__ == "__main__":
    main()
