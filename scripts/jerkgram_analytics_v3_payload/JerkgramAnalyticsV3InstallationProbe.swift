import Foundation
#if canImport(Darwin)
import Darwin
#else
import Glibc
#endif

// Pre-write proof snapshot: fixed paths and at most one useful directory entry.
// No persistent-domain copy, recursive enumeration, account IDs or file contents.
enum JerkgramAnalyticsV3InstallationProbe {
    private enum DirectoryState { case empty, nonempty, unknown }

    private static func directoryState(_ path: String, missingIsEmpty: Bool, allowEmptyLibrary: Bool = false) -> DirectoryState {
        guard let directory = opendir(path) else {
            return missingIsEmpty && errno == ENOENT ? .empty : .unknown
        }
        defer { closedir(directory) }
        // At most '.', '..', optional Library, and one useful entry. No full scan.
        for _ in 0..<4 {
            errno = 0
            guard let entry = readdir(directory) else { return errno == 0 ? .empty : .unknown }
            let capacity = MemoryLayout.size(ofValue: entry.pointee.d_name)
            let name = withUnsafePointer(to: &entry.pointee.d_name) { pointer in
                pointer.withMemoryRebound(to: CChar.self, capacity: capacity) { String(cString: $0) }
            }
            if name == "." || name == ".." { continue }
            if allowEmptyLibrary && name == "Library" {
                switch self.directoryState(path + "/Library", missingIsEmpty: false) {
                case .empty: continue
                case .nonempty: return .nonempty
                case .unknown: return .unknown
                }
            }
            return .nonempty
        }
        return .unknown
    }

    static func classify(bundleIdentityAvailable: Bool, legacyEvidence: Bool,
                         appGroupURL: URL?, userDirectories: [URL],
                         fileManager: FileManager = .default) -> JerkgramAnalyticsV3.InstallationEvidence {
        if legacyEvidence { return .provenExisting }
        guard bundleIdentityAvailable, let appGroupURL, userDirectories.count == 2 else { return .unknown }
        let root = appGroupURL.appendingPathComponent("telegram-data", isDirectory: true)
        let legacyMetadata = appGroupURL.appendingPathComponent("accounts-metadata", isDirectory: true)
        if fileManager.fileExists(atPath: root.path) || fileManager.fileExists(atPath: legacyMetadata.path) {
            return .provenExisting
        }
        guard case .empty = self.directoryState(appGroupURL.path, missingIsEmpty: false, allowEmptyLibrary: true) else { return .unknown }
        for directory in userDirectories {
            switch self.directoryState(directory.path, missingIsEmpty: true) {
            case .nonempty: return .provenExisting
            case .unknown: return .unknown
            case .empty: break
            }
        }
        return .fresh
    }
}
