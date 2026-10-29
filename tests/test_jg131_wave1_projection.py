import unittest
import os
from pathlib import Path
ROOT=Path(os.environ.get('B1_SOURCE_ROOT',str(Path(__file__).resolve().parents[1]/'work/swiftgram-src')))
G=ROOT/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'
S=ROOT/'submodules/TelegramUI/Sources/SharedAccountContext.swift'
A=ROOT/'submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift'
class ProjectionContracts(unittest.TestCase):
 def test_page_constructor_does_not_project(self):
  page=G.read_text().split('private func ghostBaseSettingsPageController(')[1].split('let statePromise')[0]
  self.assertNotIn('jerkgramProjectActiveSettings(',page)
 def test_scoped_load_is_read_only(self):
  readers=G.read_text().split('private func jerkgramScopedBool(')[1].split('private enum JerkgramSettingValue')[0]
  self.assertNotIn('.set(',readers)
 def test_existing_activation_uses_shared_projection(self):
  self.assertIn('jerkgramActivateAccountSettings(accountPeerId: accountPeerId)',S.read_text())
 def test_import_uses_shared_projection_after_transaction(self):
  self.assertIn('jerkgramActivateAccountSettings(accountPeerId: snapshot.accountPeerId)',A.read_text())
 def test_no_unconditional_hot_invalidation(self):
  self.assertNotIn('defer { JerkgramHotSettings.invalidate() }',G.read_text())
 def test_delta_comparison_precedes_all_setters(self):
  self.assertIn('JerkgramSettingsProjection.writeIfChanged',G.read_text())
 def test_single_atomic_playback_publication(self):
  body=G.read_text().split('private func jerkgramPersistChangedSettings(')[1].split('// Regression sentinel')[0]
  self.assertEqual(body.count('GhostBaseGlassStyle.setProfilePlaybackSettings('),1)
  self.assertNotIn('GhostBaseGlassStyle.setSettingsTranslucencyEnabled(',body)
 def test_snapshot_catalog_preserves_49_keys(self):
  values=G.read_text().split('private func jerkgramStateValues')[1].split('private func jerkgramPersistChangedSettings')[0]
  self.assertEqual(values.count(': .'),49)
 def test_no_secondary_visual_publication_in_page(self):
  page=G.read_text().split('private func ghostBaseSettingsPageController(')[1]
  self.assertNotIn('GhostBaseGlassStyle.setEnabled(',page)
  self.assertNotIn('jerkgram.ProfileVisualSettingsDidChange.V11M',page)
 def test_import_full_catalog_and_aliases_preserved(self):
  body=A.read_text().split('private func jerkgramProjectImportedSettingsToActiveDefaults(')[1].split('private func jerkgramPresentArchiveImportError')[0]
  for catalog in ('snapshot.toggles','snapshot.stringValues','snapshot.integerValues'):
   self.assertIn(catalog,body)
  self.assertIn('GhostBase.GhostMode.ScheduledSend',body)
  self.assertIn('GhostBase.ProtectedContent.OneTimeSave',body)
 def test_migration_only_at_existing_lifecycle(self):
  body=G.read_text().split('public func jerkgramActivateAccountSettings(')[1].split('// Regression sentinel')[0]
  self.assertIn('allowLegacyFallback: defaults.object(forKey: markerKey) == nil',body)
  self.assertEqual(S.read_text().count('jerkgramBuild135ProjectAccountSettings(accountPeerId:'),3)
if __name__=='__main__': unittest.main()
