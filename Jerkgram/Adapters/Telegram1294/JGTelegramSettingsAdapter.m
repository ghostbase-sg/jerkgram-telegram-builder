#import "JGTelegramSettingsAdapter.h"
#import "JGSettingsViewController.h"
#import "JGSettingsStore.h"
#import <UIKit/UIKit.h>
#import <objc/runtime.h>
#import <dlfcn.h>
#import <mach-o/dyld.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

NSString * const JGSettingsEntryAccessibilityIdentifier = @"com.jerkgram.m1.settings-entry";
static const char JGEntryTargetAssociationKey;
static void (*JGOriginalViewDidAppear)(id, SEL, BOOL) = NULL;
static BOOL JGAdapterInstalled = NO;
static BOOL JGDyldCallbackRegistered = NO;

typedef int64_t (*JGPeerIdToInt64Function)(uint64_t namespaceWord, uint64_t idWord);

@interface JGSettingsEntryTarget : NSObject
@property(nonatomic, weak) UIViewController *host;
@property(nonatomic) int64_t accountPeerId;
- (void)openJerkgramSettings:(id)sender;
@end

@implementation JGSettingsEntryTarget
- (void)openJerkgramSettings:(id)sender {
    UIViewController *host = self.host;
    if (host == nil || self.accountPeerId == 0) return;
    JGSettingsViewController *settings = [[JGSettingsViewController alloc] initWithAccountPeerId:self.accountPeerId];
    if (host.navigationController != nil) {
        [host.navigationController pushViewController:settings animated:YES];
    } else {
        UINavigationController *navigation = [[UINavigationController alloc] initWithRootViewController:settings];
        [host presentViewController:navigation animated:YES completion:nil];
    }
}
@end

static Ivar JGIvar(id object, const char *name) {
    Class cls = object_getClass(object);
    return cls ? class_getInstanceVariable(cls, name) : NULL;
}

static BOOL JGReadSettingsFlag(id object) {
    Ivar ivar = JGIvar(object, "isSettings");
    if (ivar == NULL) return NO;
    ptrdiff_t offset = ivar_getOffset(ivar);
    uint8_t raw = 0;
    memcpy(&raw, ((const uint8_t *)(__bridge const void *)object) + offset, sizeof(raw));
    return raw != 0;
}

static BOOL JGPeerIdSpanIsProven(id object, ptrdiff_t peerOffset) {
    Class cls = object_getClass(object);
    unsigned int count = 0;
    Ivar *ivars = class_copyIvarList(cls, &count);
    if (ivars == NULL) return NO;
    ptrdiff_t nextOffset = PTRDIFF_MAX;
    for (unsigned int i = 0; i < count; i++) {
        ptrdiff_t candidate = ivar_getOffset(ivars[i]);
        if (candidate > peerOffset && candidate < nextOffset) nextOffset = candidate;
    }
    free(ivars);
    return nextOffset != PTRDIFF_MAX && (nextOffset - peerOffset) == (ptrdiff_t)(sizeof(uint64_t) * 2);
}

static JGPeerIdToInt64Function JGPeerIdToInt64Resolver(void) {
    static JGPeerIdToInt64Function function = NULL;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        // Current Telegram 12.9.4 Postbox export. Mach-O export trie spells it with
        // the leading object-file underscore; dlsym normally resolves the source-level name.
        void *symbol = dlsym(RTLD_DEFAULT, "$s7Postbox6PeerIdV7toInt64s0E0VyF");
        if (symbol == NULL) symbol = dlsym(RTLD_DEFAULT, "_$s7Postbox6PeerIdV7toInt64s0E0VyF");
        function = (JGPeerIdToInt64Function)symbol;
    });
    return function;
}

static int64_t JGAccountPeerId(id object) {
    Ivar peerIvar = JGIvar(object, "peerId");
    if (peerIvar == NULL) return 0;
    ptrdiff_t peerOffset = ivar_getOffset(peerIvar);
    if (!JGPeerIdSpanIsProven(object, peerOffset)) return 0;
    uint64_t words[2] = {0, 0};
    memcpy(words, ((const uint8_t *)(__bridge const void *)object) + peerOffset, sizeof(words));
    JGPeerIdToInt64Function toInt64 = JGPeerIdToInt64Resolver();
    if (toInt64 == NULL) return 0;
    return toInt64(words[0], words[1]);
}

static void JGInstallEntryOnSettingsController(id object) {
    if (![object isKindOfClass:UIViewController.class] || !JGReadSettingsFlag(object)) return;
    int64_t accountPeerId = JGAccountPeerId(object);
    if (accountPeerId == 0) return;
    UIViewController *controller = (UIViewController *)object;
    [[JGSettingsStore sharedStore] activateAccountPeerId:accountPeerId];

    JGSettingsEntryTarget *target = objc_getAssociatedObject(controller, &JGEntryTargetAssociationKey);
    if (target == nil) {
        target = [JGSettingsEntryTarget new];
        target.host = controller;
        objc_setAssociatedObject(controller, &JGEntryTargetAssociationKey, target, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    target.accountPeerId = accountPeerId;

    NSMutableArray<UIBarButtonItem *> *items = [NSMutableArray array];
    for (UIBarButtonItem *candidate in controller.navigationItem.rightBarButtonItems ?: @[]) {
        if (![candidate.accessibilityIdentifier isEqualToString:JGSettingsEntryAccessibilityIdentifier]) [items addObject:candidate];
    }
    UIBarButtonItem *entry = [[UIBarButtonItem alloc] initWithTitle:@"Jerkgram" style:UIBarButtonItemStylePlain target:target action:@selector(openJerkgramSettings:)];
    entry.accessibilityIdentifier = JGSettingsEntryAccessibilityIdentifier;
    [items addObject:entry];
    controller.navigationItem.rightBarButtonItems = items;
}

static void JGPeerInfoViewDidAppear(id self, SEL _cmd, BOOL animated) {
    if (JGOriginalViewDidAppear != NULL) JGOriginalViewDidAppear(self, _cmd, animated);
    if (NSThread.isMainThread) {
        JGInstallEntryOnSettingsController(self);
    } else {
        dispatch_async(dispatch_get_main_queue(), ^{ JGInstallEntryOnSettingsController(self); });
    }
}

static void JGTryInstallAdapter(void) {
    @synchronized (NSObject.class) {
        if (JGAdapterInstalled) return;
        Class cls = objc_getClass("_TtC14PeerInfoScreen18PeerInfoScreenImpl");
        if (cls == Nil) return;
        Method method = class_getInstanceMethod(cls, sel_registerName("viewDidAppear:"));
        if (method == NULL) return;
        JGOriginalViewDidAppear = (void (*)(id, SEL, BOOL))method_getImplementation(method);
        method_setImplementation(method, (IMP)JGPeerInfoViewDidAppear);
        JGAdapterInstalled = YES;
    }
}

static void JGDyldImageAdded(const struct mach_header *header, intptr_t slide) {
    (void)header; (void)slide;
    dispatch_async(dispatch_get_main_queue(), ^{ JGTryInstallAdapter(); });
}

void JGInstallTelegram1294SettingsAdapter(void) {
    JGTryInstallAdapter();
    @synchronized (NSObject.class) {
        if (!JGAdapterInstalled && !JGDyldCallbackRegistered) {
            JGDyldCallbackRegistered = YES;
            _dyld_register_func_for_add_image(JGDyldImageAdded);
        }
    }
}
