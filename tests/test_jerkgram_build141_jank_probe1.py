from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).parents[1]
APPLY = ROOT / "scripts/apply_jerkgram_build141_jank_probe1.py"
INSTALLER = ROOT / "scripts/install_jerkgram_build141_jank_probe_hook.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ACCOUNT_FIXTURE = r'''import Foundation

public final class Account {
    public init() {}
}
'''

APP_DELEGATE_FIXTURE = r'''import UIKit
import TelegramCore

@objc(AppDelegate) class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        return true
    }
}
'''

SETTINGS_FIXTURE = r'''import Foundation
import UIKit
import TelegramCore

private enum GhostBaseSettingsEntry {
    case aboutValue(Int32, Int32, String, String)

    func item() -> Any {
        switch self {
        case let .aboutValue(_, _, title, value):
            return ItemListDisclosureItem(
                title: title,
                label: value,
                action: nil
            )
        }
    }
}

private func ghostBaseSettingsEntries(state: Int) -> [Int] {
    return [state]
}
'''

CHAT_FIXTURE = r'''import TelegramCore

public class ChatTextInputPanelNode {
    @objc public func editableTextNodeDidUpdateText(_ editableTextNode: ASEditableTextNode) {
        self.chatInputTextNodeDidUpdateText()
    }
}
'''

PROFILE_FIXTURE = r'''import TelegramCore

final class GhostBaseProfileFullscreenBackground {
    private func staticAvatarSignal() -> Int {
        // MARK: GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1
        let value = 1
        return value
    }
}
'''


class Build141JankProbeTests(unittest.TestCase):
    def test_core_runtime_is_bounded_and_report_only_formats_on_demand(self):
        patch = load_module("build141_apply_core", APPLY)
        actual = patch.patch_account(ACCOUNT_FIXTURE)
        for token in (
            patch.CORE_MARKER,
            "hitchCapacity = 64",
            "regionCapacity = 256",
            "recordFrameGap",
            "makeTextReport()",
            "JerkgramJankContext",
            "JerkgramJankRegion",
        ):
            self.assertIn(token, actual)
        self.assertNotIn("UserDefaults", actual[actual.index(patch.CORE_MARKER):actual.index("public final class Account")])
        self.assertEqual(actual, patch.patch_account(actual))

    def test_single_display_link_records_only_hitches_and_starts_once(self):
        patch = load_module("build141_apply_app", APPLY)
        actual = patch.patch_app_delegate(APP_DELEGATE_FIXTURE)
        self.assertEqual(actual.count("CADisplayLink("), 1)
        self.assertIn("durationMs >= 33.0", actual)
        self.assertIn("JerkgramJankDisplayLink.shared.start()", actual)
        self.assertEqual(actual, patch.patch_app_delegate(actual))

    def test_settings_version_copies_report_and_entries_are_timed(self):
        patch = load_module("build141_apply_settings", APPLY)
        actual = patch.patch_settings(SETTINGS_FIXTURE)
        self.assertIn("JerkgramJankProbe.shared.setContext(.settings)", actual)
        self.assertIn("begin(.settingsUpdate)", actual)
        self.assertIn("UIPasteboard.general.string = JerkgramJankProbe.shared.makeTextReport()", actual)
        self.assertEqual(actual, patch.patch_settings(actual))

    def test_typing_owner_is_timed_without_changing_native_call(self):
        patch = load_module("build141_apply_chat", APPLY)
        actual = patch.patch_chat_input(CHAT_FIXTURE)
        self.assertIn("noteTyping(true)", actual)
        self.assertIn("begin(.chatTextInput)", actual)
        self.assertEqual(actual.count("self.chatInputTextNodeDidUpdateText()"), 1)
        self.assertEqual(actual, patch.patch_chat_input(actual))

    def test_profile_pipeline_is_timed_without_touching_avatar_semantics(self):
        patch = load_module("build141_apply_profile", APPLY)
        actual = patch.patch_profile(PROFILE_FIXTURE)
        self.assertIn("noteAnimatedAvatar(true)", actual)
        self.assertIn("begin(.profileBackground)", actual)
        self.assertIn("GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1", actual)
        self.assertEqual(actual, patch.patch_profile(actual))

    def test_installer_places_build141_after_build140_identity_and_before_runtime_repair(self):
        installer = load_module("build141_installer", INSTALLER)
        order = installer.SOURCE_ORDERED
        self.assertLess(order.index("verify_jerkgram_build140_identity.py"), order.index("apply_jerkgram_build141_jank_probe1.py"))
        self.assertLess(order.index("verify_jerkgram_build141_jank_probe1.py"), order.index("verify_jerkgram_v12w_build133_runtime_repair1.py"))


if __name__ == "__main__":
    unittest.main()
