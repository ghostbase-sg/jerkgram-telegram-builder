#import "JGTelegramSettingsAdapter.h"
#import "JGSettingsViewController.h"
#import "JGSettingsStore.h"
#import "JGStrings.h"
#import <UIKit/UIKit.h>
#import <objc/runtime.h>
#import <objc/message.h>
#import <mach-o/dyld.h>

// Implemented in JGRuntimeIntrospection.swift. This is the only bridge from ObjC into
// private Swift object structure: semantic Mirror lookup, never byte offsets.
@interface JGRuntimeIntrospection : NSObject
+ (NSNumber *)isSettingsFromObject:(id)object;
+ (nullable NSNumber *)accountPeerIdFromObject:(id)object;
+ (nullable NSString *)languageCodeFromObject:(id)object;
+ (NSArray<NSDictionary *> *)regularSectionNodesFromObject:(id)object;
@end

NSString * const JGInjectedSectionAccessibilityIdentifier = @"com.jerkgram.m1.main-settings-section";

static const CGFloat JGSectionSpacing = 24.0; // PeerInfoScreen.swift Build138 contract
static const CGFloat JGFallbackRowHeight = 52.0;
static const CGFloat JGSectionCornerRadius = 16.0;
static const char JGInjectedSectionKey;
static const char JGMainTargetKey;
static const char JGSettingsIdentityKey;
static const char JGSettingsContextKey;

static void (*JGOriginalViewDidAppear)(id, SEL, BOOL) = NULL;
static void (*JGOriginalViewDidLayoutSubviews)(id, SEL) = NULL;
static BOOL JGAdapterInstalled = NO;
static BOOL JGDyldCallbackRegistered = NO;

static NSDictionary *JGMainRoute(NSString *route, NSString *title, NSString *icon, uint32_t rgb) {
    return @{ @"route": route, @"title": title, @"icon": icon, @"rgb": @(rgb) };
}

static NSArray<NSDictionary *> *JGMainRoutes(void) {
    static NSArray<NSDictionary *> *routes;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        routes = @[
            JGMainRoute(@"home", @"main.jerkgram", @"Jerkgram/Settings/Airplane", 0x53606A),
            JGMainRoute(@"ghostMode", @"main.ghost", @"Chat/Context Menu/Eye", 0x4B5064),
            JGMainRoute(@"messages", @"main.messages", @"Chat/Context Menu/MessageBubble", 0x4B6F83),
            JGMainRoute(@"protectedContent", @"main.protected", @"Premium/CopyProtection/NoForward", 0x87452F),
            JGMainRoute(@"mediaStories", @"main.media", @"Item List/Icons/Stories", 0x6A5C78),
            JGMainRoute(@"appearance", @"main.appearance", @"Chat/Context Menu/ApplyTheme", 0x676C43),
            JGMainRoute(@"debugResearch", @"main.debug", @"Chat/Context Menu/FormatCode", 0x8A6138),
            JGMainRoute(@"about", @"main.about", @"Chat/Context Menu/Info", 0x4B4F54),
        ];
    });
    return routes;
}

static UIColor *JGColorFromRGB(uint32_t rgb) {
    return [UIColor colorWithRed:((rgb >> 16) & 0xff) / 255.0
                           green:((rgb >> 8) & 0xff) / 255.0
                            blue:(rgb & 0xff) / 255.0
                           alpha:1.0];
}

static UIView *JGNodeView(id node) {
    SEL selector = sel_registerName("view");
    if (node == nil || ![node respondsToSelector:selector]) return nil;
    id value = ((id (*)(id, SEL))objc_msgSend)(node, selector);
    return [value isKindOfClass:UIView.class] ? value : nil;
}

static UIScrollView *JGNearestScrollView(UIView *view) {
    UIView *cursor = view;
    while (cursor != nil) {
        if ([cursor isKindOfClass:UIScrollView.class]) return (UIScrollView *)cursor;
        cursor = cursor.superview;
    }
    return nil;
}

static UILabel *JGFirstLabel(UIView *view) {
    if ([view isKindOfClass:UILabel.class]) return (UILabel *)view;
    for (UIView *child in view.subviews) {
        UILabel *label = JGFirstLabel(child);
        if (label != nil && label.text.length != 0) return label;
    }
    return nil;
}

static UIColor *JGSampleSectionBackground(UIView *view) {
    UIColor *best = nil;
    CGFloat bestArea = 0.0;
    NSMutableArray<UIView *> *stack = [NSMutableArray arrayWithObject:view];
    while (stack.count != 0) {
        UIView *candidate = stack.lastObject;
        [stack removeLastObject];
        for (UIView *child in candidate.subviews) [stack addObject:child];
        UIColor *color = candidate.backgroundColor;
        CGFloat alpha = CGColorGetAlpha(color.CGColor ?: UIColor.clearColor.CGColor);
        CGFloat area = candidate.bounds.size.width * candidate.bounds.size.height;
        if (color != nil && alpha > 0.08 && area > bestArea) {
            best = color;
            bestArea = area;
        }
    }
    return best ?: UIColor.secondarySystemGroupedBackgroundColor;
}

static UIColor *JGSampleSeparatorColor(UIView *view) {
    NSMutableArray<UIView *> *stack = [NSMutableArray arrayWithObject:view];
    while (stack.count != 0) {
        UIView *candidate = stack.lastObject;
        [stack removeLastObject];
        for (UIView *child in candidate.subviews) [stack addObject:child];
        if (candidate.bounds.size.height > 0.0 && candidate.bounds.size.height <= 1.5 && candidate.bounds.size.width > 80.0 && candidate.backgroundColor != nil) {
            return candidate.backgroundColor;
        }
    }
    return UIColor.separatorColor;
}

static UIImage *JGAirplaneGlyph(void) {
    // Exact Build138 Jerkgram/Settings/Airplane vector rasterized at 29 pt and treated as a template.
    static UIImage *image;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        NSString *b64 = @"iVBORw0KGgoAAAANSUhEUgAAAB0AAAAdCAYAAABWk2cPAAAABmJLR0QA/wD/AP+gvaeTAAABzElEQVRIieXWz4tPYRTH8df4jowyJE02qFEWpPxIiawsLciCjZRfS0pRZGVBFjZGtlNjISN/gFgomyllYYENmYUfUSPJgmmGa/Hc23zH3Hu/z/N1x4JPnc1znnve9znPPedc/he1/hJnJY5iEh/nG7YLt/EdGV7NF2iRcKonOajdnjYNW4VLQvp+hxV2vSnYdtzEVA2ssH1/AurFQTyKABU2haXdwJbhLMYrAr/H+Qrf41TYWgzhS81JRrERLyr8l2NhO3EX0zWwzziE9TUZyLC7DtTCASEdne5pDKuxAxM1+74JpTRHS3ASLyNg00J5tLAXXzvsf1AGPIxPEbBMqMMiVUfElcqZMujrSOBDoY/COfyMfG5TGfRixBtfFdLZwo1IWIYPWFAGlZ/glLk9c1LopdAnlEYsMBO+/ihtxbAwIbbla/1CelOAGY7FQqEnNxgQJkQqMMNgChQWCvU11iVwPBVY6IqZRjCKNwnQrkbZcjzHnra1PuG+24NP4Bbum10F+1OBG4TfjOESXy+e5YHvmT2yNuMtfmBFKnQQ73C6wn9BGGX9Jb6iFydD69SDEVyr8K8x08Ea07oOQRfjDk40CYXj2NJ00H9LvwDXNyM/sKYsRgAAAABJRU5ErkJggg==";
        NSData *data = [[NSData alloc] initWithBase64EncodedString:b64 options:0];
        image = [[UIImage imageWithData:data scale:1.0] imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
    });
    return image;
}

static UIImage *JGSourceGlyph(NSString *route, NSString *iconName) {
    if ([route isEqualToString:@"home"]) return JGAirplaneGlyph();
    UIImage *image = [UIImage imageNamed:iconName];
    return [image imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
}

@interface JGMainSettingsTarget : NSObject
@property(nonatomic, weak) UIViewController *controller;
@property(nonatomic) int64_t accountPeerId;
- (void)openRoute:(UIControl *)sender;
@end

@implementation JGMainSettingsTarget
- (void)openRoute:(UIControl *)sender {
    NSString *route = sender.accessibilityIdentifier;
    if (route.length == 0 || self.accountPeerId == 0) return;
    UIViewController *next = JGCreateSettingsHost(self.accountPeerId, route);
    if (next == nil) return;
    UINavigationController *navigation = self.controller.navigationController;
    if (navigation != nil) [navigation pushViewController:next animated:YES];
}
@end

@interface JGMainSettingsRow : UIControl
@property(nonatomic, readonly) UIImageView *tile;
@property(nonatomic, readonly) UIImageView *glyph;
@property(nonatomic, readonly) UILabel *titleLabel;
@property(nonatomic, readonly) UIImageView *arrow;
@property(nonatomic, readonly) UIView *separator;
@end

@implementation JGMainSettingsRow
- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        _tile = [[UIImageView alloc] initWithFrame:CGRectZero];
        _tile.userInteractionEnabled = NO;
        _tile.layer.cornerRadius = 7.0;
        _tile.layer.cornerCurve = kCACornerCurveContinuous;
        _tile.clipsToBounds = YES;
        [self addSubview:_tile];

        _glyph = [[UIImageView alloc] initWithFrame:CGRectZero];
        _glyph.contentMode = UIViewContentModeScaleAspectFit;
        _glyph.tintColor = UIColor.whiteColor;
        [_tile addSubview:_glyph];

        _titleLabel = [[UILabel alloc] initWithFrame:CGRectZero];
        _titleLabel.adjustsFontForContentSizeCategory = YES;
        _titleLabel.numberOfLines = 1;
        [self addSubview:_titleLabel];

        UIImage *arrowImage = [[UIImage imageNamed:@"Item List/DisclosureArrow"] imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
        if (arrowImage == nil) arrowImage = [[UIImage systemImageNamed:@"chevron.right"] imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
        _arrow = [[UIImageView alloc] initWithImage:arrowImage];
        _arrow.contentMode = UIViewContentModeCenter;
        _arrow.userInteractionEnabled = NO;
        [self addSubview:_arrow];

        _separator = [UIView new];
        _separator.userInteractionEnabled = NO;
        [self addSubview:_separator];
    }
    return self;
}
- (void)setHighlighted:(BOOL)highlighted {
    [super setHighlighted:highlighted];
    self.backgroundColor = highlighted ? [UIColor.tertiarySystemFillColor colorWithAlphaComponent:0.75] : UIColor.clearColor;
}
@end

@interface JGMainSettingsSectionView : UIView
@property(nonatomic) NSArray<JGMainSettingsRow *> *rows;
@property(nonatomic) CGFloat rowHeight;
- (void)configureWithController:(UIViewController *)controller accountPeerId:(int64_t)peerId sampleView:(UIView *)sample;
@end

@implementation JGMainSettingsSectionView
- (instancetype)initWithFrame:(CGRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        _rowHeight = JGFallbackRowHeight;
        self.accessibilityIdentifier = JGInjectedSectionAccessibilityIdentifier;
        self.layer.cornerRadius = JGSectionCornerRadius;
        self.layer.cornerCurve = kCACornerCurveContinuous;
        self.clipsToBounds = YES;
        NSMutableArray *rows = [NSMutableArray array];
        for (NSInteger i = 0; i < 8; i++) {
            JGMainSettingsRow *row = [JGMainSettingsRow new];
            [self addSubview:row];
            [rows addObject:row];
        }
        self.rows = rows;
    }
    return self;
}
- (void)layoutSubviews {
    [super layoutSubviews];
    CGFloat scale = UIScreen.mainScreen.scale;
    CGFloat pixel = 1.0 / MAX(1.0, scale);
    for (NSInteger i = 0; i < self.rows.count; i++) {
        JGMainSettingsRow *row = self.rows[i];
        row.frame = CGRectMake(0.0, self.rowHeight * i, self.bounds.size.width, self.rowHeight);
        row.tile.frame = CGRectMake(16.0, floor((self.rowHeight - 29.0) * 0.5), 29.0, 29.0);
        row.glyph.frame = CGRectInset(row.tile.bounds, 5.0, 5.0);
        CGFloat arrowW = row.arrow.image.size.width ?: 7.0;
        CGFloat arrowH = row.arrow.image.size.height ?: 12.0;
        row.arrow.frame = CGRectMake(self.bounds.size.width - 7.0 - arrowW, floor((self.rowHeight - arrowH) * 0.5), arrowW, arrowH);
        row.titleLabel.frame = CGRectMake(61.0, 0.0, MAX(1.0, CGRectGetMinX(row.arrow.frame) - 69.0), self.rowHeight);
        row.separator.frame = CGRectMake(60.0, self.rowHeight - pixel, MAX(0.0, self.bounds.size.width - 60.0), pixel);
        row.separator.hidden = i == self.rows.count - 1;
    }
}
- (void)configureWithController:(UIViewController *)controller accountPeerId:(int64_t)peerId sampleView:(UIView *)sample {
    self.backgroundColor = JGSampleSectionBackground(sample);
    UILabel *sampleLabel = JGFirstLabel(sample);
    UIFont *font = sampleLabel.font ?: [UIFont preferredFontForTextStyle:UIFontTextStyleBody];
    UIColor *textColor = sampleLabel.textColor ?: UIColor.labelColor;
    UIColor *separatorColor = JGSampleSeparatorColor(sample);
    UIColor *arrowColor = UIColor.tertiaryLabelColor;

    NSArray<NSDictionary *> *spec = JGMainRoutes();

    JGMainSettingsTarget *target = objc_getAssociatedObject(controller, &JGMainTargetKey);
    if (target == nil) {
        target = [JGMainSettingsTarget new];
        target.controller = controller;
        objc_setAssociatedObject(controller, &JGMainTargetKey, target, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    target.accountPeerId = peerId;

    for (NSInteger i = 0; i < self.rows.count; i++) {
        NSDictionary *entry = spec[i];
        JGMainSettingsRow *row = self.rows[i];
        NSString *route = entry[@"route"];
        row.accessibilityIdentifier = route;
        row.titleLabel.text = JGString(entry[@"title"]);
        row.titleLabel.font = font;
        row.titleLabel.textColor = textColor;
        row.tile.backgroundColor = JGColorFromRGB([entry[@"rgb"] unsignedIntValue]);
        row.glyph.image = JGSourceGlyph(route, entry[@"icon"]);
        row.arrow.tintColor = arrowColor;
        row.separator.backgroundColor = separatorColor;
        [row removeTarget:nil action:NULL forControlEvents:UIControlEventTouchUpInside];
        [row addTarget:target action:@selector(openRoute:) forControlEvents:UIControlEventTouchUpInside];
        row.accessibilityLabel = row.titleLabel.text;
        row.accessibilityTraits = UIAccessibilityTraitButton;
    }
    [self setNeedsLayout];
}
@end

static void JGRemoveInjectedSection(UIViewController *controller, NSArray<NSDictionary *> *sections) {
    JGMainSettingsSectionView *injected = objc_getAssociatedObject(controller, &JGInjectedSectionKey);
    [injected removeFromSuperview];
    objc_setAssociatedObject(controller, &JGInjectedSectionKey, nil, OBJC_ASSOCIATION_ASSIGN);
}

static NSInteger JGSectionOrder(NSString *key) {
    static NSArray<NSString *> *order;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        order = @[@"edit", @"phone", @"accounts", @"myProfile", @"ghostbase", @"proxy", @"apps", @"shortcuts", @"advanced", @"payment", @"extra", @"support"];
    });
    NSUInteger index = [order indexOfObject:key];
    return index == NSNotFound ? NSIntegerMax : (NSInteger)index;
}

static NSArray<NSDictionary *> *JGOrderedNativeSections(NSArray<NSDictionary *> *sections, UIView *parent) {
    NSMutableArray<NSDictionary *> *valid = [NSMutableArray array];
    for (NSDictionary *entry in sections) {
        UIView *view = JGNodeView(entry[@"node"]);
        if (view != nil && view.superview == parent && JGSectionOrder(entry[@"key"]) != NSIntegerMax) {
            [valid addObject:entry];
        }
    }
    [valid sortUsingComparator:^NSComparisonResult(NSDictionary *lhs, NSDictionary *rhs) {
        NSInteger a = JGSectionOrder(lhs[@"key"]), b = JGSectionOrder(rhs[@"key"]);
        if (a < b) return NSOrderedAscending;
        if (a > b) return NSOrderedDescending;
        return NSOrderedSame;
    }];
    return valid;
}

// Telegram remains the source of truth for section membership, width, height and the
// first section origin. We deterministically derive every y-position from that current
// native snapshot, so repeated callbacks cannot accumulate a previous translation.
static void JGApplyFromCurrentNativeGeometry(UIViewController *controller,
                                             NSArray<NSDictionary *> *sections,
                                             JGMainSettingsSectionView *injected,
                                             UIView *myProfileView,
                                             UIView *proxyView,
                                             UIScrollView *scrollView) {
    UIView *parent = myProfileView.superview;
    NSArray<NSDictionary *> *ordered = JGOrderedNativeSections(sections, parent);
    if (ordered.count == 0) return;
    UIView *first = JGNodeView(ordered.firstObject[@"node"]);
    CGFloat cursor = CGRectGetMinY(first.frame);
    CGFloat width = CGRectGetWidth(myProfileView.frame);
    CGFloat x = CGRectGetMinX(myProfileView.frame);
    CGFloat nativeRowHeight = CGRectGetHeight(myProfileView.bounds);
    injected.rowHeight = nativeRowHeight > 1.0 ? nativeRowHeight : JGFallbackRowHeight;
    CGFloat injectedHeight = injected.rowHeight * JGMainRoutes().count;
    BOOL inserted = NO;

    for (NSDictionary *entry in ordered) {
        UIView *view = JGNodeView(entry[@"node"]);
        CGRect frame = view.frame;
        frame.origin.y = cursor;
        view.frame = frame;
        cursor = CGRectGetMaxY(frame) + JGSectionSpacing;
        if ([entry[@"key"] isEqual:@"myProfile"]) {
            injected.frame = CGRectMake(x, cursor, width, injectedHeight);
            cursor = CGRectGetMaxY(injected.frame) + JGSectionSpacing;
            inserted = YES;
        }
    }
    if (!inserted) return;

    // Explicit structural assertion for the required after-My-Profile/before-Proxy order.
    if (proxyView != nil && CGRectGetMinY(proxyView.frame) < CGRectGetMaxY(injected.frame)) {
        CGRect proxyFrame = proxyView.frame;
        proxyFrame.origin.y = CGRectGetMaxY(injected.frame) + JGSectionSpacing;
        proxyView.frame = proxyFrame;
    }

    CGFloat contentHeight = cursor - JGSectionSpacing + 6.0;
    CGFloat minimumHeight = scrollView.bounds.size.height + 140.0 - scrollView.adjustedContentInset.bottom;
    scrollView.contentSize = CGSizeMake(scrollView.bounds.size.width, MAX(contentHeight, minimumHeight));
    [parent bringSubviewToFront:injected];
}

static void JGApplyParitySettingsSection(UIViewController *controller) {
    NSNumber *isSettings = objc_getAssociatedObject(controller, &JGSettingsIdentityKey);
    if (isSettings == nil) {
        isSettings = [JGRuntimeIntrospection isSettingsFromObject:controller];
        objc_setAssociatedObject(controller, &JGSettingsIdentityKey, isSettings, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    if (!isSettings.boolValue) return;

    NSDictionary *context = objc_getAssociatedObject(controller, &JGSettingsContextKey);
    NSArray<NSDictionary *> *sections = context[@"sections"];
    NSNumber *account = context[@"account"];
    if (sections == nil || account == nil) {
        sections = [JGRuntimeIntrospection regularSectionNodesFromObject:controller];
        account = [JGRuntimeIntrospection accountPeerIdFromObject:controller];
        NSString *languageCode = [JGRuntimeIntrospection languageCodeFromObject:controller] ?: @"en";
        if (sections.count != 0 && account.longLongValue != 0) {
            context = @{ @"sections": sections, @"account": account, @"language": languageCode };
            objc_setAssociatedObject(controller, &JGSettingsContextKey, context, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
        }
    }
    if (sections.count == 0) return;

    UIView *anySectionView = nil;
    for (NSDictionary *entry in sections) {
        UIView *candidate = JGNodeView(entry[@"node"]);
        if (candidate != nil) { anySectionView = candidate; break; }
    }
    UIScrollView *scrollView = JGNearestScrollView(anySectionView);

    if (account == nil || account.longLongValue == 0) {
        [[JGSettingsStore sharedStore] deactivateAccount];
        JGRemoveInjectedSection(controller, sections);
        return;
    }

    UIView *myProfileView = nil;
    UIView *proxyView = nil;
    for (NSDictionary *entry in sections) {
        if ([entry[@"key"] isEqual:@"myProfile"]) {
            myProfileView = JGNodeView(entry[@"node"]);
        } else if ([entry[@"key"] isEqual:@"proxy"]) {
            proxyView = JGNodeView(entry[@"node"]);
        }
    }
    if (myProfileView == nil || myProfileView.superview == nil || scrollView == nil) {
        [[JGSettingsStore sharedStore] deactivateAccount];
        JGRemoveInjectedSection(controller, sections);
        objc_setAssociatedObject(controller, &JGSettingsContextKey, nil, OBJC_ASSOCIATION_ASSIGN);
        return;
    }

    [[JGSettingsStore sharedStore] activateAccountPeerId:account.longLongValue];
    NSString *languageCode = context[@"language"] ?: @"en";
    JGSetLanguageOverride(languageCode);

    UIView *parent = myProfileView.superview;

    JGMainSettingsSectionView *injected = objc_getAssociatedObject(controller, &JGInjectedSectionKey);
    if (injected == nil) {
        injected = [JGMainSettingsSectionView new];
        objc_setAssociatedObject(controller, &JGInjectedSectionKey, injected, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    if (injected.superview != parent) {
        [injected removeFromSuperview];
        [parent addSubview:injected];
    }
    [injected configureWithController:controller accountPeerId:account.longLongValue sampleView:myProfileView];
    JGApplyFromCurrentNativeGeometry(controller, sections, injected, myProfileView, proxyView, scrollView);
}

static void JGPeerInfoViewDidAppear(id self, SEL _cmd, BOOL animated) {
    if (JGOriginalViewDidAppear != NULL) JGOriginalViewDidAppear(self, _cmd, animated);
    UIViewController *controller = [self isKindOfClass:UIViewController.class] ? (UIViewController *)self : nil;
    if (controller == nil) return;
    [controller.view setNeedsLayout];
    dispatch_async(dispatch_get_main_queue(), ^{ [controller.view setNeedsLayout]; });
}

static void JGPeerInfoViewDidLayoutSubviews(id self, SEL _cmd) {
    if (JGOriginalViewDidLayoutSubviews != NULL) JGOriginalViewDidLayoutSubviews(self, _cmd);
    if (![self isKindOfClass:UIViewController.class]) return;
    JGApplyParitySettingsSection((UIViewController *)self);
}

static void JGTryInstallAdapter(void) {
    @synchronized (NSObject.class) {
        if (JGAdapterInstalled) return;
        Class cls = objc_getClass("_TtC14PeerInfoScreen18PeerInfoScreenImpl");
        if (cls == Nil) return;

        SEL layoutSEL = sel_registerName("viewDidLayoutSubviews");
        Method inheritedLayout = class_getInstanceMethod(cls, layoutSEL);
        if (inheritedLayout == NULL) return;
        JGOriginalViewDidLayoutSubviews = (void (*)(id, SEL))method_getImplementation(inheritedLayout);
        if (!class_addMethod(cls, layoutSEL, (IMP)JGPeerInfoViewDidLayoutSubviews, "v@:")) {
            JGOriginalViewDidLayoutSubviews = NULL;
            return;
        }

        SEL appearSEL = sel_registerName("viewDidAppear:");
        Method appear = class_getInstanceMethod(cls, appearSEL);
        if (appear == NULL) {
            class_replaceMethod(cls, layoutSEL, (IMP)JGOriginalViewDidLayoutSubviews, method_getTypeEncoding(inheritedLayout));
            JGOriginalViewDidLayoutSubviews = NULL;
            return;
        }
        JGOriginalViewDidAppear = (void (*)(id, SEL, BOOL))method_getImplementation(appear);
        // class_addMethod is safe for inherited methods; it creates a class-local hook. If Telegram
        // owns a local method, replacing this exact Method cannot mutate Display.ViewController.
        if (!class_addMethod(cls, appearSEL, (IMP)JGPeerInfoViewDidAppear, method_getTypeEncoding(appear))) {
            method_setImplementation(appear, (IMP)JGPeerInfoViewDidAppear);
        }
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
