import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "Jerkgram/Settings/JGSettingsSchema.json"
STORE = ROOT / "Jerkgram/Settings/JGSettingsStore.m"
UI = ROOT / "Jerkgram/UI/JGSettingsViewController.m"
ADAPTER = ROOT / "Jerkgram/Adapters/Telegram1294/JGTelegramSettingsAdapter.m"
INTROSPECTION = ROOT / "Jerkgram/Adapters/Telegram1294/JGRuntimeIntrospection.swift"
STRINGS = ROOT / "Jerkgram/Localization/JGStrings.m"
WORKFLOW = ROOT / ".github/workflows/m1-settings.yml"
BOOTSTRAP = ROOT / "Jerkgram/Bootstrap/JerkgramBootstrap.m"


MAIN_ROUTES = [
    ("home", "main.jerkgram", "Jerkgram/Settings/Airplane", "53606A"),
    ("ghostMode", "main.ghost", "Chat/Context Menu/Eye", "4B5064"),
    ("messages", "main.messages", "Chat/Context Menu/MessageBubble", "4B6F83"),
    ("protectedContent", "main.protected", "Premium/CopyProtection/NoForward", "87452F"),
    ("mediaStories", "main.media", "Item List/Icons/Stories", "6A5C78"),
    ("appearance", "main.appearance", "Chat/Context Menu/ApplyTheme", "676C43"),
    ("debugResearch", "main.debug", "Chat/Context Menu/FormatCode", "8A6138"),
    ("about", "main.about", "Chat/Context Menu/Info", "4B4F54"),
]

BOOL_DEFAULTS = {
    "jerkgram.Profile.Enabled": True,
    "jerkgram.Profile.ShowIds": True,
    "jerkgram.Profile.ShowDCs": True,
    "jerkgram.Profile.ShowRegistration": True,
    "jerkgram.Glass.Enabled": True,
    "jerkgram.ProfileBlur.Avatar": True,
    "jerkgram.ProfileBlur.Animated": True,
    "jerkgram.ProfileBlur.Tint": True,
    "jerkgram.ProfileBlur.Reduced": False,
    "jerkgram.GhostMode.ReadMessages": False,
    "jerkgram.GhostMode.TypingActions": False,
    "jerkgram.GhostMode.HideRecording": False,
    "jerkgram.GhostMode.HideUploading": False,
    "jerkgram.GhostMode.HideStickerActivity": False,
    "jerkgram.GhostMode.HideGameActivity": False,
    "jerkgram.GhostMode.HideEmojiActivity": False,
    "jerkgram.GhostMode.Presence": False,
    "jerkgram.GhostMode.ScheduledSend": False,
    "jerkgram.Messages.SaveDeleted": True,
    "jerkgram.Messages.ShowDeleted": True,
    "jerkgram.Messages.SaveEditHistory": True,
    "jerkgram.Messages.ShowEditHistory": True,
    "jerkgram.Messages.HideBlockedMessages": True,
    "jerkgram.Messages.HideBlockedReactions": True,
    "jerkgram.Messages.DeletedPortableReplies": True,
    "jerkgram.Messages.PreserveDeletedMedia": True,
    "jerkgram.Appearance.ShowRamUnderClock": False,
    "jerkgram.Appearance.MessageSeconds": False,
    "jerkgram.Appearance.HideOwnPhone": False,
    "jerkgram.ProtectedContent.Enabled": True,
    "jerkgram.ProtectedContent.GalleryShare": True,
    "jerkgram.ProtectedContent.GallerySave": True,
    "jerkgram.ProtectedContent.GalleryCopy": True,
    "jerkgram.ProtectedContent.ChatSave": True,
    "jerkgram.ProtectedContent.ChatCopy": True,
    "jerkgram.ProtectedContent.ChatForward": True,
    "jerkgram.ProtectedContent.AllowScreenshots": True,
    "jerkgram.ProtectedContent.AllowScreenRecording": True,
    "jerkgram.ProtectedContent.OneTimeScreenshots": False,
    "jerkgram.ProtectedContent.OneTimeScreenRecording": False,
    "jerkgram.ProtectedContent.OneTimeSave": False,
    "jerkgram.Stories.Save": False,
    "jerkgram.Stars.LocalBalance.Enabled": False,
}

STRING_DEFAULTS = {
    "jerkgram.Messages.SendTextStyle": "normal",
    "jerkgram.Stars.LocalBalance.Amount": "0",
    "jerkgram.Stars.LocalBalance.BaseAmount": "0",
}


def text(path):
    return path.read_text(encoding="utf-8")


class Build138ParityTests(unittest.TestCase):
    def test_r4_is_materialized_not_staged(self):
        self.assertFalse((ROOT / ".m1r4-payload").exists())
        for path in (STORE, UI, ADAPTER, INTROSPECTION, STRINGS, WORKFLOW):
            self.assertTrue(path.exists(), path)

    def test_rejected_runtime_paths_are_absent(self):
        combined = "\n".join(text(p) for p in (ADAPTER, INTROSPECTION, UI) if p.exists())
        for forbidden in (
            "UIBarButtonItem", "ivar_getOffset", "memcpy(", "dlsym(",
            "PeerIdV7toInt64", "settingsItems", "PeerInfoScreenDisclosureItem",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertNotRegex(combined, r"0x[0-9a-fA-F]{7,}")

    def test_workflow_compiles_semantic_swift_bridge(self):
        workflow = text(WORKFLOW)
        self.assertIn("JGRuntimeIntrospection.swift", workflow)
        self.assertRegex(workflow, r"\bswiftc\b")
        self.assertIn("-emit-object", workflow)

    def test_account_resolution_is_semantic_and_fail_closed(self):
        resolver = text(INTROSPECTION)
        adapter = text(ADAPTER)
        self.assertIn("Mirror(reflecting:", resolver)
        self.assertIn('directChild(named: "peerId"', resolver)
        self.assertIn('directChild(named: "namespace"', resolver)
        self.assertIn('directChild(named: "id"', resolver)
        self.assertIn("guard packed != 0 else", resolver)
        self.assertIn("deactivateAccount", adapter)
        self.assertNotIn("activateAccountPeerId:0", adapter)

    def test_exact_main_settings_graph(self):
        adapter = text(ADAPTER)
        entries = re.findall(
            r'JGMainRoute\(@"([^"]+)",\s*@"([^"]+)",\s*@"([^"]+)",\s*0x([0-9A-Fa-f]{6})\)',
            adapter,
        )
        self.assertEqual([(a, b, c, d.upper()) for a, b, c, d in entries], MAIN_ROUTES)
        self.assertIn('isEqual:@"myProfile"', adapter)
        self.assertNotIn('isEqual:@"proxy"', adapter)
        self.assertNotIn('route:@"root"', adapter)

    def test_layout_preserves_native_section_baseline_and_inserts_one_bounded_section(self):
        adapter = text(ADAPTER)
        self.assertIn("JGRestoreTelegramBaseline", adapter)
        self.assertIn("JGCaptureTelegramBaseline", adapter)
        self.assertIn("baselineContentSize.height + insertionDelta", adapter)
        self.assertIn("CGRectGetMaxY(injected.frame) <= CGRectGetMinY(firstFollowingFrame)", adapter)
        self.assertNotIn("JGSectionOrder", adapter)
        self.assertNotIn("cursor = CGRectGetMaxY(frame)", adapter)

        hook = re.search(
            r"static void JGPeerInfoViewDidLayoutSubviews\(.*?\n\}", adapter, re.S
        )
        self.assertIsNotNone(hook)
        body = hook.group(0)
        self.assertLess(body.index("JGRestoreTelegramBaseline"), body.index("JGOriginalViewDidLayoutSubviews"))
        self.assertLess(body.index("JGOriginalViewDidLayoutSubviews"), body.index("JGCaptureTelegramBaseline"))
        self.assertLess(body.index("JGCaptureTelegramBaseline"), body.index("JGApplyParitySettingsSection"))

    def test_build138_main_icon_renderer_geometry(self):
        adapter = text(ADAPTER)
        self.assertIn("CGSizeMake(30.0, 30.0)", adapter)
        self.assertIn("cornerRadius:8.0", adapter)
        self.assertIn('imageNamed:@"Item List/Icons/Gradient"', adapter)
        self.assertIn('imageNamed:@"Item List/Icons/Backdrop"', adapter)
        self.assertNotIn("CGRectInset(row.tile.bounds, 5.0, 5.0)", adapter)
        self.assertNotIn("_tile.layer.cornerRadius = 7.0", adapter)

    def test_display_host_is_the_only_pushed_controller(self):
        ui = text(UI)
        adapter = text(ADAPTER)
        self.assertIn('_TtC7Display14ViewController', ui)
        self.assertIn("JGCreateSettingsHost", ui)
        self.assertNotRegex(adapter, r"pushViewController\s*:\s*settings")
        self.assertNotRegex(ui, r"pushViewController\s*:\s*(?:child|self)")
        self.assertNotIn("initWithRootViewController", adapter)

    def test_only_build138_reachable_pages_are_exposed(self):
        ui = text(UI)
        match = re.search(r"JGReachableSettingsPages\(void\)\s*\{\s*return\s*@\[(.*?)\];", ui, re.S)
        self.assertIsNotNone(match)
        pages = re.findall(r'@"([^"]+)"', match.group(1))
        self.assertEqual(pages, [
            "home", "ghostMode", "messages", "protectedContent", "mediaStories",
            "appearance", "debugResearch", "about", "stars", "dataAndBackup", "sendStyle",
            "chatRetention",
        ])
        self.assertNotIn('isEqualToString:@"root"', ui)

    def test_build138_settings_inventory_defaults_and_types(self):
        data = json.loads(text(SCHEMA))
        settings = {item["key"]: item for item in data["settings"]}
        self.assertEqual(set(settings), set(BOOL_DEFAULTS) | set(STRING_DEFAULTS))
        self.assertEqual(len(settings), 46)
        for key, default in BOOL_DEFAULTS.items():
            self.assertEqual(settings[key], {"key": key, "type": "bool", "default": default})
        for key, default in STRING_DEFAULTS.items():
            self.assertEqual(settings[key], {"key": key, "type": "string", "default": default})
        self.assertNotIn("jerkgram.global.DownloadBoost", text(SCHEMA) + text(STORE) + text(UI))

    def test_account_scope_and_build138_projection_contract(self):
        store = text(STORE)
        self.assertIn("jerkgram.account.%@.setting.%@", store)
        self.assertIn("unscopedCanonicalValue", store)
        self.assertNotIn("persistentDomainForName", store)
        self.assertNotIn('@"GhostBase."', store)
        self.assertNotIn('@"GB."', store)
        self.assertIn("activeAccountPeerId.length == 0", store)

    def test_build138_page_behavior_is_present(self):
        ui = text(UI)
        required = (
            "copyExtensionDiagnostics", "openAppChannel", "openCommunity",
            "cycleHistoryDuration", "cycleMediaLimit", "openPerChatRules",
            "cleanupExpired", "exportArchive", "importArchive",
            "ghostBaseSanitizeStarsAmount", "applyProtectedMasterValue",
            "applyProtectedChildValue", "NSStrikethroughStyleAttributeName",
            "NSUnderlineStyleAttributeName",
        )
        for token in required:
            self.assertIn(token, ui)
        self.assertNotIn("showUnavailable", ui)

    def test_data_telemetry_and_retention_are_separate_from_feature_settings(self):
        ui = text(UI)
        self.assertIn("jerkgram.telemetry.anonymous.enabled", ui)
        self.assertIn("jerkgram.retention.account.%lld", ui)
        self.assertNotIn("jerkgram.telemetry.anonymous.enabled", text(SCHEMA))

    def test_en_ru_localization_tables_are_complete_and_equal(self):
        source = text(STRINGS)
        en_part, ru_and_rest = source.split("JGRussianStrings", 1)
        ru_part = ru_and_rest.split("NSString *JGLanguageCode", 1)[0]
        key_re = re.compile(r'@"([^"]+)"\s*:\s*@"[^"]*"')
        en = set(key_re.findall(en_part))
        ru = set(key_re.findall(ru_part))
        self.assertEqual(en, ru)
        for key in (
            "main.jerkgram", "main.ghost", "main.messages", "main.protected",
            "main.media", "main.appearance", "main.debug", "main.about",
            "home.dataBackup", "debug.copyExtensionDiagnostics",
            "about.analyticsDescription", "data.perChat", "data.cleanup",
        ):
            self.assertIn(key, en)

    def test_bootstrap_contains_settings_only(self):
        bootstrap = text(BOOTSTRAP)
        adapter = text(ADAPTER)
        self.assertIn("JGInstallTelegram1294SettingsAdapter", bootstrap)
        for forbidden in ("sendMessage", "deleteMessage", "markRead", "typingActivity", "APNs"):
            self.assertNotIn(forbidden, bootstrap + adapter)


if __name__ == "__main__":
    unittest.main()
