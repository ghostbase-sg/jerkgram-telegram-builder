from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).parents[1]
INSTALLER = ROOT / "scripts/install_jerkgram_v12w_build133_probe_hook.py"
DOWNLOAD_PATCH = ROOT / "scripts/apply_jerkgram_build140_download_boost2.py"
BUILD_WORKFLOW = ROOT / ".github/workflows/build.yml"

NEW_ORDER = (
    "apply_jerkgram_push_click_bridge_v01.py",
    "verify_jerkgram_push_click_bridge_v01.py",
    "apply_jerkgram_webpush_registration_v01.py",
    "verify_jerkgram_webpush_registration_v01.py",
    "apply_jerkgram_push_binding_bridge_v01.py",
    "verify_jerkgram_push_binding_bridge_v01.py",
)

BUILD140_FEATURE_ORDER = (
    "apply_jerkgram_push_binding_bridge_v01.py",
    "verify_jerkgram_push_binding_bridge_v01.py",
    "apply_jerkgram_build140_premium_icons1.py",
    "verify_jerkgram_build140_premium_icons1.py",
    "apply_jerkgram_build140_download_boost2.py",
    "verify_jerkgram_build140_download_boost2.py",
    "apply_jerkgram_build140_identity.py",
    "verify_jerkgram_build140_identity.py",
)

OLD_PAIRING = (
    "apply_jerkgram_push_pairing_bridge_v01.py",
    "verify_jerkgram_push_pairing_bridge_v01.py",
)


def load_installer_module():
    spec = importlib.util.spec_from_file_location("build133_passwordless_push", INSTALLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_download_boost_module():
    spec = importlib.util.spec_from_file_location("build140_download_boost2", DOWNLOAD_PATCH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PasswordlessPushBindingWiringTests(unittest.TestCase):
    def test_native_passwordless_push_chain_is_exactly_once_in_order_before_bazel(self):
        installer = INSTALLER.read_text()
        for name in NEW_ORDER:
            self.assertEqual(installer.count(name), 1, f"{name} must be wired exactly once")
        for name in OLD_PAIRING:
            self.assertNotIn(name, installer, f"legacy pairing bridge still active: {name}")

        positions = [installer.index(name) for name in NEW_ORDER]
        self.assertEqual(positions, sorted(positions))

        module = load_installer_module()
        probe = (
            "header\n"
            + module.BUILD130_SOURCE_ANCHOR
            + "\n"
            + module.BAZEL_ANCHOR
            + " //Telegram:Telegram\n"
            + module.BUILD130_FINAL_ANCHOR
            + "\n"
        )
        generated = module.patch_probe(probe)
        generated_positions = [generated.index(name) for name in NEW_ORDER]
        self.assertEqual(generated_positions, sorted(generated_positions))
        bazel_position = generated.index(module.BAZEL_ANCHOR)
        self.assertTrue(all(position < bazel_position for position in generated_positions))
        for name in OLD_PAIRING:
            self.assertNotIn(name, generated)

    def test_build140_features_run_after_push_binding_and_before_identity(self):
        installer = INSTALLER.read_text()
        for name in BUILD140_FEATURE_ORDER:
            self.assertEqual(installer.count(name), 1, f"{name} must be wired exactly once")
        positions = [installer.index(name) for name in BUILD140_FEATURE_ORDER]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("apply_jerkgram_build140_download_boost1.py", installer)
        self.assertNotIn("verify_jerkgram_build140_download_boost1.py", installer)

        module = load_installer_module()
        probe = (
            "header\n"
            + module.BUILD130_SOURCE_ANCHOR
            + "\n"
            + module.BAZEL_ANCHOR
            + " //Telegram:Telegram\n"
            + module.BUILD130_FINAL_ANCHOR
            + "\n"
        )
        generated = module.patch_probe(probe)
        generated_positions = [generated.index(name) for name in BUILD140_FEATURE_ORDER]
        self.assertEqual(generated_positions, sorted(generated_positions))
        self.assertLess(generated_positions[-1], generated.index(module.BAZEL_ANCHOR))

    def test_download_boost_matches_official_four_pending_owner_topology(self):
        patch = load_download_boost_module()
        source = '''import Foundation

private let possiblePartLengths: [Int64] = [1]

if isStory {
    self.defaultPartSize = 512 * 1024
} else {
    self.defaultPartSize = 128 * 1024
}
self.cdnPartSize = 128 * 1024

let initial = FetchingState(
    partSize: self.defaultPartSize,
    maxPendingParts: 6,
    decryptionState: nil
)
let cdn = FetchingState(
    partSize: self.cdnPartSize,
    maxPendingParts: 6,
    decryptionState: nil
)
let refreshed = FetchingState(
    partSize: self.defaultPartSize,
    maxPendingParts: 6,
    decryptionState: nil
)
let cdnRefreshed = FetchingState(
    partSize: self.cdnPartSize,
    maxPendingParts: 6,
    decryptionState: nil
)
'''
        actual = patch.patch_fetch_v2(source)
        self.assertEqual(
            actual.count("maxPendingParts: jerkgramDownloadMaxPendingParts(6),"),
            4,
        )
        self.assertNotIn("maxPendingParts: 6,", actual)
        self.assertIn("self.cdnPartSize = 128 * 1024", actual)
        self.assertEqual(actual, patch.patch_fetch_v2(actual))

        broken = source.replace(
            '''let cdnRefreshed = FetchingState(
    partSize: self.cdnPartSize,
    maxPendingParts: 6,
    decryptionState: nil
)
''',
            "",
        )
        with self.assertRaisesRegex(RuntimeError, "expected 4 anchors, found 3"):
            patch.patch_fetch_v2(broken)

    def test_download_boost_renderer_accepts_materialized_attributed_selector(self):
        patch = load_download_boost_module()
        source = '''        case let .selector(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: "",
                attributedLabel: ghostBaseSendStyleAttributedText(
                    style: value,
                    text: ghostBaseSendTextStyleTitle(
                    value,
                    strings: presentationData.strings.jerkgram
                ),
                    color: presentationData.theme.list.itemSecondaryTextColor,
                    size: 15.0
                ),
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .arrow,
                action: {
                    arguments.openSendTextStyle()
                },
                tag: GhostBaseSettingsEntryTag.sendTextStyle
            )

        case let .stylePreview(_, _, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: value,
                label: "",
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .none,
                action: nil
            )
'''
        actual = patch.patch_download_boost_renderer(source)

        selector_start = actual.index("        case let .selector(_, _, title, value):")
        boost_start = actual.index("        case let .downloadBoost(_, _, title, value):")
        preview_start = actual.index("        case let .stylePreview(_, _, value):")
        self.assertLess(selector_start, boost_start)
        self.assertLess(boost_start, preview_start)
        self.assertIn("attributedLabel: ghostBaseSendStyleAttributedText(", actual[selector_start:boost_start])
        self.assertIn("arguments.openSendTextStyle()", actual[selector_start:boost_start])
        self.assertIn("arguments.openDownloadBoost()", actual[boost_start:preview_start])
        self.assertEqual(actual.count("case let .downloadBoost(_, _, title, value):"), 1)

        with self.assertRaisesRegex(RuntimeError, "stylePreview boundary missing"):
            patch.patch_download_boost_renderer(
                source.replace("        case let .stylePreview(_, _, value):", "        case let .other(_, _, value):")
            )

    def test_release_workflow_preflights_passwordless_native_push_chain(self):
        workflow = BUILD_WORKFLOW.read_text()
        for name in NEW_ORDER:
            self.assertIn(f"scripts/{name}", workflow)
        for name in OLD_PAIRING:
            self.assertNotIn(f"scripts/{name}", workflow)

        test_command = "python3 -m unittest tests.test_jerkgram_push_binding_wiring_v01"
        self.assertIn(test_command, workflow)
        self.assertNotIn("python3 -m unittest tests.test_jerkgram_push_pairing_wiring_v01", workflow)
        self.assertLess(
            workflow.index(test_command),
            workflow.index("python3 scripts/install_jerkgram_v12d_build115_probe_hook.py"),
        )


if __name__ == "__main__":
    unittest.main()
