import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build117AboutChannelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_script(
            "apply_jerkgram_v12f_build117_about_channel1.py"
        )
        cls.verifier = load_script(
            "verify_jerkgram_v12f_build117_about_channel1.py"
        )

    def test_about_uses_resolved_peer_avatar_and_bounded_latest_post(self):
        settings = '''
import TelegramCore
import AccountContext

private final class GhostBaseSettingsArguments {
    let runResearchAction: (String) -> Void
    let updateBool: (String, Bool) -> Void
    let openPage: (GhostBaseSettingsPage) -> Void
    let openSendTextStyle: () -> Void

    init(
        runResearchAction: @escaping (String) -> Void,
        updateBool: @escaping (String, Bool) -> Void,
        openPage: @escaping (GhostBaseSettingsPage) -> Void,
        openSendTextStyle: @escaping () -> Void
    ) {
        self.runResearchAction = runResearchAction
        self.updateBool = updateBool
        self.openPage = openPage
        self.openSendTextStyle = openSendTextStyle
    }
}

private enum GhostBaseSettingsEntry: ItemListNodeEntry {
    case header(Int32, String)
    case researchAction(Int32, Int32, String, String)
    case info(Int32, String)

    var section: ItemListSectionId {
        switch self {
        case let .header(section, _):
            return section
        case let .researchAction(section, _, _, _):
            return section
        case let .info(section, _):
            return section
        }
    }

    var stableId: Int32 {
        switch self {
        case let .header(section, _):
            return section * 1000
        case let .researchAction(section, index, _, _):
            return section * 1000 + index
        case let .info(section, _):
            return section * 1000 + 999
        }
    }

    static func ==(lhs: GhostBaseSettingsEntry, rhs: GhostBaseSettingsEntry) -> Bool {
        switch lhs {
        case let .header(ls, lt):
            if case let .header(rs, rt) = rhs { return ls == rs && lt == rt }
            return false
        case let .researchAction(ls, li, lt, la):
            if case let .researchAction(rs, ri, rt, ra) = rhs { return ls == rs && li == ri && lt == rt && la == ra }
            return false
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs { return ls == rs && lt == rt }
            return false
        }
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! GhostBaseSettingsArguments
        switch self {
        case let .header(_, text):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)
        case let .researchAction(_, _, title, actionId):
            return ItemListDisclosureItem(presentationData: presentationData, title: title, action: { arguments.runResearchAction(actionId) })
        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func ghostBaseSettingsEntries(
    state: GhostBaseSettingsState,
    context: AccountContext,
    page: GhostBaseSettingsPage,
    strings: JerkgramStrings
) -> [GhostBaseSettingsEntry] {
    // MARK: Jerkgram v1.2E BUILD116_ABOUT_COMMUNITY1
    if page == .about {
        return [
            .header(0, strings.about),
            .researchAction(0, 1, strings.community, "https://t.me/JerkgramApp"),
            .info(0, strings.communityHint),
            .info(1, "Jerkgram\\nBase: Official Telegram 12.9.2\\nBuild: 116")
        ]
    }
    return []
}

private func ghostBaseSettingsPageController(context: AccountContext, page: GhostBaseSettingsPage) -> ViewController {
    let statePromise = ValuePromise(initialState, ignoreRepeated: false)
    let arguments = GhostBaseSettingsArguments(
        runResearchAction: { action in },
        updateBool: { key, value in },
        openPage: { selectedPage in },
        openSendTextStyle: {}
    )
    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: ghostBaseSettingsEntries(
                state: state,
                context: context,
                page: page,
                strings: presentationData.strings.jerkgram
            ),
            style: .blocks,
            animateChanges: false
        )
        return (controllerState, (listState, arguments))
    }
    return ItemListController(context: context, state: signal)
}
'''
        strings = '''
public enum JerkgramStringKey: String, CaseIterable {
    case copyExtensionDiagnostics
}
public struct JerkgramStrings {
    public var copyExtensionDiagnostics: String { self.text(.copyExtensionDiagnostics) }
    private static let english: [JerkgramStringKey: String] = [
        .copyExtensionDiagnostics: "Copy Extension Diagnostics"
    ]
    private static let russian: [JerkgramStringKey: String] = [
        .copyExtensionDiagnostics: "Копировать диагностику расширений"
    ]
}
'''

        patched_settings = self.overlay.patch_settings(settings)
        patched_strings = self.overlay.patch_strings(strings)

        for token in (
            "BUILD117_ABOUT_CHANNEL_CARD1",
            "JerkgramAboutChannelState",
            "case aboutChannel",
            "ItemListPeerItem(",
            'resolvePeerByName(name: "JerkgramApp"',
            "aroundMessageHistoryViewForLocation",
            "String(compact.prefix(160))",
            "aboutChannelState: aboutChannelState",
            "navigateToChatController",
        ):
            self.assertIn(token, patched_settings)
        self.assertNotIn("BUILD116_ABOUT_COMMUNITY1", patched_settings)
        self.assertNotIn(".researchAction(0, 1, strings.community", patched_settings)

        for token in (
            "case communityLoading",
            "case communityUnavailable",
            "case communityNoPosts",
            "self.text(.communityLoading)",
            '.communityLoading: "Loading channel…"',
            '.communityLoading: "Загрузка канала…"',
        ):
            self.assertIn(token, patched_strings)

    def test_verifier_limits_bundle_id_check_to_about_block(self):
        settings = '''
// MARK: Jerkgram v1.2F BUILD117_ABOUT_CHANNEL_CARD1
case aboutChannel
ItemListPeerItem(
private enum JerkgramAboutChannelState {}
resolvePeerByName(name: "JerkgramApp", referrer: nil)
aroundMessageHistoryViewForLocation
String(compact.prefix(160))
aboutChannelState: aboutChannelState
navigateToChatController

// MARK: Jerkgram v1.2F BUILD117_ABOUT_CHANNEL_CARD1
if page == .about {
    return [.info(1, "Jerkgram\\nBuild: 117")]
}

private func unrelatedTechnicalDiagnostics() -> String {
    return "Bundle ID: diagnostics-only"
}
'''
        strings = '''
case communityLoading
case communityUnavailable
case communityNoPosts
self.text(.communityLoading)
self.text(.communityUnavailable)
self.text(.communityNoPosts)
'''

        self.verifier.verify(settings, strings)


if __name__ == "__main__":
    unittest.main()
