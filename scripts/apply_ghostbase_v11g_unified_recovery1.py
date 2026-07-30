#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

SOURCE_ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
)).resolve()
OFFICIAL_ROOT = Path(os.environ.get(
    "GHOSTBASE_OFFICIAL_ROOT",
    "/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official"
)).resolve()

SCRIPT_DIR = Path(__file__).resolve().parent
PAYLOAD_ROOT = Path(os.environ.get(
    "GHOSTBASE_V11G_PAYLOAD_ROOT",
    str(SCRIPT_DIR / "ghostbase_v11g_unified_recovery1_payload")
)).resolve()

PEER_SCREEN_REL = Path(
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
)
PANE_NODE_REL = Path(
    "submodules/TelegramUI/Components/PeerInfo/PeerInfoPaneNode/Sources/PeerInfoPaneNode.swift"
)
SETTINGS_REL = Path(
    "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
)
ACCOUNT_STATE_REL = Path(
    "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift"
)
UPDATE_PEERS_REL = Path(
    "submodules/TelegramCore/Sources/UpdatePeers.swift"
)


def fail(message: str) -> None:
    raise SystemExit(f"[V11G UNIFIED RECOVERY] {message}")


def require_text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def payload(name: str) -> str:
    return require_text(PAYLOAD_ROOT / name)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def official_bytes(relative: Path) -> bytes:
    external = OFFICIAL_ROOT / relative
    if external.is_file():
        return external.read_bytes()
    try:
        return subprocess.check_output(
            ["git", "-C", str(SOURCE_ROOT), "show", f"HEAD:{relative.as_posix()}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        fail(f"official reference unavailable for {relative}: {detail}")


def official_text(relative: Path) -> str:
    return official_bytes(relative).decode("utf-8")


def write(relative: Path, text: str) -> None:
    path = SOURCE_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


BACKGROUND_SWIFT = payload("GhostBaseProfileFullscreenBackground.swift")
REPORT_PANE_SWIFT = payload("GhostBaseProfileReportPaneNode.swift")
PRESENCE_HELPER = payload("PresenceHelper.swift.fragment")
ACCOUNT_RUNTIME = payload("AccountRuntime.swift.fragment")
GLOBAL_DELETE_BLOCK = payload("GlobalDelete.swift.fragment")
LOCAL_DELETE_BLOCK = payload("LocalDelete.swift.fragment")
EDIT_BLOCK = payload("EditMessage.swift.fragment")


# ---------------------------------------------------------------------------
# 1. Fullscreen profile background and stock geometry/decorations.
# ---------------------------------------------------------------------------
header_rel = PEER_SCREEN_REL / "PeerInfoHeaderNode.swift"
screen_rel = PEER_SCREEN_REL / "PeerInfoScreen.swift"
section_rel = PEER_SCREEN_REL / "PeerInfoScreenItemSectionContainerNode.swift"
profile_rel = PEER_SCREEN_REL / "PeerInfoProfileItems.swift"
pane_container_rel = PEER_SCREEN_REL / "PeerInfoPaneContainerNode.swift"
data_rel = PEER_SCREEN_REL / "PeerInfoData.swift"
background_rel = PEER_SCREEN_REL / "GhostBaseProfileFullscreenBackground.swift"
report_pane_rel = PEER_SCREEN_REL / "GhostBaseProfileReportPaneNode.swift"

header = official_text(header_rel)
header = replace_once(
    header,
    "    private var context: AccountContext\n",
    "    private var context: AccountContext\n"
    "    // MARK: GhostBase v1.1G PREMIUMDECORATIONS1\n"
    "    private let ghostBaseProfileGlassSettings: GhostBaseProfileBlurSettings?\n",
    "header settings property",
)
header = replace_once(
    header,
    "        self.context = context\n",
    "        self.context = context\n"
    "        self.ghostBaseProfileGlassSettings = isSettings ? nil : GhostBaseProfileGlassRuntime.loadSettings()\n",
    "header settings init",
)
header = replace_once(
    header,
    "        if let backgroundCoverView = self.backgroundCover.view as? PeerInfoCoverComponent.View {\n",
    "        if let backgroundCoverView = self.backgroundCover.view as? PeerInfoCoverComponent.View {\n"
    "            // Keep PeerInfoCoverComponent alive so Premium emoji/status, patterns,\n"
    "            // gifts decorations and badges remain above the fullscreen background.\n"
    "            backgroundCoverView.alpha = GhostBaseProfileGlassRuntime.shouldBlendStockCover(\n"
    "                settings: self.ghostBaseProfileGlassSettings,\n"
    "                peer: peer,\n"
    "                cachedData: cachedData,\n"
    "                presentationData: presentationData,\n"
    "                isSettings: isSettings\n"
    "            ) ? 0.88 : 1.0\n",
    "header stock cover blend",
)
write(header_rel, header)

screen = official_text(screen_rel)
screen = replace_once(
    screen,
    "enum PeerInfoSettingsSection {\n",
    "enum PeerInfoSettingsSection {\n    case ghostbase\n",
    "settings route",
)
screen = replace_once(
    screen,
    "    let paneContainerNode: PeerInfoPaneContainerNode\n",
    "    let paneContainerNode: PeerInfoPaneContainerNode\n"
    "    // MARK: GhostBase v1.1G PROFILEFULLSCREEN1\n"
    "    private let ghostBaseProfileBackgroundView: GhostBaseProfileBackgroundView?\n"
    "    private let ghostBaseProfileMetricsSettings: GhostBaseProfileMetricsSettings\n",
    "screen properties",
)
screen = replace_once(
    screen,
    "        self.sharedMediaFromForumTopic = sharedMediaFromForumTopic\n        \n        self.scrollNode = ASScrollNode()\n",
    "        self.sharedMediaFromForumTopic = sharedMediaFromForumTopic\n"
    "        self.ghostBaseProfileMetricsSettings = GhostBaseProfileMetricsSettings.load()\n"
    "        if !isSettings, let settings = GhostBaseProfileGlassRuntime.loadSettings() {\n"
    "            self.ghostBaseProfileBackgroundView = GhostBaseProfileBackgroundView(\n"
    "                context: context,\n"
    "                settings: settings\n"
    "            )\n"
    "        } else {\n"
    "            self.ghostBaseProfileBackgroundView = nil\n"
    "        }\n"
    "        \n        self.scrollNode = ASScrollNode()\n",
    "screen optional background init",
)
screen = replace_once(
    screen,
    "        super.init()\n        \n        self.paneContainerNode.parentController = controller\n",
    "        super.init()\n"
    "        if let ghostBaseProfileBackgroundView = self.ghostBaseProfileBackgroundView {\n"
    "            self.view.insertSubview(ghostBaseProfileBackgroundView, at: 0)\n"
    "        }\n"
    "        \n        self.paneContainerNode.parentController = controller\n",
    "screen background ownership",
)
screen = replace_once(
    screen,
    "        self.paneContainerNode = PeerInfoPaneContainerNode(context: context, updatedPresentationData: controller.updatedPresentationData, peerId: peerId, chatLocation: chatLocation, sharedMediaFromForumTopic: sharedMediaFromForumTopic, chatLocationContextHolder: chatLocationContextHolder, isMediaOnly: self.isMediaOnly, initialPaneKey: initialPaneKey, initialStoryFolderId: switchToStoryFolder, initialGiftCollectionId: switchToGiftCollection, switchToMediaTarget: switchToMediaTarget)\n",
    "        self.paneContainerNode = PeerInfoPaneContainerNode(context: context, updatedPresentationData: controller.updatedPresentationData, peerId: peerId, chatLocation: chatLocation, sharedMediaFromForumTopic: sharedMediaFromForumTopic, chatLocationContextHolder: chatLocationContextHolder, isMediaOnly: self.isMediaOnly, initialPaneKey: initialPaneKey, initialStoryFolderId: switchToStoryFolder, initialGiftCollectionId: switchToGiftCollection, switchToMediaTarget: switchToMediaTarget, ghostBaseGlassEnabled: self.ghostBaseProfileBackgroundView != nil)\n",
    "pane container glass state",
)
screen = replace_once(
    screen,
    "        self.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor\n",
    "        self.backgroundColor = self.presentationData.theme.list.blocksBackgroundColor\n"
    "        if self.ghostBaseProfileBackgroundView != nil {\n"
    "            self.backgroundColor = .clear\n"
    "            self.scrollNode.backgroundColor = .clear\n"
    "            self.scrollNode.view.backgroundColor = .clear\n"
    "            self.paneContainerNode.backgroundColor = .clear\n"
    "        }\n",
    "screen transparent surfaces",
)
screen = replace_once(
    screen,
    "        self.data = data\n",
    "        self.data = data\n"
    "        if !self.isSettings, let peer = data.peer, case .user = peer {\n"
    "            // Bounded asynchronous observation; no JSON or file I/O here.\n"
    "            ghostBaseRecordObservedProfileV11G(\n"
    "                accountPeerId: self.context.account.peerId,\n"
    "                peer: peer,\n"
    "                cachedData: data.cachedData\n"
    "            )\n"
    "            ghostBaseRecordPersonalChannelObservationV11G(\n"
    "                accountPeerId: self.context.account.peerId,\n"
    "                targetPeerId: peer.id,\n"
    "                personalChannel: data.personalChannel\n"
    "            )\n"
    "        }\n",
    "bounded profile observation",
)
screen = replace_once(
    screen,
    "        self.validLayout = (layout, navigationHeight)\n        \n        self.headerNode.customNavigationContentNode",
    "        self.validLayout = (layout, navigationHeight)\n"
    "        if let ghostBaseProfileBackgroundView = self.ghostBaseProfileBackgroundView {\n"
    "            transition.updateFrame(\n"
    "                view: ghostBaseProfileBackgroundView,\n"
    "                frame: CGRect(origin: .zero, size: layout.size)\n"
    "            )\n"
    "            ghostBaseProfileBackgroundView.update(\n"
    "                peer: self.data?.peer,\n"
    "                cachedData: self.data?.cachedData,\n"
    "                presentationData: self.presentationData,\n"
    "                isSettings: self.isSettings\n"
    "            )\n"
    "        }\n"
    "        \n        self.headerNode.customNavigationContentNode",
    "screen full frame update",
)
screen = replace_once(
    screen,
    " : infoItems(data: self.data, context: self.context, presentationData: self.presentationData, interaction: self.interaction, reactionSourceMessageId: self.reactionSourceMessageId, canDeleteReaction: self.canDeleteReaction, callMessages: self.callMessages, chatLocation: self.chatLocation, isOpenedFromChat: self.isOpenedFromChat, isMyProfile: self.isMyProfile)",
    " : infoItems(data: self.data, context: self.context, presentationData: self.presentationData, interaction: self.interaction, reactionSourceMessageId: self.reactionSourceMessageId, canDeleteReaction: self.canDeleteReaction, callMessages: self.callMessages, chatLocation: self.chatLocation, isOpenedFromChat: self.isOpenedFromChat, isMyProfile: self.isMyProfile, ghostBaseMetricsSettings: self.ghostBaseProfileMetricsSettings)",
    "metrics call",
)
screen = screen.replace(
    "sectionNode = PeerInfoScreenItemSectionContainerNode()",
    "sectionNode = PeerInfoScreenItemSectionContainerNode(ghostBaseGlassEnabled: self.ghostBaseProfileBackgroundView != nil)",
)
if screen.count("PeerInfoScreenItemSectionContainerNode(ghostBaseGlassEnabled:") != 2:
    fail("screen section constructor count is not two")
screen = replace_once(
    screen,
    "    private func updateBackgroundColor() {\n        let color: UIColor\n",
    "    private func updateBackgroundColor() {\n"
    "        if self.ghostBaseProfileBackgroundView != nil {\n"
    "            self.backgroundColor = .clear\n"
    "            return\n"
    "        }\n"
    "        let color: UIColor\n",
    "screen background fallback",
)
write(screen_rel, screen)

section = official_text(section_rel)
section = replace_once(
    section,
    "final class PeerInfoScreenItemSectionContainerNode: ASDisplayNode {\n",
    "final class PeerInfoScreenItemSectionContainerNode: ASDisplayNode {\n"
    "    private let ghostBaseGlassEnabled: Bool\n",
    "section glass property",
)
section = replace_once(
    section,
    "    override init() {\n        self.backgroundNode = ASDisplayNode()\n",
    "    init(ghostBaseGlassEnabled: Bool = false) {\n"
    "        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled\n"
    "        self.backgroundNode = ASDisplayNode()\n",
    "section init",
)
section = replace_once(
    section,
    "        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n"
    "        self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n"
    "        self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n",
    "        if self.ghostBaseGlassEnabled {\n"
    "            let alpha: CGFloat = presentationData.theme.overallDarkAppearance ? 0.36 : 0.56\n"
    "            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor.withAlphaComponent(alpha)\n"
    "            self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor.withAlphaComponent(0.28)\n"
    "            self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor.withAlphaComponent(0.28)\n"
    "        } else {\n"
    "            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n"
    "            self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n"
    "            self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n"
    "        }\n",
    "section translucent material",
)
write(section_rel, section)
write(background_rel, BACKGROUND_SWIFT)

# ---------------------------------------------------------------------------
# 2. Compact ID / DC / registration section, loaded once per screen.
# ---------------------------------------------------------------------------
profile = require_text(SOURCE_ROOT / profile_rel)
if "MARK: GhostBase v1.1G PROFILEMETRICS1" not in profile:
    settings_struct = '''
// MARK: GhostBase v1.1G PROFILEMETRICS1
struct GhostBaseProfileMetricsSettings {
    let enabled: Bool
    let showIds: Bool
    let showDCs: Bool
    let showRegistration: Bool
    let hideOwnPhone: Bool

    static func load() -> GhostBaseProfileMetricsSettings {
        let defaults = UserDefaults.standard
        return GhostBaseProfileMetricsSettings(
            enabled: defaults.object(forKey: "GhostBase.Profile.Enabled") as? Bool ?? true,
            showIds: defaults.object(forKey: "GhostBase.Profile.ShowIds") as? Bool ?? true,
            showDCs: defaults.object(forKey: "GhostBase.Profile.ShowDCs") as? Bool ?? true,
            showRegistration: defaults.object(forKey: "GhostBase.Profile.ShowRegistration") as? Bool ?? true,
            hideOwnPhone: defaults.object(forKey: "GhostBase.Appearance.HideOwnPhone") as? Bool ?? false
        )
    }
}

private enum GhostBaseProfileAuxiliaryStoreV11G {
    static let queue = DispatchQueue(
        label: "GhostBase.ProfileAuxiliaryStore.V11G",
        qos: .utility
    )

    static func set(_ value: String, forKey key: String) {
        self.queue.async {
            UserDefaults.standard.set(value, forKey: key)
        }
    }
}
'''
    profile = replace_once(
        profile,
        "private let enabledPrivateBioEntities: EnabledEntityTypes = [.internalUrl, .mention, .hashtag]\n",
        "private let enabledPrivateBioEntities: EnabledEntityTypes = [.internalUrl, .mention, .hashtag]\n"
        + settings_struct,
        "metrics settings struct",
    )
    profile = replace_once(
        profile,
        "    case peerInfo\n",
        "    case peerInfo\n    case ghostBaseMetrics\n",
        "metrics section",
    )
    profile = replace_once(
        profile,
        "    isOpenedFromChat: Bool,\n    isMyProfile: Bool\n)",
        "    isOpenedFromChat: Bool,\n"
        "    isMyProfile: Bool,\n"
        "    ghostBaseMetricsSettings: GhostBaseProfileMetricsSettings\n)",
        "metrics parameter",
    )
    metrics_block = '''
    // MARK: GhostBase v1.1G PROFILEMETRICS1 native compact section
    if ghostBaseMetricsSettings.enabled, let peer = data.peer {
        let headerId = 989990
        var itemId = 990000
        var metricItems: [PeerInfoScreenItem] = []

        if ghostBaseMetricsSettings.showIds {
            let idText: String
            if case let .channel(channel) = peer {
                idText = "-100" + String(channel.id.id._internalGetInt64Value())
            } else {
                idText = String(peer.id.id._internalGetInt64Value())
            }
            metricItems.append(PeerInfoScreenLabeledValueItem(
                id: itemId,
                label: "Telegram ID",
                text: idText,
                textColor: .primary,
                action: nil,
                longTapAction: nil,
                requestLayout: { _ in
                    interaction.requestLayout(false)
                }
            ))
            itemId += 1
        }

        if ghostBaseMetricsSettings.showDCs,
           let representation = peer.smallProfileImage,
           let resource = representation.resource as? CloudPeerPhotoSizeMediaResource {
            metricItems.append(PeerInfoScreenLabeledValueItem(
                id: itemId,
                label: "DC",
                text: String(resource.datacenterId),
                textColor: .primary,
                action: nil,
                longTapAction: nil,
                requestLayout: { _ in
                    interaction.requestLayout(false)
                }
            ))
            itemId += 1
        }

        if ghostBaseMetricsSettings.showRegistration,
           let cachedData = data.cachedData as? CachedUserData,
           let registrationDate = cachedData.peerStatusSettings?.registrationDate {
            let components = registrationDate.components(separatedBy: ".")
            if components.count == 2,
               let monthValue = Int32(components[0]),
               let yearValue = Int32(components[1]) {
                let dateText = stringForMonth(
                    strings: presentationData.strings,
                    month: monthValue - 1,
                    ofYear: yearValue - 1900
                )
                metricItems.append(PeerInfoScreenLabeledValueItem(
                    id: itemId,
                    label: "Дата регистрации",
                    text: dateText,
                    textColor: .primary,
                    action: nil,
                    longTapAction: nil,
                    requestLayout: { _ in
                        interaction.requestLayout(false)
                    }
                ))
            }
        }

        if !metricItems.isEmpty {
            items[.ghostBaseMetrics]!.append(
                PeerInfoScreenHeaderItem(
                    id: headerId,
                    text: "Сведения"
                )
            )
            items[.ghostBaseMetrics]!.append(contentsOf: metricItems)
        }
    }

'''
    profile = replace_once(
        profile,
        "    let bioContextAction:",
        metrics_block + "    let bioContextAction:",
        "metrics block",
    )
# Eliminate synchronous UserDefaults access from infoItems itself.
profile = profile.replace(
    '        let ghostBaseHideOwnPhone = (\n            UserDefaults.standard.object(\n                forKey: "GhostBase.Appearance.HideOwnPhone"\n            ) as? Bool\n        ) ?? false\n',
    "        let ghostBaseHideOwnPhone = ghostBaseMetricsSettings.hideOwnPhone\n",
)
profile = profile.replace(
    '                            UserDefaults.standard.set(\n                                ghostBaseInviteLink,\n                                forKey: ghostBaseInviteStatusKey\n                            )\n',
    '                            GhostBaseProfileAuxiliaryStoreV11G.set(\n                                ghostBaseInviteLink,\n                                forKey: ghostBaseInviteStatusKey\n                            )\n',
)
profile = profile.replace(
    '                            UserDefaults.standard.set(\n                                "nil",\n                                forKey: ghostBaseInviteStatusKey\n                            )\n',
    '                            GhostBaseProfileAuxiliaryStoreV11G.set(\n                                "nil",\n                                forKey: ghostBaseInviteStatusKey\n                            )\n',
)
write(profile_rel, profile)

# ---------------------------------------------------------------------------
# 3. Native lazy PeerInfo panes.
# ---------------------------------------------------------------------------
pane_node = official_text(PANE_NODE_REL)
pane_node = replace_once(
    pane_node,
    "    case storyArchive\n",
    "    case storyArchive\n"
    "    // MARK: GhostBase v1.1G NATIVEPANES1\n"
    "    case ghostBaseProfileHistory\n"
    "    case ghostBasePresence\n"
    "    case ghostBaseGiftHistory\n"
    "    case ghostBasePersonalChannel\n",
    "pane keys",
)
write(PANE_NODE_REL, pane_node)

data = require_text(SOURCE_ROOT / data_rel)
if "MARK: GhostBase v1.1G NATIVEPANES1" not in data:
    pane_policy = '''
// MARK: GhostBase v1.1G NATIVEPANES1
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
}

'''
    data = replace_once(
        data,
        "final class PeerInfoScreenData {\n",
        pane_policy + "final class PeerInfoScreenData {\n",
        "pane policy",
    )
    data = replace_once(
        data,
        "        self.availablePanes = availablePanes\n",
        "        self.availablePanes = ghostBaseAppendingProfilePanes(\n"
        "            availablePanes,\n"
        "            peer: peer,\n"
        "            personalChannel: personalChannel\n"
        "        )\n",
        "available panes assignment",
    )
write(data_rel, data)

pane_container = require_text(SOURCE_ROOT / pane_container_rel)
if "GhostBaseProfileReportPaneNode(" not in pane_container:
    creation = '''        case .ghostBaseProfileHistory,
             .ghostBasePresence,
             .ghostBaseGiftHistory,
             .ghostBasePersonalChannel:
            let kind: GhostBaseProfileReportPaneNode.Kind
            switch key {
            case .ghostBaseProfileHistory:
                kind = .profileHistory
            case .ghostBasePresence:
                kind = .presence
            case .ghostBaseGiftHistory:
                kind = .giftHistory
            case .ghostBasePersonalChannel:
                kind = .personalChannel
            default:
                preconditionFailure()
            }
            paneNode = GhostBaseProfileReportPaneNode(
                context: context,
                peerId: peerId,
                kind: kind,
                personalChannel: data.personalChannel
            )
'''
    pane_container = replace_once(
        pane_container,
        "        case .polls:\n            paneNode = PeerInfoChatPaneNode",
        creation + "        case .polls:\n            paneNode = PeerInfoChatPaneNode",
        "pane creation",
    )
    labels = '''                    case .ghostBaseProfileHistory:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "История", entities: [], enableAnimations: false))
                    case .ghostBasePresence:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Присутствие", entities: [], enableAnimations: false))
                    case .ghostBaseGiftHistory:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Подарки · история", entities: [], enableAnimations: false))
                    case .ghostBasePersonalChannel:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Канал", entities: [], enableAnimations: false))
'''
    pane_container = replace_once(
        pane_container,
        "                    case .polls:\n                        content = .title",
        labels + "                    case .polls:\n                        content = .title",
        "pane labels",
    )
if "MARK: GhostBase v1.1G PANEGLASS1" not in pane_container:
    pane_container = replace_once(
        pane_container,
        "final class PeerInfoPaneContainerNode: ASDisplayNode, ASGestureRecognizerDelegate {\n    private let context: AccountContext\n",
        "final class PeerInfoPaneContainerNode: ASDisplayNode, ASGestureRecognizerDelegate {\n"
        "    // MARK: GhostBase v1.1G PANEGLASS1\n"
        "    private let ghostBaseGlassEnabled: Bool\n"
        "    private let context: AccountContext\n",
        "pane glass property",
    )
    pane_container = replace_once(
        pane_container,
        "    init(context: AccountContext, updatedPresentationData: (initial: PresentationData, signal: Signal<PresentationData, NoError>)?, peerId: EnginePeer.Id, chatLocation: ChatLocation, sharedMediaFromForumTopic: (EnginePeer.Id, Int64)?, chatLocationContextHolder: Atomic<ChatLocationContextHolder?>, isMediaOnly: Bool, initialPaneKey: PeerInfoPaneKey?, initialStoryFolderId: Int64?, initialGiftCollectionId: Int64?, switchToMediaTarget: PeerInfoSwitchToMediaTarget?) {\n        self.context = context\n",
        "    init(context: AccountContext, updatedPresentationData: (initial: PresentationData, signal: Signal<PresentationData, NoError>)?, peerId: EnginePeer.Id, chatLocation: ChatLocation, sharedMediaFromForumTopic: (EnginePeer.Id, Int64)?, chatLocationContextHolder: Atomic<ChatLocationContextHolder?>, isMediaOnly: Bool, initialPaneKey: PeerInfoPaneKey?, initialStoryFolderId: Int64?, initialGiftCollectionId: Int64?, switchToMediaTarget: PeerInfoSwitchToMediaTarget?, ghostBaseGlassEnabled: Bool = false) {\n"
        "        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled\n"
        "        self.context = context\n",
        "pane glass init",
    )
    pane_container = replace_once(
        pane_container,
        "        self.backgroundColor = backgroundColor\n",
        "        if self.ghostBaseGlassEnabled {\n"
        "            self.backgroundColor = .clear\n"
        "        } else {\n"
        "            self.backgroundColor = backgroundColor\n"
        "        }\n",
        "pane glass background",
    )

write(pane_container_rel, pane_container)
write(report_pane_rel, REPORT_PANE_SWIFT)

# ---------------------------------------------------------------------------
# 4. Bounded async presence history; no sync JSON writes in update hot path.
# ---------------------------------------------------------------------------
update_peers = require_text(SOURCE_ROOT / UPDATE_PEERS_REL)
presence_start = -1
for marker in (
    "// MARK: GhostBase v1.1G PRESENCEBOUNDED1",
    "// MARK: GhostBase v1.1B PRESENCEGLOBAL2 transition archive",
    "// MARK: GhostBase v1.0ZH PRESENCEHISTORY1",
):
    index = update_peers.find(marker)
    if index >= 0:
        presence_start = index
        break
presence_end = update_peers.find(
    "func isPeerHiddenByCollapsedCommunity",
    max(0, presence_start),
)
if presence_end < 0:
    fail("presence insertion boundary not found")
if presence_start >= 0:
    update_peers = (
        update_peers[:presence_start]
        + PRESENCE_HELPER
        + "\n"
        + update_peers[presence_end:]
    )
else:
    # The local materialized tree may not have run the historical presence
    # patchers, while CI does. Support both states without requiring them.
    update_peers = (
        update_peers[:presence_end]
        + PRESENCE_HELPER
        + "\n"
        + update_peers[presence_end:]
    )

if update_peers.count("ghostBaseRegisterKnownUser(") < 2:
    update_peers = replace_once(
        update_peers,
        "        if let telegramUser = TelegramUser.merge(transaction.getPeer(user.peerId) as? TelegramUser, rhs: user) {\n            parsedPeers.append(telegramUser)\n",
        "        if let telegramUser = TelegramUser.merge(transaction.getPeer(user.peerId) as? TelegramUser, rhs: user) {\n"
        "            ghostBaseRegisterKnownUser(\n"
        "                accountPeerId: accountPeerId,\n"
        "                user: telegramUser\n"
        "            )\n"
        "            parsedPeers.append(telegramUser)\n",
        "known-user call site",
    )

if update_peers.count("ghostBaseRecordPresence(") < 3:
    update_peers = replace_once(
        update_peers,
        "        guard let presence = TelegramUserPresence(apiUser: user) else {\n            continue\n        }\n        switch presence.status {\n",
        "        guard let presence = TelegramUserPresence(apiUser: user) else {\n"
        "            continue\n"
        "        }\n"
        "        ghostBaseRecordPresence(\n"
        "            accountPeerId: accountPeerId,\n"
        "            peerId: peerId,\n"
        "            presence: presence\n"
        "        )\n"
        "        switch presence.status {\n",
        "presence Api.User call site",
    )
    update_peers = replace_once(
        update_peers,
        "    for (peerId, status) in peerPresences {\n        let presence = TelegramUserPresence(apiStatus: status.status)\n        switch presence.status {\n",
        "    for (peerId, status) in peerPresences {\n"
        "        let presence = TelegramUserPresence(apiStatus: status.status)\n"
        "        ghostBaseRecordPresence(\n"
        "            accountPeerId: accountPeerId,\n"
        "            peerId: peerId,\n"
        "            presence: presence\n"
        "        )\n"
        "        switch presence.status {\n",
        "presence clean call site",
    )

if update_peers.count("ghostBaseRecordPresence(") < 3:
    fail("presence call sites were lost")
if update_peers.count("ghostBaseRegisterKnownUser(") < 2:
    fail("known-user call sites were lost")
write(UPDATE_PEERS_REL, update_peers)

# ---------------------------------------------------------------------------
# 5. Remove runaway delete probes; preserve deleted/edit functionality.
# ---------------------------------------------------------------------------

account_state = official_text(ACCOUNT_STATE_REL)

# MARK: GhostBase V11G TelegramCore compatibility
#
# V10ZC and V11E are applied before V11G. V11G intentionally restores
# AccountStateManagementUtils.swift from Official, so the exact Bot Account
# helper and BOTSHADOW1 state-builder extensions have to be materialized again.
if "GhostBase v1.0ZC Bot account helper" not in account_state:
    helper_anchor = "private func peerIdsFromDifference(_ difference: Api.updates.Difference) -> Set<PeerId> {"
    helper = """// MARK: GhostBase v1.0ZC Bot account helper
func ghostBaseIsBotAccount(_ accountPeerId: PeerId) -> Bool {
    return UserDefaults.standard.bool(
        forKey: "GhostBase.BotAccount.\\(accountPeerId.toInt64())"
    )
}

"""
    account_state = replace_once(
        account_state,
        helper_anchor,
        helper + helper_anchor,
        "V10ZC bot account helper",
    )

if "GhostBase v1.1E BOTSHADOW1 state override" not in account_state:
    old_peer_sig = "func initialStateWithPeerIds(_ transaction: Transaction, peerIds: Set<PeerId>, activeChannelIds: Set<PeerId>, referencedReplyMessageIds: ReferencedReplyMessageIds, referencedGeneralMessageIds: Set<MessageId>, peerIdsRequiringLocalChatState: Set<PeerId>, locallyGeneratedMessageTimestamps: [PeerId: [(MessageId.Namespace, Int32)]], storedStories: [StoryId: UpdatesStoredStory]) -> AccountMutableState {"
    new_peer_sig = "func initialStateWithPeerIds(_ transaction: Transaction, peerIds: Set<PeerId>, activeChannelIds: Set<PeerId>, referencedReplyMessageIds: ReferencedReplyMessageIds, referencedGeneralMessageIds: Set<MessageId>, peerIdsRequiringLocalChatState: Set<PeerId>, locallyGeneratedMessageTimestamps: [PeerId: [(MessageId.Namespace, Int32)]], storedStories: [StoryId: UpdatesStoredStory], overrideState: AuthorizedAccountState.State? = nil, resetChannelStates: Bool = false) -> AccountMutableState { // MARK: GhostBase v1.1E BOTSHADOW1 state override"
    account_state = replace_once(
        account_state,
        old_peer_sig,
        new_peer_sig,
        "BOTSHADOW1 initialStateWithPeerIds signature",
    )

    old_channel = """        if peerId.namespace == Namespaces.Peer.CloudChannel {
            if let channelState = transaction.getPeerChatState(peerId) as? ChannelState {
                channelStates[peerId] = AccountStateChannelState(pts: channelState.pts)
            }
"""
    new_channel = """        if peerId.namespace == Namespaces.Peer.CloudChannel {
            if resetChannelStates {
                channelStates[peerId] = AccountStateChannelState(pts: 0)
            } else if let channelState = transaction.getPeerChatState(peerId) as? ChannelState {
                channelStates[peerId] = AccountStateChannelState(pts: channelState.pts)
            }
"""
    account_state = replace_once(
        account_state,
        old_channel,
        new_channel,
        "BOTSHADOW1 channel-state override",
    )

    old_state = "    let state = AccountMutableState(initialState: AccountInitialState(state: (transaction.getState() as? AuthorizedAccountState)!.state!, peerIds: peerIds,"
    new_state = "    let state = AccountMutableState(initialState: AccountInitialState(state: overrideState ?? (transaction.getState() as? AuthorizedAccountState)!.state!, peerIds: peerIds,"
    account_state = replace_once(
        account_state,
        old_state,
        new_state,
        "BOTSHADOW1 mutable-state override",
    )

    old_diff_sig = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference) -> Signal<AccountMutableState, NoError> {"
    new_diff_sig = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference, overrideState: AuthorizedAccountState.State? = nil, resetChannelStates: Bool = false) -> Signal<AccountMutableState, NoError> {"
    old_diff_signature = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference) -> Signal<AccountMutableState, NoError> {"
    new_diff_signature = "func initialStateWithDifference(postbox: Postbox, difference: Api.updates.Difference, overrideState: AuthorizedAccountState.State? = nil, resetChannelStates: Bool = false) -> Signal<AccountMutableState, NoError> {"

    if old_diff_signature in account_state:
        account_state = account_state.replace(
            old_diff_signature,
            new_diff_signature,
            1,
        )
    elif new_diff_signature not in account_state:
        raise SystemExit(
            "[V11G] initialStateWithDifference signature unavailable"
        )

    old_diff_forwarding = "        return initialStateWithPeerIds(transaction, peerIds: peerIds, activeChannelIds: activeChannelIds, referencedReplyMessageIds: associatedMessageIds.replyIds, referencedGeneralMessageIds: associatedMessageIds.generalIds, peerIdsRequiringLocalChatState: peerIdsRequiringLocalChatState, locallyGeneratedMessageTimestamps: locallyGeneratedMessageTimestampsFromDifference(difference), storedStories: associatedStoredStories(difference))"
    new_diff_forwarding = "        return initialStateWithPeerIds(transaction, peerIds: peerIds, activeChannelIds: activeChannelIds, referencedReplyMessageIds: associatedMessageIds.replyIds, referencedGeneralMessageIds: associatedMessageIds.generalIds, peerIdsRequiringLocalChatState: peerIdsRequiringLocalChatState, locallyGeneratedMessageTimestamps: locallyGeneratedMessageTimestampsFromDifference(difference), storedStories: associatedStoredStories(difference), overrideState: overrideState, resetChannelStates: resetChannelStates)"

    if old_diff_forwarding in account_state:
        account_state = account_state.replace(
            old_diff_forwarding,
            new_diff_forwarding,
            1,
        )
    elif new_diff_forwarding not in account_state:
        raise SystemExit(
            "[V11G] initialStateWithDifference forwarding unavailable"
        )

    old_final_sig = "func finalStateWithDifference(accountPeerId: PeerId, postbox: Postbox, network: Network, state: AccountMutableState, difference: Api.updates.Difference, asyncResetChannels: (([(peer: Peer, pts: Int32?)]) -> Void)?) -> Signal<AccountFinalState, NoError> {"
    new_final_sig = "func finalStateWithDifference(accountPeerId: PeerId, postbox: Postbox, network: Network, state: AccountMutableState, difference: Api.updates.Difference, asyncResetChannels: (([(peer: Peer, pts: Int32?)]) -> Void)?, shouldResetChannels: Bool = true) -> Signal<AccountFinalState, NoError> {"
    account_state = replace_once(
        account_state,
        old_final_sig,
        new_final_sig,
        "BOTSHADOW1 finalStateWithDifference signature",
    )

    old_final_return = "    return finalStateWithUpdates(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, updates: updates, shouldPoll: false, missingUpdates: false, shouldResetChannels: true, updatesDate: nil, asyncResetChannels: asyncResetChannels)"
    new_final_return = "    return finalStateWithUpdates(accountPeerId: accountPeerId, postbox: postbox, network: network, state: updatedState, updates: updates, shouldPoll: false, missingUpdates: false, shouldResetChannels: shouldResetChannels, updatesDate: nil, asyncResetChannels: asyncResetChannels)"
    account_state = replace_once(
        account_state,
        old_final_return,
        new_final_return,
        "BOTSHADOW1 final-state reset policy",
    )
account_state = replace_once(
    account_state,
    "import EncryptionProvider\n",
    "import EncryptionProvider\n\n" + ACCOUNT_RUNTIME,
    "account diagnostics runtime",
)
global_start = account_state.find(
    "            case let .DeleteMessagesWithGlobalIds(ids):"
)
local_start = account_state.find(
    "            case let .DeleteMessages(ids):",
    global_start,
)
min_start = account_state.find(
    "            case let .UpdateMinAvailableMessage(id):",
    local_start,
)
edit_start = account_state.find(
    "            case let .EditMessage(id, message):",
    min_start,
)
poll_start = account_state.find(
    "            case let .UpdateMessagePoll",
    edit_start,
)
if min(global_start, local_start, min_start, edit_start, poll_start) < 0:
    fail("official delete/edit case anchors missing")
account_state = (
    account_state[:global_start]
    + GLOBAL_DELETE_BLOCK
    + LOCAL_DELETE_BLOCK
    + account_state[min_start:edit_start]
    + EDIT_BLOCK
    + account_state[poll_start:]
)
write(ACCOUNT_STATE_REL, account_state)

# ---------------------------------------------------------------------------
# 6. Settings: restore profile metrics toggles and bounded Debug/Research.
# ---------------------------------------------------------------------------
settings = require_text(SOURCE_ROOT / SETTINGS_REL)

if 'static let profileEnabled = "GhostBase.Profile.Enabled"' not in settings:
    settings = replace_once(
        settings,
        "private enum GhostBaseKey {\n",
        "private enum GhostBaseKey {\n"
        "    // MARK: GhostBase v1.1G PROFILEMETRICS1\n"
        "    static let profileEnabled = \"GhostBase.Profile.Enabled\"\n"
        "    static let showIds = \"GhostBase.Profile.ShowIds\"\n"
        "    static let showDCs = \"GhostBase.Profile.ShowDCs\"\n"
        "    static let showRegistration = \"GhostBase.Profile.ShowRegistration\"\n\n",
        "settings metric keys",
    )

if 'static let glassEnabled = "GhostBase.Glass.Enabled"' not in settings:
    settings = replace_once(
        settings,
        '    static let showRegistration = "GhostBase.Profile.ShowRegistration"\n',
        '    static let showRegistration = "GhostBase.Profile.ShowRegistration"\n'
        '    // MARK: GhostBase v1.1G PROFILEBLURSETTINGS2\n'
        '    static let glassEnabled = "GhostBase.Glass.Enabled"\n'
        '    static let profileAvatarBlur = "GhostBase.ProfileBlur.Avatar"\n'
        '    static let profileBlurTint = "GhostBase.ProfileBlur.Tint"\n'
        '    static let profileBlurReduced = "GhostBase.ProfileBlur.Reduced"\n',
        "settings blur keys",
    )

if "    var profileEnabled: Bool\n" not in settings:
    settings = replace_once(
        settings,
        "struct GhostBaseSettingsState: Equatable {\n",
        "struct GhostBaseSettingsState: Equatable {\n"
        "    var profileEnabled: Bool\n"
        "    var showIds: Bool\n"
        "    var showDCs: Bool\n"
        "    var showRegistration: Bool\n"
        "    var glassEnabled: Bool\n"
        "    var profileAvatarBlur: Bool\n"
        "    var profileBlurTint: Bool\n"
        "    var profileBlurReduced: Bool\n\n",
        "settings metric and blur state",
    )

if "            profileEnabled: ghostBaseBool(" not in settings:
    settings = replace_once(
        settings,
        "        return GhostBaseSettingsState(\n",
        "        return GhostBaseSettingsState(\n"
        "            profileEnabled: ghostBaseBool(GhostBaseKey.profileEnabled, defaultValue: true),\n"
        "            showIds: ghostBaseBool(GhostBaseKey.showIds, defaultValue: true),\n"
        "            showDCs: ghostBaseBool(GhostBaseKey.showDCs, defaultValue: true),\n"
        "            showRegistration: ghostBaseBool(GhostBaseKey.showRegistration, defaultValue: true),\n"
        "            glassEnabled: ghostBaseBool(GhostBaseKey.glassEnabled, defaultValue: true),\n"
        "            profileAvatarBlur: ghostBaseBool(GhostBaseKey.profileAvatarBlur, defaultValue: true),\n"
        "            profileBlurTint: ghostBaseBool(GhostBaseKey.profileBlurTint, defaultValue: true),\n"
        "            profileBlurReduced: ghostBaseBool(GhostBaseKey.profileBlurReduced, defaultValue: false),\n\n",
        "settings metric and blur load",
    )

if "    var glassEnabled: Bool\n" not in settings:
    settings = replace_once(
        settings,
        "    var showRegistration: Bool\n\n",
        "    var showRegistration: Bool\n"
        "    var glassEnabled: Bool\n"
        "    var profileAvatarBlur: Bool\n"
        "    var profileBlurTint: Bool\n"
        "    var profileBlurReduced: Bool\n\n",
        "settings blur state",
    )

if "            glassEnabled: ghostBaseBool(" not in settings:
    settings = replace_once(
        settings,
        "            showRegistration: ghostBaseBool(GhostBaseKey.showRegistration, defaultValue: true),\n",
        "            showRegistration: ghostBaseBool(GhostBaseKey.showRegistration, defaultValue: true),\n"
        "            glassEnabled: ghostBaseBool(GhostBaseKey.glassEnabled, defaultValue: true),\n"
        "            profileAvatarBlur: ghostBaseBool(GhostBaseKey.profileAvatarBlur, defaultValue: true),\n"
        "            profileBlurTint: ghostBaseBool(GhostBaseKey.profileBlurTint, defaultValue: true),\n"
        "            profileBlurReduced: ghostBaseBool(GhostBaseKey.profileBlurReduced, defaultValue: false),\n",
        "settings blur load",
    )

if "UserDefaults.standard.set(self.profileEnabled" not in settings:
    settings = replace_once(
        settings,
        "    func save() {\n",
        "    func save() {\n"
        "        UserDefaults.standard.set(self.profileEnabled, forKey: GhostBaseKey.profileEnabled)\n"
        "        UserDefaults.standard.set(self.showIds, forKey: GhostBaseKey.showIds)\n"
        "        UserDefaults.standard.set(self.showDCs, forKey: GhostBaseKey.showDCs)\n"
        "        UserDefaults.standard.set(self.showRegistration, forKey: GhostBaseKey.showRegistration)\n"
        "        UserDefaults.standard.set(self.glassEnabled, forKey: GhostBaseKey.glassEnabled)\n"
        "        UserDefaults.standard.set(self.profileAvatarBlur, forKey: GhostBaseKey.profileAvatarBlur)\n"
        "        UserDefaults.standard.set(self.profileBlurTint, forKey: GhostBaseKey.profileBlurTint)\n"
        "        UserDefaults.standard.set(self.profileBlurReduced, forKey: GhostBaseKey.profileBlurReduced)\n\n",
        "settings metric and blur save",
    )

if "UserDefaults.standard.set(self.glassEnabled" not in settings:
    settings = replace_once(
        settings,
        "        UserDefaults.standard.set(self.showRegistration, forKey: GhostBaseKey.showRegistration)\n",
        "        UserDefaults.standard.set(self.showRegistration, forKey: GhostBaseKey.showRegistration)\n"
        "        UserDefaults.standard.set(self.glassEnabled, forKey: GhostBaseKey.glassEnabled)\n"
        "        UserDefaults.standard.set(self.profileAvatarBlur, forKey: GhostBaseKey.profileAvatarBlur)\n"
        "        UserDefaults.standard.set(self.profileBlurTint, forKey: GhostBaseKey.profileBlurTint)\n"
        "        UserDefaults.standard.set(self.profileBlurReduced, forKey: GhostBaseKey.profileBlurReduced)\n",
        "settings blur save",
    )

home_start = settings.find("    if page == .home {\n")
home_end = settings.find("\n    if page == .ghostMode {\n", home_start)
if home_start < 0 or home_end < 0:
    fail("settings home page region missing")
home_page = '''    if page == .home {
        let balance = state.localStarsAmount.isEmpty
            ? "0"
            : state.localStarsAmount

        return [
            .header(0, "Сведения профиля"),
            .toggle(0, 1, GhostBaseKey.profileEnabled, "Показывать сведения", state.profileEnabled),
            .toggle(0, 2, GhostBaseKey.showIds, "Telegram ID", state.showIds),
            .toggle(0, 3, GhostBaseKey.showDCs, "DC аватара", state.showDCs),
            .toggle(0, 4, GhostBaseKey.showRegistration, "Дата регистрации", state.showRegistration),
            .header(1, "Основные функции"),
            .toggle(1, 5, GhostBaseKey.localStarsEnabled, "Локальный баланс Stars", state.localStarsEnabled),
            .input(1, 6, GhostBaseKey.localStarsAmount, "Баланс Stars", state.localStarsAmount),
            .info(1, "Текущий визуальный баланс: \\(balance) ⭐")
        ]
    }
'''
settings = settings[:home_start] + home_page + settings[home_end:]

appearance_start = settings.find("    if page == .appearance {\n")
appearance_end = settings.find("\n    if page == .about {\n", appearance_start)
if appearance_start < 0 or appearance_end < 0:
    fail("settings appearance page region missing")
appearance_page = '    if page == .appearance {\n        return [\n            .header(0, "Фон профиля"),\n            .toggle(0, 1, GhostBaseKey.glassEnabled, "Эффект фона профиля", state.glassEnabled),\n            .toggle(0, 2, GhostBaseKey.profileAvatarBlur, "Размытие аватара в профиле", state.profileAvatarBlur),\n            .toggle(0, 3, GhostBaseKey.profileBlurTint, "Цветовой tint", state.profileBlurTint),\n            .toggle(0, 4, GhostBaseKey.profileBlurReduced, "Облегчённое размытие", state.profileBlurReduced),\n            .info(0, "При выключенном главном тумблере профиль полностью использует штатный интерфейс Telegram."),\n            .header(1, "Интерфейс"),\n            .toggle(1, 5, GhostBaseKey.messageSeconds, "Показывать секунды в сообщениях", state.messageSeconds),\n            .toggle(1, 6, GhostBaseKey.hideOwnPhone, "Скрывать мой номер", state.hideOwnPhone),\n            .info(1, "Номер скрывается только локально в интерфейсе GhostBase.")\n        ]\n    }\n'
settings = settings[:appearance_start] + appearance_page + settings[appearance_end:]

if "case GhostBaseKey.glassEnabled:" not in settings:
    switch_anchor = "            case GhostBaseKey.saveDeleted:\n"
    blur_cases = '            case GhostBaseKey.glassEnabled:\n                updated.glassEnabled = value\n            case GhostBaseKey.profileAvatarBlur:\n                updated.profileAvatarBlur = value\n            case GhostBaseKey.profileBlurTint:\n                updated.profileBlurTint = value\n            case GhostBaseKey.profileBlurReduced:\n                updated.profileBlurReduced = value\n\n'
    settings = replace_once(
        settings,
        switch_anchor,
        blur_cases + switch_anchor,
        "settings blur switch",
    )

if "case GhostBaseKey.profileEnabled:" not in settings:
    switch_anchor = "            case GhostBaseKey.saveDeleted:\n"
    profile_switch = '''            case GhostBaseKey.profileEnabled:
                updated.profileEnabled = value
            case GhostBaseKey.showIds:
                updated.showIds = value
                if value {
                    updated.profileEnabled = true
                }
            case GhostBaseKey.showDCs:
                updated.showDCs = value
                if value {
                    updated.profileEnabled = true
                }
            case GhostBaseKey.showRegistration:
                updated.showRegistration = value
                if value {
                    updated.profileEnabled = true
                }

'''
    settings = replace_once(
        settings,
        switch_anchor,
        profile_switch + switch_anchor,
        "settings metric switch",
    )

debug_marker = "// MARK: GhostBase v1.1G BOUNDEDDEBUG1"
if debug_marker not in settings:
    about_start = settings.find("    if page == .about {\n")
    if about_start < 0:
        fail("settings about page missing")
    fallback_start = settings.find("\n    entries.append(", about_start)
    if fallback_start < 0:
        fail("settings fallback region missing")
    debug_page = '''
    // MARK: GhostBase v1.1G BOUNDEDDEBUG1
    if page == .debugResearch {
        let defaults = UserDefaults.standard
        let runtimeLines = defaults.stringArray(
            forKey: "GhostBase.Runtime.Diagnostics.V11G"
        ) ?? []
        let runtimeText = runtimeLines.suffix(80).joined(separator: "\\n")
        let presenceSummary = defaults.string(
            forKey: "GhostBase.Runtime.PresenceSummary.V11G"
        ) ?? "История присутствия пока пуста"
        let knownUsersSummary = defaults.string(
            forKey: "GhostBase.Runtime.KnownUsersSummary.V11G"
        ) ?? "Известные пользователи: нет данных"

        return [
            .header(0, "Runtime"),
            .info(0, presenceSummary),
            .info(0, knownUsersSummary),
            .header(1, "Последние события"),
            .info(1, runtimeText.isEmpty ? "Событий пока нет" : runtimeText),
            .info(
                1,
                "Буфер ограничен 200 строками. Сбор не запускается при открытии этой страницы."
            )
        ]
    }
'''
    settings = settings[:fallback_start] + debug_page + settings[fallback_start:]

if "    let profile = GhostBaseSettingsSection.profileMetrics.rawValue\n" not in settings:
    settings = replace_once(
        settings,
        "    let ghost = GhostBaseSettingsSection.ghostMode.rawValue\n",
        "    let profile = GhostBaseSettingsSection.profileMetrics.rawValue\n"
        "    let ghost = GhostBaseSettingsSection.ghostMode.rawValue\n",
        "settings legacy fallback profile section id",
    )
settings = re.sub(
    r"Version: v1\.[^\n]*",
    "Version: v1.1G-unified-recovery",
    settings,
)
settings = settings.replace(
    "Base: Official Telegram 12.8",
    "Base: Official Telegram 12.9.2",
)
settings = settings.replace(
    "Base: Official Telegram 12.7",
    "Base: Official Telegram 12.9.2",
)
write(SETTINGS_REL, settings)

print("[V11G] UNIFIEDRECOVERY1 applied")
print(f"[V11G] source={SOURCE_ROOT}")
print(f"[V11G] official={OFFICIAL_ROOT}")
