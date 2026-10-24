import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
P = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/"
class ExpandedDiagnosticsTests(unittest.TestCase):
    def test_client_hooks_preserve_every_original_source_byte(self):
        import hashlib,json,re
        manifest=json.loads((ROOT/'patches/jg13-expanded-diagnostics.sha256.json').read_text())
        for path in ('submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift','submodules/TelegramUI/Sources/ChatControllerNode.swift','submodules/TelegramUI/Sources/ChatHistoryListNode.swift','submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift','submodules/TelegramUI/Sources/CoreListChatHistoryBackend.swift','submodules/TelegramUI/Components/Chat/ChatMessageItemImpl/Sources/ChatMessageItemImpl.swift'):
            text=(SOURCE/path).read_text()
            import sys
            sys.path.insert(0, str(ROOT / "scripts"))
            from materialize_jg13_history_backend import preceding_owner
            text=preceding_owner(path, text)
            text=re.sub(r'JerkgramPerformanceDiagnostics.shared.measureOperation\(\.\w+\) \{ ([^\n]+) \}',r'\1',text)
            if path.endswith('CoreListChatHistoryBackend.swift'):
                text=text.replace('import TelegramCore\n','',1)
            if path.endswith('ChatHistoryListNode.swift'):
                # Exactly one behavior change: single-pass equivalent ID/max
                # bounds, covered by actual native fragment/reference cases.
                text=re.sub(r'            // JG155 bounds begin[^\n]*\n.*?            // JG155 bounds end', '            let previousIds = Set(previous.originalView.entries.map { $0.message.id })\n            let previousLastIndex = previous.originalView.entries.map { $0.message.index }.max()', text, flags=re.S)
                start=text.index('    private func jgHistoryTransaction(')
                brace=text.index(') {',start)+2
                end,depth=brace+1,1
                while depth:
                    depth+=(text[end]=='{')-(text[end]=='}');end+=1
                self.assertEqual(text[end:end+2],'\n\n')
                text=text[:start]+text[end+2:]
                text=text.replace('self.jgHistoryTransaction(', 'self.listView.chatHistoryTransaction(')
                text=re.sub(r'\n        let jgBackend = JerkgramPerformanceDiagnostics.shared.beginOperation\(self.usesCoreListBackend \? .historyBackendCore : .historyBackendLegacy\)\n        defer \{ JerkgramPerformanceDiagnostics.shared.endOperation\(jgBackend\) \}', '',text)
            text=re.sub(r'            do \{\n                let jgOperation = JerkgramPerformanceDiagnostics.shared.beginOperation\(.inputDecorate\)\n                defer \{ JerkgramPerformanceDiagnostics.shared.endOperation\(jgOperation\) \}\n([^\n]+decorateAfterTextChange[^\n]+)\n            \}',r'\1',text)
            text=re.sub(r'\n[ ]{8,12}let jgOperation = JerkgramPerformanceDiagnostics.shared.beginOperation\(\.\w+\)\n[ ]{8,12}defer \{ JerkgramPerformanceDiagnostics.shared.endOperation\(jgOperation\) \}', '',text)
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), manifest['owners'][path]['before_sha256'],path)
    def test_owner_checked_route_release(self):
        s=(SOURCE / 'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift').read_text()
        self.assertIn('private weak var visibleRouteOwner: AnyObject?', s)
        self.assertIn('public func clearVisibleRoute(owner: AnyObject)', s)
        self.assertIn('guard self.visibleRouteOwner === owner else {', s)
        self.assertIn('routeReleasesIgnored', s)
        for path in ('submodules/TelegramUI/Sources/ChatController.swift', 'submodules/ChatListUI/Sources/ChatListController.swift', P+'PeerInfoScreen.swift'):
            text=(SOURCE/path).read_text()
            self.assertIn('clearVisibleRoute(owner: self)',text)
            self.assertNotIn('setVisibleRoute("other")',text)
    def test_operation_budget_and_real_callers(self):
        s=(SOURCE / 'submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift').read_text()
        self.assertIn('public enum Operation: String, CaseIterable',s)
        self.assertIn('self.measure("client.work"',s)
        self.assertIn('public func reserveClientWork()',s)
        owner=(SOURCE/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
        self.assertIn('JerkgramPerformanceDiagnostics.shared.reserveClientWork()',owner)
        self.assertIn('generation: self.generation',s)
        for path, names in (
            ('submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift', ('inputText','inputLayout','inputDecorate')),
            ('submodules/TelegramUI/Sources/ChatControllerNode.swift', ('keyboardLayout','historyScroll')),
            ('submodules/TelegramUI/Sources/ChatHistoryListNode.swift', ('historyUpdate','historyVisible','historyLayout')),
            ('submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift', ('mediaState','mediaFill')),
            ('submodules/TelegramUI/Sources/ChatController.swift', ('chatOpen',))):
            text=(SOURCE/path).read_text()
            for name in names:
                self.assertIn('beginOperation(.'+name+')',text)
            self.assertIn('defer { JerkgramPerformanceDiagnostics.shared.endOperation(jgOperation) }',text)
    def test_editing_overload_is_exact_preference_injection(self):
        import sys
        sys.path.insert(0,str(ROOT/'tests'))
        from run_jg13_secondary_timebase import block
        original=block((SOURCE/(P+'PeerInfoSettingsItems.swift')).read_text(),'func settingsEditingItems(')
        screen=(SOURCE/(P+'PeerInfoScreen.swift')).read_text()
        overload=block(screen,'private func settingsEditingItems(')
        normalized=overload.replace('private func','func',1).replace(', hideOwnPhone: Bool','',1).replace('hideOwnPhone ?','((UserDefaults.standard.object(forKey: "jerkgram.Appearance.HideOwnPhone") as? Bool) ?? false) ?')
        self.assertEqual([line.rstrip() for line in normalized.splitlines()], [line.rstrip() for line in original.splitlines()])
        self.assertIn('isMyProfile: self.isMyProfile, hideOwnPhone: GhostBaseGlassStyle.profileHideOwnPhone)',screen)
    def test_section_operations_and_locked_row_owner(self):
        s=(SOURCE / (P+"PeerInfoScreen.swift")).read_text()
        for name in ("sectionsBuild", "sectionsRegularUpdate", "sectionsRegularPlacement", "sectionsRegularRemoval", "sectionsEditingBuild", "sectionsEditingUpdate", "sectionsEditingPlacement", "sectionsEditingRemoval"):
            self.assertIn('"settings.'+name+'"',s)
        self.assertEqual(s.count('sectionNode.update(context: self.context, width: sectionWidth'),2)
    def test_frames_routes_and_bounds(self):
        core=(SOURCE / "submodules/TelegramCore/Sources/Utils/JerkgramPerformanceDiagnostics.swift").read_text()
        for name in ("setVisibleRoute", "sampleRefreshOpportunity", "missedOpportunities", "frameIntervals", "timingKeysRejected", "600.0", "capacity = 512", "timings.count < 32"):
            self.assertIn(name,core)
        settings=(SOURCE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text()
        for name in ("CADisplayLink", ".common", "invalidate()", "snapshotChanged", "JerkgramRefreshIntervalProbe", "targetTimestamp"):
            self.assertIn(name,settings)
        self.assertNotIn("preferredFramesPerSecond",settings)
        for file,route in (("ChatController.swift","chat"),("ChatListController.swift","chatList")):
            s=(SOURCE / (("submodules/ChatListUI/Sources/" if route == "chatList" else "submodules/TelegramUI/Sources/")+file)).read_text()
            self.assertIn('setVisibleRoute("'+route+'", owner: self)',s)
            self.assertIn('measure("'+route+'.layout"',s)
    def test_full_hash_gate_rejects_tamper_in_every_new_owner(self):
        import sys, json, shutil, tempfile
        sys.path.insert(0, str(ROOT / "scripts"))
        import materialize_jg13_expanded_diagnostics as gate
        manifest=json.loads(gate.MANIFEST.read_text())
        with tempfile.TemporaryDirectory() as directory:
            fixture=Path(directory)
            for name in set(manifest["owners"]) | set(manifest["regression_locks"]):
                target=fixture/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(SOURCE/name,target)
            import hashlib
            from configure_jg13_release_ui import OWNER, read_manifest, verify_release_ui
            release = read_manifest()
            final_owners = verify_release_ui(SOURCE) if hashlib.sha256((SOURCE / OWNER).read_bytes()).hexdigest() != manifest['owners'][OWNER]['after_sha256'] else {}
            gate.check(fixture,"after", final_owners=final_owners)
            for name in manifest["owners"]:
                target=fixture/name;before=target.read_bytes()
                target.write_bytes(before+b"\n// hash-preserving-marker tamper\n")
                with self.assertRaisesRegex(RuntimeError,"after hash mismatch"):
                    gate.check(fixture,"after", final_owners=final_owners)
                target.write_bytes(before)
    def test_canonical_gate_after_preferences(self):
        s=(ROOT / "scripts/materialize_jg13.py").read_text()
        self.assertLess(s.index('    apply_preferences(SOURCE)'),s.index('    apply_expanded(SOURCE)'))
        self.assertIn("verify_expanded",(ROOT / "scripts/verify_jg13_source.py").read_text())
if __name__ == '__main__': unittest.main()
