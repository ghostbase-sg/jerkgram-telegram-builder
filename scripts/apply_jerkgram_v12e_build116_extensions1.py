#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

HEADER = ROOT / "submodules/BuildConfig/PublicHeaders/BuildConfig/BuildConfig.h"
IMPLEMENTATION = ROOT / "submodules/BuildConfig/Sources/BuildConfig.m"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
SETTINGS_BUILD = ROOT / "submodules/SettingsUI/BUILD"

OWNERS = {
    "submodules/TelegramUI/Sources/AppDelegate.swift": "app",
    "Telegram/SiriIntents/IntentHandler.swift": "siri",
    "Telegram/WidgetKitWidget/TodayViewController.swift": "widget",
    "Telegram/BroadcastUpload/BroadcastUploadExtension.swift": "broadcast",
    "Telegram/Share/ShareRootController.swift": "share",
    "Telegram/NotificationContent/NotificationViewController.swift": "notificationContent",
    "Telegram/NotificationService/Sources/NotificationService.swift": "notificationService",
}


def require(value, message):
    if not value:
        raise RuntimeError("[Build116 extensions] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_buildconfig(header, implementation):
    require("@interface BuildConfig : NSObject" in header, "BuildConfig primary interface missing")
    require("@interface BuildConfig (JerkgramExtensionDiagnostics)" not in header, "diagnostic category already declared")
    declaration = '''

@interface BuildConfig (JerkgramExtensionDiagnostics)
+ (void)jerkgramRecordExtensionDiagnosticWithProcess:(NSString * _Nonnull)process
    stage:(NSString * _Nonnull)stage
    appGroupIdentifier:(NSString * _Nonnull)appGroupIdentifier
    sharedContainerPath:(NSString * _Nullable)sharedContainerPath
    detail:(NSString * _Nonnull)detail
    NS_SWIFT_NAME(jerkgramRecordExtensionDiagnostic(process:stage:appGroupIdentifier:sharedContainerPath:detail:));
+ (NSString * _Nonnull)jerkgramExtensionDiagnosticsReport;

@end
'''
    header = header.rstrip() + declaration

    implementation += r'''

// MARK: Jerkgram v1.2E BUILD116_EXTENSION_DIAGNOSTICS1
static NSString *JerkgramDiagnosticsDirectory(NSString *sharedContainerPath) {
    return [sharedContainerPath stringByAppendingPathComponent:@"telegram-data/jerkgram-extension-diagnostics"];
}

static NSString *JerkgramResolvedDiagnosticsGroup(void) {
    NSMutableArray<NSURL *> *profileURLs = [[NSMutableArray alloc] init];
    NSURL *bundleURL = NSBundle.mainBundle.bundleURL;
    [profileURLs addObject:[bundleURL URLByAppendingPathComponent:@"embedded.mobileprovision"]];
    NSURL *containingApp = bundleURL.URLByDeletingLastPathComponent.URLByDeletingLastPathComponent;
    if ([containingApp.pathExtension isEqualToString:@"app"]) {
        [profileURLs addObject:[containingApp URLByAppendingPathComponent:@"embedded.mobileprovision"]];
    }
    for (NSURL *profileURL in profileURLs) {
        NSData *data = [NSData dataWithContentsOfURL:profileURL];
        if (data == nil) {
            continue;
        }
        NSString *text = [[NSString alloc] initWithData:data encoding:NSISOLatin1StringEncoding];
        NSRange start = [text rangeOfString:@"<plist"];
        NSRange end = [text rangeOfString:@"</plist>" options:NSBackwardsSearch];
        if (start.location == NSNotFound || end.location == NSNotFound) {
            continue;
        }
        NSRange range = NSMakeRange(start.location, NSMaxRange(end) - start.location);
        NSData *plistData = [[text substringWithRange:range] dataUsingEncoding:NSUTF8StringEncoding];
        NSDictionary *root = [NSPropertyListSerialization propertyListWithData:plistData options:0 format:nil error:nil];
        NSArray<NSString *> *groups = root[@"Entitlements"][@"com.apple.security.application-groups"];
        NSString *fallback = [@"group." stringByAppendingString:NSBundle.mainBundle.bundleIdentifier ?: @""];
        if ([groups containsObject:fallback]) {
            return fallback;
        }
        NSArray<NSString *> *roleOne = [groups filteredArrayUsingPredicate:[NSPredicate predicateWithBlock:^BOOL(NSString *value, NSDictionary *_) {
            return [value hasSuffix:@".1"];
        }]];
        if (roleOne.count == 1) {
            return roleOne.firstObject;
        }
        if (groups.count == 1) {
            return groups.firstObject;
        }
    }
    return [@"group." stringByAppendingString:NSBundle.mainBundle.bundleIdentifier ?: @""];
}

@implementation BuildConfig (JerkgramExtensionDiagnostics)

+ (void)jerkgramRecordExtensionDiagnosticWithProcess:(NSString *)process
    stage:(NSString *)stage
    appGroupIdentifier:(NSString *)appGroupIdentifier
    sharedContainerPath:(NSString *)sharedContainerPath
    detail:(NSString *)detail {
    NSString *boundedDetail = detail ?: @"";
    if (boundedDetail.length > 240) {
        boundedDetail = [boundedDetail substringToIndex:240];
    }
    NSLog(@"[JerkgramExtension] %@ %@ group=%@ path=%@ %@", process, stage, appGroupIdentifier, sharedContainerPath, boundedDetail);
    if (sharedContainerPath.length == 0) {
        return;
    }
    NSString *directory = JerkgramDiagnosticsDirectory(sharedContainerPath);
    [NSFileManager.defaultManager createDirectoryAtPath:directory withIntermediateDirectories:YES attributes:nil error:nil];
    NSDictionary *record = @{
        @"schemaVersion": @1,
        @"process": process ?: @"unknown",
        @"stage": stage ?: @"unknown",
        @"appGroupIdentifier": appGroupIdentifier ?: @"",
        @"sharedContainerPath": sharedContainerPath ?: @"",
        @"detail": boundedDetail,
        @"timestampMs": @((long long)(NSDate.date.timeIntervalSince1970 * 1000.0))
    };
    NSData *json = [NSJSONSerialization dataWithJSONObject:record options:NSJSONWritingSortedKeys error:nil];
    NSString *safeProcess = [[process ?: @"unknown" componentsSeparatedByCharactersInSet:NSCharacterSet.alphanumericCharacterSet.invertedSet] componentsJoinedByString:@"_"];
    NSURL *fileURL = [NSURL fileURLWithPath:[directory stringByAppendingPathComponent:[safeProcess stringByAppendingPathExtension:@"json"]]];
    [json writeToURL:fileURL options:NSDataWritingAtomic error:nil];
}

+ (NSString *)jerkgramExtensionDiagnosticsReport {
    NSString *group = JerkgramResolvedDiagnosticsGroup();
    NSURL *container = [NSFileManager.defaultManager containerURLForSecurityApplicationGroupIdentifier:group];
    if (container == nil) {
        return @"{\"schemaVersion\":1,\"error\":\"shared-container-unavailable\"}";
    }
    NSString *directory = JerkgramDiagnosticsDirectory(container.path);
    NSArray<NSString *> *names = [[NSFileManager.defaultManager contentsOfDirectoryAtPath:directory error:nil] sortedArrayUsingSelector:@selector(compare:)];
    NSMutableArray *records = [[NSMutableArray alloc] init];
    for (NSString *name in [names subarrayWithRange:NSMakeRange(0, MIN(names.count, 16))]) {
        NSData *data = [NSData dataWithContentsOfFile:[directory stringByAppendingPathComponent:name]];
        id record = data == nil ? nil : [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
        if (record != nil) {
            [records addObject:record];
        }
    }
    NSDictionary *report = @{@"schemaVersion": @1, @"appGroupIdentifier": group, @"records": records};
    NSData *json = [NSJSONSerialization dataWithJSONObject:report options:(NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys) error:nil];
    return [[NSString alloc] initWithData:json encoding:NSUTF8StringEncoding] ?: @"{}";
}

@end
'''
    return header, implementation


def diagnostic_call(process, stage, path, detail):
    return f'''BuildConfig.jerkgramRecordExtensionDiagnostic(
    process: "{process}",
    stage: "{stage}",
    appGroupIdentifier: appGroupName,
    sharedContainerPath: {path},
    detail: "{detail}"
)'''


def patch_owner(text, process):
    marker = "// MARK: Jerkgram v1.2E BUILD116_EXTENSION_STAGE1"
    require(marker not in text, "owner already patched: " + process)

    group_pattern = re.compile(
        r'(let appGroupName = jerkgramResolvedApplicationGroupIdentifier\(\s*'
        r'fallback: "group\.\\\(baseAppBundleId\)"\s*\))'
    )
    group_matches = list(group_pattern.finditer(text))
    require(group_matches, "resolved AppGroup call missing: " + process)
    offset = 0
    for index, match in enumerate(group_matches):
        insertion = "\n" + ((marker + "\n") if index == 0 else "") + diagnostic_call(
            process, "profile", "nil", "selected app-group identifier"
        )
        point = match.end() + offset
        text = text[:point] + insertion + text[point:]
        offset += len(insertion)

    container_pattern = re.compile(
        r'(let maybeAppGroupUrl = FileManager\.default\.containerURL\('
        r'forSecurityApplicationGroupIdentifier: appGroupName\))'
    )
    matches = list(container_pattern.finditer(text))
    require(matches, "containerURL owner missing: " + process)
    offset = 0
    for match in matches:
        insertion = "\n" + diagnostic_call(
            process, "container", "maybeAppGroupUrl?.path", "containerURL resolved"
        )
        point = match.end() + offset
        text = text[:point] + insertion + text[point:]
        offset += len(insertion)

    encryption_pattern = re.compile(r'(let deviceSpecificEncryptionParameters = BuildConfig\.deviceSpecificEncryptionParameters\([^\n]+)')
    match = encryption_pattern.search(text)
    if match:
        insertion = (
            "\n" + diagnostic_call(process, "root", "appGroupUrl.path", "telegram-data root ready")
            + "\n" + diagnostic_call(process, "encryption", "appGroupUrl.path", "encryption parameters ready")
        )
        text = text[:match.end()] + insertion + text[match.end():]
    else:
        root_pattern = re.compile(r'(let rootPath = [^\n]+)')
        match = root_pattern.search(text)
        if match:
            insertion = "\n" + diagnostic_call(process, "root", "appGroupUrl.path", "telegram-data root ready")
            text = text[:match.end()] + insertion + text[match.end():]

    account_pattern = re.compile(
        r'((?:let\s+accountManager|self\.accountManager)\s*=\s*AccountManager[^\n]+)'
    )
    match = account_pattern.search(text)
    if match:
        insertion = "\n" + diagnostic_call(process, "account", "appGroupUrl.path", "account metadata owner initialized")
        text = text[:match.end()] + insertion + text[match.end():]

    stage_anchors = {
        "widget": "    var itemsByAccount:",
        "share": "            self.impl = ShareRootControllerImpl(",
        "notificationContent": "            self.impl = NotificationViewControllerImpl(",
    }
    if process in stage_anchors and 'stage: "account"' not in text:
        anchor = stage_anchors[process]
        require(anchor in text, "implementation/account boundary missing: " + process)
        indentation = anchor[: len(anchor) - len(anchor.lstrip())]
        insertion = diagnostic_call(
            process,
            "account",
            "appGroupUrl.path",
            "account-backed implementation initialization",
        )
        insertion = "\n".join(indentation + line for line in insertion.splitlines()) + "\n"
        text = text.replace(anchor, insertion + anchor, 1)

    if process == "broadcast":
        anchor = 'let embeddedBroadcastImplementationTypePath = rootPath + "/broadcast-coordination-type-v2"'
        require(anchor in text, "broadcast coordination owner missing")
        text = text.replace(
            anchor,
            anchor + "\n" + diagnostic_call(process, "broadcastCoordination", "appGroupUrl.path", "coordination selector ready"),
            1,
        )
    return text


def patch_settings(text):
    if "import BuildConfig\n" not in text:
        text = replace_once(text, "import AccountContext\n", "import AccountContext\nimport BuildConfig\n", "Settings import")
    empty = '''    // MARK: Jerkgram v1.2E BUILD116_SETTINGS_RUNTIME_CLEANUP1
    if page == .debugResearch {
        return []
    }'''
    action = '''    // MARK: Jerkgram v1.2E BUILD116_SETTINGS_RUNTIME_CLEANUP1
    if page == .debugResearch {
        return [
            .researchAction(0, 0, strings.copyExtensionDiagnostics, "copyExtensionDiagnostics")
        ]
    }'''
    text = replace_once(text, empty, action, "copy diagnostics page")
    switch_anchor = '''            switch action {
'''
    switch_replacement = '''            switch action {
            case "copyExtensionDiagnostics":
                UIPasteboard.general.string = BuildConfig.jerkgramExtensionDiagnosticsReport()

'''
    return replace_once(text, switch_anchor, switch_replacement, "copy diagnostics action")


def patch_settings_build(text):
    dependency = '        "//submodules/BuildConfig:BuildConfig",\n'
    if dependency in text:
        return text
    return replace_once(
        text,
        "    deps = [\n",
        "    deps = [\n" + dependency,
        "SettingsUI dependency list",
    )


def main():
    for path in (HEADER, IMPLEMENTATION, SETTINGS, SETTINGS_BUILD):
        require(path.is_file(), "source owner missing: " + str(path))
    header, implementation = patch_buildconfig(
        HEADER.read_text(encoding="utf-8"),
        IMPLEMENTATION.read_text(encoding="utf-8"),
    )
    HEADER.write_text(header, encoding="utf-8")
    IMPLEMENTATION.write_text(implementation, encoding="utf-8")
    for relative, process in OWNERS.items():
        path = ROOT / relative
        require(path.is_file(), "extension owner missing: " + relative)
        path.write_text(patch_owner(path.read_text(encoding="utf-8"), process), encoding="utf-8")
    SETTINGS.write_text(patch_settings(SETTINGS.read_text(encoding="utf-8")), encoding="utf-8")
    SETTINGS_BUILD.write_text(patch_settings_build(SETTINGS_BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build116 extensions] bounded diagnostics installed in 7/7 runtime owners")


if __name__ == "__main__":
    main()
