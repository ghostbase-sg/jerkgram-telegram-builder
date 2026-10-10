import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
P = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/"
class ExpandedDiagnosticsTests(unittest.TestCase):
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
            self.assertIn('setVisibleRoute("'+route+'")',s)
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
            gate.check(fixture,"after")
            for name in manifest["owners"]:
                target=fixture/name;before=target.read_bytes()
                target.write_bytes(before+b"\n// hash-preserving-marker tamper\n")
                with self.assertRaisesRegex(RuntimeError,"after hash mismatch"):
                    gate.check(fixture,"after")
                target.write_bytes(before)
    def test_canonical_gate_after_preferences(self):
        s=(ROOT / "scripts/materialize_jg13.py").read_text()
        self.assertLess(s.index('    apply_preferences(SOURCE)'),s.index('    apply_expanded(SOURCE)'))
        self.assertIn("verify_expanded",(ROOT / "scripts/verify_jg13_source.py").read_text())
if __name__ == '__main__': unittest.main()
