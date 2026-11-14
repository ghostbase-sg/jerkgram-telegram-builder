import Foundation

let fm = FileManager.default
let base = fm.temporaryDirectory.appendingPathComponent(UUID().uuidString)
try fm.createDirectory(at: base, withIntermediateDirectories: true)
defer { try? fm.removeItem(at: base) }
let group = base.appendingPathComponent("group")
let documents = base.appendingPathComponent("documents")
let support = base.appendingPathComponent("support")
for directory in [group, documents, support] { try fm.createDirectory(at: directory, withIntermediateDirectories: true) }
func classify(_ bundleAvailable: Bool = true, _ legacy: Bool = false, _ container: URL? = group) -> JerkgramAnalyticsV3.InstallationEvidence {
    JerkgramAnalyticsV3InstallationProbe.classify(bundleIdentityAvailable: bundleAvailable, legacyEvidence: legacy, appGroupURL: container, userDirectories: [documents, support])
}
func expect(_ actual: JerkgramAnalyticsV3.InstallationEvidence, _ expected: JerkgramAnalyticsV3.InstallationEvidence, _ message: String) {
    precondition(actual == expected, message)
}
expect(JerkgramAnalyticsV3InstallationProbe.classify(bundleIdentityAvailable: true, legacyEvidence: false, appGroupURL: group, userDirectories: [documents]), .unknown, "Both sandbox directories must be probed")
expect(classify(), .fresh, "Only a verified empty pre-bootstrap installation is fresh")
expect(classify(true, true), .provenExisting, "An old opt-out is an existing installation")
expect(classify(true, true), .provenExisting, "Legacy receipt/report evidence is never fresh")
expect(classify(false), .unknown, "Missing bundle domain identity is ambiguous")
expect(classify(true, false, nil), .unknown, "Unavailable shared container is ambiguous")
expect(classify(true, false, group.appendingPathComponent("unavailable")), .unknown, "Unsuccessful filesystem access is ambiguous")
let metadata = group.appendingPathComponent("telegram-data/accounts-metadata")
try fm.createDirectory(at: metadata, withIntermediateDirectories: true)
expect(classify(), .provenExisting, "A logged-out account manager persists across updates")
try fm.removeItem(at: group.appendingPathComponent("telegram-data"))
let legacyMetadata = group.appendingPathComponent("accounts-metadata")
try fm.createDirectory(at: legacyMetadata, withIntermediateDirectories: true)
expect(classify(), .provenExisting, "Legacy app-group metadata also proves an update")
try fm.removeItem(at: legacyMetadata)
try Data([1]).write(to: documents.appendingPathComponent("existing-local-data"))
expect(classify(), .provenExisting, "Existing sandbox storage is never counted fresh")
try fm.removeItem(at: documents.appendingPathComponent("existing-local-data"))
let library = group.appendingPathComponent("Library")
try fm.createDirectory(at: library, withIntermediateDirectories: true)
expect(classify(), .fresh, "An empty OS-created Library alone contains no prior app evidence")
try fm.createDirectory(at: library.appendingPathComponent("Preferences"), withIntermediateDirectories: true)
expect(classify(), .unknown, "Ambiguous nonempty group state is never fresh")
try fm.removeItem(at: library.appendingPathComponent("Preferences"))
let populated = group.appendingPathComponent("large-existing-folder")
try fm.createDirectory(at: populated, withIntermediateDirectories: true)
for index in 0..<1000 { _ = fm.createFile(atPath: populated.appendingPathComponent("fixture-\(index)").path, contents: nil) }
let started = Date()
for _ in 0..<1000 { expect(classify(), .unknown, "First entry proves nonempty without traversing contents") }
print("Bounded probe fixture timing (not a startup/device performance claim):", Date().timeIntervalSince(started))
print("Analytics v3 native pre-bootstrap installation evidence PASS")
