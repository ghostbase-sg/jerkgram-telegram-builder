"""Selected Telegram language coverage, including regional RU packs."""
from pathlib import Path
import os,re,shutil,subprocess,tempfile,unittest
ROOT=Path(os.environ.get('JG_LOCALIZATION_SOURCE',Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
OWNER='submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
class LocalizationTests(unittest.TestCase):
 def test_recent_features_use_current_localization(self):
  s=(ROOT/OWNER).read_text()
  for prop in ['mutualContact','registrationEstimate','translucentSettings','removedFromChat','localTranslationUnavailable','archiveErrorGeneric']:
   self.assertTrue('var '+prop+': String' in s,prop)
  panel=(ROOT/'submodules/TelegramUI/Sources/JerkgramExcludedChatInputPanelNode.swift').read_text()
  self.assertIn('JerkgramStrings(baseLanguageCode:',panel)
  self.assertIn('.removedFromChat',panel)
  self.assertNotIn('baseLanguageCode == "ru"',panel)
  backup=(ROOT/'submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift').read_text()
  self.assertNotIn('(Forever + Unlimited)',backup)
  self.assertIn('strings.archiveFormat',backup)
 @unittest.skipUnless(shutil.which('swiftc'),'Swift unavailable: actual localization fixture runs in macOS CI')
 def test_actual_current_language_and_fallback_for_all_keys(self):
  s=(ROOT/OWNER).read_text().replace('import PresentationStrings','')
  s=re.sub(r'public extension PresentationStrings \{.*?\n\}\n', '', s, flags=re.S)
  fixture=r'''
for code in ["ru", "RU", "ru-RU", "ru_RU", "RU-raw"] {
 let strings=JerkgramStrings(baseLanguageCode: code)
 assert(strings.mutualContact=="Взаимный контакт")
 assert(strings.removedFromChat=="Вы были исключены из этого чата")
 assert(strings.localTranslationRetry=="Повторить перевод")
 for key in JerkgramStringKey.allCases { assert(!strings.text(key).isEmpty) }
}
for code in ["en", "en-US", "en_raw", "xx"] {
 let strings=JerkgramStrings(baseLanguageCode: code)
 assert(strings.mutualContact=="Mutual Contact")
 assert(strings.removedFromChat=="You were removed from this chat")
 for key in JerkgramStringKey.allCases { assert(!strings.text(key).isEmpty) }
}
print("current-language RU/EN/fallback PASS")
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text(s+fixture)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
if __name__=='__main__':unittest.main()
