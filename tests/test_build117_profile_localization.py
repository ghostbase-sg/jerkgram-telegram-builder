import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build117ProfileLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load("apply_jerkgram_v12f_build117_profile_localization1.py")

    def test_catalog_localizes_tabs_loading_and_every_report_token(self):
        strings = '''public enum JerkgramStringKey: String, CaseIterable {
    case communityNoPosts
}
public struct JerkgramStrings {
    public var communityNoPosts: String { self.text(.communityNoPosts) }
    private static let english: [JerkgramStringKey: String] = [
        .communityNoPosts: "No posts yet"
    ]
    private static let russian: [JerkgramStringKey: String] = [
        .communityNoPosts: "Публикаций пока нет"
    ]
}
'''
        patched = self.overlay.patch_strings(strings)
        for token in (
            "BUILD117_PROFILE_REPORT_LOCALIZATION1",
            "case profileHistoryTab",
            "case presenceHistoryTab",
            "case giftHistoryTab",
            "case personalChannelTab",
            "case profileReportLoading",
            "localizedProfileReport",
            '"История изменений профиля": "Profile change history"',
            '"История присутствия пока пуста.": "Presence history is empty."',
            '"исчез из публичного профиля": "removed from public profile"',
            '"был в этом месяце": "last seen within a month"',
        ):
            self.assertIn(token, patched)

    def test_report_is_localized_at_render_time_and_tabs_use_catalog(self):
        report = '''        let text = self.reportText ?? "Загрузка…"
        let sections = Self.reportSections(text)
'''
        tabs = '''                    case .ghostBaseProfileHistory:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "История", entities: [], enableAnimations: false))
                    case .ghostBasePresence:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Присутствие", entities: [], enableAnimations: false))
                    case .ghostBaseGiftHistory:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Подарки · история", entities: [], enableAnimations: false))
                    case .ghostBasePersonalChannel:
                        content = .title(HorizontalTabsComponent.Tab.Title(text: "Канал", entities: [], enableAnimations: false))
'''
        patched_report = self.overlay.patch_report(report)
        patched_tabs = self.overlay.patch_tabs(tabs)
        self.assertIn("let strings = presentationData.strings.jerkgram", patched_report)
        self.assertIn("strings.localizedProfileReport", patched_report)
        self.assertIn("strings.profileReportLoading", patched_report)
        self.assertNotIn('?? "Загрузка…"', patched_report)
        for accessor in (
            "profileHistoryTab",
            "presenceHistoryTab",
            "giftHistoryTab",
            "personalChannelTab",
        ):
            self.assertIn("presentationData.strings.jerkgram." + accessor, patched_tabs)
        for literal in ("История", "Присутствие", "Подарки · история", "Канал"):
            self.assertNotIn('text: "' + literal + '"', patched_tabs)

    def test_partial_materialization_retry_is_idempotent(self):
        strings = '''
// MARK: Jerkgram v1.2F BUILD117_PROFILE_REPORT_LOCALIZATION1
case profileHistoryTab
case profileReportLoading
.profileHistoryTab: "History"
.profileHistoryTab: "История"
'''
        report = "strings.localizedProfileReport(rawText)\n"
        tabs = '''
presentationData.strings.jerkgram.profileHistoryTab
presentationData.strings.jerkgram.presenceHistoryTab
presentationData.strings.jerkgram.giftHistoryTab
presentationData.strings.jerkgram.personalChannelTab
'''
        self.assertEqual(strings, self.overlay.patch_strings(strings))
        self.assertEqual(report, self.overlay.patch_report(report))
        self.assertEqual(tabs, self.overlay.patch_tabs(tabs))


if __name__ == "__main__":
    unittest.main()
