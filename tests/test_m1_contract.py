import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'Jerkgram' / 'Settings' / 'JGSettingsSchema.json'
ADAPTER = ROOT / 'Jerkgram' / 'Adapters' / 'Telegram1294' / 'JGTelegramSettingsAdapter.m'
UI = ROOT / 'Jerkgram' / 'UI' / 'JGSettingsViewController.m'
STRINGS = ROOT / 'Jerkgram' / 'Localization' / 'JGStrings.m'
STORE = ROOT / 'Jerkgram' / 'Settings' / 'JGSettingsStore.m'
BOOTSTRAP = ROOT / 'Jerkgram' / 'Bootstrap' / 'JerkgramBootstrap.m'

CANONICAL = {
    'jerkgram.Profile.Enabled','jerkgram.Profile.ShowIds','jerkgram.Profile.ShowDCs','jerkgram.Profile.ShowRegistration',
    'jerkgram.GhostMode.ReadMessages','jerkgram.GhostMode.TypingActions','jerkgram.GhostMode.HideRecording','jerkgram.GhostMode.HideUploading','jerkgram.GhostMode.HideStickerActivity','jerkgram.GhostMode.HideGameActivity','jerkgram.GhostMode.HideEmojiActivity','jerkgram.GhostMode.Presence','jerkgram.GhostMode.ScheduledSend',
    'jerkgram.Messages.SaveDeleted','jerkgram.Messages.ShowDeleted','jerkgram.Messages.SaveEditHistory','jerkgram.Messages.ShowEditHistory','jerkgram.Messages.HideBlockedMessages','jerkgram.Messages.HideBlockedReactions','jerkgram.Messages.SendTextStyle','jerkgram.Messages.DeletedPortableReplies','jerkgram.Messages.PreserveDeletedMedia','jerkgram.Messages.DeletedMediaCacheLimit','jerkgram.Messages.DeletedMediaRetentionDays','jerkgram.Messages.ForwardWithoutAuthor',
    'jerkgram.Appearance.ShowRamUnderClock','jerkgram.Appearance.MessageSeconds','jerkgram.Appearance.HideOwnPhone','jerkgram.Glass.Enabled','jerkgram.ProfileBlur.Avatar','jerkgram.ProfileBlur.Animated','jerkgram.ProfileBlur.Tint','jerkgram.ProfileBlur.Reduced',
    'jerkgram.ProtectedContent.Enabled','jerkgram.ProtectedContent.GalleryShare','jerkgram.ProtectedContent.GallerySave','jerkgram.ProtectedContent.GalleryCopy','jerkgram.ProtectedContent.ChatSave','jerkgram.ProtectedContent.ChatCopy','jerkgram.ProtectedContent.ChatForward','jerkgram.ProtectedContent.AllowScreenshots','jerkgram.ProtectedContent.AllowScreenRecording','jerkgram.ProtectedContent.OneTimeScreenshots','jerkgram.ProtectedContent.OneTimeScreenRecording','jerkgram.ProtectedContent.OneTimeSave',
    'jerkgram.Stories.Save','jerkgram.Stars.LocalBalance.Enabled','jerkgram.Stars.LocalBalance.Amount','jerkgram.Stars.LocalBalance.BaseAmount','jerkgram.global.DownloadBoost'
}

class ContractTests(unittest.TestCase):
    def test_schema_exists_and_is_complete(self):
        data = json.loads(SCHEMA.read_text())
        keys = {x['key'] for x in data['settings']}
        self.assertEqual(keys, CANONICAL)
        self.assertEqual(data['schemaVersion'], 1)
        self.assertEqual(data['migrationMarker'], 'jerkgram.runtime.namespaceMigration.v1')
        self.assertEqual(data['globalKeys'], ['jerkgram.global.DownloadBoost'])
        self.assertEqual({x['section'] for x in data['settings']}, {
            'Ghost Mode','Messages','Protected Content','Stories / Media','Profile','Appearance','Other'
        })

    def test_account_key_contract_and_global_exception_are_literal(self):
        text = STORE.read_text()
        self.assertIn('jerkgram.account.%@.setting.%@', text)
        self.assertIn('jerkgram.global.DownloadBoost', text)
        self.assertIn('jerkgram.runtime.namespaceMigration.v1', text)
        self.assertIn('persistentDomainForName', text)
        self.assertNotIn('removeObjectForKey:legacy', text)

    def test_migration_canonical_wins(self):
        text = STORE.read_text()
        self.assertRegex(text, r'if \(domain\[canonicalKey\] == nil\)')
        self.assertIn('caseInsensitiveCompare', text)
        self.assertIn('GhostBase.', text)
        self.assertIn('GB.', text)

    def test_adapter_uses_runtime_boundaries_not_fixed_offsets(self):
        text = ADAPTER.read_text()
        for required in ['objc_getClass', 'class_getInstanceVariable', 'ivar_getOffset', 'viewDidAppear:', 'dlsym', 'PeerInfoScreenImpl']:
            self.assertIn(required, text)
        self.assertNotRegex(text, r'0x[0-9a-fA-F]{5,}')
        self.assertNotIn('PeerInfoScreenDisclosureItem', text)
        self.assertNotIn('settingsItems', text)
        self.assertNotIn('PeerInfoScreenNode', text)
        self.assertIn('JGSettingsEntryAccessibilityIdentifier', text)

    def test_only_settings_lifecycle_is_hooked(self):
        text = ADAPTER.read_text()
        self.assertEqual(text.count('method_setImplementation'), 1)
        self.assertIn('isSettings', text)
        self.assertNotIn('sendMessage', text)
        self.assertNotIn('deleteMessage', text)
        self.assertNotIn('typing', text.lower())

    def test_ui_is_owned_scrollable_table_and_about_identity(self):
        text = UI.read_text()
        self.assertIn('UITableViewController', text)
        for section in ['Ghost Mode','Messages','Protected Content','Stories / Media','Profile','Appearance','Other','About']:
            self.assertIn(section, text)
        self.assertIn('Jerkgram 1.0.2', text)
        self.assertIn('Telegram 12.9.4', text)

    def test_localization_has_en_and_ru_tables_same_keys(self):
        text = STRINGS.read_text()
        en = set(re.findall(r'@\"([^\"]+)\"\s*:\s*@\"[^\"]*\"', text.split('static NSDictionary<NSString *, NSString *> *JGRussianStrings')[0]))
        ru_part = text.split('static NSDictionary<NSString *, NSString *> *JGRussianStrings',1)[1].split('NSString *JGLanguageCode',1)[0]
        ru = set(re.findall(r'@\"([^\"]+)\"\s*:\s*@\"[^\"]*\"', ru_part))
        self.assertTrue(en)
        self.assertEqual(en, ru)
        for key in ['section.ghost','section.messages','section.protected','section.stories','section.profile','section.appearance','section.other','section.about','about.jerkgram','about.base']:
            self.assertIn(key, en)

    def test_bootstrap_installs_settings_adapter_only(self):
        text = BOOTSTRAP.read_text()
        self.assertIn('JGInstallTelegram1294SettingsAdapter', text)
        self.assertNotRegex(text, r'GhostMode|Deleted|ProtectedContent|Notification')

if __name__ == '__main__':
    unittest.main()
