#import "JGTelegramSettingsAdapter.h"
#import "JGSettingsViewController.h"
#import "JGSettingsStore.h"
#import "JGStrings.h"
#import <UIKit/UIKit.h>
#import <objc/runtime.h>
#import <objc/message.h>
#import <mach-o/dyld.h>
#import <QuartzCore/QuartzCore.h>

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
static const char JGTelegramBaselineKey;
static const char JGObservedControllerKey;
static const char JGObservedSubclassKey;
static const char JGOwnContentSizeMutationKey;

static void (*JGOriginalViewDidAppear)(id, SEL, BOOL) = NULL;
static void (*JGOriginalViewDidLayoutSubviews)(id, SEL) = NULL;
static BOOL JGAdapterInstalled = NO;
static BOOL JGDyldCallbackRegistered = NO;

@interface JGWeakControllerBox : NSObject
@property(nonatomic, weak) UIViewController *controller;
@end
@implementation JGWeakControllerBox
@end

static void JGCaptureTelegramBaseline(UIViewController *controller);
static void JGApplyParitySettingsSection(UIViewController *controller);
static void JGTraceLayoutState(UIViewController *controller, NSString *callback, NSValue * _Nullable requestedContentSize);
static void JGInstallScrollCompletionObserver(UIScrollView *scrollView, UIViewController *controller);

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
    // Exact Build138 Jerkgram/Settings/Airplane SVG rasterized at 3x with its native 24 pt canvas.
    static UIImage *image;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        NSString *b64 = @"iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAYAAABV7bNHAAAACXBIWXMAACxKAAAsSgF3enRNAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAABg1JREFUeJztm2+IFVUUwH9nt023dXVTywjLtkyNjdJCKgw1yRI0IStZSC3xg2FaVlaiaBl+ighE7A9IhIRUqBRpUZhuaOQfqi9aav9sMdNKS2zd1V339OHOy9lx3ps3M3fmjfoOXHhzZ+655/7enXPO3LkjqkpZ8ktFqQ3IupQBBUgZUICUAQVIGVCAXPCAROQ2EVkpIptEZKGI9Oxy/kIM8yLSDXgIeAIY7jm9GbhHVTvgAgMkIoOAWcBUoHeBS+9S1SaAi1Kwq6QiIpXAeGAmMI7i3EqP3I/zFpCI9ACmAM8AA0M2P/y/nvPtFhOR/sAi4BGgWwQVbcClqtoG58kMEpEKYBQwF7gPkBjqtufgwDkOSEQuBh4FFgADLKnd6j44JwGJyGBMiJ4K1FpWv7FLX+eSDxKRYcCLxL+N8slR4DJV7cxVZH4GOZntZExEGkkyYHKyzQ0HMgxIROowkWgxhZM6m7LJW5E5QCJyEybbnQLUpNz9hrNqVLXkBZPdTsJEEC1ROehnW0mf5kWkh4g8DuwB1gIjYqj7FTPzokadL3xrSzRjrgZeBf4h/j/fAbyMeX6qB05H1DPH19aUwQwD3gZOWQCjwH5ghKN7CPBjDF1DSgIIqAQeAL62BEWBTuB1oKfTx1Dgrxj69uW1P0EwtcBTwE8WwShwALjbMyvjwFFgdWqAMH5giQWj/cp7QJ2rr0nAcQt6H0wcEHAL8A7GadoGcwyz4CWu/uZgbrW4ujvc0K0CwiSa9wNNCUDJlc3ANa4+BZNd24CjwI6CY4wIphfGv+xPEEwn5lat8PwhKy3384o1QEBf4AXgzwTBKPAbMM7Td3fgowT6mhgbEGZNdxnwb8JgFPgQj08A6oDPEujrlLevUICAMY7BUbPTMOUkMA+XI3ZsuB7Ym1CfnwdODh8oVcAMYGcKUHJlD3Czjy03AocS7Hd+KEDAYODbFMEosBqo9YFzB3Ak4b6vKxoQ5hWJ7ay3UGkBnsxza08keX93FM/tHARoVIpwfgAa8sCZSTo+7/1iApR7PaiadGQdMFxVd3tPiMgM4DXS2XWyMfgSusygyzGRJKl/rAOYm2fWVGLSiLRmsAIDi0pxPIa+lJAxf+BJ/Fx91gDrU4aTd3mjmDA/GngXaLVkzF5gUB44vYFtKcNRYFlkQC7jazFvFj4F2iMasgHolUd/H9JPKXJlWmxAnsH0BZ7GLIwXa8QbQGUefQ3EWx6NW+qtAvI401uBNzHbRPw6bwWmF9AxEjuL9VHLl6HGHOZiz0D7A885M6ET+B2zIJ83OgBjMQliqeAosCQVQB5fUlPEdY0FZl2a5d5UATmDr6JA2o7ZkWFrBTBOOYnPc1/igBwIvoCApRkAkytbwo7LWkqvqioiVe46EZkNLLTVhwVpCtvA9jNPn9wPERmNeb2cJTlre0uQWN1hJiI1qtoiIv2AXZj8KSvyN9BPVdvDNLI9g9pEpDfmzUOW4ACsCQsHLG+gUtXTItIITPCcWo+Z3lswaz2jMMup0zARMA1pitTKVhRzbtUaTJadixq7gLEFrm/ArMskHb06gSsijckyoO6c2SW2FrikmPQAWBFisB3AdmAV8AHGtwS1+TnymCyBuRJ4FnMbtTvTuVuI9pXAxwGDPA48j9mm621/J/BVgbarSgYIs7PrF49BYyJCPpZngLsJeAOBCTiz8d+c9XApATX6GLQ0oq4lPrq+w4TnYnVM4uwdJpH8j6qdTPqET11HRF1veY5bgPGqetjvYj9R1XXAfFdVs6oeimiPlRnUHfieM//WEeDaGPqaXboWRNQhGH+owM5Y44sLyDGoF+ZTpMXAVTF1bXWBLtrR++h5zAW6GZhcMkC2CiZpzEWj5TF1raGrHzoBVIXVk5nPwkVkKOaN6+1OlZ9vCyMNnuNqTKQMJZkBhPm2dIDreJ6I1MfQt8NzfAA4GFZJlgD19BxX+NSFkVnAJ87vb4AJGuFhNTMf1DmLa8tdVfuAG9Tz/VYEvdWq2hq1fZY+h1qBeUyZjvFFi+LCAYgDBzI0g7IqWfJBmZQyoAApAwqQMqAAKQMKkP8AxafSqEhG9c8AAAAASUVORK5CYII=";
        NSData *data = [[NSData alloc] initWithBase64EncodedString:b64 options:0];
        image = [[UIImage imageWithData:data scale:3.0] imageWithRenderingMode:UIImageRenderingModeAlwaysOriginal];
    });
    return image;
}

static UIImage *JGSourceGlyph(NSString *route, NSString *iconName) {
    if ([route isEqualToString:@"home"]) return JGAirplaneGlyph();
    UIImage *image = [UIImage imageNamed:iconName];
    return [image imageWithRenderingMode:UIImageRenderingModeAlwaysOriginal];
}

// Exact Telegram/Build138 renderSettingsIcon contract: a 30 pt tile, radius 8,
// native glyph optical size, plus the stock Gradient and Backdrop compositing layers.
static UIImage *JGRenderBuild138SettingsIcon(NSString *route, NSString *iconName, uint32_t rgb) {
    CGSize size = CGSizeMake(30.0, 30.0);
    UIGraphicsBeginImageContextWithOptions(size, NO, 0.0);
    CGContextRef context = UIGraphicsGetCurrentContext();
    CGRect bounds = (CGRect){CGPointZero, size};
    UIBezierPath *rounded = [UIBezierPath bezierPathWithRoundedRect:bounds cornerRadius:8.0];
    [rounded addClip];
    [JGColorFromRGB(rgb) setFill];
    UIRectFill(bounds);

    UIImage *gradient = [UIImage imageNamed:@"Item List/Icons/Gradient"];
    [gradient drawInRect:bounds blendMode:kCGBlendModePlusLighter alpha:1.0];
    UIImage *backdrop = [UIImage imageNamed:@"Item List/Icons/Backdrop"];
    [backdrop drawInRect:bounds blendMode:kCGBlendModeOverlay alpha:1.0];

    UIImage *glyph = JGSourceGlyph(route, iconName);
    CGImageRef mask = glyph.CGImage;
    if (mask != NULL) {
        CGSize glyphSize = glyph.size;
        CGRect glyphRect = CGRectMake(floor((size.width - glyphSize.width) * 0.5),
                                      floor((size.height - glyphSize.height) * 0.5),
                                      glyphSize.width, glyphSize.height);
        CGContextSaveGState(context);
        CGContextTranslateCTM(context, 0.0, size.height);
        CGContextScaleCTM(context, 1.0, -1.0);
        CGRect flippedRect = CGRectMake(glyphRect.origin.x,
                                        size.height - CGRectGetMaxY(glyphRect),
                                        glyphRect.size.width, glyphRect.size.height);
        CGContextClipToMask(context, flippedRect, mask);
        CGContextSetFillColorWithColor(context, UIColor.whiteColor.CGColor);
        CGContextFillRect(context, flippedRect);
        CGContextRestoreGState(context);
    }
    UIImage *result = UIGraphicsGetImageFromCurrentImageContext();
    UIGraphicsEndImageContext();
    return result;
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
        _tile.contentMode = UIViewContentModeCenter;
        [self addSubview:_tile];

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
        row.tile.frame = CGRectMake(16.0, floor((self.rowHeight - 30.0) * 0.5), 30.0, 30.0);
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
        row.tile.image = JGRenderBuild138SettingsIcon(route, entry[@"icon"], [entry[@"rgb"] unsignedIntValue]);
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
    objc_setAssociatedObject(controller, &JGTelegramBaselineKey, nil, OBJC_ASSOCIATION_ASSIGN);
}

static NSArray<NSDictionary *> *JGNativeSectionViews(NSArray<NSDictionary *> *sections, UIView *parent) {
    NSMutableArray<NSDictionary *> *valid = [NSMutableArray array];
    for (NSDictionary *entry in sections) {
        UIView *view = JGNodeView(entry[@"node"]);
        if (view != nil && view.superview == parent) {
            [valid addObject:@{ @"key": entry[@"key"] ?: @"unknown", @"view": view }];
        }
    }
    [valid sortUsingComparator:^NSComparisonResult(NSDictionary *lhs, NSDictionary *rhs) {
        CGFloat a = CGRectGetMinY([lhs[@"view"] frame]);
        CGFloat b = CGRectGetMinY([rhs[@"view"] frame]);
        if (a < b) return NSOrderedAscending;
        if (a > b) return NSOrderedDescending;
        return NSOrderedSame;
    }];
    return valid;
}

static NSDictionary *JGResolveSettingsContext(UIViewController *controller) {
    NSNumber *isSettings = objc_getAssociatedObject(controller, &JGSettingsIdentityKey);
    if (isSettings == nil) {
        isSettings = [JGRuntimeIntrospection isSettingsFromObject:controller];
        objc_setAssociatedObject(controller, &JGSettingsIdentityKey, isSettings, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    if (!isSettings.boolValue) return nil;

    NSDictionary *context = objc_getAssociatedObject(controller, &JGSettingsContextKey);
    NSArray<NSDictionary *> *sections = context[@"sections"];
    BOOL cachedNodesAreLive = NO;
    for (NSDictionary *entry in sections) {
        UIView *view = JGNodeView(entry[@"node"]);
        if ([entry[@"key"] isEqual:@"myProfile"] && view.superview != nil) {
            cachedNodesAreLive = YES;
            break;
        }
    }
    if (context != nil && cachedNodesAreLive) return context;

    sections = [JGRuntimeIntrospection regularSectionNodesFromObject:controller];
    NSNumber *account = [JGRuntimeIntrospection accountPeerIdFromObject:controller];
    NSString *languageCode = [JGRuntimeIntrospection languageCodeFromObject:controller] ?: @"en";
    if (sections.count == 0 || account.longLongValue == 0) return nil;
    context = @{ @"sections": sections, @"account": account, @"language": languageCode };
    objc_setAssociatedObject(controller, &JGSettingsContextKey, context, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    return context;
}

static NSURL *JGLayoutTraceURL(void) {
    NSURL *caches = [NSFileManager.defaultManager URLsForDirectory:NSCachesDirectory inDomains:NSUserDomainMask].firstObject;
    NSURL *directory = [caches URLByAppendingPathComponent:@"Jerkgram" isDirectory:YES];
    [NSFileManager.defaultManager createDirectoryAtURL:directory withIntermediateDirectories:YES attributes:nil error:nil];
    return [directory URLByAppendingPathComponent:@"M1LayoutTrace.jsonl"];
}

static dispatch_queue_t JGLayoutTraceQueue(void) {
    static dispatch_queue_t queue;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        queue = dispatch_queue_create("com.jerkgram.m1.layout-trace", DISPATCH_QUEUE_SERIAL);
    });
    return queue;
}

static NSString *JGPointerString(id object) {
    return object == nil ? @"nil" : [NSString stringWithFormat:@"%p", object];
}

static void JGTraceLayoutState(UIViewController *controller, NSString *callback, NSValue *requestedContentSize) {
    if (controller == nil) return;
    NSDictionary *context = JGResolveSettingsContext(controller);
    NSArray<NSDictionary *> *sections = context[@"sections"] ?: @[];
    UIView *myProfileView = nil;
    for (NSDictionary *entry in sections) {
        if ([entry[@"key"] isEqual:@"myProfile"]) {
            myProfileView = JGNodeView(entry[@"node"]);
            break;
        }
    }
    UIView *parent = myProfileView.superview;
    NSArray<NSDictionary *> *ordered = parent == nil ? @[] : JGNativeSectionViews(sections, parent);
    NSMutableArray *native = [NSMutableArray arrayWithCapacity:ordered.count];
    NSInteger myProfileIndex = NSNotFound;
    NSDictionary *wallet = nil;
    for (NSInteger index = 0; index < ordered.count; index++) {
        NSDictionary *entry = ordered[index];
        UIView *view = entry[@"view"];
        NSString *key = entry[@"key"] ?: @"unknown";
        NSDictionary *item = @{
            @"key": key,
            @"identity": JGPointerString(view),
            @"frame": NSStringFromCGRect(view.frame)
        };
        [native addObject:item];
        if ([key isEqual:@"myProfile"]) myProfileIndex = index;
        if ([key isEqual:@"payment"]) wallet = item;
    }
    UIScrollView *scrollView = JGNearestScrollView(myProfileView);
    NSDictionary *baseline = objc_getAssociatedObject(controller, &JGTelegramBaselineKey);
    JGMainSettingsSectionView *injected = objc_getAssociatedObject(controller, &JGInjectedSectionKey);
    CGSize baselineSize = [baseline[@"contentSize"] CGSizeValue];
    NSMutableDictionary *record = [@{
        @"timestamp": @(CACurrentMediaTime()),
        @"callback": callback ?: @"unknown",
        @"controller": [NSString stringWithFormat:@"%@:%@", NSStringFromClass(controller.class), JGPointerString(controller)],
        @"jerkgramExists": @(injected.superview != nil),
        @"nativeSectionCount": @(native.count),
        @"nativeSections": native,
        @"myProfileIndex": myProfileIndex == NSNotFound ? @(-1) : @(myProfileIndex),
        @"wallet": wallet ?: (id)NSNull.null,
        @"telegramBaselineContentSize": NSStringFromCGSize(baselineSize),
        @"jerkgramFrame": injected == nil ? @"nil" : NSStringFromCGRect(injected.frame),
        @"finalContentSize": scrollView == nil ? @"nil" : NSStringFromCGSize(scrollView.contentSize)
    } mutableCopy];
    if (requestedContentSize != nil) record[@"requestedContentSize"] = NSStringFromCGSize(requestedContentSize.CGSizeValue);

    NSData *json = [NSJSONSerialization dataWithJSONObject:record options:NSJSONWritingSortedKeys error:nil];
    if (json == nil) return;
    NSMutableData *line = [json mutableCopy];
    [line appendBytes:"\n" length:1];
    dispatch_async(JGLayoutTraceQueue(), ^{
        NSURL *url = JGLayoutTraceURL();
        NSDictionary *attributes = [NSFileManager.defaultManager attributesOfItemAtPath:url.path error:nil];
        if ([attributes fileSize] > 2 * 1024 * 1024) [NSData.data writeToURL:url atomically:YES];
        NSFileHandle *handle = [NSFileHandle fileHandleForWritingAtPath:url.path];
        if (handle == nil) {
            [line writeToURL:url atomically:YES];
        } else {
            [handle seekToEndOfFile];
            [handle writeData:line];
            [handle closeFile];
        }
    });
}

NSString *JGCopyM1LayoutTrace(void) {
    __block NSData *data = nil;
    dispatch_sync(JGLayoutTraceQueue(), ^{ data = [NSData dataWithContentsOfURL:JGLayoutTraceURL()]; });
    return data == nil ? @"" : [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding] ?: @"";
}

static void JGSetContentSizeFromAdapter(UIScrollView *scrollView, CGSize size) {
    if (scrollView == nil) return;
    objc_setAssociatedObject(scrollView, &JGOwnContentSizeMutationKey, @YES, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    scrollView.contentSize = size;
    objc_setAssociatedObject(scrollView, &JGOwnContentSizeMutationKey, nil, OBJC_ASSOCIATION_ASSIGN);
}

// Restore the exact frames captured after Telegram's preceding native layout. This runs
// before Telegram's next layout callback, so Telegram never receives our translated frames.
static void JGRestoreTelegramBaseline(UIViewController *controller) {
    NSDictionary *baseline = objc_getAssociatedObject(controller, &JGTelegramBaselineKey);
    for (NSDictionary *entry in baseline[@"sections"]) {
        UIView *view = entry[@"view"];
        UIView *parent = entry[@"parent"];
        if (view.superview == parent) view.frame = [entry[@"frame"] CGRectValue];
    }
    UIScrollView *scrollView = baseline[@"scrollView"];
    if (scrollView != nil) JGSetContentSizeFromAdapter(scrollView, [baseline[@"contentSize"] CGSizeValue]);
    JGMainSettingsSectionView *injected = objc_getAssociatedObject(controller, &JGInjectedSectionKey);
    injected.hidden = YES;
}

// Capture only complete Telegram-owned section container views, in Telegram's current
// visual order. No child row is ever included or moved independently.
static void JGCaptureTelegramBaseline(UIViewController *controller) {
    NSDictionary *context = JGResolveSettingsContext(controller);
    NSArray<NSDictionary *> *sections = context[@"sections"];
    UIView *myProfileView = nil;
    for (NSDictionary *entry in sections) {
        if ([entry[@"key"] isEqual:@"myProfile"]) {
            myProfileView = JGNodeView(entry[@"node"]);
            break;
        }
    }
    UIView *parent = myProfileView.superview;
    UIScrollView *scrollView = JGNearestScrollView(myProfileView);
    if (parent == nil || scrollView == nil) return;

    JGInstallScrollCompletionObserver(scrollView, controller);

    NSArray<NSDictionary *> *ordered = JGNativeSectionViews(sections, parent);
    NSMutableArray<NSDictionary *> *snapshot = [NSMutableArray arrayWithCapacity:ordered.count];
    for (NSDictionary *entry in ordered) {
        UIView *view = entry[@"view"];
        [snapshot addObject:@{
            @"key": entry[@"key"], @"view": view, @"parent": parent,
            @"frame": [NSValue valueWithCGRect:view.frame]
        }];
    }
    NSDictionary *baseline = @{
        @"sections": snapshot,
        @"scrollView": scrollView,
        @"contentSize": [NSValue valueWithCGSize:scrollView.contentSize]
    };
    objc_setAssociatedObject(controller, &JGTelegramBaselineKey, baseline, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
}

static void JGApplyParitySettingsSection(UIViewController *controller) {
    NSDictionary *context = JGResolveSettingsContext(controller);
    NSArray<NSDictionary *> *sections = context[@"sections"];
    NSNumber *account = context[@"account"];
    NSDictionary *baseline = objc_getAssociatedObject(controller, &JGTelegramBaselineKey);
    if (context == nil || sections.count == 0 || baseline == nil || account.longLongValue == 0) {
        [[JGSettingsStore sharedStore] deactivateAccount];
        JGRemoveInjectedSection(controller, sections);
        return;
    }

    UIView *myProfileView = nil;
    for (NSDictionary *entry in sections) {
        if ([entry[@"key"] isEqual:@"myProfile"]) {
            myProfileView = JGNodeView(entry[@"node"]);
        }
    }
    UIScrollView *scrollView = baseline[@"scrollView"];
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

    NSArray<NSDictionary *> *nativeSections = baseline[@"sections"];
    NSInteger myProfileIndex = NSNotFound;
    CGRect myProfileFrame = CGRectZero;
    for (NSInteger index = 0; index < nativeSections.count; index++) {
        NSDictionary *entry = nativeSections[index];
        if ([entry[@"key"] isEqual:@"myProfile"] && entry[@"view"] == myProfileView) {
            myProfileIndex = index;
            myProfileFrame = [entry[@"frame"] CGRectValue];
            break;
        }
    }
    if (myProfileIndex == NSNotFound) return;

    CGFloat nativeRowHeight = CGRectGetHeight(myProfileFrame);
    injected.rowHeight = nativeRowHeight > 1.0 ? nativeRowHeight : JGFallbackRowHeight;
    CGFloat injectedHeight = injected.rowHeight * JGMainRoutes().count;
    CGFloat insertionDelta = JGSectionSpacing + injectedHeight;
    injected.frame = CGRectMake(CGRectGetMinX(myProfileFrame),
                                CGRectGetMaxY(myProfileFrame) + JGSectionSpacing,
                                CGRectGetWidth(myProfileFrame), injectedHeight);
    injected.hidden = NO;

    CGRect firstFollowingFrame = CGRectNull;
    for (NSInteger index = 0; index < nativeSections.count; index++) {
        NSDictionary *entry = nativeSections[index];
        UIView *view = entry[@"view"];
        CGRect frame = [entry[@"frame"] CGRectValue];
        if (index > myProfileIndex) {
            frame.origin.y += insertionDelta;
            if (CGRectIsNull(firstFollowingFrame) && CGRectGetHeight(frame) > 1.0) {
                firstFollowingFrame = frame;
            }
        }
        view.frame = frame;
    }

    CGSize baselineContentSize = [baseline[@"contentSize"] CGSizeValue];
    JGSetContentSizeFromAdapter(scrollView, CGSizeMake(baselineContentSize.width,
                                                       baselineContentSize.height + insertionDelta));
    BOOL bounded = CGRectIsNull(firstFollowingFrame) ||
        CGRectGetMaxY(injected.frame) <= CGRectGetMinY(firstFollowingFrame);
    if (!bounded) {
        JGRestoreTelegramBaseline(controller);
        return;
    }
    [parent bringSubviewToFront:injected];
}

static void JGCallOriginalSetContentSize(UIScrollView *scrollView, SEL selector, CGSize size) {
    struct objc_super superInfo = {
        .receiver = scrollView,
        .super_class = class_getSuperclass(object_getClass(scrollView))
    };
    ((void (*)(struct objc_super *, SEL, CGSize))objc_msgSendSuper)(&superInfo, selector, size);
}

static void JGObservedScrollSetContentSize(UIScrollView *scrollView, SEL selector, CGSize size) {
    if ([objc_getAssociatedObject(scrollView, &JGOwnContentSizeMutationKey) boolValue]) {
        JGCallOriginalSetContentSize(scrollView, selector, size);
        return;
    }
    JGWeakControllerBox *box = objc_getAssociatedObject(scrollView, &JGObservedControllerKey);
    UIViewController *controller = box.controller;
    if (controller == nil) {
        JGCallOriginalSetContentSize(scrollView, selector, size);
        return;
    }

    // Build138's PeerInfoScreenNode writes contentSize only after updating every
    // regular section frame.  Treat this instance-local UIKit setter as the native
    // layout completion marker; no Swift value or private object layout crosses it.
    objc_setAssociatedObject(controller, &JGSettingsContextKey, nil, OBJC_ASSOCIATION_ASSIGN);
    JGTraceLayoutState(controller, @"scroll.setContentSize.beforeOriginal", [NSValue valueWithCGSize:size]);
    JGCallOriginalSetContentSize(scrollView, selector, size);
    JGTraceLayoutState(controller, @"scroll.setContentSize.afterOriginal", [NSValue valueWithCGSize:size]);
    JGCaptureTelegramBaseline(controller);
    JGApplyParitySettingsSection(controller);
    JGTraceLayoutState(controller, @"scroll.setContentSize.afterApply", [NSValue valueWithCGSize:size]);
}

static void JGInstallScrollCompletionObserver(UIScrollView *scrollView, UIViewController *controller) {
    if (scrollView == nil || controller == nil) return;
    JGWeakControllerBox *box = objc_getAssociatedObject(scrollView, &JGObservedControllerKey);
    if (box == nil) {
        box = [JGWeakControllerBox new];
        objc_setAssociatedObject(scrollView, &JGObservedControllerKey, box, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    }
    box.controller = controller;

    Class currentClass = object_getClass(scrollView);
    if ([NSStringFromClass(currentClass) hasPrefix:@"JGObservedSettingsScroll_"]) return;
    @synchronized (currentClass) {
        Class subclass = objc_getAssociatedObject(currentClass, &JGObservedSubclassKey);
        if (subclass == Nil) {
            NSString *name = [NSString stringWithFormat:@"JGObservedSettingsScroll_%p", currentClass];
            subclass = objc_allocateClassPair(currentClass, name.UTF8String, 0);
            Method setter = class_getInstanceMethod(currentClass, @selector(setContentSize:));
            if (subclass == Nil || setter == NULL ||
                !class_addMethod(subclass, @selector(setContentSize:), (IMP)JGObservedScrollSetContentSize, method_getTypeEncoding(setter))) {
                if (subclass != Nil) objc_disposeClassPair(subclass);
                return;
            }
            objc_registerClassPair(subclass);
            objc_setAssociatedObject(currentClass, &JGObservedSubclassKey, subclass, OBJC_ASSOCIATION_ASSIGN);
        }
        object_setClass(scrollView, subclass);
    }
}

static void JGPeerInfoViewDidAppear(id self, SEL _cmd, BOOL animated) {
    if (JGOriginalViewDidAppear != NULL) JGOriginalViewDidAppear(self, _cmd, animated);
    UIViewController *controller = [self isKindOfClass:UIViewController.class] ? (UIViewController *)self : nil;
    if (controller == nil) return;
    JGTraceLayoutState(controller, @"viewDidAppear.afterOriginal", nil);
    [controller.view setNeedsLayout];
}

static void JGPeerInfoViewDidLayoutSubviews(id self, SEL _cmd) {
    if ([self isKindOfClass:UIViewController.class]) {
        UIViewController *controller = (UIViewController *)self;
        JGTraceLayoutState(controller, @"viewDidLayoutSubviews.enter", nil);
        JGRestoreTelegramBaseline(controller);
    }
    if (JGOriginalViewDidLayoutSubviews != NULL) JGOriginalViewDidLayoutSubviews(self, _cmd);
    if (![self isKindOfClass:UIViewController.class]) return;
    UIViewController *controller = (UIViewController *)self;
    JGTraceLayoutState(controller, @"viewDidLayoutSubviews.afterOriginal", nil);
    JGCaptureTelegramBaseline(controller);
    JGApplyParitySettingsSection(controller);
    JGTraceLayoutState(controller, @"viewDidLayoutSubviews.afterApply", nil);
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
