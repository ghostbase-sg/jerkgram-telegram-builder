import importlib.util
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


class NoAdsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = REPO / "scripts/apply_jerkgram_build140_no_ads1.py"
        spec = importlib.util.spec_from_file_location("build140_no_ads", path)
        cls.patch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.patch)

    def test_chat_sponsored_state_is_replaced_with_nil_signal(self):
        source = "before\n" + self.patch.CHAT_OWNER + "after\n"
        actual = self.patch.patch_chat_history_list(source)
        self.assertIn(self.patch.CHAT_MARKER, actual)
        self.assertIn("adMessagesState = .single(nil)", actual)
        self.assertNotIn("adMessagesContext.state", actual)
        self.assertEqual(actual, self.patch.patch_chat_history_list(actual))

    def test_gallery_ad_subscription_is_removed_and_state_is_cleared(self):
        source = '''func setMessage(context: AccountContext, message: Message) {
        self.context = context
        guard self.message?.id != message.id else {
            return
        }
        self.message = message
        
        let adContext = context.engine.messages.adMessages(peerId: message.id.peerId, messageId: message.id)
        self.adContext = adContext
        self.adDisposable.set((adContext.state
        |> deliverOnMainQueue).start(next: { [weak self] state in
            self.adState = (state.startDelay, state.betweenDelay, state.messages)
            var schedule: [(Int32, Message?)] = []
            self.adSchedule = schedule
        }))
    }
'''
        actual = self.patch.patch_video_gallery(source)
        self.assertIn(self.patch.GALLERY_MARKER, actual)
        self.assertNotIn("context.engine.messages.adMessages", actual)
        self.assertNotIn("adContext.state", actual)
        self.assertIn("self.adDisposable.set(nil)", actual)
        self.assertIn("self.adState = nil", actual)
        self.assertIn("self.adSchedule = []", actual)
        self.assertEqual(actual, self.patch.patch_video_gallery(actual))

    def test_patch_has_no_global_premium_spoof_or_download_changes(self):
        patch_source = (REPO / "scripts/apply_jerkgram_build140_no_ads1.py").read_text(encoding="utf-8")
        self.assertNotIn("isPremium = true", patch_source)
        self.assertNotIn("isPremium: true", patch_source)
        self.assertNotIn("downloadSpeedBoost", patch_source)
        self.assertNotIn("getSGDownloadPartSize", patch_source)

    def test_runtime_chain_runs_no_ads_before_identity(self):
        installer = (REPO / "scripts/install_jerkgram_v12w_build133_probe_hook.py").read_text(encoding="utf-8")
        apply_name = "apply_jerkgram_build140_no_ads1.py"
        verify_name = "verify_jerkgram_build140_no_ads1.py"
        identity_name = "apply_jerkgram_build140_identity.py"
        self.assertEqual(installer.count(apply_name), 1)
        self.assertEqual(installer.count(verify_name), 1)
        self.assertLess(installer.index(apply_name), installer.index(verify_name))
        self.assertLess(installer.index(verify_name), installer.index(identity_name))
        self.assertIn("tests.test_jerkgram_build140_no_ads1", installer)


if __name__ == "__main__":
    unittest.main()
