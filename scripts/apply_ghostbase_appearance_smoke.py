from pathlib import Path

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [
        cwd / "work/swiftgram-src",
        cwd,
        cwd.parent / "swiftgram-src",
    ]:
        if (c / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources").exists():
            return c
    raise SystemExit(f"cannot find swiftgram-src base from cwd={cwd}")

BASE = find_base()
actions_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"

if not actions_p.exists():
    raise SystemExit(f"missing file: {actions_p}")

s = actions_p.read_text()

old = '''        case .appearance:
            push(themeSettingsController(context: self.context))
'''

new = '''        case .appearance:
            let accountId = self.context.account.peerId.id._internalGetInt64Value()
            let bundleId = Bundle.main.bundleIdentifier ?? "unknown"
            let appGroup = "group.4a348a9b186b700c.1"
            let text = "GhostBase Appearance Smoke Test\\n\\nTelegram ID: \\(accountId)\\nBundle ID: \\(bundleId)\\nAppGroup: \\(appGroup)\\nBase: Official Telegram 12.7\\nKeychainFix: sideloadKeychainFix.dylib"
            self.controller?.present(textAlertController(context: self.context, updatedPresentationData: self.controller?.updatedPresentationData, title: "GhostBase", text: text, actions: [
                TextAlertAction(type: .defaultAction, title: "OK", action: {})
            ]), in: .window(.root))
'''

if "GhostBase Appearance Smoke Test" not in s:
    if old not in s:
        raise SystemExit("appearance action insertion point not found")
    s = s.replace(old, new, 1)
    actions_p.write_text(s)
    print("patched appearance action")
else:
    print("appearance smoke already patched")

s = actions_p.read_text()
for needle in [
    "GhostBase Appearance Smoke Test",
    "Telegram ID:",
    "KeychainFix: sideloadKeychainFix.dylib",
]:
    if needle not in s:
        raise SystemExit(f"verification failed: {needle}")

print(f"GhostBase Appearance smoke patch OK: {actions_p}")
