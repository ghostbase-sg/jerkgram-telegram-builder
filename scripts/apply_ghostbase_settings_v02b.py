from pathlib import Path
import re

GROUP = "group.4a348a9b186b700c.1"

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
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()
ROOT = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"

screen = ROOT / "PeerInfoScreen.swift"
items = ROOT / "PeerInfoSettingsItems.swift"
actions = ROOT / "PeerInfoScreenSettingsActions.swift"

for p in (screen, items, actions):
    if not p.exists():
        raise SystemExit(f"missing: {p}")

def save(p, s):
    old = p.read_text()
    if s != old:
        p.write_text(s)
        print("patched", p)

# PeerInfoSettingsSection: add .ghostbase
s = screen.read_text()
if "case ghostbase" not in s:
    if "    case swiftgramPro\n" in s:
        s = s.replace(
            "    case swiftgramPro\n",
            "    case swiftgramPro\n    case ghostbase\n",
            1
        )
    elif "    case avatar\n" in s:
        s = s.replace(
            "    case avatar\n",
            "    case ghostbase\n    case avatar\n",
            1
        )
    else:
        raise SystemExit("PeerInfoSettingsSection insertion point not found")
save(screen, s)

# SettingsSection: separate block under My Profile
s = items.read_text()

if "case ghostbase" not in s:
    s = s.replace(
        "    case myProfile\n    case proxy\n",
        "    case myProfile\n    case ghostbase\n    case proxy\n",
        1
    )

# remove old GhostBase from advanced block
lines = s.splitlines(True)
out = []
i = 0
while i < len(lines):
    window = "".join(lines[i:i + 16])
    if "items[.advanced]!.append(PeerInfoScreenDisclosureItem" in lines[i] and 'text: "GhostBase"' in window:
        while i < len(lines):
            if '}))' in lines[i]:
                i += 1
                break
            i += 1
        continue
    out.append(lines[i])
    i += 1
s = "".join(out)

ghostbase = """
    items[.ghostbase]!.append(PeerInfoScreenDisclosureItem(id: 0, text: "GhostBase", icon: PresentationResourcesSettings.security, action: {
        interaction.openSettings(.ghostbase)
    }))
"""

if "items[.ghostbase]!.append" not in s:
    pattern = r'    items\[\.myProfile\]!\.append\(PeerInfoScreenDisclosureItem\(id: 0,[\s\S]*?interaction\.openSettings\(\.profile\)[\s\S]*?\}\)\)\n'
    m = re.search(pattern, s)
    if not m:
        raise SystemExit("myProfile regex insertion point not found")
    s = s[:m.end()] + ghostbase + s[m.end():]

save(items, s)

def replace_case(src, name, body):
    lines = src.splitlines(True)
    start = None

    for i, line in enumerate(lines):
        if line.strip() == f"case .{name}:":
            start = i
            break

    if start is None:
        return src, False

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("        case ."):
            end = j
            break

    replacement = [f"        case .{name}:\n"] + body.splitlines(True)
    return "".join(lines[:start] + replacement + lines[end:]), True


s = actions.read_text()

appearance_body = '''            push(themeSettingsController(context: self.context))
'''

ghostbase_body = f'''            let accountId = self.context.account.peerId.id._internalGetInt64Value()
            let bundleId = Bundle.main.bundleIdentifier ?? "unknown"
            let appGroup = "{GROUP}"
            let text = "Telegram ID: \\(accountId)\\nBundle ID: \\(bundleId)\\nAppGroup: \\(appGroup)\\nBase: Official Telegram 12.7\\nKeychainFix: sideloadKeychainFix.dylib"
            self.controller?.present(textAlertController(context: self.context, updatedPresentationData: self.controller?.updatedPresentationData, title: "GhostBase", text: text, actions: [
                TextAlertAction(type: .defaultAction, title: "OK", action: {{}})
            ]), in: .window(.root))
'''

s, ok = replace_case(s, "appearance", appearance_body)
if not ok:
    raise SystemExit("case .appearance not found")

s, ok = replace_case(s, "ghostbase", ghostbase_body)
if not ok:
    anchor = "        case .avatar:\n"
    if anchor not in s:
        raise SystemExit("case .avatar insertion point not found")
    s = s.replace(anchor, "        case .ghostbase:\n" + ghostbase_body + anchor, 1)

save(actions, s)

screen_s = screen.read_text()
items_s = items.read_text()
actions_s = actions.read_text()

checks = [
    ("screen case ghostbase", "case ghostbase" in screen_s),
    ("section case ghostbase", "case ghostbase" in items_s),
    ("items ghostbase", "items[.ghostbase]!.append" in items_s),
    ("open ghostbase", "openSettings(.ghostbase)" in items_s),
    ("action ghostbase", "case .ghostbase:" in actions_s),
    ("appearance restored", "case .appearance:\n            push(themeSettingsController(context: self.context))" in actions_s),
    ("no smoke", "GhostBase Appearance Smoke Test" not in actions_s),
    ("telegram id", "Telegram ID:" in actions_s),
    ("keychainfix", "KeychainFix: sideloadKeychainFix.dylib" in actions_s),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

if re.search(r'items\[\.advanced\]!\.append\(PeerInfoScreenDisclosureItem[\s\S]{0,500}text: "GhostBase"', items_s):
    raise SystemExit("GhostBase still in advanced")

print("GhostBase Settings v0.2B patch OK")
