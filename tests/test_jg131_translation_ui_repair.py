"""Supplemental source contracts; device/Apple/NL runtime is not exercised here."""
import os
import re
import unittest
from pathlib import Path
BUILDER = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('JERKGRAM_TRANSLATION_REPAIR_SOURCE', str(BUILDER / 'work/swiftgram-src')))
if not ROOT.exists():
    ROOT = BUILDER.parent / 'jerkgram-next/task-a/source'

def source(suffix):
    if suffix == 'Translate.swift':
        return (ROOT / 'submodules/TranslateUI/Sources/Translate.swift').read_text()
    return next(ROOT.rglob(suffix)).read_text()

class TranslationUIRepair(unittest.TestCase):
    def test_account_scoped_availability(self):
        for file in ROOT.rglob('*.swift'):
            if 'TelegramCore' not in str(file):
                self.assertNotIn('jerkgramLocalTranslationAvailable', file.read_text(), str(file))
        self.assertIn('JerkgramTranslationSettings.enabled(accountPeerId: context.account.peerId.toInt64())', source('Translate.swift'))

    def test_canonical_settings(self):
        text = source('GhostBaseSettingsController.swift')
        self.assertIn('var enhancedTranslation: Bool = true', text)
        self.assertIn('JerkgramTranslationSettings.preferenceKey: .bool(state.enhancedTranslation)', text)
        self.assertIn('JerkgramTranslationSettings.update(accountPeerId: accountPeerId, enabled: current.enhancedTranslation)', text)
        self.assertIn('Улучшенный перевод', text)
        self.assertIn('Enhanced Translation', text)

    def test_renderer_requires_account(self):
        for file in ROOT.rglob('*.swift'):
            if 'TelegramCore' not in str(file):
                for call in re.findall(r'isValidForMessage\(([^)]*)\)', file.read_text()):
                    self.assertIn('accountPeerId:', call, str(file))

    def test_detection_bounds_and_mask(self):
        text = source('ChatTranslation.swift')
        for bound in ['count: 32', 'count >= 16', 'prefix(256)', 'withMaximum: 4']:
            self.assertIn(bound, text)
        self.assertNotIn('private let languageRecognizer', text)
        self.assertIn('Range(NSRange', text)
        self.assertIn('guard !fromLang.isEmpty', text)

    def test_single_delivery_policy_guard_and_native_route(self):
        text = source('TextProcessingTranslateContentComponent.swift')
        self.assertIn('composeAIMessage(', text)
        self.assertIn('policyGeneration', text)
        self.assertIn('jerkgramTranslateText(', text)
        self.assertIn('localOnly:', text)
        self.assertIn('!component.context.isPremium', text)


class UIReviewRegressions(unittest.TestCase):
    def test_secret_draft_compose_translate_tab_carries_locality(self):
        text = source('ChatControllerNode.swift')
        compose = text[text.index('    func openAICompose()'):]
        self.assertIn('inputText: composedInputText,\n                localOnly: self.chatLocation.peerId?.namespace == Namespaces.Peer.SecretChat,', compose)
        self.assertIn('self.translateState.localOnly = component.localOnly', source('TextProcessingScreen.swift'))

    def test_success_cache_shortcuts_reject_failure_markers(self):
        checks = cache_skip_conditions()
        self.assertEqual(len(checks), 4)
        for condition in checks:
            self.assertIn('!translation.jerkgramUnavailable', condition)
            self.assertIn('accountPeerId:', condition)

    def test_manual_fallback_initializes_on_main_at_common_request_boundary(self):
        text = source('Translate.swift')
        adapter = text[text.index('public func jerkgramTranslateText'):text.index('func alternativeTranslateText')]
        self.assertIn('engineExperimentalInternalTranslationService == nil', adapter)
        self.assertIn('context.sharedContext.mainWindow?.hostView', adapter)
        self.assertIn('ExperimentalInternalTranslationServiceImpl(view: hostView.containerView)', adapter)
        self.assertIn('runOn(Queue.mainQueue())', adapter)
        self.assertLess(adapter.index('engineExperimentalInternalTranslationService == nil'), adapter.index('enhancedTranslate('))
        component = source('TextProcessingTranslateContentComponent.swift')
        self.assertIn('signal = jerkgramTranslateText(context: component.context, text: text, entities: entities,', component)
        self.assertIn('allowLocalDownloads: true, localOnly: localOnly', adapter)

    def test_failure_message_describes_telegram_and_system_route(self):
        text = source('JerkgramStrings.swift')
        message = text[text.index('    var localTranslationUnavailable:'):text.index('    var localTranslationRetry:')]
        self.assertNotIn('On-device translation failed', message)
        self.assertNotIn('Не удалось перевести на устройстве', message)
        for word in ['connection', 'language', 'unsupported', 'соединение', 'языка', 'поддерживаться']:
            self.assertIn(word, message)


def cache_skip_conditions():
    conditions = []
    for name in ['ChatTranslation.swift', 'ChatHistoryListNode.swift']:
        for line in source(name).splitlines():
            if 'if let translation =' in line and 'translation.isValidForMessage(' in line:
                conditions.append(line.split('as? TranslationMessageAttribute, ', 1)[1].rsplit(' {', 1)[0])
    return conditions


class NativeRetryEligibility(unittest.TestCase):
    @unittest.skipUnless(__import__('shutil').which('swift'), 'Swift unavailable; production cache predicate execution requires macOS CI')
    def test_actual_four_production_predicates(self):
        import subprocess, tempfile
        # Extract each actual admission predicate, stubbing only the independently
        # tested core validator outcome and external account/message containers.
        conditions = cache_skip_conditions()
        self.assertEqual(len(conditions), 4)
        prelude = r'''import Foundation
struct PeerId { func toInt64() -> Int64 { 7 } }
struct Account { let peerId = PeerId() }
struct Context { let account = Account() }
struct Translation {
    let toLang: String
    let jerkgramUnavailable: Bool
    let valid: Bool
    func isValidForMessage(_ message: Int, accountPeerId: Int64) -> Bool { valid && accountPeerId == 7 }
}
let context = Context()
let message = 1, replyMessage = 1
let toLang = "en", translateToLanguage = "en"
'''
        checks = []
        for index, condition in enumerate(conditions):
            condition = condition.replace('self.context.', 'context.')
            checks.append(f'''func skip{index}(_ translation: Translation) -> Bool {{
    if {condition} {{ return true }}
    return false
}}
precondition(!skip{index}(Translation(toLang: "en", jerkgramUnavailable: true, valid: true)))
precondition(skip{index}(Translation(toLang: "en", jerkgramUnavailable: false, valid: true)))
precondition(!skip{index}(Translation(toLang: "de", jerkgramUnavailable: false, valid: true)))
precondition(!skip{index}(Translation(toLang: "en", jerkgramUnavailable: false, valid: false)))
''')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'main.swift'
            path.write_text(prelude + '\n'.join(checks) + '\nprint("production retry predicates passed")\n')
            result = subprocess.run(['swift', str(path)], capture_output=True, text=True, timeout=55)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('production retry predicates passed', result.stdout)


class NativeRecognitionMask(unittest.TestCase):
    @unittest.skipUnless(__import__('shutil').which('swift'), 'Swift unavailable; actual Foundation mask execution requires macOS CI')
    def test_actual_production_mask(self):
        import subprocess, tempfile
        text = source('ChatTranslation.swift')
        helper = text[text.index('private func jerkgramTranslationRecognitionSample'):text.index('public func translateMessageIds')]
        cases = r'''
let input = "😀 Hello world https://example.com"
let url = (input as NSString).range(of: "https://example.com")
let output = jerkgramTranslationRecognitionSample(input, maskedRanges: [url.location ..< (url.location + url.length)])
precondition(output.hasPrefix("😀 Hello world "))
precondition(!output.contains("https"))
precondition(output.utf16.count == input.utf16.count)
let overlap = jerkgramTranslationRecognitionSample("abcdefghij", maskedRanges: [2..<8, 4..<10])
precondition(overlap == "ab        ")
precondition(jerkgramTranslationRecognitionSample("😀abc", maskedRanges: [1..<2]) == "😀abc")
precondition(jerkgramTranslationRecognitionSample("abc", maskedRanges: [-1..<2]) == "abc")
precondition(jerkgramTranslationRecognitionSample(String(repeating: "x", count: 300), maskedRanges: [250..<300]).count == 256)
precondition(jerkgramTranslationRecognitionSample("abc", maskedRanges: [0..<3]).trimmingCharacters(in: .whitespaces).isEmpty)
print("production recognition mask passed")
'''
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'main.swift'
            path.write_text('import Foundation\n' + helper + cases)
            result = subprocess.run(['swift', str(path)], capture_output=True, text=True, timeout=55)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('production recognition mask passed', result.stdout)

if __name__ == '__main__': unittest.main()
