#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

typedef NS_ENUM(NSInteger, JGSettingValueType) {
    JGSettingValueTypeBool = 0,
    JGSettingValueTypeString = 1,
};

@interface JGSettingDescriptor : NSObject
@property(nonatomic, readonly) NSString *key;
@property(nonatomic, readonly) JGSettingValueType type;
@property(nonatomic, readonly) id defaultValue;
- (instancetype)initWithKey:(NSString *)key
                       type:(JGSettingValueType)type
               defaultValue:(id)defaultValue;
+ (NSArray<JGSettingDescriptor *> *)allDescriptors;
+ (nullable JGSettingDescriptor *)descriptorForKey:(NSString *)key;
@end

@interface JGSettingsStore : NSObject
@property(nonatomic, readonly, nullable) NSString *activeAccountPeerId;
+ (instancetype)sharedStore;
- (BOOL)activateAccountPeerId:(int64_t)peerId;
- (void)deactivateAccount;
- (BOOL)boolForKey:(NSString *)key;
- (NSString *)stringForKey:(NSString *)key;
- (void)setBool:(BOOL)value forKey:(NSString *)key;
- (void)setString:(NSString *)value forKey:(NSString *)key;
@end

FOUNDATION_EXPORT NSString *JGScopedStorageKey(NSString *accountPeerId, NSString *baseKey);

NS_ASSUME_NONNULL_END
