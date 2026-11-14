import Foundation
import UIKit
import Darwin
import TelegramPresentationData

// MARK: Jerkgram ANALYTICS_V3_BRIDGE
// Called before legacy defaults migration and before current-launch account
// initialization. File existence/empty-directory checks never read account IDs.
final class JerkgramAnalyticsV3Bridge {
    static let shared = JerkgramAnalyticsV3Bridge()
    private var initialized = false
    private var preferenceObserver: NSObjectProtocol?
    private static let enabledKey = "jerkgram.telemetry.anonymous.enabled"
    private static let legacyKeys = [
        "jerkgram.telemetry.secret.v1", "jerkgram.telemetry.firstDate.v1",
        "jerkgram.telemetry.installReceipt.v1", "jerkgram.telemetry.installReported.v1",
        "jerkgram.telemetry.lastSuccess.v1", "jerkgram.telemetry.lastAttempt.v2",
        "jerkgram.telemetry.opens.day", "jerkgram.telemetry.opens.count",
        "jerkgram.telemetry.anonymous.enabled", "jerkgram.runtime.namespaceMigration.v1"
    ]

    private static var enabled: Bool {
        let defaults = UserDefaults.standard
        return defaults.object(forKey: Self.enabledKey) == nil ? true : defaults.bool(forKey: Self.enabledKey)
    }

    func bootstrap(appGroupURL: URL?) {
        guard !self.initialized else { return }
        self.initialized = true
        let defaults = UserDefaults.standard
        let userDirectories = [FileManager.SearchPathDirectory.documentDirectory, .applicationSupportDirectory].compactMap {
            FileManager.default.urls(for: $0, in: .userDomainMask).first
        }
        let evidence = JerkgramAnalyticsV3InstallationProbe.classify(
            bundleIdentityAvailable: Bundle.main.bundleIdentifier != nil,
            legacyEvidence: Self.legacyKeys.contains { defaults.object(forKey: $0) != nil },
            appGroupURL: appGroupURL,
            userDirectories: userDirectories
        )
        JerkgramAnalyticsV3.shared.configure(metadata: JerkgramAnalyticsV3.Metadata(
            appVersion: JerkgramReleaseIdentity.technicalVersion,
            build: JerkgramReleaseIdentity.build,
            osVersion: UIDevice.current.systemVersion,
            osMajor: ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
            deviceRegion: Locale.current.regionCode,
            deviceModel: Self.hardwareModel()
        ))
        JerkgramAnalyticsV3.shared.initialize(enabled: Self.enabled, evidence: evidence)
        self.preferenceObserver = NotificationCenter.default.addObserver(
            forName: Notification.Name("JerkgramTelemetryPreferenceChanged"), object: nil, queue: nil
        ) { _ in
            // The existing Settings writer remains the single consent owner.
            // OFF is sent even while production delivery is disabled.
            JerkgramAnalyticsV3.shared.setEnabled(Self.enabled)
        }
    }

    // Re-read consent after the unchanged legacy namespace migration; this
    // is queued before any active lifecycle event and does not change v1.
    func synchronizeConsent() { JerkgramAnalyticsV3.shared.setEnabled(Self.enabled) }

    func didBecomeActive() { JerkgramAnalyticsV3.shared.didBecomeActive() }
    func didResignActive() { JerkgramAnalyticsV3.shared.didResignActive() }
    func didEnterBackground() { JerkgramAnalyticsV3.shared.didEnterBackground() }

    private static func hardwareModel() -> String? {
        var info = utsname()
        guard uname(&info) == 0 else { return nil }
        let capacity = MemoryLayout.size(ofValue: info.machine)
        return withUnsafePointer(to: &info.machine) { pointer in
            pointer.withMemoryRebound(to: CChar.self, capacity: capacity) { String(cString: $0) }
        }
    }
}
