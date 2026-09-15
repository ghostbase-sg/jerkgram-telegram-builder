#import "JGSettingsViewController.h"
#import "JGSettingsStore.h"
#import "JGStrings.h"
#import "JGTelegramSettingsAdapter.h"
#import <objc/runtime.h>
#import <objc/message.h>

static NSString * const JGTelemetryPreferenceKey = @"jerkgram.telemetry.anonymous.enabled";
static const char JGHostedChildKey;

static NSDictionary *JGRow(NSString *kind, NSString *titleKey, NSString *settingKey, NSString *page, NSString *action) {
    NSMutableDictionary *row = [@{ @"kind": kind ?: @"", @"title": titleKey ?: @"" } mutableCopy];
    if (settingKey) row[@"key"] = settingKey;
    if (page) row[@"page"] = page;
    if (action) row[@"action"] = action;
    return row;
}

static NSDictionary *JGSection(NSString *headerKey, NSString *footerKey, NSArray *rows) {
    return @{ @"header": headerKey ?: @"", @"footer": footerKey ?: @"", @"rows": rows ?: @[] };
}

NSArray<NSString *> *JGReachableSettingsPages(void) {
    return @[@"home", @"ghostMode", @"messages", @"protectedContent", @"mediaStories", @"appearance", @"debugResearch", @"about", @"stars", @"dataAndBackup", @"sendStyle", @"chatRetention"];
}

static NSString *JGPageTitleKey(NSString *page) {
    NSDictionary *map = @{
        @"home": @"page.home", @"ghostMode": @"page.ghost", @"messages": @"page.messages",
        @"protectedContent": @"page.protected", @"mediaStories": @"page.media", @"appearance": @"page.appearance",
        @"debugResearch": @"page.debug", @"about": @"page.about", @"stars": @"page.stars",
        @"dataAndBackup": @"page.data", @"sendStyle": @"page.sendStyle", @"chatRetention": @"data.perChat"
    };
    return map[page] ?: @"main.jerkgram";
}

static NSString *JGRetentionStorageKey(int64_t accountPeerId) {
    return [NSString stringWithFormat:@"jerkgram.retention.account.%lld", (long long)accountPeerId];
}

static NSDictionary *JGDefaultRetention(void) {
    return @{ @"history": @"30d", @"media": @(1073741824LL), @"archiveSecretChats": @NO, @"chatOverrides": @[] };
}

static NSString *JGHistoryStorageValue(NSString *value) {
    return @{ @"off": @"disabled", @"7d": @"days7", @"30d": @"days30", @"90d": @"days90", @"forever": @"forever" }[value] ?: @"days30";
}

static NSString *JGHistoryDisplayValue(NSString *value) {
    return @{ @"disabled": @"off", @"days7": @"7d", @"days30": @"30d", @"days90": @"90d", @"forever": @"forever" }[value] ?: @"30d";
}

static NSString *JGMediaStorageValue(NSNumber *value) {
    long long bytes = value.longLongValue;
    if (bytes < 0) return @"unlimited";
    if (bytes == 0) return @"disabled";
    if (bytes == 250LL * 1024 * 1024) return @"megabytes250";
    if (bytes == 500LL * 1024 * 1024) return @"megabytes500";
    if (bytes == 2LL * 1024 * 1024 * 1024) return @"gigabytes2";
    if (bytes == 5LL * 1024 * 1024 * 1024) return @"gigabytes5";
    return @"gigabytes1";
}

static NSNumber *JGMediaDisplayValue(NSString *value) {
    NSDictionary *map = @{ @"disabled": @0, @"megabytes250": @(250LL * 1024 * 1024), @"megabytes500": @(500LL * 1024 * 1024), @"gigabytes1": @(1073741824LL), @"gigabytes2": @(2LL * 1024 * 1024 * 1024), @"gigabytes5": @(5LL * 1024 * 1024 * 1024), @"unlimited": @(-1) };
    return map[value] ?: @(1073741824LL);
}

static NSMutableDictionary *JGLoadRetention(int64_t accountPeerId) {
    if (accountPeerId == 0) return [JGDefaultRetention() mutableCopy];
    id raw = [NSUserDefaults.standardUserDefaults objectForKey:JGRetentionStorageKey(accountPeerId)];
    if (![raw isKindOfClass:NSData.class]) return [JGDefaultRetention() mutableCopy];
    NSDictionary *stored = [NSJSONSerialization JSONObjectWithData:raw options:0 error:nil];
    if (![stored isKindOfClass:NSDictionary.class] || [stored[@"accountPeerId"] longLongValue] != accountPeerId || [stored[@"schemaVersion"] integerValue] != 1) return [JGDefaultRetention() mutableCopy];
    NSDictionary *policy = [stored[@"accountPolicy"] isKindOfClass:NSDictionary.class] ? stored[@"accountPolicy"] : @{};
    NSMutableDictionary *value = [JGDefaultRetention() mutableCopy];
    value[@"history"] = JGHistoryDisplayValue(policy[@"historyDuration"]);
    value[@"media"] = JGMediaDisplayValue(policy[@"mediaByteLimit"]);
    value[@"archiveSecretChats"] = @([policy[@"archiveSecretChats"] boolValue]);
    value[@"chatOverrides"] = [stored[@"chatOverrides"] isKindOfClass:NSArray.class] ? stored[@"chatOverrides"] : @[];
    return value;
}

static void JGSaveRetention(int64_t accountPeerId, NSDictionary *value) {
    if (accountPeerId == 0 || value == nil) return;
    NSDictionary *stored = @{
        @"schemaVersion": @1,
        @"accountPeerId": @(accountPeerId),
        @"accountPolicy": @{
            @"historyDuration": JGHistoryStorageValue(value[@"history"]),
            @"mediaByteLimit": JGMediaStorageValue(value[@"media"]),
            @"archiveSecretChats": @([value[@"archiveSecretChats"] boolValue]),
        },
        @"chatOverrides": [value[@"chatOverrides"] isKindOfClass:NSArray.class] ? value[@"chatOverrides"] : @[],
    };
    NSData *data = [NSJSONSerialization dataWithJSONObject:stored options:NSJSONWritingSortedKeys error:nil];
    if (data != nil) [NSUserDefaults.standardUserDefaults setObject:data forKey:JGRetentionStorageKey(accountPeerId)];
}

static NSString *JGHistoryLabel(NSString *value) {
    if ([value isEqualToString:@"off"]) return JGString(@"data.disabled");
    if ([value isEqualToString:@"7d"]) return JGString(@"data.7days");
    if ([value isEqualToString:@"30d"]) return JGString(@"data.30days");
    if ([value isEqualToString:@"90d"]) return JGString(@"data.90days");
    return JGString(@"data.forever");
}

static NSString *JGMediaLabel(NSNumber *value) {
    long long bytes = value.longLongValue;
    if (bytes < 0) return JGString(@"data.unlimited");
    if (bytes == 0) return JGString(@"data.disabled");
    if (bytes == 250LL * 1024 * 1024) return JGString(@"data.250mb");
    if (bytes == 500LL * 1024 * 1024) return JGString(@"data.500mb");
    if (bytes == 2LL * 1024 * 1024 * 1024) return JGString(@"data.2gb");
    if (bytes == 5LL * 1024 * 1024 * 1024) return JGString(@"data.5gb");
    return JGString(@"data.1gb");
}

static NSString *JGStyleLabel(NSString *value) {
    NSDictionary *map = @{ @"normal": @"style.normal", @"bold": @"style.bold", @"italic": @"style.italic", @"monospace": @"style.monospace", @"strikethrough": @"style.strikethrough", @"underline": @"style.underline", @"spoiler": @"style.spoiler" };
    return JGString(map[value] ?: @"style.normal");
}

@interface JGParitySettingsController : UITableViewController <UIDocumentPickerDelegate>
@property(nonatomic) int64_t accountPeerId;
@property(nonatomic, copy) NSString *page;
@property(nonatomic) NSArray<NSDictionary *> *sections;
@end

@implementation JGParitySettingsController

- (instancetype)initWithAccountPeerId:(int64_t)accountPeerId page:(NSString *)page {
    self = [super initWithStyle:UITableViewStyleInsetGrouped];
    if (self) {
        _accountPeerId = accountPeerId;
        _page = [page copy];
    }
    return self;
}

- (void)viewDidLoad {
    [super viewDidLoad];
    self.tableView.backgroundColor = UIColor.systemGroupedBackgroundColor;
    self.tableView.separatorInset = UIEdgeInsetsMake(0.0, 59.0, 0.0, 0.0);
    self.tableView.rowHeight = 44.0;
    self.tableView.estimatedRowHeight = 44.0;
    if (@available(iOS 15.0, *)) self.tableView.sectionHeaderTopPadding = 8.0;
    [[JGSettingsStore sharedStore] activateAccountPeerId:self.accountPeerId];
    [self rebuildSections];
}

- (void)rebuildSections {
    if ([self.page isEqualToString:@"home"]) {
        self.sections = @[
            JGSection(@"section.profileInformation", nil, @[
                JGRow(@"switch", @"profile.show", @"jerkgram.Profile.Enabled", nil, nil),
                JGRow(@"switch", @"profile.telegramId", @"jerkgram.Profile.ShowIds", nil, nil),
                JGRow(@"switch", @"profile.avatarDc", @"jerkgram.Profile.ShowDCs", nil, nil),
                JGRow(@"switch", @"profile.registration", @"jerkgram.Profile.ShowRegistration", nil, nil),
            ]),
            JGSection(@"section.basicFunctions", nil, @[
                JGRow(@"stars", @"home.stars", nil, @"stars", nil),
            ]),
            JGSection(@"home.backup", nil, @[
                JGRow(@"disclosure", @"home.dataBackup", nil, @"dataAndBackup", nil),
            ])
        ];
    } else if ([self.page isEqualToString:@"ghostMode"]) {
        self.sections = @[JGSection(@"main.ghost", nil, @[
            JGRow(@"switch", @"ghost.read", @"jerkgram.GhostMode.ReadMessages", nil, nil),
            JGRow(@"switch", @"ghost.typing", @"jerkgram.GhostMode.TypingActions", nil, nil),
            JGRow(@"switch", @"ghost.recording", @"jerkgram.GhostMode.HideRecording", nil, nil),
            JGRow(@"switch", @"ghost.uploading", @"jerkgram.GhostMode.HideUploading", nil, nil),
            JGRow(@"switch", @"ghost.sticker", @"jerkgram.GhostMode.HideStickerActivity", nil, nil),
            JGRow(@"switch", @"ghost.game", @"jerkgram.GhostMode.HideGameActivity", nil, nil),
            JGRow(@"switch", @"ghost.emoji", @"jerkgram.GhostMode.HideEmojiActivity", nil, nil),
            JGRow(@"switch", @"ghost.presence", @"jerkgram.GhostMode.Presence", nil, nil),
            JGRow(@"switch", @"ghost.scheduled", @"jerkgram.GhostMode.ScheduledSend", nil, nil),
        ])];
    } else if ([self.page isEqualToString:@"messages"]) {
        self.sections = @[
            JGSection(@"messages.deleted.section", nil, @[
                JGRow(@"switch", @"messages.saveDeleted", @"jerkgram.Messages.SaveDeleted", nil, nil),
                JGRow(@"switch", @"messages.showDeleted", @"jerkgram.Messages.ShowDeleted", nil, nil),
            ]),
            JGSection(@"messages.edits.section", @"messages.savedDataHint", @[
                JGRow(@"switch", @"messages.saveEdits", @"jerkgram.Messages.SaveEditHistory", nil, nil),
                JGRow(@"switch", @"messages.showEdits", @"jerkgram.Messages.ShowEditHistory", nil, nil),
            ]),
            JGSection(@"messages.text.section", @"messages.sendStyleHint", @[
                JGRow(@"sendStyle", @"messages.sendStyle", @"jerkgram.Messages.SendTextStyle", @"sendStyle", nil),
                JGRow(@"stylePreview", @"style.example.body", @"jerkgram.Messages.SendTextStyle", nil, nil),
            ]),
            JGSection(@"messages.reply.section", @"messages.portableReplyHint", @[
                JGRow(@"switch", @"messages.portableReply", @"jerkgram.Messages.DeletedPortableReplies", nil, nil),
                JGRow(@"switch", @"messages.deletedMedia", @"jerkgram.Messages.PreserveDeletedMedia", nil, nil),
            ]),
            JGSection(@"messages.blocked.section", nil, @[
                JGRow(@"switch", @"messages.hideBlocked", @"jerkgram.Messages.HideBlockedMessages", nil, nil),
                JGRow(@"switch", @"messages.hideReactions", @"jerkgram.Messages.HideBlockedReactions", nil, nil),
            ])
        ];
    } else if ([self.page isEqualToString:@"protectedContent"]) {
        self.sections = @[JGSection(@"main.protected", nil, @[
            JGRow(@"switch", @"protected.enabled", @"jerkgram.ProtectedContent.Enabled", nil, nil),
            JGRow(@"switch", @"protected.galleryShare", @"jerkgram.ProtectedContent.GalleryShare", nil, nil),
            JGRow(@"switch", @"protected.gallerySave", @"jerkgram.ProtectedContent.GallerySave", nil, nil),
            JGRow(@"switch", @"protected.galleryCopy", @"jerkgram.ProtectedContent.GalleryCopy", nil, nil),
            JGRow(@"switch", @"protected.chatSave", @"jerkgram.ProtectedContent.ChatSave", nil, nil),
            JGRow(@"switch", @"protected.chatCopy", @"jerkgram.ProtectedContent.ChatCopy", nil, nil),
            JGRow(@"switch", @"protected.chatForward", @"jerkgram.ProtectedContent.ChatForward", nil, nil),
            JGRow(@"switch", @"protected.screenshots", @"jerkgram.ProtectedContent.AllowScreenshots", nil, nil),
            JGRow(@"switch", @"protected.recording", @"jerkgram.ProtectedContent.AllowScreenRecording", nil, nil),
        ])];
    } else if ([self.page isEqualToString:@"mediaStories"]) {
        self.sections = @[JGSection(@"main.media", nil, @[
            JGRow(@"switch", @"media.oneTimeScreenshots", @"jerkgram.ProtectedContent.OneTimeScreenshots", nil, nil),
            JGRow(@"switch", @"media.oneTimeRecording", @"jerkgram.ProtectedContent.OneTimeScreenRecording", nil, nil),
            JGRow(@"switch", @"media.oneTimeSave", @"jerkgram.ProtectedContent.OneTimeSave", nil, nil),
            JGRow(@"switch", @"media.storySave", @"jerkgram.Stories.Save", nil, nil),
        ])];
    } else if ([self.page isEqualToString:@"appearance"]) {
        self.sections = @[
            JGSection(@"appearance.profile.section", nil, @[
                JGRow(@"switch", @"appearance.glass", @"jerkgram.Glass.Enabled", nil, nil),
                JGRow(@"switch", @"appearance.avatar", @"jerkgram.ProfileBlur.Avatar", nil, nil),
                JGRow(@"switch", @"appearance.animated", @"jerkgram.ProfileBlur.Animated", nil, nil),
                JGRow(@"switch", @"appearance.tint", @"jerkgram.ProfileBlur.Tint", nil, nil),
                JGRow(@"switch", @"appearance.reduced", @"jerkgram.ProfileBlur.Reduced", nil, nil),
            ]),
            JGSection(@"appearance.interface.section", @"appearance.hidePhoneHint", @[
                JGRow(@"switch", @"appearance.seconds", @"jerkgram.Appearance.MessageSeconds", nil, nil),
                JGRow(@"switch", @"appearance.hidePhone", @"jerkgram.Appearance.HideOwnPhone", nil, nil),
                JGRow(@"switch", @"appearance.ram", @"jerkgram.Appearance.ShowRamUnderClock", nil, nil),
            ])
        ];
    } else if ([self.page isEqualToString:@"debugResearch"]) {
        self.sections = @[JGSection(@"main.debug", nil, @[JGRow(@"action", @"debug.copyExtensionDiagnostics", nil, nil, @"copyDiagnostics")])];
    } else if ([self.page isEqualToString:@"about"]) {
        self.sections = @[
            JGSection(@"about.channels.section", nil, @[
                JGRow(@"channel", @"about.app", nil, nil, @"openAppChannel"),
                JGRow(@"channel", @"about.community", nil, nil, @"openCommunity"),
            ]),
            JGSection(@"about.version.section", nil, @[
                JGRow(@"value", @"about.version", nil, nil, @"version"),
                JGRow(@"value", @"about.build", nil, nil, @"build"),
                JGRow(@"value", @"about.telegramBase", nil, nil, @"base"),
            ]),
            JGSection(@"about.privacy.section", @"about.analyticsDescription", @[
                JGRow(@"telemetry", @"about.analytics", JGTelemetryPreferenceKey, nil, nil),
            ])
        ];
    } else if ([self.page isEqualToString:@"stars"]) {
        self.sections = @[
            JGSection(@"stars.section", nil, @[
                JGRow(@"switch", @"stars.local", @"jerkgram.Stars.LocalBalance.Enabled", nil, nil),
                JGRow(@"starsInfo", @"stars.balance", @"jerkgram.Stars.LocalBalance.Amount", nil, nil),
            ]),
            JGSection(@"stars.change.section", @"stars.hint", @[
                JGRow(@"text", @"stars.balance", @"jerkgram.Stars.LocalBalance.Amount", nil, @"editStars"),
            ])
        ];
    } else if ([self.page isEqualToString:@"dataAndBackup"]) {
        NSMutableDictionary *retention = JGLoadRetention(self.accountPeerId);
        NSString *footer = nil;
        if ([retention[@"history"] isEqualToString:@"forever"] && [retention[@"media"] longLongValue] < 0) footer = @"data.warning";
        self.sections = @[
            JGSection(nil, nil, @[JGRow(@"dataSummary", @"data.title", nil, nil, nil)]),
            JGSection(@"data.retention.section", footer, @[
                JGRow(@"retentionHistory", @"data.history", nil, nil, @"history"),
                JGRow(@"retentionMedia", @"data.media", nil, nil, @"media"),
                JGRow(@"retentionSwitch", @"data.secret", nil, nil, @"secret"),
                JGRow(@"disclosure", @"data.perChat", nil, nil, @"perChat"),
                JGRow(@"action", @"data.cleanup", nil, nil, @"cleanup"),
            ]),
            JGSection(@"data.backup.section", nil, @[
                JGRow(@"actionValue", @"data.export", nil, nil, @"export"),
                JGRow(@"actionValue", @"data.import", nil, nil, @"import"),
                JGRow(@"accountInfo", @"data.title", nil, nil, nil),
            ])
        ];
    } else if ([self.page isEqualToString:@"sendStyle"]) {
        self.sections = @[JGSection(nil, nil, @[
            JGRow(@"styleOption", @"style.normal", @"normal", nil, nil),
            JGRow(@"styleOption", @"style.bold", @"bold", nil, nil),
            JGRow(@"styleOption", @"style.italic", @"italic", nil, nil),
            JGRow(@"styleOption", @"style.monospace", @"monospace", nil, nil),
            JGRow(@"styleOption", @"style.strikethrough", @"strikethrough", nil, nil),
            JGRow(@"styleOption", @"style.underline", @"underline", nil, nil),
            JGRow(@"styleOption", @"style.spoiler", @"spoiler", nil, nil),
        ])];
    } else if ([self.page isEqualToString:@"chatRetention"]) {
        self.sections = @[JGSection(@"data.perChat", nil, @[
            JGRow(@"retentionSwitch", @"data.saveThisChat", nil, nil, @"chatCapture"),
            JGRow(@"retentionHistory", @"data.history", nil, nil, @"chatDuration"),
            JGRow(@"retentionMedia", @"data.media", nil, nil, @"chatMedia"),
        ])];
    } else {
        self.sections = @[];
    }
    [self.tableView reloadData];
}

- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return self.sections.count; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section { return [self.sections[section][@"rows"] count]; }
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    NSString *key = self.sections[section][@"header"];
    return key.length ? JGString(key) : nil;
}
- (NSString *)tableView:(UITableView *)tableView titleForFooterInSection:(NSInteger)section {
    NSString *key = self.sections[section][@"footer"];
    return key.length ? JGString(key) : nil;
}
- (NSDictionary *)rowAtIndexPath:(NSIndexPath *)indexPath { return self.sections[indexPath.section][@"rows"][indexPath.row]; }

- (BOOL)telemetryEnabled {
    id stored = [NSUserDefaults.standardUserDefaults objectForKey:JGTelemetryPreferenceKey];
    return stored == nil ? YES : [stored boolValue];
}

- (void)toggleChanged:(UISwitch *)sender {
    NSString *key = sender.accessibilityIdentifier ?: @"";
    if ([key isEqualToString:JGTelemetryPreferenceKey]) {
        [NSUserDefaults.standardUserDefaults setBool:sender.isOn forKey:key];
        return;
    }
    if ([key isEqualToString:@"jerkgram.ProtectedContent.Enabled"]) {
        [self applyProtectedMasterValue:sender.isOn];
    } else if ([key hasPrefix:@"jerkgram.ProtectedContent."] || [key isEqualToString:@"jerkgram.Stories.Save"]) {
        [self applyProtectedChildValue:sender.isOn key:key];
    } else {
        [[JGSettingsStore sharedStore] setBool:sender.isOn forKey:key];
        if (sender.isOn && ([key isEqualToString:@"jerkgram.Profile.ShowIds"] || [key isEqualToString:@"jerkgram.Profile.ShowDCs"] || [key isEqualToString:@"jerkgram.Profile.ShowRegistration"])) {
            [[JGSettingsStore sharedStore] setBool:YES forKey:@"jerkgram.Profile.Enabled"];
        }
    }
    [self.tableView reloadData];
}

- (NSArray<NSString *> *)protectedChildKeys {
    return @[
        @"jerkgram.ProtectedContent.GalleryShare", @"jerkgram.ProtectedContent.GallerySave",
        @"jerkgram.ProtectedContent.GalleryCopy", @"jerkgram.ProtectedContent.ChatSave",
        @"jerkgram.ProtectedContent.ChatCopy", @"jerkgram.ProtectedContent.ChatForward",
        @"jerkgram.ProtectedContent.AllowScreenshots", @"jerkgram.ProtectedContent.AllowScreenRecording",
        @"jerkgram.ProtectedContent.OneTimeScreenshots", @"jerkgram.ProtectedContent.OneTimeScreenRecording",
        @"jerkgram.ProtectedContent.OneTimeSave", @"jerkgram.Stories.Save"
    ];
}

- (void)applyProtectedMasterValue:(BOOL)value {
    JGSettingsStore *store = [JGSettingsStore sharedStore];
    [store setBool:value forKey:@"jerkgram.ProtectedContent.Enabled"];
    for (NSString *key in [self protectedChildKeys]) [store setBool:value forKey:key];
}

- (void)applyProtectedChildValue:(BOOL)value key:(NSString *)key {
    JGSettingsStore *store = [JGSettingsStore sharedStore];
    [store setBool:value forKey:key];
    BOOL anyEnabled = NO;
    for (NSString *childKey in [self protectedChildKeys]) anyEnabled |= [store boolForKey:childKey];
    [store setBool:anyEnabled forKey:@"jerkgram.ProtectedContent.Enabled"];
}

- (void)retentionSwitchChanged:(UISwitch *)sender {
    NSMutableDictionary *retention = JGLoadRetention(self.accountPeerId);
    retention[@"archiveSecretChats"] = @(sender.isOn);
    JGSaveRetention(self.accountPeerId, retention);
}

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    NSDictionary *row = [self rowAtIndexPath:indexPath];
    NSString *kind = row[@"kind"];
    NSString *title = JGString(row[@"title"]);
    UITableViewCellStyle style = ([kind isEqualToString:@"channel"] ? UITableViewCellStyleSubtitle : UITableViewCellStyleValue1);
    UITableViewCell *cell = [[UITableViewCell alloc] initWithStyle:style reuseIdentifier:nil];
    cell.textLabel.text = title;
    cell.textLabel.adjustsFontForContentSizeCategory = YES;
    cell.backgroundColor = UIColor.secondarySystemGroupedBackgroundColor;

    if ([kind isEqualToString:@"switch"] || [kind isEqualToString:@"telemetry"] || [kind isEqualToString:@"retentionSwitch"]) {
        UISwitch *toggle = [UISwitch new];
        if ([kind isEqualToString:@"telemetry"]) {
            toggle.on = [self telemetryEnabled];
            toggle.accessibilityIdentifier = JGTelemetryPreferenceKey;
            [toggle addTarget:self action:@selector(toggleChanged:) forControlEvents:UIControlEventValueChanged];
        } else if ([kind isEqualToString:@"retentionSwitch"]) {
            toggle.on = [JGLoadRetention(self.accountPeerId)[@"archiveSecretChats"] boolValue];
            [toggle addTarget:self action:@selector(retentionSwitchChanged:) forControlEvents:UIControlEventValueChanged];
        } else {
            NSString *key = row[@"key"];
            toggle.on = [[JGSettingsStore sharedStore] boolForKey:key];
            toggle.accessibilityIdentifier = key;
            [toggle addTarget:self action:@selector(toggleChanged:) forControlEvents:UIControlEventValueChanged];
        }
        cell.accessoryView = toggle;
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"disclosure"] || [kind isEqualToString:@"sendStyle"] || [kind isEqualToString:@"stars"] || [kind isEqualToString:@"channel"]) {
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
        if ([kind isEqualToString:@"sendStyle"]) cell.detailTextLabel.text = JGStyleLabel([[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Messages.SendTextStyle"]);
        if ([kind isEqualToString:@"stars"]) {
            BOOL enabled = [[JGSettingsStore sharedStore] boolForKey:@"jerkgram.Stars.LocalBalance.Enabled"];
            NSString *amount = [[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Stars.LocalBalance.Amount"];
            cell.detailTextLabel.text = [NSString stringWithFormat:@"%@ · %@ ⭐", JGString(enabled ? @"home.local" : @"home.off"), amount.length ? amount : @"0"];
        }
        if ([kind isEqualToString:@"channel"]) {
            cell.detailTextLabel.text = [row[@"action"] isEqualToString:@"openAppChannel"] ? JGString(@"about.app.subtitle") : JGString(@"about.community.subtitle");
        }
    } else if ([kind isEqualToString:@"stylePreview"]) {
        NSString *body = JGString(@"style.example.body");
        NSString *prefix = JGString(@"style.example.prefix");
        NSString *selected = [[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Messages.SendTextStyle"];
        NSMutableAttributedString *preview = [[NSMutableAttributedString alloc] initWithString:[prefix stringByAppendingString:body]];
        NSRange bodyRange = NSMakeRange(prefix.length, body.length);
        if ([selected isEqualToString:@"bold"]) [preview addAttribute:NSFontAttributeName value:[UIFont boldSystemFontOfSize:17.0] range:bodyRange];
        else if ([selected isEqualToString:@"italic"]) [preview addAttribute:NSFontAttributeName value:[UIFont italicSystemFontOfSize:17.0] range:bodyRange];
        else if ([selected isEqualToString:@"monospace"]) [preview addAttribute:NSFontAttributeName value:[UIFont monospacedSystemFontOfSize:17.0 weight:UIFontWeightRegular] range:bodyRange];
        else if ([selected isEqualToString:@"strikethrough"]) [preview addAttribute:NSStrikethroughStyleAttributeName value:@(NSUnderlineStyleSingle) range:bodyRange];
        else if ([selected isEqualToString:@"underline"]) [preview addAttribute:NSUnderlineStyleAttributeName value:@(NSUnderlineStyleSingle) range:bodyRange];
        else if ([selected isEqualToString:@"spoiler"]) [preview addAttribute:NSBackgroundColorAttributeName value:UIColor.secondaryLabelColor range:bodyRange];
        cell.textLabel.attributedText = preview;
        cell.textLabel.numberOfLines = 0;
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"styleOption"]) {
        NSString *selected = [[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Messages.SendTextStyle"];
        cell.accessoryType = [selected isEqualToString:row[@"key"]] ? UITableViewCellAccessoryCheckmark : UITableViewCellAccessoryNone;
    } else if ([kind isEqualToString:@"value"]) {
        NSString *action = row[@"action"];
        if ([action isEqualToString:@"version"]) cell.detailTextLabel.text = @"1.0.2";
        else if ([action isEqualToString:@"build"]) cell.detailTextLabel.text = @"138";
        else cell.detailTextLabel.text = @"12.9.4";
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"starsInfo"]) {
        NSString *amount = [[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Stars.LocalBalance.Amount"];
        cell.detailTextLabel.text = [NSString stringWithFormat:@"%@ ⭐", amount.length ? amount : @"0"];
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"text"]) {
        cell.detailTextLabel.text = [[JGSettingsStore sharedStore] stringForKey:row[@"key"]];
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    } else if ([kind isEqualToString:@"retentionHistory"]) {
        cell.detailTextLabel.text = JGHistoryLabel(JGLoadRetention(self.accountPeerId)[@"history"]);
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    } else if ([kind isEqualToString:@"retentionMedia"]) {
        cell.detailTextLabel.text = JGMediaLabel(JGLoadRetention(self.accountPeerId)[@"media"]);
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    } else if ([kind isEqualToString:@"dataSummary"]) {
        NSDictionary *retention = JGLoadRetention(self.accountPeerId);
        cell.detailTextLabel.text = [NSString stringWithFormat:@"%@ · %@ · %@ %lld", JGHistoryLabel(retention[@"history"]), JGMediaLabel(retention[@"media"]), [JGLanguageCode() isEqualToString:@"ru"] ? @"аккаунт" : @"account", (long long)self.accountPeerId];
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"actionValue"]) {
        cell.textLabel.textColor = self.view.tintColor;
        cell.detailTextLabel.text = [row[@"action"] isEqualToString:@"export"] ? @"Build138 Stable" : @"Archive v2";
    } else if ([kind isEqualToString:@"accountInfo"]) {
        cell.textLabel.text = [NSString stringWithFormat:@"%@ %lld", [JGLanguageCode() isEqualToString:@"ru"] ? @"Telegram ID" : @"Telegram ID", (long long)self.accountPeerId];
        cell.textLabel.font = [UIFont monospacedDigitSystemFontOfSize:14 weight:UIFontWeightRegular];
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else if ([kind isEqualToString:@"action"]) {
        cell.textLabel.textColor = self.view.tintColor;
    }
    return cell;
}

- (UIViewController *)hostController { return self.parentViewController ?: self; }

- (void)pushPage:(NSString *)page {
    UIViewController *next = JGCreateSettingsHost(self.accountPeerId, page);
    if (next != nil) [[self hostController].navigationController pushViewController:next animated:YES];
}

- (void)openURLString:(NSString *)value {
    NSURL *url = [NSURL URLWithString:value];
    if (url && [UIApplication.sharedApplication canOpenURL:url]) [UIApplication.sharedApplication openURL:url options:@{} completionHandler:nil];
}

- (void)cycleHistoryDuration {
    NSArray *choices = @[@"off", @"7d", @"30d", @"90d", @"forever"];
    NSMutableDictionary *retention = JGLoadRetention(self.accountPeerId);
    NSUInteger index = [choices indexOfObject:retention[@"history"]];
    retention[@"history"] = choices[(index == NSNotFound ? 0 : index + 1) % choices.count];
    JGSaveRetention(self.accountPeerId, retention);
    [self rebuildSections];
}

- (void)cycleMediaLimit {
    NSArray *choices = @[@0, @(250LL*1024*1024), @(500LL*1024*1024), @(1073741824LL), @(2LL*1024*1024*1024), @(5LL*1024*1024*1024), @(-1)];
    NSMutableDictionary *retention = JGLoadRetention(self.accountPeerId);
    NSUInteger index = [choices indexOfObject:retention[@"media"]];
    retention[@"media"] = choices[(index == NSNotFound ? 0 : index + 1) % choices.count];
    JGSaveRetention(self.accountPeerId, retention);
    [self rebuildSections];
}

- (void)openPerChatRules {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:JGString(@"data.perChat") message:nil preferredStyle:UIAlertControllerStyleAlert];
    [alert addTextFieldWithConfigurationHandler:^(UITextField *field) { field.keyboardType = UIKeyboardTypeNumberPad; field.placeholder = @"Telegram chat ID"; }];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.cancel") style:UIAlertActionStyleCancel handler:nil]];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.done") style:UIAlertActionStyleDefault handler:^(__unused UIAlertAction *action) {
        if (alert.textFields.firstObject.text.longLongValue != 0) [self pushPage:@"chatRetention"];
    }]];
    [[self hostController] presentViewController:alert animated:YES completion:nil];
}

- (void)cleanupExpired {
    // M1 owns settings and retention configuration only. With no migrated event store,
    // Build138 cleanup has no product data to remove and is a deterministic no-op.
}

- (NSURL *)settingsArchiveURL {
    return [NSURL fileURLWithPath:[NSTemporaryDirectory() stringByAppendingPathComponent:[NSString stringWithFormat:@"Jerkgram-138-%lld.json", (long long)self.accountPeerId]]];
}

- (NSDictionary *)settingsArchive {
    NSMutableDictionary *values = [NSMutableDictionary dictionary];
    for (JGSettingDescriptor *descriptor in [JGSettingDescriptor allDescriptors]) {
        values[descriptor.key] = descriptor.type == JGSettingValueTypeBool ? @([[JGSettingsStore sharedStore] boolForKey:descriptor.key]) : ([[JGSettingsStore sharedStore] stringForKey:descriptor.key] ?: @"");
    }
    return @{@"format": @"JerkgramArchiveV2", @"build": @138, @"accountPeerId": @(self.accountPeerId), @"settings": values, @"retention": JGLoadRetention(self.accountPeerId)};
}

- (void)exportArchive {
    NSData *data = [NSJSONSerialization dataWithJSONObject:[self settingsArchive] options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:nil];
    NSURL *url = [self settingsArchiveURL];
    if (![data writeToURL:url atomically:YES]) return;
    UIActivityViewController *share = [[UIActivityViewController alloc] initWithActivityItems:@[url] applicationActivities:nil];
    share.popoverPresentationController.sourceView = self.view;
    [[self hostController] presentViewController:share animated:YES completion:nil];
}

- (void)importArchive {
    UIDocumentPickerViewController *picker = [[UIDocumentPickerViewController alloc] initWithDocumentTypes:@[@"public.json", @"public.data"] inMode:UIDocumentPickerModeImport];
    picker.delegate = self;
    [[self hostController] presentViewController:picker animated:YES completion:nil];
}

- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls {
    NSData *data = [NSData dataWithContentsOfURL:urls.firstObject];
    NSDictionary *archive = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
    if (![archive[@"format"] isEqual:@"JerkgramArchiveV2"] || [archive[@"accountPeerId"] longLongValue] != self.accountPeerId) return;
    NSDictionary *values = archive[@"settings"];
    for (JGSettingDescriptor *descriptor in [JGSettingDescriptor allDescriptors]) {
        id value = values[descriptor.key];
        if (descriptor.type == JGSettingValueTypeBool && [value isKindOfClass:NSNumber.class]) [[JGSettingsStore sharedStore] setBool:[value boolValue] forKey:descriptor.key];
        if (descriptor.type == JGSettingValueTypeString && [value isKindOfClass:NSString.class]) [[JGSettingsStore sharedStore] setString:value forKey:descriptor.key];
    }
    [self rebuildSections];
}

- (void)copyExtensionDiagnostics {
    NSString *layoutTrace = JGCopyM1LayoutTrace();
    UIPasteboard.generalPasteboard.string = [NSString stringWithFormat:@"Jerkgram 1.0.2\nBuild 138\nTelegram 12.9.4\nAccount %lld\nDisplay host: %@\n\nM1 layout trace (JSONL):\n%@", (long long)self.accountPeerId, NSStringFromClass([self hostController].class), layoutTrace];
}

static NSString *ghostBaseSanitizeStarsAmount(NSString *text) {
    NSMutableString *result = [NSMutableString string];
    BOOL separator = NO;
    NSString *trimmed = [text stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    for (NSUInteger index = 0; index < trimmed.length; index++) {
        unichar ch = [trimmed characterAtIndex:index];
        if (ch == '-' && result.length == 0 && index == 0) [result appendString:@"-"];
        else if (ch == '+' && result.length == 0 && index == 0) continue;
        else if (ch >= '0' && ch <= '9') [result appendFormat:@"%C", ch];
        else if ((ch == ',' || ch == '.') && !separator) { [result appendString:@"."]; separator = YES; }
        else if (ch == ' ' || ch == 0x00a0) continue;
    }
    return ([result isEqual:@"."] || [result isEqual:@"-."]) ? @"" : result;
}

- (void)editStarsAt:(NSIndexPath *)indexPath {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:JGString(@"stars.balance") message:JGString(@"stars.hint") preferredStyle:UIAlertControllerStyleAlert];
    [alert addTextFieldWithConfigurationHandler:^(UITextField *field) { field.keyboardType = UIKeyboardTypeDecimalPad; field.text = [[JGSettingsStore sharedStore] stringForKey:@"jerkgram.Stars.LocalBalance.Amount"]; }];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.cancel") style:UIAlertActionStyleCancel handler:nil]];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.save") style:UIAlertActionStyleDefault handler:^(__unused UIAlertAction *action) {
        NSString *value = ghostBaseSanitizeStarsAmount(alert.textFields.firstObject.text ?: @""); if (value.length == 0) value = @"0"; [[JGSettingsStore sharedStore] setString:value forKey:@"jerkgram.Stars.LocalBalance.Amount"]; [self.tableView reloadData];
    }]];
    [[self hostController] presentViewController:alert animated:YES completion:nil];
}

- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    NSDictionary *row = [self rowAtIndexPath:indexPath];
    NSString *kind = row[@"kind"];
    if ([kind isEqualToString:@"disclosure"] || [kind isEqualToString:@"sendStyle"] || [kind isEqualToString:@"stars"]) {
        NSString *page = row[@"page"];
        if (page.length) [self pushPage:page]; else if ([row[@"action"] isEqualToString:@"perChat"]) [self openPerChatRules];
    } else if ([kind isEqualToString:@"styleOption"]) {
        [[JGSettingsStore sharedStore] setString:row[@"key"] forKey:@"jerkgram.Messages.SendTextStyle"];
        [self.tableView reloadData];
    } else if ([kind isEqualToString:@"channel"]) {
        [self openURLString:[row[@"action"] isEqualToString:@"openAppChannel"] ? @"tg://resolve?domain=JerkgramApp" : @"tg://resolve?domain=JerkgramCommunity"];
    } else if ([kind isEqualToString:@"action"]) {
        NSString *action = row[@"action"];
        if ([action isEqualToString:@"copyDiagnostics"]) [self copyExtensionDiagnostics];
        else if ([action isEqualToString:@"cleanup"]) [self cleanupExpired];
    } else if ([kind isEqualToString:@"actionValue"]) {
        if ([row[@"action"] isEqualToString:@"export"]) [self exportArchive];
        else [self importArchive];
    } else if ([kind isEqualToString:@"retentionHistory"]) {
        [self cycleHistoryDuration];
    } else if ([kind isEqualToString:@"retentionMedia"]) {
        [self cycleMediaLimit];
    } else if ([kind isEqualToString:@"text"]) {
        [self editStarsAt:indexPath];
    }
}
@end

UIViewController *JGCreateSettingsHost(int64_t accountPeerId, NSString *page) {
    if (accountPeerId == 0 || ![JGReachableSettingsPages() containsObject:page]) return nil;
    Class displayClass = objc_getClass("_TtC7Display14ViewController");
    if (displayClass == Nil || ![displayClass isSubclassOfClass:UIViewController.class]) return nil;

    SEL initSelector = sel_registerName("initWithNibName:bundle:");
    if (![displayClass instancesRespondToSelector:initSelector]) return nil;
    id allocated = ((id (*)(id, SEL))objc_msgSend)(displayClass, sel_registerName("alloc"));
    UIViewController *host = ((id (*)(id, SEL, NSString *, NSBundle *))objc_msgSend)(allocated, initSelector, nil, nil);
    if (![host isKindOfClass:UIViewController.class]) return nil;

    JGParitySettingsController *child = [[JGParitySettingsController alloc] initWithAccountPeerId:accountPeerId page:page];
    host.title = JGString(JGPageTitleKey(page));
    host.navigationItem.largeTitleDisplayMode = UINavigationItemLargeTitleDisplayModeNever;
    [host addChildViewController:child];
    UIView *hostView = host.view;
    child.view.frame = hostView.bounds;
    child.view.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [hostView addSubview:child.view];
    [child didMoveToParentViewController:host];
    objc_setAssociatedObject(host, &JGHostedChildKey, child, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    return host;
}
