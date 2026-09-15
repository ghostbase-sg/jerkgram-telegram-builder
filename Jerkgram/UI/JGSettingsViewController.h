#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN
FOUNDATION_EXPORT CFTimeInterval JGSettingsNavigationTimestamp(void);
FOUNDATION_EXPORT void JGSettingsNavigationTrace(NSString *route, NSString *stage, CFTimeInterval tapTimestamp);
FOUNDATION_EXPORT UIViewController * _Nullable JGCreateSettingsHost(int64_t accountPeerId, NSString *page, CFTimeInterval tapTimestamp);
FOUNDATION_EXPORT NSArray<NSString *> *JGReachableSettingsPages(void);
NS_ASSUME_NONNULL_END
