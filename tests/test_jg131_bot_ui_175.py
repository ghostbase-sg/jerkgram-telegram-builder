"""Build175 visible bot UI owners; native fixtures execute extracted production policies."""
import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[2]
ORIGINAL=Path('/home/pixi/Projects/Jerkgram/iOS/jerkgram-telegram-builder/work/swiftgram-src')
PREFIX='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
def source(name):
 root=os.environ.get('JG_BOT_SOURCE')
 if not root and not (PACKAGE/'settings-transparency').exists(): root=Path(__file__).resolve().parents[1]/'work/swiftgram-src'
 if root: return (Path(root)/name).read_text()
 for stage in ['profile-polish','profile-metadata','excluded-history','settings-transparency','performance-followup','translation']:
  p=PACKAGE/stage
  if (p/'owners.json').exists() and name in json.loads((p/'owners.json').read_text()): return (p/'after'/name).read_text()
 return (ORIGINAL/name).read_text()
def function(text,name):
 start=text.index('private func '+name+'(')
 opening=text.index('{',start); depth=1; end=opening+1
 while depth:
  depth += (text[end]=='{')-(text[end]=='}'); end+=1
 return text[start:end].replace('private func ','func ',1)
class BotUI175Tests(unittest.TestCase):
 def test_visible_native_settings_rows_guarded(self):
  s=source(PREFIX+'PeerInfoSettingsItems.swift')
  self.assertIn('let isBotAccount = jerkgramSettingsIsBotAccount(',s)
  self.assertIn('hasBotInfo = user.botInfo != nil',s)
  self.assertIn('persistentMarker: UserDefaults.standard.bool',s)
  for token in ['text: presentationData.strings.jerkgram.ghostMode','text: presentationData.strings.CallSettings_RecentCalls']:
   idx=s.index(token); start=s.rfind('if !isBotAccount {',0,idx)
   self.assertGreater(start,0)
   self.assertNotIn('\n    }',s[start:idx])
 def test_inner_page_uses_persistent_marker_even_with_partial_peer(self):
  s=source('submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift')
  self.assertIn('isBotAccount = user.botInfo != nil || persistentBotAccount',s)
  self.assertIn('if isBotAccount && page == .ghostMode { return [] }',s)
 def test_root_initial_and_updated_tabs_guarded(self):
  s=source('submodules/TelegramUI/Sources/TelegramRootController.swift')
  self.assertEqual(s.count('if showCallsTab && !UserDefaults.standard.bool(forKey: "jerkgram.BotAccount.'),2)
 def test_header_and_badge_call_production_policy(self):
  self.assertIn('jerkgramSettingsSubtitle(phone:',source(PREFIX+'PeerInfoHeaderNode.swift'))
  s=source(PREFIX+'ListItems/PeerInfoScreenMemberItem.swift')
  self.assertIn('string: jerkgramBotAccountBadge(languageCode: presentationData.strings.baseLanguageCode)',s)
  self.assertIn('user.botInfo != nil || UserDefaults.standard.bool',s)
 @unittest.skipUnless(shutil.which('swiftc'),'Swift compiler unavailable; native production-policy fixture requires macOS')
 def test_actual_production_policy_fixtures(self):
  funcs='\n'.join(function(source(PREFIX+file),name) for file,name in [
   ('PeerInfoSettingsItems.swift','jerkgramSettingsIsBotAccount'),
   ('PeerInfoHeaderNode.swift','jerkgramSettingsSubtitle'),
   ('ListItems/PeerInfoScreenMemberItem.swift','jerkgramBotAccountBadge')])
  fixtures='''
assert(!jerkgramSettingsIsBotAccount(hasBotInfo: false, persistentMarker: false))
assert(jerkgramSettingsIsBotAccount(hasBotInfo: false, persistentMarker: true))
assert(jerkgramSettingsIsBotAccount(hasBotInfo: true, persistentMarker: false))
assert(jerkgramSettingsSubtitle(phone: "", username: "bot") == "@bot")
assert(jerkgramSettingsSubtitle(phone: "+123", username: "user") == "+123 • @user")
assert(jerkgramSettingsSubtitle(phone: "+123", username: nil) == "+123")
assert(jerkgramSettingsSubtitle(phone: "", username: nil) == "")
assert(jerkgramSettingsSubtitle(phone: "", username: "") == "")
assert(jerkgramBotAccountBadge(languageCode: "ru") == "БОТ")
assert(jerkgramBotAccountBadge(languageCode: "ru-RU") == "БОТ")
assert(jerkgramBotAccountBadge(languageCode: "en") == "BOT")
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+funcs+fixtures)
   subprocess.run(['swiftc',str(p),'-o',d+'/fixture'],check=True)
   subprocess.run([d+'/fixture'],check=True)
if __name__=='__main__': unittest.main()
