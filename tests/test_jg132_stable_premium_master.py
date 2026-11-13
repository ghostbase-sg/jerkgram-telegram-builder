"""Stable182 actual-owner master/appearance/native picker contracts and extracted native execution."""
from pathlib import Path
import os, shutil, subprocess, tempfile, unittest
import test_jg131_beta2_bot_codec as codec
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_STABLE182_PREMIUM_SOURCE', os.environ.get('JG_STABLE182_SOURCE', ROOT.parent/'jerkgram-next/stable182-premium')))
def read(p): return (SOURCE/'submodules'/p).read_text()
def decl(p,anchor): return codec.declaration(read(p),anchor)
def fixture():
    parts=['import Foundation\n', (ROOT/'tests/fixtures/post180/appearance-boundaries.swift').read_text()]
    for name in ('JerkgramLocalAppearanceSettings.swift','JerkgramLocalAppearanceStore.swift'):
        parts.append('\n'.join(l for l in read('TelegramCore/Sources/Settings/'+name).splitlines() if not l.startswith('import ')))
    for path,anchor in [('Postbox/Sources/LocalSavedTagsTable.swift','public enum JerkgramLocalPremiumPolicy'),('TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift','public enum JerkgramDownloadBoostMode'),('TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift','public enum JerkgramDownloadBoostSettings'),('TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift','enum JerkgramDownloadBoostPolicy'),('TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift','public enum JerkgramSponsoredContentPolicy'),('TelegramCore/Sources/TelegramEngine/Messages/Translate.swift','public enum JerkgramTranslationSettings'),('SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift','enum JerkgramAppIconAccess')]:
        parts.append(decl(path,anchor))
    parts.append('final class JerkgramTranslationAdmission { static let shared = JerkgramTranslationAdmission(); func cancel(accountPeerId: Int64) {} }')
    parts.append('public struct TelegramMediaFile { public struct Id { let id: Int64 }; let fileId: Id; init(_ id: Int64) { fileId = Id(id: id) } }')
    parts.append(decl('AccountContext/Sources/AccountContext.swift','public enum EmojiStatusSelectionControllerMode'))
    route=decl('TelegramUI/Components/EmojiStatusSelectionComponent/Sources/EmojiStatusSelectionComponent.swift','private func completeLocalSelection(')
    parts.append('''final class PickerHarness {
        final class Context { let jerkgramLocalAppearance: JerkgramLocalAppearanceStore; init(_ store: JerkgramLocalAppearanceStore) { jerkgramLocalAppearance = store } }
        let context: Context; let localAppearance: Bool; let localAppearanceGeneration: Int64?; let currentSelection: Int64?; let mode: EmojiStatusSelectionControllerMode = .statusSelection
        init(_ store: JerkgramLocalAppearanceStore, local: Bool, selection: Int64? = nil) { context = Context(store); localAppearance = local; localAppearanceGeneration = store.snapshot.activityGeneration; currentSelection = selection }
        func run(_ file: TelegramMediaFile?, _ expiration: Int32?) -> Bool { completeLocalSelection(file: file, expirationDate: expiration) }
    '''+route+'\n}')
    parts.append((ROOT/'tests/fixtures/stable182/premium/master-matrix.swift').read_text())
    return '\n'.join(parts)
class PremiumMaster(unittest.TestCase):
    def test_all_real_runtime_owners(self):
        self.assertIn('guard JerkgramLocalPremiumPolicy.enabled else { return .off }',read('TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift'))
        fetch=decl('TelegramCore/Sources/Network/FetchV2.swift','private func update()')
        self.assertIn('state.maxPendingParts = effectiveBoost.maxPendingParts',fetch)
        self.assertIn('state.partSize = effectiveBoost.partSize',fetch)
        self.assertIn('guard JerkgramLocalPremiumPolicy.enabled else { return false }',read('TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift'))
        ads=read('TelegramCore/Sources/TelegramEngine/Messages/AdMessages.swift')
        self.assertIn('forName: JerkgramLocalPremiumPolicy.changed',ads)
        self.assertIn('strongSelf.policyGeneration == policyGeneration',ads)
        self.assertEqual(ads.count('removeSponsored: JerkgramSponsoredContentPolicy.removeSponsored('),2)
        self.assertIn('JerkgramLocalPremiumPolicy.effective(value(accountPeerId: accountPeerId).0)',read('TelegramCore/Sources/TelegramEngine/Messages/Translate.swift'))
        tags=read('Postbox/Sources/Postbox.swift')
        self.assertEqual(tags.count('guard JerkgramLocalPremiumPolicy.savedTagsEnabled('),7)
        lifecycle=tags.split('public func updateLocalSavedTagsMetadata',1)[1].split('// END LOCAL SAVED TAGS TRANSACTION API',1)[0]
        self.assertNotIn('JerkgramLocalPremiumPolicy',lifecycle)
    def test_native_picker_has_no_server_fallback_for_local_sessions(self):
        picker=read('TelegramUI/Components/EmojiStatusSelectionComponent/Sources/EmojiStatusSelectionComponent.swift')
        route=codec.declaration(picker,'private func completeLocalSelection(')
        self.assertIn('case .statusSelection:',route)
        self.assertIn('expectedGeneration: self.localAppearanceGeneration',route)
        self.assertIn('guard store.snapshot.emojiUnlocked else { return true }',route)
        self.assertNotIn('engine.',route)
        tap=codec.declaration(picker,'private func applyItem(')
        self.assertIn('if !completedLocally {',tap)
        self.assertLess(tap.index('completeLocalSelection'),tap.index('setEmojiStatus'))
        timer=picker.split('if let result, let previewItem = strongSelf.previewItem',1)[1]
        self.assertLess(timer.index('completeLocalSelection'),timer.index('setStarGiftStatus'))
        self.assertIn('animateOutToStatus',timer.split('if let itemGift',1)[0])
        peer=read('TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift')
        self.assertEqual(peer.count('localAppearance: strongSelf.context.jerkgramLocalAppearance.snapshot.emojiUnlocked'),2)
        appearance=read('TelegramUI/Components/Settings/PeerNameColorScreen/Sources/UserApperanceScreen.swift')
        local=appearance.split('if component.localAppearance {',1)[1].split('if resolvedState.changes.isEmpty',1)[0]
        self.assertIn('guard store.snapshot.colorsUnlocked',local)
        self.assertNotIn('settings.colorsEnabled = true',local)
        self.assertNotIn('engine.',local)
    def test_one_settings_master_no_extra_editor(self):
        text=read('SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift')
        page=text.split('if page == .localPremium {',1)[1].split('if page == .stars {',1)[0]
        self.assertEqual(page.count('.toggle(0, 1, JerkgramLocalPremiumPolicy.preferenceKey'),1)
        self.assertIn('Разблокировать локальный Premium',page)
        self.assertIn('Unlock Local Premium',page)
        self.assertIn('enabled: enabled',text)
        self.assertNotIn('makeJerkgramProfileAppearanceController',text)
        self.assertNotIn('case localAppearance',text)
        self.assertNotIn('EmojiStatusSelectionController',read('TelegramUI/Sources/JerkgramProfileAppearanceController.swift'))
        self.assertNotIn('makeJerkgramProfileAppearanceController',read('AccountContext/Sources/AccountContext.swift'))
        settings=read('TelegramCore/Sources/Settings/JerkgramLocalAppearanceSettings.swift')
        self.assertIn('owner == recordId && peer == ownPeerId',settings)
        self.assertIn('ownIsBot == false && !displayedIsBot',settings)
    def test_fixture_assembled_from_actual_owners(self):
        text=fixture()
        self.assertIn('OFF ON rejects stale callback',text)
        self.assertIn('server peer never mutated',text)
        self.assertIn('public func project(',text)
    def test_native_matrix(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE')=='1': self.fail('Premium native matrix requires macOS Swift; refusing CI skip')
            self.skipTest('native Swift unavailable; CI must set JG_STABLE182_REQUIRE_NATIVE=1')
        with tempfile.TemporaryDirectory(prefix='stable182-premium-') as directory:
            folder=Path(directory); (folder/'main.swift').write_text(fixture())
            for opt in ('-Onone','-O'):
                executable=codec.compile_fixture(folder,opt,main_override=fixture())
                result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=='__main__': unittest.main(verbosity=2)
