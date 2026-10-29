"""Integration contracts for coherent profile revision wiring, not rendered UIKit tests."""
import os,unittest
from pathlib import Path
SOURCE=Path(os.environ.get('JG_WAVE1_SOURCE',str(Path(__file__).resolve().parents[1]/'work/swiftgram-src')))
P='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
class ProfileRevisionContracts(unittest.TestCase):
 def test_root_refreshes_all_retained_visual_owners(self):
  s=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
  self.assertTrue('override public func jerkgramSettingsVisualStateUpdated()' in s, 'missing revision hook')
  self.assertIn('self.jerkgramTracksVisualSettings = true',s)
  a=s.index('func reconcileJerkgramVisualState(');b=s.index('func setGhostBaseProfileBackgroundActive',a)
  body=s[a:b]
  for owner in ['headerNode.updateJerkgramVisualState','paneContainerNode.updateJerkgramVisualState','ghostBaseProfileMetricsSettings = GhostBaseProfileMetricsSettings.load()','sectionNode.updateJerkgramVisualState']:
   self.assertTrue(owner in body,owner)
  self.assertIn('self.isNodeLoaded',s[s.index('override public func jerkgramSettingsVisualStateUpdated()'):][:350])
 def test_enable_after_initial_nil_can_create_background(self):
  s=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
  self.assertIn('fileprivate var ghostBaseProfileBackgroundView:',s)
  body=s[s.index('func reconcileJerkgramVisualState('):s.index('func setGhostBaseProfileBackgroundActive')]
  self.assertTrue('ensureJerkgramBackground(settings: settings, attachToRoot: true)' in body)
  self.assertIn('setSceneActive(false)',body)
  self.assertTrue('background.setSceneActive(true)' in s[s.index('private func ensureJerkgramBackground'):s.index('// Reconcile once per coherent revision')], 'new visible background must activate')
  self.assertIn('removeFromSuperview()',body)
 def test_header_and_sections_are_mutable_revision_consumers(self):
  for name in ['PeerInfoHeaderNode.swift','PeerInfoScreenItemSectionContainerNode.swift']:
   s=(SOURCE/(P+name)).read_text();self.assertIn('func updateJerkgramVisualState(',s)
   self.assertNotIn('private let ghostBaseProfileGlassSettings',s)
   self.assertNotIn('private let ghostBaseGlassEnabled',s)
 def test_disabling_glass_clears_owned_bio_mask(self):
  s=(SOURCE/(P+'PeerInfoScreenItemSectionContainerNode.swift')).read_text()
  self.assertTrue('self.itemContainerNode.layer.mask === self.bioContentMask' in s,'native fallback must clear old owned mask')
 def test_accessibility_fields_and_cards_restore_native_fill(self):
  for name in [P+'PeerInfoScreenMultilineInputtem.swift','submodules/ItemListUI/Sources/Items/ItemListMultilineInputItem.swift',P+'GhostBaseProfileReportPaneNode.swift']:
   text=(SOURCE/name).read_text()
   self.assertTrue('GhostBaseGlassStyle.allowsTransparentSurfaces' in text,name)
 def test_hidden_root_export_reuses_descendant_without_full_reconcile(self):
  text=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
  body=text.split('func makeSettingsBackdropView(existing: UIView? = nil)',1)[-1].split('    }',1)[0]
  self.assertTrue('ensureJerkgramBackground' in body,'visible child must lazily ensure source after master enable')
  self.assertTrue('reconcileJerkgramVisualState' not in body,'hidden root must avoid full visual/layout reconciliation')
  self.assertTrue('existing: existing' in text,'preserve child material identity')
 def test_hidden_theme_update_stores_value_without_layout(self):
  s=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
  body=s.split('func updatePresentationData(_ presentationData: PresentationData)',1)[1].split('private func updateNavigationHeight',1)[0]
  self.assertTrue('guard self.ghostBaseProfileSceneVisible else { return }' in body,'theme delta must defer hidden root layout')
  self.assertLess(body.index('self.presentationData = presentationData'),body.index('guard self.ghostBaseProfileSceneVisible'))
  self.assertLess(body.index('guard self.ghostBaseProfileSceneVisible'),body.index('self.updateBackgroundColor()'))
 def test_no_direct_unversioned_theme_post(self):
  s=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
  self.assertNotIn('NotificationCenter.default.post(name: GhostBaseGlassStyle.settingsStyleDidChange',s)
if __name__=='__main__':unittest.main()
