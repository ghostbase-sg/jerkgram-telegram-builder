"""Source contract gates; native execution requires the Apple/Telegram build environment."""
from pathlib import Path
import unittest
import os
BUILDER = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get('JERKGRAM_TRANSLATION_REPAIR_SOURCE', BUILDER / 'work/swiftgram-src'))
ROOT = SOURCE_ROOT / 'submodules/TelegramCore/Sources' 
class TranslationCoreContract(unittest.TestCase):
    def test_explicit_route_does_not_replace_stock_local(self):
        s = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        self.assertIn('enhanced: Bool = false', s)
        self.assertNotIn('if enableLocalIfPossible {\n            return jerkgramTranslateLocalMessages', s)
    def test_stock_body_is_exact_and_secret_enhanced_route_is_local(self):
        source = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        clean = (Path(__file__).parent / 'fixtures/translation-core/stock-translation-excerpts.swift').read_text()
        def body(text, name, end):
            start = text.index('func ' + name + '(')
            return text[start:text.index(end, start)]
        name = '_internal_translateTexts'
        self.assertEqual(body(source, name, 'func _internal_translateMessages('), body(clean, name, 'func _internal_translateMessages('))
        name = '_internal_translateMessagesByPeerId'
        current = body(source, name, 'func _internal_togglePeerMessagesTranslationHidden')
        current = current.replace('enableLocalIfPossible: Bool, enhanced: Bool = false,', 'enableLocalIfPossible: Bool,')
        branch = current[current.index('        if enhanced {'):current.index('        guard let inputPeer')]
        self.assertIn('localOnly: peerId.namespace == Namespaces.Peer.SecretChat', branch)
        current = current.replace(branch, '')
        self.assertEqual(current, body(clean, name, 'func _internal_togglePeerMessagesTranslationHidden'))

    def test_policy_before_immutable_fingerprint_cache(self):
        s = (ROOT / 'SyncCore/SyncCore_TranslationMessageAttribute.swift').read_text()
        self.assertIn('jerkgramPolicyVersion', s)
        self.assertLess(s.index('JerkgramTranslationSettings.enabled'), s.index('self.jerkgramCachedMessage === message'))
    def test_shared_route_is_bounded_and_validates_output(self):
        s = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        for token in ('JerkgramTranslationAdmission', '128 * 1024', '16 * 1024', 'active < 2', '30.0', '256', '1024 * 1024', 'jerkgramValidTranslatedEntities', 'results.count == texts.count'):
            self.assertIn(token, s)
    def test_terminal_timer_has_no_strong_job_edge_and_payloads_use_full_encoding(self):
        source = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        # Supplemental ownership/source integration checks. Weak-lifetime and
        # giant TextUrl behavior execute against actual production code natively.
        self.assertRegex(source, r'DispatchWorkItem\s*\{\s*\[weak self, weak job\]')
        self.assertIn('job.timer = nil', source)
        self.assertIn('JSONEncoder().encode(text.1)', source)
        self.assertIn('guard let bytes = jerkgramTranslationPayloadBytes(texts)', source)
        self.assertIn('if let size = jerkgramTranslationPayloadBytes(value)', source)

    def test_settings_public_contract_and_transaction_generation(self):
        s = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        for token in ('public enum JerkgramTranslationSettings', '"jerkgram.EnhancedTranslation"', 'generation(accountPeerId:', 'jerkgramPolicyIsCurrent(account: account, generation: generation)'):
            self.assertIn(token, s)

class NativeProductionPolicyAdmission(unittest.TestCase):
    @unittest.skipUnless(__import__('shutil').which('swift'), 'Swift unavailable; native policy/admission execution requires macOS CI')
    def test_actual_policy_and_admission_with_pinned_signal_lifetimes(self):
        import subprocess, tempfile
        source = (ROOT / 'TelegramEngine/Messages/Translate.swift').read_text()
        policy = source[source.index('public enum JerkgramTranslationSettings'):source.index('private func jerkgramPolicyIsCurrent')]
        admission = source[source.index('private typealias JerkgramTranslatedTexts'):source.index('private func jerkgramEnhancedTexts')]
        attr = (ROOT / 'SyncCore/SyncCore_TranslationMessageAttribute.swift').read_text()
        method = attr[attr.index('    public func isValidForMessage'):attr.index('    public let additional:')].replace('public func isValidForMessage', 'func isValidForMessage')
        validity = """
private final class Message { let fingerprint: String; init(_ value: String) { fingerprint = value } }
private func jerkgramTranslationSourceFingerprint(_ message: Message) -> String { message.fingerprint }
private final class TranslationValidityFixture {
    let jerkgramSourceFingerprint: String?
    let jerkgramPolicyVersion: Int32
    private let jerkgramSourceLock = NSLock()
    private weak var jerkgramCachedMessage: Message?
    private var jerkgramCachedValidity = false
    init(_ fingerprint: String?, _ version: Int32) { jerkgramSourceFingerprint = fingerprint; jerkgramPolicyVersion = version }
""" + method + "\n}\n"
        fixtures = Path(__file__).parent / 'fixtures/translation-core'
        # Exact pinned SwiftSignalKit implementations, not a behavioral model.
        deps = '\n'.join((fixtures / name).read_text().split('@available(iOS 13.0, macOS 10.15, *)')[0] for name in ('Atomic.swift', 'Disposable.swift', 'Subscriber.swift', 'Signal.swift'))
        cases = (fixtures / 'cases.swift').read_text()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'main.swift'
            path.write_text(deps + '\n' + policy + admission + validity + cases)
            result = subprocess.run(['swift', str(path)], capture_output=True, text=True, timeout=55)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('production policy/admission cases passed', result.stdout)

if __name__ == '__main__': unittest.main()
