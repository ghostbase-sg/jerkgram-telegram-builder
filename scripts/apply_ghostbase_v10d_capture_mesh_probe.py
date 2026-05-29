from pathlib import Path
import runpy
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

base = ROOT / "scripts/apply_ghostbase_v10c_story_diff.py"
if not base.exists():
    raise SystemExit("[v1.0D] ERROR: missing v1.0C base patcher")

print("[v1.0D] replay v1.0C base")
runpy.run_path(str(base), run_name="__main__")

def read(path):
    return path.read_text()

def write(path, text):
    path.write_text(text)

def replace_once(text, old, new, label):
    if new in text:
        print(f"[v1.0D] already patched: {label}")
        return text
    if old not in text:
        raise SystemExit(f"[v1.0D] ERROR: pattern not found: {label}")
    return text.replace(old, new, 1)

def ensure(text, needle, label):
    if needle not in text:
        raise SystemExit(f"[v1.0D] ERROR: missing proof: {label}")

# MARK: GhostBase v1.0D source-level AppGroup override
appgroup_p = SRC / "Swiftgram/SGAppGroupIdentifier/Sources/SGAppGroupIdentifier.swift"
appgroup = read(appgroup_p)

appgroup = replace_once(
    appgroup,
    '    let result: String = "group.\\(sgBaseBundleIdentifier())"',
    '    let result: String = "group.4a348a9b186b700c.1"',
    "SGAppGroupIdentifier fixed provisioning group"
)

write(appgroup_p, appgroup)

# MARK: GhostBase v1.0D NSE capture probe
nse_p = SRC / "Telegram/NotificationService/Sources/NotificationService.swift"
nse = read(nse_p)

if "// MARK: GhostBase v1.0D NSE Capture Probe" not in nse:
    helper = r'''
// MARK: GhostBase v1.0D NSE Capture Probe
private func ghostBaseV10DNSEDefaults() -> UserDefaults? {
    return UserDefaults(suiteName: sgAppGroupIdentifier())
}

private func ghostBaseV10DRecordNSE(_ name: String, amount: Int = 1) {
    guard amount > 0, let defaults = ghostBaseV10DNSEDefaults() else {
        return
    }
    let prefix = "GhostBase.V10D.NSE."
    let key = prefix + name + ".Count"
    defaults.set(defaults.integer(forKey: key) + amount, forKey: key)
    defaults.set(defaults.integer(forKey: prefix + "Total") + amount, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(amount, forKey: prefix + "LastAmount")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
    defaults.set(sgAppGroupIdentifier(), forKey: prefix + "AppGroup")
    defaults.synchronize()
}

private func ghostBaseV10DSetNSE(_ key: String, _ value: String) {
    guard let defaults = ghostBaseV10DNSEDefaults() else {
        return
    }
    defaults.set(value, forKey: "GhostBase.V10D.NSE." + key)
    defaults.synchronize()
}

private func ghostBaseV10DPreview(_ value: String, limit: Int = 180) -> String {
    if value.count <= limit {
        return value
    }
    return String(value.prefix(limit))
}
'''
    nse = nse.replace("private let groupUserDefaults: UserDefaults? = UserDefaults(suiteName: sgAppGroupIdentifier())", helper + "\nprivate let groupUserDefaults: UserDefaults? = UserDefaults(suiteName: sgAppGroupIdentifier())", 1)

write(nse_p, nse)

nse = read(nse_p)

nse = replace_once(
    nse,
    '''        let episode = String(UInt32.random(in: 0 ..< UInt32.max), radix: 16)
        self.episode = episode''',
    '''        let episode = String(UInt32.random(in: 0 ..< UInt32.max), radix: 16)
        ghostBaseV10DRecordNSE("didReceive")
        ghostBaseV10DSetNSE("LastInitialTitle", ghostBaseV10DPreview(request.content.title))
        ghostBaseV10DSetNSE("LastInitialBody", ghostBaseV10DPreview(request.content.body))
        if !request.content.body.isEmpty {
            ghostBaseV10DRecordNSE(request.content.body == "New Message" ? "initialGenericBody" : "initialBody")
        }
        self.episode = episode''',
    "NSE didReceive probe"
)

nse = replace_once(
    nse,
    '''                updateCurrentContent: { value in
                    let _ = content.swap(value)
                },''',
    '''                updateCurrentContent: { value in
                    ghostBaseV10DRecordNSE("contentUpdated")
                    if let title = value.title, !title.isEmpty {
                        ghostBaseV10DRecordNSE("finalTitle")
                        ghostBaseV10DSetNSE("LastFinalTitle", ghostBaseV10DPreview(title))
                    }
                    if let body = value.body, !body.isEmpty {
                        ghostBaseV10DRecordNSE(body == "New Message" ? "finalGenericBody" : "finalBody")
                        ghostBaseV10DSetNSE("LastFinalBody", ghostBaseV10DPreview(body))
                    }
                    let _ = content.swap(value)
                },''',
    "NSE final content probe"
)

write(nse_p, nse)

nse = read(nse_p)

nse = replace_once(
    nse,
    '''                    Logger.shared.log("NotificationService \\(episode)", "Decrypted payload: \\(payloadJson)")''',
    '''                    Logger.shared.log("NotificationService \\(episode)", "Decrypted payload: \\(payloadJson)")
                    ghostBaseV10DRecordNSE("decryptedPayload")
                    ghostBaseV10DSetNSE("LastPayloadKeys", payloadJson.keys.sorted().joined(separator: ","))
                    if payloadJson["msg_id"] != nil {
                        ghostBaseV10DRecordNSE("payloadMsgId")
                    }
                    if payloadJson["story_id"] != nil {
                        ghostBaseV10DRecordNSE("payloadStoryId")
                    }
                    if payloadJson["from_id"] != nil || payloadJson["chat_id"] != nil || payloadJson["channel_id"] != nil || payloadJson["encryption_id"] != nil {
                        ghostBaseV10DRecordNSE("payloadPeerId")
                    }
                    if let locKey = payloadJson["loc-key"] as? String {
                        ghostBaseV10DSetNSE("LastLocKey", locKey)
                    }''',
    "NSE decrypted payload probe"
)

write(nse_p, nse)

settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
settings = read(settings_p)

insert_before = '    let ghostBaseCorePrefixV10C = "GhostBase.V10C.Core."'

capture_ui = r'''    let ghostBaseNsePrefix = "GhostBase.V10D.NSE."
    let ghostBaseNseDefaults = UserDefaults(suiteName: "group.4a348a9b186b700c.1") ?? UserDefaults.standard

    entries.append(.info(debug, """
Capture Mesh / NSE Probe:
AppGroup: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "AppGroup") ?? "none")
Total: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "Total"))
Last: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "Last") ?? "none") x\(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "LastAmount")) @ \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "LastTime"))
didReceive: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "didReceive.Count"))
decryptedPayload: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "decryptedPayload.Count"))
payloadMsgId: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "payloadMsgId.Count"))
payloadPeerId: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "payloadPeerId.Count"))
initialBody: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "initialBody.Count"))
initialGenericBody: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "initialGenericBody.Count"))
finalBody: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "finalBody.Count"))
finalGenericBody: \(ghostBaseNseDefaults.integer(forKey: ghostBaseNsePrefix + "finalGenericBody.Count"))
LastLocKey: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "LastLocKey") ?? "none")
LastPayloadKeys: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "LastPayloadKeys") ?? "none")
LastFinalTitle: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "LastFinalTitle") ?? "none")
LastFinalBody: \(ghostBaseNseDefaults.string(forKey: ghostBaseNsePrefix + "LastFinalBody") ?? "none")
"""))

'''

settings = replace_once(settings, insert_before, capture_ui + insert_before, "settings Capture Mesh / NSE Probe UI")
settings = re.sub(r"Version: v[0-9A-Za-z.\-]+", "Version: v1.0D", settings, count=1)

write(settings_p, settings)

story_p = SRC / "submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerComponent.swift"
story = read(story_p)

story = replace_once(
    story,
    'return generateTintedImage(image: UIImage(bundleImageName: accountUser.isPremium ? "Chat/Context Menu/Download" : "Chat/Context Menu/DownloadLocked"), color: theme.contextMenu.primaryColor)',
    'return generateTintedImage(image: UIImage(bundleImageName: (accountUser.isPremium || ((UserDefaults.standard.object(forKey: "GhostBase.Stories.Save") as? Bool) ?? false)) ? "Chat/Context Menu/Download" : "Chat/Context Menu/DownloadLocked"), color: theme.contextMenu.primaryColor)',
    "story save unlocked icon"
)

write(story_p, story)

appgroup = read(appgroup_p)
nse = read(nse_p)
settings = read(settings_p)
story = read(story_p)

ensure(appgroup, 'let result: String = "group.4a348a9b186b700c.1"', "fixed AppGroup source")
ensure(nse, "GhostBase v1.0D NSE Capture Probe", "NSE helper")
ensure(nse, 'ghostBaseV10DRecordNSE("didReceive")', "NSE didReceive")
ensure(nse, 'ghostBaseV10DRecordNSE("decryptedPayload")', "NSE decrypted payload")
ensure(nse, 'ghostBaseV10DRecordNSE(body == "New Message" ? "finalGenericBody" : "finalBody")', "NSE final body")
ensure(settings, "Capture Mesh / NSE Probe", "settings Capture Mesh UI")
ensure(settings, "Version: v1.0D", "settings v1.0D")
ensure(story, 'GhostBase.Stories.Save") as? Bool', "story save icon polish")

print("[v1.0D] GhostBase Capture Mesh / NSE Probe patch OK")
