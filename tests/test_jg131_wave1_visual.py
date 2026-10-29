import shutil, subprocess, tempfile
from pathlib import Path
import unittest, os
base=Path(os.environ.get('VISUAL_SOURCE',str(Path(__file__).resolve().parents[1]/'work/swiftgram-src')))
def source(path): return (base/'submodules'/path).read_text()
class Visual(unittest.TestCase):
 def test_atomic_real_delta(self):
  s=source('Display/Source/GhostBaseGlass.swift'); self.assertIn('public static var visualRevision',s); self.assertIn('guard changed else { return }',s); self.assertIn('settingsTranslucencyEnabled: Bool? = nil',s)
 def test_hidden_dirty(self):
  s=source('Display/Source/ViewController.swift'); self.assertIn('jerkgramSettingsAppearanceVisible',s); self.assertIn('guard self.jerkgramSettingsAppearanceVisible else',s); self.assertIn('ignoreRepeated: true',s); self.assertNotIn('jerkgramSettingsStyleRevision.set(0)',s)
 def test_hidden_releases_attached_output(self):
  s=source('Display/Source/ViewController.swift'); disappearance=s.split('open override func viewDidDisappear(_ animated: Bool) {',1)[1].split('open func viewWillLeaveNavigation',1)[0]
  self.assertIn('jerkgramSettingsBackdropView?.removeFromSuperview()',disappearance)
  self.assertIn('jerkgramSettingsDirtyRevision = GhostBaseGlassStyle.visualRevision',disappearance)
 def test_expired_lease_counter(self):
  s=source('TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift')
  self.assertIn('let previousLayerCount = self.layers.count',s)
  self.assertIn('self.layers.count - previousLayerCount',s)
 def test_retained_backdrop_rebinds_revision(self):
  s=source('Display/Source/ViewController.swift')
  self.assertIn('((UIView?) -> UIView?)?',s)
  self.assertIn('jerkgramSettingsBackdropProvider?(self.jerkgramSettingsBackdropView)',s)
  s=source('TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift')
  self.assertIn('makeSettingsBackdropView(existing: UIView? = nil)',s)
  self.assertIn('existing as? JerkgramSettingsBackdropView',s)
 def test_placeholder_admitted_before_async_source(self):
  s=source('TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift')
  body=s.split('func makeSettingsBackdropView(existing: UIView? = nil)',1)[1].split('private func updateSettingsBackdrop',1)[0]
  self.assertNotIn('guard self.usesCustomBackground',body)
  self.assertIn('self.settingsBackdrops.add(backdrop)',body)
 def test_reduced_native(self):
  s=source('TelegramPresentationData/Sources/PresentationTheme.swift'); self.assertIn('GhostBaseGlassStyle.allowsTransparentSurfaces',s); self.assertNotIn('reduced ? 0.90',s)
 def test_successor_lease(self):
  s=source('TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift'); self.assertIn('let successor = self.window != nil ? session?.attach',s); self.assertIn('GhostBaseGlassStyle.allowsVideo',s); self.assertIn('lastMaterialStyle',s)
class InstrumentedVisibility(unittest.TestCase):
 def test_full_refresh_counter_records_owner_visibility(self):
  s=source('Display/Source/ViewController.swift')
  self.assertTrue('"visibleOwnerRefreshes" : "hiddenOwnerRefreshes"' in s, 'actual full refresh must classify owner visibility')
class NativeVisual(unittest.TestCase):
 @unittest.skipUnless(shutil.which('swift'), 'Swift compiler unavailable; production policy runs on macOS CI')
 def test_actual_production_policy(self):
  text=source('Display/Source/GhostBaseGlass.swift')
  policy=text.split('// JG176 pure policy begin\n')[1].split('// JG176 pure policy end')[0]
  fixture=(Path(__file__).parent/'fixtures/build176/policy_fixture.swift').read_text()
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'main.swift';path.write_text(policy+fixture)
   subprocess.run(['swift',str(path)],check=True)
if __name__=='__main__': unittest.main()
