import unittest
import pathlib
import re


ROW_COUNT = 8
ROW_HEIGHT = 52.0
SECTION_SPACING = 24.0
ROOT = pathlib.Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "Jerkgram/Adapters/Telegram1294/JGTelegramSettingsAdapter.m"


def apply_insertion(baseline_frames, my_profile_index, baseline_content_height):
    """Executable statement of the Build138 main-Settings geometry contract."""
    injected_height = ROW_COUNT * ROW_HEIGHT
    insertion_delta = SECTION_SPACING + injected_height
    profile = baseline_frames[my_profile_index]
    injected = (profile[1] + profile[2] + SECTION_SPACING, injected_height)
    shifted = list(baseline_frames)
    for index in range(my_profile_index + 1, len(shifted)):
        name, y, height = baseline_frames[index]
        shifted[index] = (name, y + insertion_delta, height)
    return injected, shifted, baseline_content_height + insertion_delta


class MainSettingsLayoutModelTests(unittest.TestCase):
    def setUp(self):
        # Standalone My Profile, then Wallet and Telegram-owned later sections.
        self.baseline = [
            ("My Profile", 100.0, 52.0),
            ("Wallet", 176.0, 52.0),
            ("Advanced", 252.0, 260.0),
            ("Support", 536.0, 104.0),
        ]

    def test_section_has_exactly_eight_rows_and_ends_before_wallet(self):
        injected, shifted, _ = apply_insertion(self.baseline, 0, 900.0)
        self.assertEqual(shifted[1][0], "Wallet")
        self.assertEqual(injected[1], ROW_COUNT * ROW_HEIGHT)
        self.assertEqual(injected[0] + injected[1] + SECTION_SPACING, shifted[1][1])
        self.assertLessEqual(injected[0] + injected[1], shifted[1][1])

    def test_stock_sections_keep_frames_and_move_as_independent_containers(self):
        _, shifted, _ = apply_insertion(self.baseline, 0, 900.0)
        delta = SECTION_SPACING + ROW_COUNT * ROW_HEIGHT
        for original, result in zip(self.baseline[1:], shifted[1:]):
            self.assertEqual(result, (original[0], original[1] + delta, original[2]))

    def test_two_layout_passes_are_identical(self):
        first = apply_insertion(self.baseline, 0, 900.0)
        second = apply_insertion(self.baseline, 0, 900.0)
        self.assertEqual(first, second)

    def test_changed_telegram_baseline_does_not_accumulate_old_delta(self):
        changed = [
            ("My Profile", 132.0, 52.0),
            ("Wallet", 208.0, 52.0),
            ("Advanced", 284.0, 260.0),
            ("Support", 568.0, 104.0),
        ]
        _, shifted, content = apply_insertion(changed, 0, 932.0)
        delta = SECTION_SPACING + ROW_COUNT * ROW_HEIGHT
        self.assertEqual(shifted[1][1], changed[1][1] + delta)
        self.assertEqual(content, 932.0 + delta)

    def test_late_native_layout_has_an_authoritative_completion_boundary(self):
        """Catch a regression to controller-layout-only finalization.

        Build138 writes every native section frame before assigning the Settings
        scroll view's contentSize.  R4 must observe that exact instance boundary
        and rederive the injected layout after the native setter returns.
        """
        adapter = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("JGObservedScrollSetContentSize", adapter)
        self.assertIn("JGInstallScrollCompletionObserver", adapter)
        self.assertIn("JGTraceLayoutState", adapter)
        self.assertNotIn("dispatch_after", adapter)

        hook = re.search(
            r"static void JGObservedScrollSetContentSize\(.*?\n\}", adapter, re.S
        )
        self.assertIsNotNone(hook)
        body = hook.group(0)
        cache_refresh = "objc_setAssociatedObject(controller, &JGSettingsContextKey, nil"
        self.assertIn(cache_refresh, body)
        self.assertLess(body.index("JGCallOriginalSetContentSize"), body.index("JGCaptureTelegramBaseline"))
        self.assertLess(body.index(cache_refresh), body.index("JGCaptureTelegramBaseline"))
        self.assertLess(body.index("JGCaptureTelegramBaseline"), body.index("JGApplyParitySettingsSection"))

    def test_late_native_baseline_replaces_the_prior_transformed_state(self):
        first = apply_insertion(self.baseline, 0, 900.0)
        late_baseline = [
            ("My Profile", 118.0, 52.0),
            ("Wallet", 194.0, 52.0),
            ("Advanced", 270.0, 260.0),
            ("Support", 554.0, 104.0),
        ]
        late = apply_insertion(late_baseline, 0, 918.0)
        delta = SECTION_SPACING + ROW_COUNT * ROW_HEIGHT
        self.assertNotEqual(first, late)
        self.assertEqual(late[1][1], ("Wallet", 194.0 + delta, 52.0))
        self.assertEqual(late[2], 918.0 + delta)


if __name__ == "__main__":
    unittest.main()
