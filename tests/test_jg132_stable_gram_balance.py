"""Actual GRAM controls, parser, autosave and account scope; macOS gate is mandatory in CI."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
from test_jg131_beta2_bot_codec import declaration
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_STABLE182_SOURCE', ROOT.parent/'jerkgram-next/stable182-gram'))
EDITOR = 'submodules/SettingsUI/Sources/Jerkgram/JerkgramGramEditorController.swift'
HELPER = 'submodules/AccountContext/Sources/JerkgramLocalGramBalance.swift'
WALLET = 'submodules/TelegramUI/Components/Wallet/WalletScreen/Sources/WalletScreen.swift'

def fixture():
    editor = (SOURCE/EDITOR).read_text()
    anchors = ['private struct JerkgramGramDraftState:', 'private final class JerkgramGramEditorArguments',
               'private func jerkgramIsValidGramDraft(', 'private func jerkgramSanitizeGramDraft(',
               'private func jerkgramSavedGramAmount(', 'private func jerkgramGramPreset(',
               'private final class JerkgramGramAutosave']
    source = '\n'.join(declaration(editor, anchor) for anchor in anchors).replace('private struct ', 'struct ').replace('private final class ', 'final class ')
    start = editor.index('    let arguments = JerkgramGramEditorArguments(')
    end = editor.index('\n    )', start) + len('\n    )')
    controls = editor[start:end]
    matrix = (ROOT/'tests/fixtures/stable182/gram-matrix.swift').read_text()
    matrix = matrix.replace('EXPECT_IMMEDIATE_TOGGLE', str('autosave.flush()' in controls).lower())
    wallet = (SOURCE/WALLET).read_text()
    methods = '\n'.join(declaration(wallet, anchor) for anchor in
        ('private func refreshLocalGramBalance(', 'private var displayBalance: Int64?'))
    methods = methods.replace('private func ', 'func ').replace('private var ', 'var ').replace('JerkgramLocalGramBalance.visualBalance', 'CountingGramBalance.visualBalance')
    cache = (ROOT/'tests/fixtures/stable182/gram-display-cache.swift').read_text().replace('// ACTUAL_WALLET_METHODS', methods)
    stars=(SOURCE/'submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift').read_text()
    methods='\n'.join(declaration(stars,anchor) for anchor in ('private func refreshLocalGramBalance(', 'private var displayBalance: StarsAmount'))
    methods=methods.replace('private func ', 'func ').replace('private var ', 'var ').replace('JerkgramLocalGramBalance.visualBalance','CountingGramBalance.visualBalance')
    starsCache=(ROOT/'tests/fixtures/stable182/gram-stars-display-cache.swift').read_text().replace('// ACTUAL_STARS_METHODS',methods)
    return 'import Foundation\nimport Dispatch\n'+(SOURCE/HELPER).read_text()+'\n'+source+'\n'+matrix.replace('// ACTUAL_CONTROL_ARGUMENTS', controls)+'\n'+cache+'\n'+starsCache

class GramBalance(unittest.TestCase):
    def test_wallet_only_presentation_boundary(self):
        text = (SOURCE/WALLET).read_text()
        owner = declaration(text, 'private var displayBalance: Int64?')
        self.assertIn('self.localGramVisualBalance', owner)
        for forbidden in ('UserDefaults', 'visualBalance(', 'savedAmount(', 'nanotokens(', 'refreshLocalGramBalance'):
            self.assertNotIn(forbidden, owner)
        refresh = declaration(text, 'private func refreshLocalGramBalance(')
        self.assertIn('component.context.account.peerId.toInt64()', refresh)
        self.assertIn('changedAccountPeerId.int64Value == accountPeerId', refresh)
        self.assertIn('JerkgramLocalGramBalance.visualBalance(accountPeerId: accountPeerId)', refresh)
        self.assertIn('Notification.Name("JerkgramSettingsDidImport")', text)
        self.assertIn('if localGramIdentityChanged {\n                self.refreshLocalGramBalance()', text)
        self.assertIn('self.component?.walletContext !== component.walletContext', text)
        self.assertIn('for observer in self.localGramObservers { NotificationCenter.default.removeObserver(observer) }', text)
        self.assertIn('self.walletState?.balance.currentValue', owner)
        self.assertEqual(text.count('balance: self.displayBalance'), 2)
        self.assertEqual(text.count('JerkgramLocalGramBalance.visualBalance'), 1)
        self.assertIn('"Wallet/TopGram"', text)
        self.assertIn('withAlphaComponent(0.45)', text)
        self.assertNotIn('self.walletState =', owner)
        for relative in ('submodules/TelegramCore/Sources/TelegramEngine/Payments/Stars.swift',
                         'submodules/TelegramUI/Components/Wallet/WalletSendScreen/Sources/WalletSendScreen.swift',
                         'submodules/TelegramUI/Components/Wallet/WalletTransactionScreen/Sources/WalletTransactionScreen.swift'):
            self.assertNotIn('JerkgramLocalGramBalance', (SOURCE/relative).read_text())
        helper = (SOURCE/HELPER).read_text()
        self.assertNotIn('WalletContext.', helper.replace('// Uses the existing per-account Settings scope. GRAM overrides never enter WalletContext.', ''))
        self.assertNotIn('TelegramEngine', helper)
        self.assertNotIn('Stars.LocalBalance', helper)

    def test_all_current_account_gram_balance_presentations(self):
        text=(SOURCE/'submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift').read_text()
        display=declaration(text,'private var displayBalance: StarsAmount')
        self.assertIn('self.localGramVisualBalance.map',display)
        self.assertNotIn('UserDefaults',display)
        self.assertNotIn('visualBalance(accountPeerId:',display)
        refresh=declaration(text,'private func refreshLocalGramBalance(')
        self.assertIn('component.starsContext === component.context.tonContext',refresh)
        self.assertIn('JerkgramSettingsDidImport',text)
        self.assertIn('formatTonAmountText(self.displayBalance.value',text)
        self.assertIn('count: self.displayBalance',text)
        self.assertNotIn('state.balance =',text)

    def test_controls_and_native_fixture_assembled_from_actual_owners(self):
        text = (SOURCE/EDITOR).read_text()
        self.assertIn('textUpdated: { arguments.setAmount(jerkgramSanitizeGramDraft($0)) }', text)
        self.assertIn('shouldUpdateText: { jerkgramIsValidGramDraft($0) }', text)
        self.assertIn('rightNavigationButton: nil', text)
        self.assertIn('willDisappear = { _ in autosave.flush() }', text)
        self.assertIn('0.25', text)
        signature=(ROOT/'tests/fixtures/stable182/gram-disclosure-signature.txt').read_text()
        self.assertLess(signature.index('icon: UIImage?'), signature.index('title: String'))
        self.assertLess(text.index('icon: UIImage(bundleImageName:'), text.index('title: amount'))
        self.assertIn('let arguments = JerkgramGramEditorArguments(', fixture())
        self.assertIn('Int64.max', fixture())
        settings=(SOURCE/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
        self.assertIn('strings.gramOverrideSummary(state.localGramEnabled, state.localGramAmount)', settings)
        self.assertIn('pushController?(jerkgramGramEditorController(context: context))', settings)
        archive=(SOURCE/'submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift').read_text()
        self.assertIn('key != JerkgramLocalGramBalance.enabledKey', archive)
        self.assertIn('key != JerkgramLocalGramBalance.amountKey', archive)
        self.assertIn('"jerkgram.Gram.LocalBalance.Enabled"', archive)
        self.assertIn('"jerkgram.Gram.LocalBalance.Amount"', archive)

    def test_native_controls_autosave_scope(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE') == '1':
                self.fail('GRAM control/state matrix requires native macOS Swift; cannot silently skip in CI')
            self.skipTest('native Swift unavailable; CI must set JG_STABLE182_REQUIRE_NATIVE=1')
        with tempfile.TemporaryDirectory(prefix='stable182-gram-') as directory:
            path=Path(directory)
            (path/'main.swift').write_text(fixture())
            for optimization in ('-Onone', '-O'):
                command=['xcrun','swiftc',optimization,str(path/'main.swift'),'-o',str(path/'fixture')]
                built=subprocess.run(command,capture_output=True,text=True,timeout=90)
                self.assertEqual(built.returncode,0,built.stdout+built.stderr)
                result=subprocess.run([str(path/'fixture')],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__ == '__main__': unittest.main(verbosity=2)
