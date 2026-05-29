from pathlib import Path
import runpy
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

base = ROOT / "scripts/apply_ghostbase_v10d_capture_mesh_probe.py"
if not base.exists():
    raise SystemExit("[v1.0E] ERROR: missing v1.0D base patcher")

print("[v1.0E] replay v1.0D base")
runpy.run_path(str(base), run_name="__main__")

def read(path):
    return path.read_text()

def write(path, text):
    path.write_text(text)

def replace_once(text, old, new, label):
    if new in text:
        print(f"[v1.0E] already patched: {label}")
        return text
    if old not in text:
        raise SystemExit(f"[v1.0E] ERROR: pattern not found: {label}")
    print(f"[v1.0E] patch {label}")
    return text.replace(old, new, 1)

def ensure(text, needle, label):
    if needle not in text:
        raise SystemExit(f"[v1.0E] ERROR: missing proof: {label}")

app_p = SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
app = read(app_p)

if "// MARK: GhostBase v1.0E Main Push Probe" not in app:
    helper = r'''
// MARK: GhostBase v1.0E Main Push Probe
private func ghostBaseV10EPushRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }
    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10E.Push."
    let key = prefix + name + ".Count"
    defaults.set(defaults.integer(forKey: key) + amount, forKey: key)
    defaults.set(defaults.integer(forKey: prefix + "Total") + amount, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(amount, forKey: prefix + "LastAmount")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
}

private func ghostBaseV10EPushSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: "GhostBase.V10E.Push." + key)
}

private func ghostBaseV10EPushPreview(_ value: String, limit: Int = 160) -> String {
    if value.count <= limit {
        return value
    }
    return String(value.prefix(limit))
}
'''
    lines = app.splitlines()
    last_import = -1
    for i, line in enumerate(lines[:180]):
        if line.startswith("import "):
            last_import = i
    if last_import < 0:
        raise SystemExit("[v1.0E] ERROR: AppDelegate import block not found")
    lines.insert(last_import + 1, helper)
    app = "\n".join(lines) + "\n"

write(app_p, app)

app = read(app_p)

app = replace_once(
    app,
    '''    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Logger.shared.log("App \\(self.episodeId)", "register for notifications: didRegisterForRemoteNotificationsWithDeviceToken (deviceToken: \\(hexString(deviceToken)))")
        self.notificationTokenPromise.set(.single(deviceToken))
    }''',
    '''    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        ghostBaseV10EPushRecord("didRegisterDeviceToken")
        ghostBaseV10EPushSet("LastDeviceTokenLength", "\\(deviceToken.count)")
        Logger.shared.log("App \\(self.episodeId)", "register for notifications: didRegisterForRemoteNotificationsWithDeviceToken (deviceToken: \\(hexString(deviceToken)))")
        self.notificationTokenPromise.set(.single(deviceToken))
    }''',
    "AppDelegate didRegister device token"
)

app = replace_once(
    app,
    '''    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        Logger.shared.log("App \\(self.episodeId)", "register for notifications: didFailToRegisterForRemoteNotificationsWithError (error: \\(error))")
    }''',
    '''    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        ghostBaseV10EPushRecord("didFailRegisterDeviceToken")
        ghostBaseV10EPushSet("LastRegisterFail", ghostBaseV10EPushPreview(String(describing: error)))
        Logger.shared.log("App \\(self.episodeId)", "register for notifications: didFailToRegisterForRemoteNotificationsWithError (error: \\(error))")
    }''',
    "AppDelegate didFail device token"
)

app = replace_once(
    app,
    '''    func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable : Any], fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        let _ = (self.sharedContextPromise.get()''',
    '''    func application(_ application: UIApplication, didReceiveRemoteNotification userInfo: [AnyHashable : Any], fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        ghostBaseV10EPushRecord("didReceiveRemoteNotification")
        ghostBaseV10EPushSet("LastUserInfoKeys", userInfo.keys.map { "\\($0)" }.sorted().joined(separator: ","))
        if userInfo["p"] != nil {
            ghostBaseV10EPushRecord("remoteEncryptedPayload")
        }
        if let aps = userInfo["aps"] as? [AnyHashable: Any] {
            ghostBaseV10EPushSet("LastAPSKeys", aps.keys.map { "\\($0)" }.sorted().joined(separator: ","))
        }
        let _ = (self.sharedContextPromise.get()''',
    "AppDelegate didReceive remote notification"
)

write(app_p, app)

app = read(app_p)

app = replace_once(
    app,
    '''            Logger.shared.log("App \\(self.episodeId)", "register for notifications: received settings: \\(settings.authorizationStatus)")
            
            switch (settings.authorizationStatus, authorize) {''',
    '''            Logger.shared.log("App \\(self.episodeId)", "register for notifications: received settings: \\(settings.authorizationStatus)")
            ghostBaseV10EPushRecord("notificationSettingsRead")
            ghostBaseV10EPushSet("LastAuthorizationStatus", "\\(settings.authorizationStatus)")
            
            switch (settings.authorizationStatus, authorize) {''',
    "notification settings read probe"
)

app = replace_once(
    app,
    '''                    notificationCenter.requestAuthorization(options: authorizationOptions, completionHandler: { result, _ in
                        Logger.shared.log("App \\(self.episodeId)", "register for notifications: received authorization: \\(result)")
                        completion(result)''',
    '''                    notificationCenter.requestAuthorization(options: authorizationOptions, completionHandler: { result, _ in
                        ghostBaseV10EPushRecord(result ? "requestAuthorizationTrue" : "requestAuthorizationFalse")
                        Logger.shared.log("App \\(self.episodeId)", "register for notifications: received authorization: \\(result)")
                        completion(result)''',
    "requestAuthorization result probe"
)

app = replace_once(
    app,
    '''                                Logger.shared.log("App \\(self.episodeId)", "register for notifications: invoke registerForRemoteNotifications")
                                UIApplication.shared.registerForRemoteNotifications()''',
    '''                                ghostBaseV10EPushRecord("authorizedRegisterForRemoteNotifications")
                                Logger.shared.log("App \\(self.episodeId)", "register for notifications: invoke registerForRemoteNotifications")
                                UIApplication.shared.registerForRemoteNotifications()''',
    "authorized registerForRemoteNotifications probe"
)

app = replace_once(
    app,
    '''    func requestNotificationTokenInvalidation() {
        UIApplication.shared.unregisterForRemoteNotifications()
        DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + 1.0, execute: {
            UIApplication.shared.registerForRemoteNotifications()
        })
    }''',
    '''    func requestNotificationTokenInvalidation() {
        ghostBaseV10EPushRecord("requestNotificationTokenInvalidation")
        UIApplication.shared.unregisterForRemoteNotifications()
        DispatchQueue.main.asyncAfter(deadline: DispatchTime.now() + 1.0, execute: {
            ghostBaseV10EPushRecord("invalidationRegisterForRemoteNotifications")
            UIApplication.shared.registerForRemoteNotifications()
        })
    }''',
    "requestNotificationTokenInvalidation probe"
)

write(app_p, app)

app = read(app_p)

app = replace_once(
    app,
    '''            guard var encryptedPayload = payload.dictionaryPayload["p"] as? String else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "encryptedPayload is nil")
                completion()
                return
            }''',
    '''            guard var encryptedPayload = payload.dictionaryPayload["p"] as? String else {
                ghostBaseV10EPushRecord("pushRegistryEncryptedPayloadNil")
                ghostBaseV10EPushSet("LastPushRegistryKeys", payload.dictionaryPayload.keys.map { "\\($0)" }.sorted().joined(separator: ","))
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "encryptedPayload is nil")
                completion()
                return
            }
            ghostBaseV10EPushRecord("pushRegistryEncryptedPayload")
            ghostBaseV10EPushSet("LastPushRegistryKeys", payload.dictionaryPayload.keys.map { "\\($0)" }.sorted().joined(separator: ","))''',
    "PushRegistry encrypted payload probe"
)

app = replace_once(
    app,
    '''            guard let payloadData = Data(base64Encoded: encryptedPayload) else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decode encryptedPayload")
                completion()
                return
            }''',
    '''            guard let payloadData = Data(base64Encoded: encryptedPayload) else {
                ghostBaseV10EPushRecord("pushRegistryBase64Failed")
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decode encryptedPayload")
                completion()
                return
            }''',
    "PushRegistry base64 failed probe"
)

app = replace_once(
    app,
    '''            guard let keyId = notificationPayloadKeyId(data: payloadData) else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't parse payload key id")
                completion()
                return
            }''',
    '''            guard let keyId = notificationPayloadKeyId(data: payloadData) else {
                ghostBaseV10EPushRecord("pushRegistryKeyIdFailed")
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't parse payload key id")
                completion()
                return
            }
            ghostBaseV10EPushRecord("pushRegistryKeyId")''',
    "PushRegistry key id probe"
)

write(app_p, app)

app = read(app_p)

app = replace_once(
    app,
    '''            guard let accountId = maybeAccountId, let notificationKey = maybeNotificationKey else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "accountId or notificationKey is nil")
                completion()
                return
            }''',
    '''            guard let accountId = maybeAccountId, let notificationKey = maybeNotificationKey else {
                ghostBaseV10EPushRecord("pushRegistryNotificationKeyMissing")
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "accountId or notificationKey is nil")
                completion()
                return
            }
            ghostBaseV10EPushRecord("pushRegistryNotificationKeyFound")''',
    "PushRegistry notification key probe"
)

app = replace_once(
    app,
    '''            guard let decryptedPayload = decryptedNotificationPayload(key: notificationKey, data: payloadData) else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decrypt payload")
                completion()
                return
            }''',
    '''            guard let decryptedPayload = decryptedNotificationPayload(key: notificationKey, data: payloadData) else {
                ghostBaseV10EPushRecord("pushRegistryDecryptFailed")
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decrypt payload")
                completion()
                return
            }
            ghostBaseV10EPushRecord("pushRegistryDecryptedPayload")''',
    "PushRegistry decrypted payload probe"
)

app = replace_once(
    app,
    '''            guard let payloadJson = try? JSONSerialization.jsonObject(with: decryptedPayload, options: []) as? [AnyHashable: Any] else {
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decode payload json")
                completion()
                return
            }
            
            decryptedPayloadAndAccountId = (payloadJson, accountId)''',
    '''            guard let payloadJson = try? JSONSerialization.jsonObject(with: decryptedPayload, options: []) as? [AnyHashable: Any] else {
                ghostBaseV10EPushRecord("pushRegistryJsonFailed")
                Logger.shared.log("App \\(self.episodeId) PushRegistry", "Couldn't decode payload json")
                completion()
                return
            }
            ghostBaseV10EPushRecord("pushRegistryJson")
            ghostBaseV10EPushSet("LastPushRegistryPayloadKeys", payloadJson.keys.map { "\\($0)" }.sorted().joined(separator: ","))
            if payloadJson["msg_id"] != nil {
                ghostBaseV10EPushRecord("pushRegistryMsgId")
            }
            
            decryptedPayloadAndAccountId = (payloadJson, accountId)''',
    "PushRegistry payload json probe"
)

write(app_p, app)

reg_p = SRC / "submodules/TelegramCore/Sources/TelegramEngine/AccountData/RegisterNotificationToken.swift"
reg = read(reg_p)

if "// MARK: GhostBase v1.0E RegisterDevice Probe" not in reg:
    helper = r'''
// MARK: GhostBase v1.0E RegisterDevice Probe
private func ghostBaseV10EPushRecord(_ name: String, amount: Int = 1) {
    guard amount > 0 else {
        return
    }
    let defaults = UserDefaults.standard
    let prefix = "GhostBase.V10E.Push."
    let key = prefix + name + ".Count"
    defaults.set(defaults.integer(forKey: key) + amount, forKey: key)
    defaults.set(defaults.integer(forKey: prefix + "Total") + amount, forKey: prefix + "Total")
    defaults.set(name, forKey: prefix + "Last")
    defaults.set(amount, forKey: prefix + "LastAmount")
    defaults.set(Int(Date().timeIntervalSince1970), forKey: prefix + "LastTime")
}

private func ghostBaseV10EPushSet(_ key: String, _ value: String) {
    UserDefaults.standard.set(value, forKey: "GhostBase.V10E.Push." + key)
}
'''
    lines = reg.splitlines()
    last_import = -1
    for i, line in enumerate(lines[:50]):
        if line.startswith("import "):
            last_import = i
    if last_import < 0:
        raise SystemExit("[v1.0E] ERROR: RegisterNotificationToken import block not found")
    lines.insert(last_import + 1, helper)
    reg = "\n".join(lines) + "\n"

write(reg_p, reg)

reg = read(reg_p)

reg = replace_once(
    reg,
    '''func _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {
    return masterNotificationsKey(account: account, ignoreDisabled: false)''',
    '''func _internal_registerNotificationToken(account: Account, token: Data, type: NotificationTokenType, sandbox: Bool, otherAccountUserIds: [PeerId.Id], excludeMutedChats: Bool) -> Signal<Bool, NoError> {
    ghostBaseV10EPushRecord("registerDeviceEntry")
    ghostBaseV10EPushSet("LastRegisterDeviceSandbox", sandbox ? "true" : "false")
    ghostBaseV10EPushSet("LastRegisterDeviceTokenLength", "\\(token.count)")
    return masterNotificationsKey(account: account, ignoreDisabled: false)''',
    "registerDevice entry probe"
)

reg = replace_once(
    reg,
    '''        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
        |> map { _ -> Bool in
            return true
        }
        |> `catch` { error -> Signal<Bool, NoError> in
            if error.errorDescription == "TOKEN_WAS_INVALIDATED" {
                return .single(false)
            } else {
                return .single(true)
            }
        }''',
    '''        ghostBaseV10EPushRecord("registerDeviceRequest")
        ghostBaseV10EPushSet("LastRegisterDeviceType", "\\(mappedType)")
        ghostBaseV10EPushSet("LastRegisterDeviceSecretLength", "\\(keyData.count)")
        return account.network.request(Api.functions.account.registerDevice(flags: flags, tokenType: mappedType, token: hexString(token), appSandbox: sandbox ? .boolTrue : .boolFalse, secret: Buffer(data: keyData), otherUids: otherAccountUserIds.map({ $0._internalGetInt64Value() })))
        |> map { _ -> Bool in
            ghostBaseV10EPushRecord("registerDeviceSuccess")
            return true
        }
        |> `catch` { error -> Signal<Bool, NoError> in
            ghostBaseV10EPushSet("LastRegisterDeviceError", error.errorDescription)
            if error.errorDescription == "TOKEN_WAS_INVALIDATED" {
                ghostBaseV10EPushRecord("registerDeviceInvalidated")
                return .single(false)
            } else {
                ghostBaseV10EPushRecord("registerDeviceError")
                return .single(true)
            }
        }''',
    "registerDevice request/result probe"
)

write(reg_p, reg)

settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
settings = read(settings_p)

anchor = '''    let ghostBaseNsePrefix = "GhostBase.V10D.NSE."'''

ui = r'''    let ghostBasePushPrefix = "GhostBase.V10E.Push."
    let ghostBasePushDefaults = UserDefaults.standard

    entries.append(.info(debug, """
Main Push Registration Probe:
Total: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "Total"))
Last: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "Last") ?? "none") x\(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "LastAmount")) @ \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "LastTime"))
settingsRead: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "notificationSettingsRead.Count"))
authTrue: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "requestAuthorizationTrue.Count"))
authFalse: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "requestAuthorizationFalse.Count"))
authorizedRegister: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "authorizedRegisterForRemoteNotifications.Count"))
invalidationRegister: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "invalidationRegisterForRemoteNotifications.Count"))
didRegisterToken: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "didRegisterDeviceToken.Count"))
didFailToken: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "didFailRegisterDeviceToken.Count"))
registerDeviceEntry: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "registerDeviceEntry.Count"))
registerDeviceRequest: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "registerDeviceRequest.Count"))
registerDeviceSuccess: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "registerDeviceSuccess.Count"))
registerDeviceInvalidated: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "registerDeviceInvalidated.Count"))
registerDeviceError: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "registerDeviceError.Count"))
didReceiveRemote: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "didReceiveRemoteNotification.Count"))
remoteEncryptedPayload: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "remoteEncryptedPayload.Count"))
pushRegistryEncrypted: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryEncryptedPayload.Count"))
pushRegistryKeyId: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryKeyId.Count"))
pushRegistryKeyFound: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryNotificationKeyFound.Count"))
pushRegistryDecryptFailed: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryDecryptFailed.Count"))
pushRegistryDecrypted: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryDecryptedPayload.Count"))
pushRegistryJson: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryJson.Count"))
pushRegistryMsgId: \(ghostBasePushDefaults.integer(forKey: ghostBasePushPrefix + "pushRegistryMsgId.Count"))
LastAuthorizationStatus: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastAuthorizationStatus") ?? "none")
LastRegisterFail: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastRegisterFail") ?? "none")
LastRegisterDeviceType: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastRegisterDeviceType") ?? "none")
LastRegisterDeviceSandbox: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastRegisterDeviceSandbox") ?? "none")
LastRegisterDeviceError: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastRegisterDeviceError") ?? "none")
LastUserInfoKeys: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastUserInfoKeys") ?? "none")
LastAPSKeys: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastAPSKeys") ?? "none")
LastPushRegistryKeys: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastPushRegistryKeys") ?? "none")
LastPushRegistryPayloadKeys: \(ghostBasePushDefaults.string(forKey: ghostBasePushPrefix + "LastPushRegistryPayloadKeys") ?? "none")
Public main-app path: YES
NSE required: NO
"""))

'''

settings = replace_once(settings, anchor, ui + anchor, "settings Main Push Probe UI")
settings = re.sub(r"Version: v[0-9A-Za-z.\-]+", "Version: v1.0E", settings, count=1)

write(settings_p, settings)

app = read(app_p)
reg = read(reg_p)
settings = read(settings_p)

ensure(app, "GhostBase v1.0E Main Push Probe", "AppDelegate helper")
ensure(app, 'ghostBaseV10EPushRecord("didRegisterDeviceToken")', "didRegister probe")
ensure(app, 'ghostBaseV10EPushRecord("didFailRegisterDeviceToken")', "didFail probe")
ensure(app, 'ghostBaseV10EPushRecord("didReceiveRemoteNotification")', "didReceiveRemote probe")
ensure(app, '"requestAuthorizationTrue"', "requestAuthorization true probe")
ensure(app, '"requestAuthorizationFalse"', "requestAuthorization false probe")
ensure(app, 'ghostBaseV10EPushRecord("pushRegistryDecryptedPayload")', "PushRegistry decrypt probe")
ensure(reg, "GhostBase v1.0E RegisterDevice Probe", "RegisterDevice helper")
ensure(reg, 'ghostBaseV10EPushRecord("registerDeviceRequest")', "registerDevice request")
ensure(reg, 'ghostBaseV10EPushRecord("registerDeviceSuccess")', "registerDevice success")
ensure(settings, "Main Push Registration Probe:", "settings push probe")
ensure(settings, "Public main-app path: YES", "settings public path")
ensure(settings, "Version: v1.0E", "settings v1.0E")

print("[v1.0E] GhostBase Main Push Registration Probe patch OK")
