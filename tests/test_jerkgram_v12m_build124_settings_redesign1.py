from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_settings_redesign1.py"


SETTINGS_FIXTURE = '''
private func ghostBaseSettingsEntries(state: GhostBaseSettingsState, page: GhostBaseSettingsPage, strings: JerkgramStrings) -> [GhostBaseSettingsEntry] {
    if page == .root {
        return [
            .header(0, strings.features),
            .disclosure(0, 1, strings.basicFunctions, "Jerkgram/Settings/Airplane", .home),
            .disclosure(0, 2, strings.ghostMode, "Chat/Context Menu/Eye", .ghostMode),
            .disclosure(0, 3, strings.messages, "Chat/Context Menu/MessageBubble", .messages),
            .disclosure(0, 4, strings.protectedContent, "Premium/CopyProtection/NoForward", .protectedContent),
            .disclosure(0, 5, strings.mediaAndStories, "Item List/Icons/Stories", .mediaStories),
            .disclosure(0, 6, strings.appearance, "Chat/Context Menu/ApplyTheme", .appearance),
            .disclosure(0, 7, strings.debugResearch, "Chat/Context Menu/FormatCode", .debugResearch),
            .disclosure(0, 8, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),
            .disclosure(0, 9, strings.about, "Chat/Context Menu/Info", .about)
        ]
    }
    if page == .home {
        return [
            .header(0, strings.profileCard),
            .toggle(0, 1, GhostBaseKey.profileEnabled, strings.profileCard, state.profileEnabled)
        ]
    }
    if page == .ghostMode {
        return [
            .header(0, strings.ghostMode),
            .toggle(0, 1, GhostBaseKey.readMessages, strings.readGhost, state.readMessages)
        ]
    }
    if page == .messages {
        return [
            .header(0, strings.messages),
            .toggle(0, 1, GhostBaseKey.saveDeleted, strings.deletedMessages, state.saveDeleted),
            .action(1, 1, strings.styleOfTextSending, state.sendTextStyle, "sendStyle")
        ]
    }
    if page == .protectedContent {
        return [
            .header(0, strings.protectedContent),
            .toggle(0, 1, GhostBaseKey.protectedEnabled, strings.protectedMaster, state.protectedEnabled)
        ]
    }
    if page == .mediaStories {
        return [
            .header(0, strings.oneTimeMedia),
            .toggle(0, 1, GhostBaseKey.oneTimeSave, strings.save, state.oneTimeSave)
        ]
    }
    if page == .appearance {
        return [
            .header(0, strings.appearance),
            .toggle(0, 1, GhostBaseKey.glassEnabled, strings.glassProfile, state.glassEnabled)
        ]
    }
    if page == .debugResearch {
        return [
            .header(0, strings.debugResearch),
            .action(0, 1, strings.researchHiddenGiftsProbe, "", "researchHiddenGifts")
        ]
    }
    if page == .about {
        return [
            .header(0, strings.about),
            .info(1, strings.aboutBuild119Summary)
        ]
    }
    return []
}
'''

STARS_FIXTURE = '''
// MARK: Jerkgram v1.2K BUILD122_STARS_DRAFT_EDITOR1
case let .preview(_, amount, status):
    return ItemListDisclosureItem(
        presentationData: presentationData,
        title: "⭐  \\(amount)", label: status, labelStyle: .text,
        sectionId: self.section, style: .blocks,
        disclosureStyle: .none, action: nil
    )
case let .toggle(_, title, value):
    return ItemListSwitchItem(
        presentationData: presentationData, title: title, value: value,
        sectionId: self.section, style: .blocks,
        updated: { arguments.setEnabled($0) }
    )
let leftNavigationButton = ItemListNavigationButton(content: .text(presentationData.strings.Common_Cancel), style: .regular, enabled: true, action: {})
let rightNavigationButton = ItemListNavigationButton(content: .text(presentationData.strings.Common_Save), style: .bold, enabled: dirty, action: {
    jerkgramCommitStarsDraft(accountPeerId: accountPeerId, state: stateValue.with { $0 })
})
'''

DATA_FIXTURE = '''
// MARK: Jerkgram v1.2H BUILD119_DATA_SUMMARY1
case let .summary(_, _, title, value):
    return ItemListDisclosureItem(
        presentationData: presentationData, systemStyle: .glass,
        title: title, label: value, labelStyle: .text,
        sectionId: self.section, style: .blocks,
        disclosureStyle: .none, action: nil
    )
case let .action(_, _, title, value, action):
    if action == "export" || action == "import" || action == "cleanup" {
        return ItemListActionItem(presentationData: presentationData, title: title, kind: .generic, alignment: .center, sectionId: self.section, style: .blocks, action: { arguments.action(action) })
    }
    return ItemListDisclosureItem(
        presentationData: presentationData,
        title: title, label: value, labelStyle: .text,
        sectionId: self.section, style: .blocks,
        disclosureStyle: action == "perChat" ? .arrow : .none,
        action: { arguments.action(action) }
    )
let summary = strings.build119DataSummary(duration, mediaLimit, state.configuration.accountPeerId)
.action(2, 1, strings.exportArchive, "Build119", "export")
.action(2, 2, strings.importArchive, "Archive v2", "import")
'''

TIME_MACHINE_FIXTURE = '''
// MARK: Jerkgram v1.2H BUILD119_TIME_MACHINE_SUMMARY1
case let .summary(_, _, title, value):
    return ItemListDisclosureItem(
        presentationData: presentationData, systemStyle: .glass,
        title: title, label: value, labelStyle: .text,
        sectionId: self.section, style: .blocks,
        disclosureStyle: .none, action: nil
    )
case let .filter(_, _, title, value, kind):
    return ItemListDisclosureItem(
        presentationData: presentationData, systemStyle: .glass,
        title: title, label: value, labelStyle: .text,
        sectionId: self.section, style: .blocks,
        disclosureStyle: .none,
        action: { if let kind { arguments.toggleKind(kind) } else { arguments.selectSender() } }
    )
strings.build119TimeMachineSummary(results.count, state.kinds.count, state.senderPeerId != nil)
Queue.concurrentDefaultQueue().async {
    let page = try eventStore.eventPage(limit: 250)
}
'''


class Build124SettingsRedesignTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_settings_redesign", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_root_stays_telegram_native_and_internal_pages_get_summaries(self):
        module = self.load_patch()
        updated = module.patch_settings_text(SETTINGS_FIXTURE)
        root = module.block_text(updated, "if page == .root {")
        self.assertEqual(root.count(".disclosure("), 9)
        self.assertNotIn("BUILD124_SETTINGS_PAGE_SUMMARY1", root)
        self.assertNotIn('"Jerkgram",', root)
        for page in module.PAGE_SUMMARIES:
            block = module.block_text(updated, f"if page == .{page} {{")
            self.assertIn("BUILD124_SETTINGS_PAGE_SUMMARY1", block, page)
            self.assertIn(".info(-1,", block, page)
        self.assertIn('"sendStyle"', updated)
        self.assertIn('"researchHiddenGifts"', updated)

    def test_about_no_longer_reports_build119(self):
        module = self.load_patch()
        updated = module.patch_settings_text(SETTINGS_FIXTURE)
        about = module.block_text(updated, "if page == .about {")
        self.assertNotIn("aboutBuild119Summary", about)
        self.assertIn("build124AboutSummary", about)

    def test_stars_keeps_draft_save_cancel_but_uses_glass_surface(self):
        module = self.load_patch()
        updated = module.patch_stars_text(STARS_FIXTURE)
        self.assertGreaterEqual(updated.count("systemStyle: .glass"), 2)
        self.assertIn("Common_Cancel", updated)
        self.assertIn("Common_Save", updated)
        self.assertIn("jerkgramCommitStarsDraft", updated)

    def test_data_keeps_real_actions_and_updates_build_identity(self):
        module = self.load_patch()
        updated = module.patch_data_text(DATA_FIXTURE)
        self.assertIn('action == "export" || action == "import" || action == "cleanup"', updated)
        self.assertIn("ItemListActionItem", updated)
        self.assertIn("build124DataSummary", updated)
        self.assertNotIn("build119DataSummary", updated)
        self.assertIn('strings.exportArchive, "Build124 Canary", "export"', updated)
        self.assertIn("systemStyle: .glass", updated)

    def test_time_machine_preserves_bounded_off_main_loading(self):
        module = self.load_patch()
        updated = module.patch_time_machine_text(TIME_MACHINE_FIXTURE)
        self.assertIn("build124TimeMachineSummary", updated)
        self.assertNotIn("build119TimeMachineSummary", updated)
        self.assertIn("systemStyle: .glass", updated)
        self.assertIn("Queue.concurrentDefaultQueue().async", updated)
        self.assertIn("eventPage(limit: 250)", updated)

    def test_strings_cover_every_internal_surface_in_ru_and_en(self):
        module = self.load_patch()
        extension = module.STRINGS_EXTENSION
        for token in (
            "build124HomeSummary", "build124GhostSummary", "build124MessagesSummary",
            "build124ProtectedSummary", "build124MediaSummary", "build124AppearanceSummary",
            "build124DiagnosticsSummary", "build124AboutSummary", "build124DataSummary",
            "build124TimeMachineSummary",
        ):
            self.assertIn(token, extension)
        self.assertIn('self.languageCode == "ru"', extension)
        self.assertIn("Build 124 Canary", extension)


if __name__ == "__main__":
    unittest.main()
