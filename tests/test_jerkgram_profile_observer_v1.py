import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/apply_jerkgram_profile_observer_v1.py"
PAYLOAD = ROOT / "scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileObserver.swift"

spec = importlib.util.spec_from_file_location("jerkgram_profile_observer_patch", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProfileObserverPatchTests(unittest.TestCase):
    def test_update_peers_patches_once(self):
        original = (
            "func updatePeers(transaction: Transaction, accountPeerId: PeerId, peers: AccumulatedPeers) {\n"
            "    updatePeersCustom(transaction: transaction, peers: parsedPeers, update: { _, updated in updated })\n"
            "}\n"
        )
        patched = module.patch_update_peers(original)
        self.assertIn("jerkgramObserverExcludingPeerId: PeerId? = nil", patched)
        self.assertIn("jerkgramProfileObserverUpdatedPeers(", patched)
        self.assertEqual(module.patch_update_peers(patched), patched)

    def test_full_user_combines_bio_and_identity(self):
        original = (
            "                                let userFullNotifySettings = userFullData.notifySettings\n"
            "                                updatePeers(transaction: transaction, accountPeerId: accountPeerId, peers: parsedPeers)\n"
        )
        patched = module.patch_full_user(original)
        self.assertIn("jerkgramObserverExcludingPeerId: peerId", patched)
        self.assertIn("jerkgramProfileObserverFullUser(", patched)
        self.assertIn("about: userFullData.about", patched)
        self.assertEqual(module.patch_full_user(patched), patched)

    def test_user_profile_open_enrolls_once(self):
        original = (
            "            ghostBaseRecordObservedProfileV11G(\n"
            "                accountPeerId: self.context.account.peerId,\n"
            "                peer: peer,\n"
            "                cachedData: data.cachedData\n"
            "            )\n"
        )
        patched = module.patch_profile_ui(original)
        self.assertEqual(patched.count("jerkgramProfileObserverBegin("), 1)
        self.assertEqual(module.patch_profile_ui(patched), patched)

    def test_build_dep_is_idempotent(self):
        original = '    deps = [\n        "//submodules/Postbox:Postbox",\n    ]\n'
        patched = module.patch_core_build(original)
        self.assertIn('"//submodules/sqlcipher:sqlcipher"', patched)
        self.assertEqual(module.patch_core_build(patched), patched)

    def test_observation_does_not_inherit_presence(self):
        swift = PAYLOAD.read_text(encoding="utf-8")
        self.assertIn("guard enroll || self.watched.contains(key) else { return }", swift)
        self.assertIn("guard self.watched.contains(key) else { continue }", swift)
        self.assertIn('return ["baseline"]', swift)
        self.assertIn("if let previous, next == previous { return }", swift)
        self.assertIn("qos: .utility", swift)
        self.assertNotIn("UserDefaults.standard", swift)
        self.assertNotIn("TelegramUserPresence", swift)
        self.assertNotIn("Timer.scheduledTimer", swift)
        self.assertNotIn("maximumEvents", swift)

    def test_anchors_fail_closed(self):
        with self.assertRaises(RuntimeError):
            module.patch_update_peers("func updatePeers() {}")
        with self.assertRaises(RuntimeError):
            module.patch_full_user("switch fullUser {}")


if __name__ == "__main__":
    unittest.main()
