#import "JGSettingsStore.h"

NSString * const JGSettingsSchemaVersionKey = @"jerkgram.settings.schemaVersion";
NSString * const JGSettingsMigrationMarker = @"jerkgram.runtime.namespaceMigration.v1";
static NSString * const JGGlobalDownloadBoostKey = @"jerkgram.global.DownloadBoost";
static const NSInteger JGSettingsSchemaVersion = 1;

NSString *JGScopedStorageKey(NSString *accountPeerId, NSString *baseKey) {
    return [NSString stringWithFormat:@"jerkgram.account.%@.setting.%@", accountPeerId, baseKey];
}

@implementation JGSettingDescriptor
- (instancetype)initWithSection:(NSString *)section key:(NSString *)key labelKey:(NSString *)labelKey type:(JGSettingValueType)type defaultValue:(NSNumber *)defaultValue global:(BOOL)global {
    self = [super init];
    if (self) { _section=[section copy]; _key=[key copy]; _labelKey=[labelKey copy]; _type=type; _defaultValue=defaultValue; _global=global; }
    return self;
}
+ (NSArray<JGSettingDescriptor *> *)allDescriptors {
    static NSArray<JGSettingDescriptor *> *items;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        items = @[
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.ReadMessages" labelKey:@"setting.GhostMode_ReadMessages" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.TypingActions" labelKey:@"setting.GhostMode_TypingActions" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.HideRecording" labelKey:@"setting.GhostMode_HideRecording" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.HideUploading" labelKey:@"setting.GhostMode_HideUploading" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.HideStickerActivity" labelKey:@"setting.GhostMode_HideStickerActivity" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.HideGameActivity" labelKey:@"setting.GhostMode_HideGameActivity" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.HideEmojiActivity" labelKey:@"setting.GhostMode_HideEmojiActivity" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.Presence" labelKey:@"setting.GhostMode_Presence" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Ghost Mode" key:@"jerkgram.GhostMode.ScheduledSend" labelKey:@"setting.GhostMode_ScheduledSend" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.SaveDeleted" labelKey:@"setting.Messages_SaveDeleted" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.ShowDeleted" labelKey:@"setting.Messages_ShowDeleted" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.SaveEditHistory" labelKey:@"setting.Messages_SaveEditHistory" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.ShowEditHistory" labelKey:@"setting.Messages_ShowEditHistory" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.HideBlockedMessages" labelKey:@"setting.Messages_HideBlockedMessages" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.HideBlockedReactions" labelKey:@"setting.Messages_HideBlockedReactions" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.SendTextStyle" labelKey:@"setting.Messages_SendTextStyle" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.DeletedPortableReplies" labelKey:@"setting.Messages_DeletedPortableReplies" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.PreserveDeletedMedia" labelKey:@"setting.Messages_PreserveDeletedMedia" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.DeletedMediaCacheLimit" labelKey:@"setting.Messages_DeletedMediaCacheLimit" type:JGSettingValueTypeInteger defaultValue:@(1073741824) global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.DeletedMediaRetentionDays" labelKey:@"setting.Messages_DeletedMediaRetentionDays" type:JGSettingValueTypeInteger defaultValue:@(30) global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Messages" key:@"jerkgram.Messages.ForwardWithoutAuthor" labelKey:@"setting.Messages_ForwardWithoutAuthor" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.Enabled" labelKey:@"setting.ProtectedContent_Enabled" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.GalleryShare" labelKey:@"setting.ProtectedContent_GalleryShare" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.GallerySave" labelKey:@"setting.ProtectedContent_GallerySave" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.GalleryCopy" labelKey:@"setting.ProtectedContent_GalleryCopy" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.ChatSave" labelKey:@"setting.ProtectedContent_ChatSave" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.ChatCopy" labelKey:@"setting.ProtectedContent_ChatCopy" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.ChatForward" labelKey:@"setting.ProtectedContent_ChatForward" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.AllowScreenshots" labelKey:@"setting.ProtectedContent_AllowScreenshots" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.AllowScreenRecording" labelKey:@"setting.ProtectedContent_AllowScreenRecording" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.OneTimeScreenshots" labelKey:@"setting.ProtectedContent_OneTimeScreenshots" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.OneTimeScreenRecording" labelKey:@"setting.ProtectedContent_OneTimeScreenRecording" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Protected Content" key:@"jerkgram.ProtectedContent.OneTimeSave" labelKey:@"setting.ProtectedContent_OneTimeSave" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Stories / Media" key:@"jerkgram.Stories.Save" labelKey:@"setting.Stories_Save" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Profile" key:@"jerkgram.Profile.Enabled" labelKey:@"setting.Profile_Enabled" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Profile" key:@"jerkgram.Profile.ShowIds" labelKey:@"setting.Profile_ShowIds" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Profile" key:@"jerkgram.Profile.ShowDCs" labelKey:@"setting.Profile_ShowDCs" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Profile" key:@"jerkgram.Profile.ShowRegistration" labelKey:@"setting.Profile_ShowRegistration" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.Appearance.ShowRamUnderClock" labelKey:@"setting.Appearance_ShowRamUnderClock" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.Appearance.MessageSeconds" labelKey:@"setting.Appearance_MessageSeconds" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.Appearance.HideOwnPhone" labelKey:@"setting.Appearance_HideOwnPhone" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.Glass.Enabled" labelKey:@"setting.Glass_Enabled" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.ProfileBlur.Avatar" labelKey:@"setting.ProfileBlur_Avatar" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.ProfileBlur.Animated" labelKey:@"setting.ProfileBlur_Animated" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.ProfileBlur.Tint" labelKey:@"setting.ProfileBlur_Tint" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Appearance" key:@"jerkgram.ProfileBlur.Reduced" labelKey:@"setting.ProfileBlur_Reduced" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Other" key:@"jerkgram.Stars.LocalBalance.Enabled" labelKey:@"setting.Stars_LocalBalance_Enabled" type:JGSettingValueTypeBool defaultValue:@NO global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Other" key:@"jerkgram.Stars.LocalBalance.Amount" labelKey:@"setting.Stars_LocalBalance_Amount" type:JGSettingValueTypeInteger defaultValue:@(0) global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Other" key:@"jerkgram.Stars.LocalBalance.BaseAmount" labelKey:@"setting.Stars_LocalBalance_BaseAmount" type:JGSettingValueTypeInteger defaultValue:@(0) global:NO],
            [[JGSettingDescriptor alloc] initWithSection:@"Other" key:@"jerkgram.global.DownloadBoost" labelKey:@"setting.global_DownloadBoost" type:JGSettingValueTypeInteger defaultValue:@(0) global:YES],
        ];
    });
    return items;
}
+ (JGSettingDescriptor *)descriptorForKey:(NSString *)key {
    for (JGSettingDescriptor *d in [self allDescriptors]) { if ([d.key isEqualToString:key]) return d; }
    return nil;
}
@end

@interface JGSettingsStore ()
@property(nonatomic, readwrite, nullable) NSString *activeAccountPeerId;
@property(nonatomic) NSMutableDictionary<NSString *, NSNumber *> *cache;
@end

@implementation JGSettingsStore
+ (instancetype)sharedStore { static JGSettingsStore *s; static dispatch_once_t onceToken; dispatch_once(&onceToken, ^{ s=[JGSettingsStore new]; }); return s; }
- (instancetype)init { self=[super init]; if(self) _cache=[NSMutableDictionary dictionary]; return self; }

- (BOOL)isKnownCanonicalKey:(NSString *)key { return [JGSettingDescriptor descriptorForKey:key] != nil; }

- (NSString *)canonicalKeyForLegacyKey:(NSString *)legacyKey {
    NSArray<NSString *> *prefixes = @[@"GhostBase.", @"GB."];
    for (NSString *prefix in prefixes) {
        if (legacyKey.length > prefix.length && [[legacyKey substringToIndex:prefix.length] caseInsensitiveCompare:prefix] == NSOrderedSame) {
            return [@"jerkgram." stringByAppendingString:[legacyKey substringFromIndex:prefix.length]];
        }
    }
    return nil;
}

- (void)performOneTimeNamespaceMigrationForAccount:(NSString *)accountPeerId defaults:(NSUserDefaults *)defaults {
    if ([defaults boolForKey:JGSettingsMigrationMarker]) return;
    NSString *domainName = NSBundle.mainBundle.bundleIdentifier;
    if (domainName.length == 0) return;
    NSMutableDictionary *domain = [[defaults persistentDomainForName:domainName] mutableCopy] ?: [NSMutableDictionary dictionary];
    NSArray<NSString *> *legacyKeys = [[domain.allKeys filteredArrayUsingPredicate:[NSPredicate predicateWithBlock:^BOOL(id key, NSDictionary *_) { return [key isKindOfClass:NSString.class]; }]] sortedArrayUsingSelector:@selector(localizedCaseInsensitiveCompare:)];
    for (NSString *legacy in legacyKeys) {
        NSString *canonicalKey = [self canonicalKeyForLegacyKey:legacy];
        if (canonicalKey == nil || ![self isKnownCanonicalKey:canonicalKey]) continue;
        if (domain[canonicalKey] == nil) {
            id value = domain[legacy];
            if (value != nil) {
                [defaults setObject:value forKey:canonicalKey];
                domain[canonicalKey] = value;
            }
        }
    }
    // Seed only the account active during the one-time legacy migration. The marker prevents
    // selected-account carrier values from leaking into accounts activated later.
    for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
        if (descriptor.isGlobal) continue;
        NSString *scoped = JGScopedStorageKey(accountPeerId, descriptor.key);
        if ([defaults objectForKey:scoped] == nil && domain[descriptor.key] != nil) {
            [defaults setObject:domain[descriptor.key] forKey:scoped];
        }
    }
    [defaults setBool:YES forKey:JGSettingsMigrationMarker];
}

- (NSNumber *)normalizedValue:(id)value descriptor:(JGSettingDescriptor *)descriptor {
    if (![value isKindOfClass:NSNumber.class]) return descriptor.defaultValue;
    NSNumber *number=(NSNumber *)value;
    if (descriptor.type == JGSettingValueTypeBool) return @([number boolValue]);
    NSInteger v=[number integerValue];
    if ([descriptor.key isEqualToString:JGGlobalDownloadBoostKey]) v=MAX(0,MIN(2,v));
    if ([descriptor.key isEqualToString:@"jerkgram.Messages.DeletedMediaCacheLimit"] ||
        [descriptor.key isEqualToString:@"jerkgram.Messages.DeletedMediaRetentionDays"] ||
        [descriptor.key hasPrefix:@"jerkgram.Stars.LocalBalance."]) v=MAX(0,v);
    return @(v);
}

- (BOOL)activateAccountPeerId:(int64_t)peerId {
    if (peerId == 0) return NO;
    NSString *account=[NSString stringWithFormat:@"%lld", (long long)peerId];
    @synchronized (self) {
        if ([self.activeAccountPeerId isEqualToString:account] && self.cache.count != 0) return YES;
        NSUserDefaults *defaults=NSUserDefaults.standardUserDefaults;
        [self performOneTimeNamespaceMigrationForAccount:account defaults:defaults];
        NSMutableDictionary *next=[NSMutableDictionary dictionary];
        for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
            NSString *storageKey = descriptor.isGlobal ? descriptor.key : JGScopedStorageKey(account, descriptor.key);
            id stored=[defaults objectForKey:storageKey];
            NSNumber *value=[self normalizedValue:stored descriptor:descriptor];
            next[descriptor.key]=value;
        }
        self.activeAccountPeerId=account;
        self.cache=next;
        [defaults setInteger:JGSettingsSchemaVersion forKey:JGSettingsSchemaVersionKey];
        // M-1 compatibility projection: the selected account is reflected in unscoped base keys.
        for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
            if (descriptor.isGlobal) continue;
            [defaults setObject:next[descriptor.key] forKey:descriptor.key];
        }
        return YES;
    }
}

- (NSNumber *)valueForKey:(NSString *)key {
    @synchronized (self) {
        JGSettingDescriptor *descriptor=[JGSettingDescriptor descriptorForKey:key];
        if (descriptor == nil) return nil;
        NSNumber *value=self.cache[key];
        return value ?: descriptor.defaultValue;
    }
}
- (BOOL)boolForKey:(NSString *)key { return [[self valueForKey:key] boolValue]; }
- (NSInteger)integerForKey:(NSString *)key { return [[self valueForKey:key] integerValue]; }
- (void)setBool:(BOOL)value forKey:(NSString *)key { [self setNumber:@(value) forKey:key expectedType:JGSettingValueTypeBool]; }
- (void)setInteger:(NSInteger)value forKey:(NSString *)key { [self setNumber:@(value) forKey:key expectedType:JGSettingValueTypeInteger]; }
- (void)setNumber:(NSNumber *)number forKey:(NSString *)key expectedType:(JGSettingValueType)type {
    @synchronized (self) {
        JGSettingDescriptor *descriptor=[JGSettingDescriptor descriptorForKey:key];
        if (descriptor == nil || descriptor.type != type) return;
        if (!descriptor.isGlobal && self.activeAccountPeerId.length == 0) return;
        NSNumber *value=[self normalizedValue:number descriptor:descriptor];
        NSUserDefaults *defaults=NSUserDefaults.standardUserDefaults;
        NSString *storageKey=descriptor.isGlobal ? descriptor.key : JGScopedStorageKey(self.activeAccountPeerId, descriptor.key);
        [defaults setObject:value forKey:storageKey];
        self.cache[key]=value;
        if (!descriptor.isGlobal) [defaults setObject:value forKey:descriptor.key];
    }
}
@end
