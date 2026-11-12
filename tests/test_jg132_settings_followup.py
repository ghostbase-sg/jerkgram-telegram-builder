"""Beta3 native Settings corrections; actual Swift autosave behavior requires macOS."""
from pathlib import Path
import os,sys,unittest,subprocess,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_BETA3_SOURCE',ROOT/'work/swiftgram-src'))
SETTINGS=SOURCE/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
STARS=SOURCE/'submodules/SettingsUI/Sources/Jerkgram/JerkgramStarsEditorController.swift'
sys.path.insert(0,str(ROOT/'tests'))
from test_jg131_beta2_bot_codec import declaration

class SettingsFollowup(unittest.TestCase):
 def test_controls_have_one_canonical_hub_owner(self):
  s=SETTINGS.read_text();s=s[s.index('    if page == .root {'):s.index('    if page == .debugResearch {',s.index('    if page == .root {'))]
  for expression in ['JerkgramSponsoredContentPolicy.preferenceKey','JerkgramTranslationSettings.preferenceKey','JerkgramAppIconAccess.preferenceKey','.downloadBoost(']:
   self.assertEqual(s.count(expression),1,expression)
  self.assertIn('.info(2, strings.anonymousAnalyticsDescription)',s)
  self.assertIn('strings.localPremium, "Item List/Icons/Gram"',s)
  self.assertIn('return PresentationResourcesSettings.ton',SETTINGS.read_text())
  self.assertNotIn('translationNeedsWork',s)
  strings=(SOURCE/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
  hint=strings[strings.index('    var localPremiumScopeHint:'): ]
  self.assertNotIn('Translation needs work.',hint)
  self.assertNotIn('Перевод требует доработки.',hint)
 def test_autosave_wiring_preserves_storage(self):
  s=STARS.read_text();self.assertNotIn('Common_Save',s);self.assertNotIn('Common_Cancel',s)
  self.assertIn('controller?.willDisappear',s);self.assertIn('autosave.update(value)',s)
  commit=declaration(s,'private func jerkgramCommitStarsDraft(')
  self.assertEqual(commit.count('defaults.set('),4)
  self.assertIn('accountPeerId',commit)
 def test_common_release_identity(self):
  s=(SOURCE/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
  for key,value in [('displayVersion','1.2.0 Beta 3'),('technicalVersion','1.2.0-beta.3'),('build','180'),('telegramBase','13.2')]:
   self.assertTrue(f'public static let {key} = "{value}"' in s, key)
  self.assertIn('<string>13.2</string>',(SOURCE/'Telegram/BUILD').read_text())
 def test_native_autosave_behavior(self):
  if not shutil.which('swiftc') or sys.platform!='darwin':
   if os.environ.get('JG_BETA3_REQUIRE_NATIVE')=='1':self.fail('requires macOS Swift; native autosave unverified')
   self.skipTest('requires macOS Swift; native autosave unverified')
  s=STARS.read_text()
  code='import Foundation\nimport Dispatch\n'+ '\n'.join(declaration(s,x) for x in ['private struct JerkgramStarsDraftState','private func jerkgramSavedStarsAmount(','private func jerkgramStarsPreset(','private final class JerkgramStarsAutosave'])
  code+=(ROOT/'tests/fixtures/beta3_settings/autosave.swift').read_text()
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'main.swift').write_text(code)
   for opt in ['-Onone','-O']:
    subprocess.run(['swiftc',opt,str(p/'main.swift'),'-o',str(p/'check')],check=True)
    subprocess.run([str(p/'check')],check=True)
if __name__=='__main__':unittest.main(verbosity=2)
