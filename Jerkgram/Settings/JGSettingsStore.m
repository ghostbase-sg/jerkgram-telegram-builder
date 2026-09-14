#import "JGSettingsStore.h"

NSString *JGScopedStorageKey(NSString *accountPeerId, NSString *baseKey) {
    return [NSString stringWithFormat:@"jerkgram.account.%@.setting.%@", accountPeerId, baseKey];
}

@implementation JGSettingDescriptor
- (instancetype)initWithKey:(NSString *)key type:(JGSettingValueType)type defaultValue:(id)defaultValue {
    self = [super init];
    if (self) {
        _key = [key copy];
        _type = type;
        _defaultValue = defaultValue;
    }
    return self;
}

+ (NSArray<JGSettingDescriptor *> *)allDescriptors {
    static NSArray<JGSettingDescriptor *> *items;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
#define JG_BOOL(k, v) [[JGSettingDescriptor alloc] initWithKey:(k) type:JGSettingValueTypeBool defaultValue:@(v)]
#define JG_STRING(k, v) [[JGSettingDescriptor alloc] initWithKey:(k) type:JGSettingValueTypeString defaultValue:(v)]
        items = @[
            JG_BOOL(@"jerkgram.Profile.Enabled", YES),
            JG_BOOL(@"jerkgram.Profile.ShowIds", YES),
            JG_BOOL(@"jerkgram.Profile.ShowDCs", YES),
            JG_BOOL(@"jerkgram.Profile.ShowRegistration", YES),
            JG_BOOL(@"jerkgram.Glass.Enabled", YES),
            JG_BOOL(@"jerkgram.ProfileBlur.Avatar", YES),
            JG_BOOL(@"jerkgram.ProfileBlur.Animated", YES),
            JG_BOOL(@"jerkgram.ProfileBlur.Tint", YES),
            JG_BOOL(@"jerkgram.ProfileBlur.Reduced", NO),
            JG_BOOL(@"jerkgram.GhostMode.ReadMessages", NO),
            JG_BOOL(@"jerkgram.GhostMode.TypingActions", NO),
            JG_BOOL(@"jerkgram.GhostMode.HideRecording", NO),
            JG_BOOL(@"jerkgram.GhostMode.HideUploading", NO),
            JG_BOOL(@"jerkgram.GhostMode.HideStickerActivity", NO),
            JG_BOOL(@"jerkgram.GhostMode.HideGameActivity", NO),
            JG_BOOL(@"jerkgram.GhostMode.HideEmojiActivity", NO),
            JG_BOOL(@"jerkgram.GhostMode.Presence", NO),
            JG_BOOL(@"jerkgram.GhostMode.ScheduledSend", NO),
            JG_BOOL(@"jerkgram.Messages.SaveDeleted", YES),
            JG_BOOL(@"jerkgram.Messages.ShowDeleted", YES),
            JG_BOOL(@"jerkgram.Messages.SaveEditHistory", YES),
            JG_BOOL(@"jerkgram.Messages.ShowEditHistory", YES),
            JG_BOOL(@"jerkgram.Messages.HideBlockedMessages", YES),
            JG_BOOL(@"jerkgram.Messages.HideBlockedReactions", YES),
            JG_STRING(@"jerkgram.Messages.SendTextStyle", @"normal"),
            JG_BOOL(@"jerkgram.Messages.DeletedPortableReplies", YES),
            JG_BOOL(@"jerkgram.Messages.PreserveDeletedMedia", YES),
            JG_BOOL(@"jerkgram.Appearance.ShowRamUnderClock", NO),
            JG_BOOL(@"jerkgram.Appearance.MessageSeconds", NO),
            JG_BOOL(@"jerkgram.Appearance.HideOwnPhone", NO),
            JG_BOOL(@"jerkgram.ProtectedContent.Enabled", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.GalleryShare", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.GallerySave", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.GalleryCopy", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.ChatSave", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.ChatCopy", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.ChatForward", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.AllowScreenshots", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.AllowScreenRecording", YES),
            JG_BOOL(@"jerkgram.ProtectedContent.OneTimeScreenshots", NO),
            JG_BOOL(@"jerkgram.ProtectedContent.OneTimeScreenRecording", NO),
            JG_BOOL(@"jerkgram.ProtectedContent.OneTimeSave", NO),
            JG_BOOL(@"jerkgram.Stories.Save", NO),
            JG_BOOL(@"jerkgram.Stars.LocalBalance.Enabled", NO),
            JG_STRING(@"jerkgram.Stars.LocalBalance.Amount", @"0"),
            JG_STRING(@"jerkgram.Stars.LocalBalance.BaseAmount", @"0"),
        ];
#undef JG_BOOL
#undef JG_STRING
        NSCAssert(items.count == 46, @"Build138 has exactly 46 reachable Settings values");
    });
    return items;
}

+ (JGSettingDescriptor *)descriptorForKey:(NSString *)key {
    for (JGSettingDescriptor *descriptor in self.allDescriptors) {
        if ([descriptor.key isEqualToString:key]) return descriptor;
    }
    return nil;
}
@end

@interface JGSettingsStore ()
@property(nonatomic, readwrite, nullable) NSString *activeAccountPeerId;
@property(nonatomic) NSMutableDictionary<NSString *, id> *cache;
@end

@implementation JGSettingsStore
+ (instancetype)sharedStore {
    static JGSettingsStore *store;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{ store = [JGSettingsStore new]; });
    return store;
}

- (instancetype)init {
    self = [super init];
    if (self) _cache = [NSMutableDictionary dictionary];
    return self;
}

- (void)deactivateAccount {
    @synchronized (self) {
        self.activeAccountPeerId = nil;
        [self.cache removeAllObjects];
    }
}

- (id)normalizedValue:(id)value descriptor:(JGSettingDescriptor *)descriptor {
    if (descriptor.type == JGSettingValueTypeBool) {
        return [value isKindOfClass:NSNumber.class] ? @([value boolValue]) : descriptor.defaultValue;
    }
    return [value isKindOfClass:NSString.class] ? value : descriptor.defaultValue;
}

- (BOOL)activateAccountPeerId:(int64_t)peerId {
    if (peerId == 0) return NO;
    NSString *account = [NSString stringWithFormat:@"%lld", (long long)peerId];
    @synchronized (self) {
        if ([self.activeAccountPeerId isEqualToString:account] && self.cache.count == 46) return YES;
        NSUserDefaults *defaults = NSUserDefaults.standardUserDefaults;
        NSMutableDictionary<NSString *, id> *next = [NSMutableDictionary dictionaryWithCapacity:46];
        for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
            NSString *scopedKey = JGScopedStorageKey(account, descriptor.key);
            id stored = [defaults objectForKey:scopedKey];
            if (stored == nil) {
                id unscopedCanonicalValue = [defaults objectForKey:descriptor.key];
                stored = [self normalizedValue:unscopedCanonicalValue descriptor:descriptor];
                [defaults setObject:stored forKey:scopedKey];
            } else {
                stored = [self normalizedValue:stored descriptor:descriptor];
            }
            next[descriptor.key] = stored;
        }
        self.activeAccountPeerId = account;
        self.cache = next;
        for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
            [defaults setObject:next[descriptor.key] forKey:descriptor.key];
        }
        return YES;
    }
}

- (id)valueForKeySafely:(NSString *)key expectedType:(JGSettingValueType)type {
    JGSettingDescriptor *descriptor = [JGSettingDescriptor descriptorForKey:key];
    if (descriptor == nil || descriptor.type != type) return nil;
    @synchronized (self) {
        if (self.activeAccountPeerId.length == 0) return descriptor.defaultValue;
        return self.cache[key] ?: descriptor.defaultValue;
    }
}

- (BOOL)boolForKey:(NSString *)key {
    return [[self valueForKeySafely:key expectedType:JGSettingValueTypeBool] boolValue];
}

- (NSString *)stringForKey:(NSString *)key {
    id value = [self valueForKeySafely:key expectedType:JGSettingValueTypeString];
    return [value isKindOfClass:NSString.class] ? value : @"";
}

- (void)setValueSafely:(id)value forKey:(NSString *)key expectedType:(JGSettingValueType)type {
    JGSettingDescriptor *descriptor = [JGSettingDescriptor descriptorForKey:key];
    if (descriptor == nil || descriptor.type != type) return;
    @synchronized (self) {
        if (self.activeAccountPeerId.length == 0) return;
        id normalized = [self normalizedValue:value descriptor:descriptor];
        NSUserDefaults *defaults = NSUserDefaults.standardUserDefaults;
        [defaults setObject:normalized forKey:JGScopedStorageKey(self.activeAccountPeerId, key)];
        [defaults setObject:normalized forKey:key];
        self.cache[key] = normalized;
    }
}

- (void)setBool:(BOOL)value forKey:(NSString *)key {
    [self setValueSafely:@(value) forKey:key expectedType:JGSettingValueTypeBool];
}

- (void)setString:(NSString *)value forKey:(NSString *)key {
    [self setValueSafely:value ?: @"" forKey:key expectedType:JGSettingValueTypeString];
}
@end
