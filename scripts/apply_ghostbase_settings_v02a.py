from pathlib import Path

def find_base() -> Path:
    cwd = Path.cwd()
    candidates = [
        cwd / "work/swiftgram-src",
        cwd,
        cwd.parent / "swiftgram-src",
    ]
    for c in candidates:
        if (c / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources").exists():
            return c
    raise SystemExit(f"cannot find swiftgram-src base from cwd={cwd}")

BASE = find_base()

items_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift"
actions_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"
screen_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift"

for p in [items_p, actions_p, screen_p]:
    if not p.exists():
        raise SystemExit(f"missing file: {p}")

print(f"GhostBase patch BASE={BASE}")

s = screen_p.read_text()
if "case ghostbase" not in s:
    needle = "    case appearance\n"
    if needle not in s:
        raise SystemExit("PeerInfoSettingsSection insertion point not found")
    s = s.replace(needle, needle + "    case ghostbase\n")
    screen_p.write_text(s)
    print("patched enum case")

s = items_p.read_text()
if "interaction.openSettings(.ghostbase)" not in s:
    needle = '''    items[.advanced]!.append(PeerInfoScreenDisclosureItem(id: 3, text: presentationData.strings.Settings_Appearance, icon: PresentationResourcesSettings.appearance, action: {
        interaction.openSettings(.appearance)
    }))
'''
    insert = needle + '''    items[.advanced]!.append(PeerInfoScreenDisclosureItem(id: 50, text: "GhostBase", icon: PresentationResourcesSettings.security, action: {
        interaction.openSettings(.ghostbase)
    }))
'''
    if needle not in s:
        raise SystemExit("advanced settings insertion point not found")
    s = s.replace(needle, insert)
    items_p.write_text(s)
    print("patched settings row")

s = actions_p.read_text()
if "case .ghostbase:" not in s:
    needle = '''        case .appearance:
            push(themeSettingsController(context: self.context))
'''
    insert = needle + '''        case .ghostbase:
            let accountId = self.context.account.peerId.id._internalGetInt64Value()
            let bundleId = Bundle.main.bundleIdentifier ?? "unknown"
            let appGroup = "group.4a348a9b186b700c.1"
            let text = "Telegram ID: \\(accountId)\\nBundle ID: \\(bundleId)\\nAppGroup: \\(appGroup)\\nBase: Official Telegram 12.7\\nKeychainFix: sideloadKeychainFix.dylib"
            self.controller?.present(textAlertController(context: self.context, updatedPresentationData: self.controller?.updatedPresentationData, title: "GhostBase", text: text, actions: [
                TextAlertAction(type: .defaultAction, title: self.presentationData.strings.Common_OK, action: {})
            ]), in: .window(.root))
'''
    if needle not in s:
        raise SystemExit("settings action insertion point not found")
    s = s.replace(needle, insert)
    actions_p.write_text(s)
    print("patched settings action")

checks = [
    (screen_p, "case ghostbase"),
    (items_p, "interaction.openSettings(.ghostbase)"),
    (items_p, '"GhostBase"'),
    (actions_p, "case .ghostbase:"),
    (actions_p, "Telegram ID:"),
    (actions_p, "KeychainFix: sideloadKeychainFix.dylib"),
]

for p, needle in checks:
    if needle not in p.read_text():
        raise SystemExit(f"verification failed: {needle} missing in {p}")

print("GhostBase Settings v0.2A patch OK")
