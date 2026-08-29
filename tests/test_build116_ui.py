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


class Build116UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_script("apply_jerkgram_v12e_build116_ui1.py")
        cls.verifier = load_script("verify_jerkgram_v12e_build116_ui1.py")

    def test_profile_panes_are_restored_and_raw_settings_runtime_is_removed(self):
        profile = '''
// MARK: GhostBase v1.1G NATIVEPANES1
// MARK: Jerkgram v1.2D BUILD115_HIDE_RESEARCH_PANES1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    // Keep PROFILEINTEL/history recording and persisted data intact,
    // but do not publish raw research/report panes in the normal
    // Telegram profile UI.
    return availablePanes
}
'''
        settings = '''
    // MARK: GhostBase v1.1G BOUNDEDDEBUG1
    if page == .debugResearch {
        let defaults = UserDefaults.standard
        let runtimeLines = defaults.stringArray(
            forKey: "jerkgram.Runtime.Diagnostics.V11G"
        ) ?? []
        let runtimeText = runtimeLines.suffix(80).joined(separator: "\\n")
        return [
            .header(0, "Runtime"),
            .info(0, runtimeText),
            .header(1, strings.recentEvents),
            .info(1, strings.diagnosticsBufferHint)
        ]
    }
'''

        patched_profile = self.overlay.patch_profile_ui(profile)
        patched_settings = self.overlay.patch_settings_runtime(settings)

        for token in (
            "PeerInfoPaneKey.ghostBaseProfileHistory",
            "PeerInfoPaneKey.ghostBasePresence",
            "PeerInfoPaneKey.ghostBaseGiftHistory",
            ".ghostBasePersonalChannel",
        ):
            self.assertIn(token, patched_profile)
        self.assertNotIn("return availablePanes\n}", patched_profile)
        self.assertNotIn("runtimeLines", patched_settings)
        self.assertNotIn('header(0, "Runtime")', patched_settings)
        self.assertIn("BUILD116_SETTINGS_RUNTIME_CLEANUP1", patched_settings)

    def test_actual_chat_owner_routes_numeric_mentions_and_keeps_usernames(self):
        chat = '''
    func openPeerMention(_ name: String, navigation: ChatControllerInteractionNavigateToPeer = .default, sourceMessageId: MessageId? = nil, progress: Promise<Bool>? = nil) {
        let _ = self.presentVoiceMessageDiscardAlert(action: {
            let disposable: MetaDisposable
            if let resolvePeerByNameDisposable = self.resolvePeerByNameDisposable {
                disposable = resolvePeerByNameDisposable
            } else {
                disposable = MetaDisposable()
                self.resolvePeerByNameDisposable = disposable
            }
            var resolveSignal = self.context.engine.peers.resolvePeerByName(name: name, referrer: nil, ageLimit: 10)

            var cancelImpl: (() -> Void)?
'''

        patched = self.overlay.patch_chat_mentions(chat)

        self.assertIn("BUILD116_CHAT_NUMERIC_MENTION1", patched)
        self.assertIn("jerkgramNumericMentionPeerId(name)", patched)
        self.assertIn('self.openUrl("https://t.me/@id\\(idValue)"', patched)
        self.assertIn("self.context.engine.peers.resolvePeerByName(name: name", patched)

    def test_numeric_normalization_accepts_explicit_forms_only(self):
        normalize = self.overlay.numeric_peer_id

        self.assertEqual(normalize("@8405914445"), 8405914445)
        self.assertEqual(normalize("@id8405914445"), 8405914445)
        self.assertEqual(normalize("id8405914445"), 8405914445)
        self.assertEqual(normalize("8405914445"), 8405914445)
        self.assertIsNone(normalize("@id"))
        self.assertIsNone(normalize("+8405914445"))
        self.assertIsNone(normalize("12a"))
        self.assertIsNone(normalize("0"))

    def test_send_style_and_about_use_semantic_localization(self):
        strings = '''
public enum JerkgramStringKey: String, CaseIterable {
    case exportArchive
}
public struct JerkgramStrings {
    public var exportArchive: String { self.text(.exportArchive) }
    private static let english: [JerkgramStringKey: String] = [
        .exportArchive: "Export Jerkgram Archive"
    ]
    private static let russian: [JerkgramStringKey: String] = [
        .exportArchive: "Экспорт архива Jerkgram"
    ]
}
'''
        settings = '''
private func ghostBaseSendTextStyleTitle(
    _ value: String
) -> String {
    switch value {
    case "bold":
        return "Жирный"
    case "italic":
        return "Курсив"
    case "monospace":
        return "Моноширинный"
    case "strikethrough":
        return "Зачёркнутый"
    case "underline":
        return "Подчёркнутый"
    case "spoiler":
        return "Спойлер"
    default:
        return "Обычный"
    }
}
let previewPrefix = "Пример: "
let previewBody = "так будет выглядеть ваш текст"
let styles: [(String, String)] = [
    ("normal", "Обычный"),
    ("bold", "Жирный"),
    ("italic", "Курсив"),
    ("monospace", "Моноширинный"),
    ("strikethrough", "Зачёркнутый"),
    ("underline", "Подчёркнутый"),
    ("spoiler", "Спойлер")
]
let styleTitle = "Стиль отправки"
if page == .about {
    let bundleId = Bundle.main.bundleIdentifier ?? "unknown"
    return [
        .header(0, strings.about),
        .info(0, "Bundle ID: \\(bundleId)")
    ]
}
'''

        patched_strings = self.overlay.patch_strings(strings)
        patched_settings = self.overlay.patch_settings_localization_about(settings)

        for token in (
            "case sendStyleNormal",
            "case sendStyleSpoiler",
            "case sendStyleExamplePrefix",
            "case sendStyleExampleBody",
            "case community",
            "case communityHint",
            "case copyExtensionDiagnostics",
            'self.text(.sendStyleNormal)',
            '.community: "Jerkgram Community"',
            '.community: "Сообщество Jerkgram"',
        ):
            self.assertIn(token, patched_strings)

        for literal in (
            "Жирный",
            "Курсив",
            "Моноширинный",
            "Зачёркнутый",
            "Подчёркнутый",
            "Спойлер",
            "Обычный",
            "Пример",
            "Стиль отправки",
            "Bundle ID",
        ):
            self.assertNotIn(literal, patched_settings)

        self.assertIn("BUILD116_STYLE_LOCALIZATION1", patched_settings)
        self.assertIn("https://t.me/JerkgramApp", patched_settings)
        self.assertIn("strings.community", patched_settings)
        self.assertIn("strings.communityHint", patched_settings)

    def test_final_verifier_accepts_composed_build116_sources(self):
        profile = self.overlay.patch_profile_ui('''
// MARK: GhostBase v1.1G NATIVEPANES1
// MARK: Jerkgram v1.2D BUILD115_HIDE_RESEARCH_PANES1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    // Keep PROFILEINTEL/history recording and persisted data intact,
    // but do not publish raw research/report panes in the normal
    // Telegram profile UI.
    return availablePanes
}
''')
        chat = self.overlay.patch_chat_mentions('''
    func openPeerMention(_ name: String, navigation: ChatControllerInteractionNavigateToPeer = .default, sourceMessageId: MessageId? = nil, progress: Promise<Bool>? = nil) {
        let _ = self.presentVoiceMessageDiscardAlert(action: {
            let signal = self.context.engine.peers.resolvePeerByName(name: name, referrer: nil, ageLimit: 10)
''')
        settings = self.overlay.patch_settings_runtime('''
    // MARK: GhostBase v1.1G BOUNDEDDEBUG1
    if page == .debugResearch {
        let runtimeLines = UserDefaults.standard.stringArray(forKey: "jerkgram.Runtime.Diagnostics.V11G") ?? []
        return [.header(0, "Runtime"), .info(0, runtimeLines.joined())]
    }
''')
        settings += self.overlay.patch_settings_localization_about('''
private func ghostBaseSendTextStyleTitle(
    _ value: String
) -> String {
    switch value {
    case "bold":
        return "Жирный"
    case "italic":
        return "Курсив"
    case "monospace":
        return "Моноширинный"
    case "strikethrough":
        return "Зачёркнутый"
    case "underline":
        return "Подчёркнутый"
    case "spoiler":
        return "Спойлер"
    default:
        return "Обычный"
    }
}
if page == .about {
    let bundleId = Bundle.main.bundleIdentifier ?? "unknown"
    return [.info(0, "Bundle ID: \\(bundleId)")]
}
''')
        strings = self.overlay.patch_strings('''
public enum JerkgramStringKey: String, CaseIterable {
    case exportArchive
}
public struct JerkgramStrings {
    public var exportArchive: String { self.text(.exportArchive) }
    private static let english: [JerkgramStringKey: String] = [
        .exportArchive: "Export Jerkgram Archive"
    ]
    private static let russian: [JerkgramStringKey: String] = [
        .exportArchive: "Экспорт архива Jerkgram"
    ]
}
''')

        self.verifier.verify(profile, chat, settings, strings)

    def test_partial_materialization_retry_is_idempotent(self):
        profile = "// MARK: Jerkgram v1.2E BUILD116_PROFILE_SCOPE1\n"
        chat = "// MARK: Jerkgram v1.2E BUILD116_CHAT_NUMERIC_MENTION1\n"
        settings_runtime = "// MARK: Jerkgram v1.2E BUILD116_SETTINGS_RUNTIME_CLEANUP1\n"
        strings = '''case copyExtensionDiagnostics
self.text(.copyExtensionDiagnostics)
.copyExtensionDiagnostics: "Copy Extension Diagnostics"
.copyExtensionDiagnostics: "Копировать диагностику расширений"
'''

        self.assertEqual(profile, self.overlay.patch_profile_ui(profile))
        self.assertEqual(chat, self.overlay.patch_chat_mentions(chat))
        self.assertEqual(settings_runtime, self.overlay.patch_settings_runtime(settings_runtime))
        self.assertEqual(strings, self.overlay.patch_strings(strings))


if __name__ == "__main__":
    unittest.main()
