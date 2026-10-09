"""Target-only structural contracts; not a Swift compile or device performance test."""
import os
import shutil
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
sys.path.insert(0, str(ROOT / "scripts"))
import materialize_jg13_profile_cleanup as cleanup
PROFILE = "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/"

def source(path):
    return (SOURCE / path).read_text()

class ProfileCleanupTests(unittest.TestCase):
    def test_full_hash_gate_rejects_marker_preserving_tamper(self):
        import json
        owners = json.loads(cleanup.MANIFEST.read_text())["owners"]
        final_owners = json.loads((ROOT / "patches/jg13-profile-p0-diagnostics.sha256.json").read_text())["owners"] if os.environ.get("JG13_P0_FINAL") == "1" else None
        self.assertEqual(len(owners), 7)
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for name in owners:
                target = fixture / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(SOURCE / name, target)
            cleanup.check_hashes(fixture, "after", final_owners=final_owners)
            with (fixture / next(iter(owners))).open("a") as output:
                output.write("\n// Marker-preserving tamper\n")
            with self.assertRaisesRegex(RuntimeError, "after owner hash mismatch"):
                cleanup.check_hashes(fixture, "after", final_owners=final_owners)

    def test_persistent_stack_and_layout_no_processing(self):
        text = source(PROFILE + "GhostBaseProfileFullscreenBackground.swift")
        self.assertEqual(text.count("UIVisualEffectView(effect:"), 1)
        self.assertEqual(text.count("self.imageView = UIImageView()"), 1)
        self.assertEqual(source(PROFILE + "PeerInfoScreen.swift").count("GhostBaseProfileBackgroundView("), 1)
        self.assertNotIn("AVPlayer(", text)
        self.assertNotIn("UniversalVideoNode(", text)
        self.assertIn("cache.countLimit = 64", text)
        self.assertIn("ghostBaseAvatarDiskCacheLimit = 48", text)
        layout = text.split("override func layoutSubviews()", 1)[1].split("override func didMoveToWindow()", 1)[0]
        for token in ("sampledTint(", "UIImage(", ".start(", "UIGraphics", "UIVisualEffectView("):
            self.assertNotIn(token, layout)

    def test_avatar_worker_and_warm_hit(self):
        text = source(PROFILE + "GhostBaseProfileFullscreenBackground.swift")
        apply = text.split("private func apply(", 1)[1].split("private func", 1)[0]
        self.assertNotIn("ghostBaseLoadAvatarDiskCache(", apply)
        ram = apply.split("// Final avatar RAM hit", 1)[1].split("self.currentLoadKey = loadKey", 1)[0]
        self.assertIn("return", ram)
        worker = text.split("private func avatarEntrySignal(", 1)[1].split("private func resourceEntrySignal", 1)[0]
        self.assertIn("return deferred", worker)
        self.assertIn("ghostBaseLoadAvatarDiskCache", worker)
        self.assertIn("|> runOn(Queue.concurrentDefaultQueue())", worker)
        self.assertIn("completeOnly: true", worker)
        self.assertIn("synchronousLoad: false", worker)

    def test_scene_lifecycle(self):
        text = source(PROFILE + "GhostBaseProfileFullscreenBackground.swift")
        self.assertTrue("func setSceneActive(" in text, "Missing appearance lifecycle gate")
        lifecycle = text.split("func setSceneActive(", 1)[1].split("private func", 1)[0]
        disposal = "self.sourceDisposable.set(nil)"
        if os.environ.get("JG13_P0_FINAL") == "1":
            disposal = "self.setSourceSubscription(nil)"
            wrapper = text.split("private func setSourceSubscription(", 1)[1].split("private func", 1)[0]
            self.assertIn("self.sourceDisposable.set(value)", wrapper)
            self.assertEqual(text.count("self.sourceDisposable.set("), 1)
        for token in (disposal, "self.secondaryVideoDisposable?.dispose()", "self.currentLoadKey = nil"):
            self.assertIn(token, lifecycle)
        self.assertIn("guard self.isSceneActive else", text)
        for token in ("UIApplication.willResignActiveNotification", "UIApplication.didBecomeActiveNotification", "active && self.isApplicationActive", "self.lifecycleObservers", "NotificationCenter.default.removeObserver(observer)"):
            self.assertTrue(token in text, f"Missing application lifecycle contract: {token}")
        screen = source(PROFILE + "PeerInfoScreen.swift")
        self.assertIn("override public func viewDidDisappear", screen)
        self.assertIn("setGhostBaseProfileBackgroundActive(false)", screen)
        self.assertIn("setGhostBaseProfileBackgroundActive(true)", screen)

    def test_number_card_container_background_opt_in(self):
        settings = source(PROFILE + "PeerInfoSettingsItems.swift")
        phone = settings.split("settings.suggestPhoneNumberConfirmation", 1)[1].split("settings.suggestPasswordConfirmation", 1)[0]
        self.assertIn("usesContainerBackground: true", phone)
        for action in ("Settings_KeepPhoneNumber", "dismissServerProvidedSuggestion", "interaction.openSettings(.phoneNumber)", "interaction.openFaq"):
            self.assertIn(action, phone)
        section = source(PROFILE + "PeerInfoScreenItemSectionContainerNode.swift")
        self.assertIn("infoItem.ghostBaseContainerBackgroundEnabled = self.ghostBaseGlassEnabled", section)
        info = source(PROFILE + "ListItems/PeerInfoScreenInfoItem.swift")
        self.assertIn("item.usesContainerBackground && item.ghostBaseContainerBackgroundEnabled", info)
        self.assertIn("usesContainerBackground: Bool = false", info)
        self.assertIn("var ghostBaseContainerBackgroundEnabled = false", info)
        item = source("submodules/ItemListUI/Sources/Items/ItemListInfoItem.swift")
        self.assertIn("public func setBackgroundOwnedByContainer", item)
        self.assertIn("self.backgroundNode.isHidden = value", item)
        for text in (section, info, item):
            self.assertNotIn("UIVisualEffectView(", text)

    def test_no_seasonal_user_flow_normal_gifts_retained(self):
        text = source("submodules/TelegramUI/Components/Gifts/GiftOptionsScreen/Sources/GiftOptionsScreen.swift")
        for token in ("Seasonal", "seasonal", "DeletedGiftsStickers"):
            self.assertFalse(token in text, f"Forbidden gifting token: {token}")
        for token in ("cachedStarGifts()", "case .resale:", "case .transfer:", "ProfileGiftsContext", "GiftSetupScreen", "GiftItemComponent", "filteredStarGifts = starGifts"):
            self.assertIn(token, text)

if __name__ == "__main__":
    unittest.main()
