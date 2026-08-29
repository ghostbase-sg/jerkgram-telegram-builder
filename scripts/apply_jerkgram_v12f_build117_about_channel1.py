#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

SETTINGS = ROOT / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 About channel] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_strings(text):
    if (
        "case communityLoading" in text
        and "case communityUnavailable" in text
        and "case communityNoPosts" in text
        and "self.text(.communityLoading)" in text
        and '.communityLoading: "Loading channel…"' in text
        and '.communityLoading: "Загрузка канала…"' in text
    ):
        return text
    text = replace_once(
        text,
        "    case copyExtensionDiagnostics\n}",
        '''    case copyExtensionDiagnostics
    case communityLoading
    case communityUnavailable
    case communityNoPosts
}''',
        "Build117 string keys",
    )
    text = replace_once(
        text,
        "    public var copyExtensionDiagnostics: String { self.text(.copyExtensionDiagnostics) }",
        '''    public var copyExtensionDiagnostics: String { self.text(.copyExtensionDiagnostics) }
    public var communityLoading: String { self.text(.communityLoading) }
    public var communityUnavailable: String { self.text(.communityUnavailable) }
    public var communityNoPosts: String { self.text(.communityNoPosts) }''',
        "Build117 string accessors",
    )
    text = replace_once(
        text,
        '        .copyExtensionDiagnostics: "Copy Extension Diagnostics"\n',
        '''        .copyExtensionDiagnostics: "Copy Extension Diagnostics",
        .communityLoading: "Loading channel…",
        .communityUnavailable: "Channel information is temporarily unavailable",
        .communityNoPosts: "No posts yet"
''',
        "English About states",
    )
    return replace_once(
        text,
        '        .copyExtensionDiagnostics: "Копировать диагностику расширений"\n',
        '''        .copyExtensionDiagnostics: "Копировать диагностику расширений",
        .communityLoading: "Загрузка канала…",
        .communityUnavailable: "Информация о канале временно недоступна",
        .communityNoPosts: "Публикаций пока нет"
''',
        "Russian About states",
    )


def patch_arguments(text):
    text = replace_once(
        text,
        "private final class GhostBaseSettingsArguments {\n",
        "private final class GhostBaseSettingsArguments {\n"
        "    let context: AccountContext\n"
        "    let openAboutChannel: (EnginePeer) -> Void\n",
        "arguments properties",
    )
    text = replace_once(
        text,
        '''    init(
        runResearchAction: @escaping (String) -> Void,''',
        '''    init(
        context: AccountContext,
        openAboutChannel: @escaping (EnginePeer) -> Void,
        runResearchAction: @escaping (String) -> Void,''',
        "arguments initializer signature",
    )
    return replace_once(
        text,
        '''    ) {
        self.runResearchAction = runResearchAction''',
        '''    ) {
        self.context = context
        self.openAboutChannel = openAboutChannel
        self.runResearchAction = runResearchAction''',
        "arguments initializer body",
    )


def patch_entry(text):
    text = replace_once(
        text,
        "    case researchAction(Int32, Int32, String, String)\n",
        "    case aboutChannel(Int32, Int32, String, EnginePeer?, String, Bool)\n"
        "    case researchAction(Int32, Int32, String, String)\n",
        "About entry case",
    )
    text = replace_once(
        text,
        '''        case let .researchAction(section, _, _, _):
            return section''',
        '''        case let .aboutChannel(section, _, _, _, _, _):
            return section
        case let .researchAction(section, _, _, _):
            return section''',
        "About entry section",
    )
    text = replace_once(
        text,
        '''        case let .researchAction(section, index, _, _):
            return section * 1000 + index''',
        '''        case let .aboutChannel(section, index, _, _, _, _):
            return section * 1000 + index
        case let .researchAction(section, index, _, _):
            return section * 1000 + index''',
        "About entry stable id",
    )
    text = replace_once(
        text,
        '''        case let .researchAction(ls, li, lt, la):''',
        '''        case let .aboutChannel(ls, li, lt, lp, lv, ll):
            if case let .aboutChannel(rs, ri, rt, rp, rv, rl) = rhs {
                return ls == rs && li == ri && lt == rt
                    && lp == rp && lv == rv && ll == rl
            }
            return false
        case let .researchAction(ls, li, lt, la):''',
        "About entry equality",
    )
    return replace_once(
        text,
        '''        case let .researchAction(_, _, title, actionId):''',
        '''        // MARK: Jerkgram v1.2F BUILD117_ABOUT_CHANNEL_CARD1
        case let .aboutChannel(_, _, title, peer, preview, _):
            if let peer {
                return ItemListPeerItem(
                    presentationData: presentationData,
                    systemStyle: .glass,
                    dateTimeFormat: PresentationDateTimeFormat(),
                    nameDisplayOrder: .firstLast,
                    context: arguments.context,
                    peer: peer,
                    height: .generic,
                    aliasHandling: .standard,
                    nameStyle: .plain,
                    presence: nil,
                    text: .text(preview, .secondary),
                    label: .none,
                    editing: ItemListPeerItemEditing(
                        editable: false,
                        editing: false,
                        revealed: false
                    ),
                    switchValue: nil,
                    enabled: true,
                    selectable: true,
                    sectionId: self.section,
                    action: {
                        arguments.openAboutChannel(peer)
                    },
                    setPeerIdWithRevealedOptions: { _, _ in },
                    removePeer: { _ in }
                )
            } else {
                return ItemListDisclosureItem(
                    presentationData: presentationData,
                    systemStyle: .glass,
                    title: title,
                    label: preview,
                    labelStyle: .text,
                    sectionId: self.section,
                    style: .blocks,
                    disclosureStyle: .none,
                    action: nil
                )
            }

        case let .researchAction(_, _, title, actionId):''',
        "About entry renderer",
    )


def about_state_source():
    return r'''

private enum JerkgramAboutChannelState: Equatable {
    case loading
    case available(peer: EnginePeer, preview: String)
    case unavailable
}

private func jerkgramAboutChannelState(
    context: AccountContext,
    enabled: Bool
) -> Signal<JerkgramAboutChannelState, NoError> {
    guard enabled else {
        return .single(.unavailable)
    }

    return context.engine.peers.resolvePeerByName(name: "JerkgramApp", referrer: nil)
    |> mapToSignal { result -> Signal<JerkgramAboutChannelState, NoError> in
        switch result {
        case .progress:
            return .single(.loading)
        case let .result(peer):
            guard let peer else {
                return .single(.unavailable)
            }

            let history = context.account.postbox
                .aroundMessageHistoryViewForLocation(
                    .peer(peerId: peer.id, threadId: nil),
                    anchor: .upperBound,
                    ignoreMessagesInTimestampRange: nil,
                    ignoreMessageIds: Set(),
                    count: 10,
                    clipHoles: false,
                    fixedCombinedReadStates: nil,
                    topTaggedMessageIdNamespaces: Set(),
                    tag: nil,
                    appendMessagesFromTheSameGroup: false,
                    namespaces: .not(Namespaces.Message.allNonRegular),
                    orderStatistics: []
                )
            let poll: Signal<Void, NoError> = .single(Void())
            |> then(
                context.account.viewTracker.polledChannel(peerId: peer.id)
            )

            return combineLatest(history, poll)
            |> map { viewData, _ -> JerkgramAboutChannelState in
                let (view, _, _) = viewData
                let raw = view.entries.last?.message.text ?? ""
                let compact = raw
                    .split(whereSeparator: { $0.isWhitespace })
                    .joined(separator: " ")
                return .available(
                    peer: peer,
                    preview: String(compact.prefix(160))
                )
            }
        }
    }
    |> distinctUntilChanged
}
'''


def patch_about_entries(text):
    signature = '''private func ghostBaseSettingsEntries(
    state: GhostBaseSettingsState,
    context: AccountContext,
    page: GhostBaseSettingsPage,
    strings: JerkgramStrings
) -> [GhostBaseSettingsEntry] {'''
    replacement = '''private func ghostBaseSettingsEntries(
    state: GhostBaseSettingsState,
    context: AccountContext,
    page: GhostBaseSettingsPage,
    strings: JerkgramStrings,
    aboutChannelState: JerkgramAboutChannelState
) -> [GhostBaseSettingsEntry] {'''
    text = replace_once(text, signature, replacement, "entries state signature")

    old = '''// MARK: Jerkgram v1.2E BUILD116_ABOUT_COMMUNITY1
    if page == .about {
        return [
            .header(0, strings.about),
            .researchAction(
                0,
                1,
                strings.community,
                "https://t.me/JerkgramApp"
            ),
            .info(0, strings.communityHint),
            .info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 116")
        ]
    }'''
    compact_old = '''// MARK: Jerkgram v1.2E BUILD116_ABOUT_COMMUNITY1
    if page == .about {
        return [
            .header(0, strings.about),
            .researchAction(0, 1, strings.community, "https://t.me/JerkgramApp"),
            .info(0, strings.communityHint),
            .info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 116")
        ]
    }'''
    new = '''// MARK: Jerkgram v1.2F BUILD117_ABOUT_CHANNEL_CARD1
    if page == .about {
        let channelEntry: GhostBaseSettingsEntry
        switch aboutChannelState {
        case .loading:
            channelEntry = .aboutChannel(
                0, 1, strings.community, nil,
                strings.communityLoading, true
            )
        case let .available(peer, preview):
            let visiblePreview = preview.isEmpty
                ? strings.communityNoPosts
                : "@JerkgramApp · \\(preview)"
            channelEntry = .aboutChannel(
                0, 1, strings.community, peer,
                visiblePreview, false
            )
        case .unavailable:
            channelEntry = .aboutChannel(
                0, 1, strings.community, nil,
                strings.communityUnavailable, false
            )
        }

        return [
            .header(0, strings.about),
            channelEntry,
            .info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 117")
        ]
    }'''
    if old in text:
        return replace_once(text, old, new, "Build116 About block")
    return replace_once(text, compact_old, new, "Build116 compact About block")


def patch_controller(text):
    arguments_anchor = "    let arguments = GhostBaseSettingsArguments(\n"
    setup = '''    let aboutChannelSignal = jerkgramAboutChannelState(
        context: context,
        enabled: page == .about
    )
    var openAboutChannelImpl: ((EnginePeer) -> Void)?

    let arguments = GhostBaseSettingsArguments(
        context: context,
        openAboutChannel: { peer in
            openAboutChannelImpl?(peer)
        },
'''
    text = replace_once(text, arguments_anchor, setup, "About controller state")

    text = replace_once(
        text,
        '''    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in''',
        '''    let signal = combineLatest(
        context.sharedContext.presentationData,
        statePromise.get(),
        aboutChannelSignal
    )
    |> deliverOnMainQueue
    |> map { presentationData, state, aboutChannelState
        -> (ItemListControllerState, (ItemListNodeState, Any)) in''',
        "About signal composition",
    )
    text = replace_once(
        text,
        '''                page: page,
                strings: presentationData.strings.jerkgram
            ),''',
        '''                page: page,
                strings: presentationData.strings.jerkgram,
                aboutChannelState: aboutChannelState
            ),''',
        "About entries state call",
    )
    controller_anchor = '''    let controller = ItemListController(
        context: context,
        state: signal
    )
'''
    navigation = '''    let controller = ItemListController(
        context: context,
        state: signal
    )

    openAboutChannelImpl = { [weak controller] peer in
        guard let navigationController = controller?.navigationController
            as? NavigationController else {
            return
        }
        context.sharedContext.navigateToChatController(
            NavigateToChatControllerParams(
                navigationController: navigationController,
                context: context,
                chatLocation: .peer(peer)
            )
        )
    }
'''
    if controller_anchor in text:
        text = replace_once(
            text,
            controller_anchor,
            navigation,
            "About native navigation",
        )
    else:
        text = replace_once(
            text,
            "    return ItemListController(context: context, state: signal)\n",
            navigation + "    return controller\n",
            "About compact native navigation",
        )
    text = text.replace(
        '''            case "https://t.me/JerkgramApp":
                context.sharedContext.applicationBindings.openUrl(action)

''',
        "",
        1,
    )
    return text


def patch_settings(text):
    if (
        "JerkgramAboutChannelState" in text
        and "BUILD117_ABOUT_CHANNEL_CARD1" in text
        and "aboutChannelState: aboutChannelState" in text
        and "openAboutChannel: (EnginePeer) -> Void" in text
    ):
        return text
    if "import Postbox\n" not in text:
        text = replace_once(text, "import TelegramCore\n", "import TelegramCore\nimport Postbox\n", "Postbox import")
    if "import ItemListPeerItem\n" not in text:
        text = replace_once(text, "import AccountContext\n", "import AccountContext\nimport ItemListPeerItem\n", "peer item import")
    text = patch_arguments(text)
    text = patch_entry(text)
    marker = "private func ghostBaseSettingsEntries("
    text = replace_once(text, marker, about_state_source() + "\n" + marker, "About state owner")
    text = patch_about_entries(text)
    return patch_controller(text)


def main():
    for path in (SETTINGS, STRINGS):
        require(path.is_file(), "source owner missing: " + str(path))
    SETTINGS.write_text(patch_settings(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")
    STRINGS.write_text(patch_strings(STRINGS.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build117 About channel] live @JerkgramApp credit installed")


if __name__ == "__main__":
    main()
