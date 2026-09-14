#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

typedef NS_ENUM(NSInteger, JGSettingValueType) {
    JGSettingValueTypeBool = 0,
    JGSettingValueTypeInteger = 1,
};

@interface JGSettingDescriptor : NSObject
@property(nonatomic, readonly) NSString *section;
@property(nonatomic, readonly) NSString *key;
@property(nonatomic, readonly) NSString *labelKey;
@property(nonatomic, readonly) JGSettingValueType type;
@property(nonatomic, readonly) NSNumber *defaultValue;
@property(nonatomic, readonly, getter=isGlobal) BOOL global;
- (instancetype)initWithSection:(NSString *)section key:(NSString *)key labelKey:(NSString *)labelKey type:(JGSettingValueType)type defaultValue:(NSNumber *)defaultValue global:(BOOL)global;
+ (NSArray<JGSettingDescriptor *> *)allDescriptors;
+ (nullable JGSettingDescriptor *)descriptorForKey:(NSString *)key;
@end

@interface JGSettingsStore : NSObject
@property(nonatomic, readonly, nullable) NSString *activeAccountPeerId;
+ (instancetype)sharedStore;
- (BOOL)activateAccountPeerId:(int64_t)peerId;
- (nullable NSNumber *)valueForKey:(NSString *)key;
- (BOOL)boolForKey:(NSString *)key;
- (NSInteger)integerForKey:(NSString *)key;
- (void)setBool:(BOOL)value forKey:(NSString *)key;
- (void)setInteger:(NSInteger)value forKey:(NSString *)key;
@end

FOUNDATION_EXPORT NSString * const JGSettingsSchemaVersionKey;
FOUNDATION_EXPORT NSString * const JGSettingsMigrationMarker;
FOUNDATION_EXPORT NSString *JGScopedStorageKey(NSString *accountPeerId, NSString *baseKey);

NS_ASSUME_NONNULL_END
