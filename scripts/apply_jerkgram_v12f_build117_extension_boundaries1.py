#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
HEADER = ROOT / "submodules/BuildConfig/PublicHeaders/BuildConfig/BuildConfig.h"
IMPLEMENTATION = ROOT / "submodules/BuildConfig/Sources/BuildConfig.m"
SHARE = ROOT / "Telegram/Share/ShareRootController.swift"
WIDGET = ROOT / "Telegram/WidgetKitWidget/TodayViewController.swift"
BROADCAST = ROOT / "Telegram/BroadcastUpload/BroadcastUploadExtension.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 extension boundaries] " + message)


def replace_once(text, old, new, label):
    count = text.count(old)
    require(count == 1, f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_buildconfig(header, implementation):
    declaration = '''+ (NSString * _Nonnull)jerkgramExtensionContainerClassificationForPath:(NSString * _Nullable)path
    NS_SWIFT_NAME(jerkgramExtensionContainerClassification(path:));
+ (NSString * _Nonnull)jerkgramExtensionBoundarySummaryWithProcess:(NSString * _Nonnull)process
    stage:(NSString * _Nonnull)stage
    path:(NSString * _Nullable)path
    NS_SWIFT_NAME(jerkgramExtensionBoundarySummary(process:stage:path:));
'''
    header = replace_once(
        header,
        "@interface BuildConfig (JerkgramExtensionDiagnostics)\n",
        "@interface BuildConfig (JerkgramExtensionDiagnostics)\n" + declaration,
        "BuildConfig diagnostic category",
    )
    methods = r'''

// MARK: Jerkgram v1.2F BUILD117_EXTENSION_BOUNDARY_CLASSIFIER1
+ (NSString *)jerkgramExtensionContainerClassificationForPath:(NSString *)path {
    if (path.length == 0) {
        return @"missing";
    }
    if ([path containsString:@"/Containers/Shared/AppGroup/"]) {
        return @"shared";
    }
    if ([path hasSuffix:@"/Documents/AppGroup"] || [path containsString:@"/Documents/AppGroup/"]) {
        return @"processLocal";
    }
    return @"other";
}

+ (NSString *)jerkgramExtensionBoundarySummaryWithProcess:(NSString *)process
    stage:(NSString *)stage
    path:(NSString *)path {
    NSString *classification = [self jerkgramExtensionContainerClassificationForPath:path];
    NSString *safeProcess = process.length == 0 ? @"extension" : process;
    NSString *safeStage = stage.length == 0 ? @"unknown" : stage;
    return [NSString stringWithFormat:
        @"Jerkgram %@: %@ failed (container=%@). Open the main app once, then retry. If this remains processLocal, the signer isolated the App Group.",
        safeProcess, safeStage, classification];
}
'''
    category = "@implementation BuildConfig (JerkgramExtensionDiagnostics)"
    require(category in implementation, "BuildConfig diagnostic implementation missing")
    prefix, separator, suffix = implementation.rpartition("\n@end")
    require(separator != "", "BuildConfig diagnostic category terminator missing")
    require(category in prefix, "final Objective-C implementation is not diagnostics")
    implementation = prefix + methods + separator + suffix
    return header, implementation


def patch_share(text):
    class_anchor = '''class ShareRootController: UIViewController {
    private var impl: ShareRootControllerImpl?
'''
    helper = '''class ShareRootController: UIViewController {
    private var impl: ShareRootControllerImpl?

    // MARK: Jerkgram v1.2F BUILD117_SHARE_VISIBLE_DIAGNOSTIC1
    private func showJerkgramExtensionDiagnostic(_ message: String) {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.textColor = .secondaryLabel
        label.font = .preferredFont(forTextStyle: .body)
        label.text = String(message.prefix(240))
        label.translatesAutoresizingMaskIntoConstraints = false
        self.view.backgroundColor = .systemBackground
        self.view.addSubview(label)
        NSLayoutConstraint.activate([
            label.leadingAnchor.constraint(equalTo: self.view.leadingAnchor, constant: 24.0),
            label.trailingAnchor.constraint(equalTo: self.view.trailingAnchor, constant: -24.0),
            label.centerYAnchor.constraint(equalTo: self.view.centerYAnchor)
        ])
    }
'''
    text = replace_once(text, class_anchor, helper, "Share diagnostic view")
    guard_anchor = '''guard let appGroupUrl = maybeAppGroupUrl else {
                return
            }
'''
    boundary = '''guard let appGroupUrl = maybeAppGroupUrl else {
                self.showJerkgramExtensionDiagnostic(
                    BuildConfig.jerkgramExtensionBoundarySummary(
                        process: "Share", stage: "container", path: nil
                    )
                )
                return
            }
            let classification = BuildConfig.jerkgramExtensionContainerClassification(
                path: appGroupUrl.path
            )
            if classification != "shared" {
                self.showJerkgramExtensionDiagnostic(
                    BuildConfig.jerkgramExtensionBoundarySummary(
                        process: "Share", stage: "account", path: appGroupUrl.path
                    )
                )
                return
            }
'''
    return replace_once(text, guard_anchor, boundary, "Share container boundary")


def patch_widget(text):
    text = replace_once(text, "        case peers(ParsedPeers)\n", "        case peers(ParsedPeers)\n        case diagnostic(String)\n", "Widget entry diagnostic")
    widget_guard = '''guard let appGroupUrl = maybeAppGroupUrl else {
        completion(Timeline(entries: [SimpleEntry(date: entryDate, contents: .recent)], policy: .atEnd))
        return
    }
'''
    widget_boundary = '''guard let appGroupUrl = maybeAppGroupUrl else {
        let message = BuildConfig.jerkgramExtensionBoundarySummary(
            process: "Widget", stage: "container", path: nil
        )
        completion(Timeline(entries: [SimpleEntry(date: entryDate, contents: .diagnostic(message))], policy: .atEnd))
        return
    }
    let classification = BuildConfig.jerkgramExtensionContainerClassification(path: appGroupUrl.path)
    if classification != "shared" {
        let message = BuildConfig.jerkgramExtensionBoundarySummary(
            process: "Widget", stage: "account", path: appGroupUrl.path
        )
        completion(Timeline(entries: [SimpleEntry(date: entryDate, contents: .diagnostic(message))], policy: .atEnd))
        return
    }
'''
    text = replace_once(text, widget_guard, widget_boundary, "Widget container boundary")
    text = replace_once(text, "    case peers(ParsedPeers)\n}\n", "    case peers(ParsedPeers)\n    case diagnostic(String)\n}\n", "Widget data diagnostic")
    switch_anchor = '''    case let .peers(peers):
        return .peers(peers)
    }
'''
    switch_new = '''    case let .peers(peers):
        return .peers(peers)
    case let .diagnostic(message):
        return .diagnostic(message)
    }
'''
    text = replace_once(text, switch_anchor, switch_new, "Widget diagnostic mapping")
    view_marker = '''@available(iOSApplicationExtension 14.0, iOS 14.0, *)
struct WidgetView: View {
'''
    diagnostic_view = '''// MARK: Jerkgram v1.2F BUILD117_WIDGET_VISIBLE_DIAGNOSTIC1
@available(iOSApplicationExtension 14.0, iOS 14.0, *)
private struct JerkgramWidgetDiagnosticView: View {
    let message: String
    var body: some View {
        VStack(spacing: 8.0) {
            Image(systemName: "exclamationmark.triangle")
            Text("Jerkgram")
                .font(.headline)
            Text(String(message.prefix(240)))
                .font(.caption)
                .multilineTextAlignment(.center)
        }
        .padding(12.0)
    }
}

@available(iOSApplicationExtension 14.0, iOS 14.0, *)
struct WidgetView: View {
'''
    text = replace_once(text, view_marker, diagnostic_view, "Widget diagnostic view")
    # Both widget bodies keep their native layout but visibly replace it on boundary failure.
    for label in ("chats", "avatars"):
        anchor = '''    var body: some View {
        GeometryReader(content: { geometry in
            return VStack(alignment: .center, spacing: 0.0, content: {''' if label == "chats" else '''    var body: some View {
        return VStack(alignment: .center, spacing: 18.0, content: {'''
        if label == "chats":
            replacement = '''    var body: some View {
        GeometryReader(content: { geometry in
            if case let .diagnostic(message) = data {
                JerkgramWidgetDiagnosticView(message: message)
            } else {
                VStack(alignment: .center, spacing: 0.0, content: {'''
            text = replace_once(text, anchor, replacement, "Chats widget diagnostic branch")
            close_anchor = '''                chatUpdateView(size: geometry.size)
            })
        })'''
            close_new = '''                chatUpdateView(size: geometry.size)
                })
            }
        })'''
            text = replace_once(text, close_anchor, close_new, "Chats widget branch close")
        else:
            replacement = '''    var body: some View {
        Group {
            if case let .diagnostic(message) = data {
                JerkgramWidgetDiagnosticView(message: message)
            } else {
                VStack(alignment: .center, spacing: 18.0, content: {'''
            text = replace_once(text, anchor, replacement, "Avatars widget diagnostic branch")
            close_anchor = '''        })
        .padding(EdgeInsets(top: 10.0, leading: 10.0, bottom: 10.0, trailing: 10.0))'''
            close_new = '''                })
                .padding(EdgeInsets(top: 10.0, leading: 10.0, bottom: 10.0, trailing: 10.0))
            }
        }'''
            text = replace_once(text, close_anchor, close_new, "Avatars widget branch close")
    return text


def patch_broadcast(text):
    old = '''    private func finishWithError() {
        let errorString = "Finished"
        let error = NSError(domain: "BroadcastUploadExtension", code: 1, userInfo: [
            NSLocalizedDescriptionKey: errorString
        ])
        self.finishBroadcastWithError(error)
    }
'''
    new = '''    // MARK: Jerkgram v1.2F BUILD117_BROADCAST_VISIBLE_DIAGNOSTIC1
    private func finishWithError(stage: String, path: String? = nil) {
        let errorString = BuildConfig.jerkgramExtensionBoundarySummary(
            process: "Broadcast", stage: stage, path: path
        )
        let error = NSError(domain: "BroadcastUploadExtension", code: 117, userInfo: [
            NSLocalizedDescriptionKey: errorString
        ])
        self.finishBroadcastWithError(error)
    }
'''
    text = replace_once(text, old, new, "Broadcast staged error")
    text = text.replace("self.finishWithError()", 'self.finishWithError(stage: "bundle")', 1)
    guard_anchor = '''guard let appGroupUrl = maybeAppGroupUrl else {
            self.finishWithError()
            return
        }
'''
    boundary = '''guard let appGroupUrl = maybeAppGroupUrl else {
            self.finishWithError(stage: "container")
            return
        }
        let classification = BuildConfig.jerkgramExtensionContainerClassification(path: appGroupUrl.path)
        if classification != "shared" {
            self.finishWithError(stage: "coordination", path: appGroupUrl.path)
            return
        }
'''
    return replace_once(text, guard_anchor, boundary, "Broadcast container boundary")


def main():
    for path in (HEADER, IMPLEMENTATION, SHARE, WIDGET, BROADCAST):
        require(path.is_file(), "source owner missing: " + str(path))
    header, implementation = patch_buildconfig(HEADER.read_text(), IMPLEMENTATION.read_text())
    HEADER.write_text(header)
    IMPLEMENTATION.write_text(implementation)
    SHARE.write_text(patch_share(SHARE.read_text()))
    WIDGET.write_text(patch_widget(WIDGET.read_text()))
    BROADCAST.write_text(patch_broadcast(BROADCAST.read_text()))
    print("[Build117 extension boundaries] visible Share/Widget/Broadcast diagnostics installed")


if __name__ == "__main__":
    main()
