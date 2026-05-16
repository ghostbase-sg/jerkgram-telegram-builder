from pathlib import Path
import re
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_peerid_v03b.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()
profile_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
gb_screen_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

if not profile_p.exists():
    raise SystemExit(f"missing file: {profile_p}")
if not gb_screen_p.exists():
    raise SystemExit(f"missing file: {gb_screen_p}")

gb = gb_screen_p.read_text()
gb = gb.replace("Version: v0.3B", "Version: v0.3C")
gb = gb.replace("Version: v0.3A", "Version: v0.3C")
gb = gb.replace(
    "GhostBase diagnostics screen. PeerInfo ID card is enabled in v0.3B. Toggles and runtime modules will be added in later builds.",
    "GhostBase diagnostics screen. PeerInfo Metrics Card is enabled in v0.3C. Toggles and runtime modules will be added in later builds."
)
gb = gb.replace(
    "GhostBase diagnostics screen. Toggles and runtime modules will be added in later builds.",
    "GhostBase diagnostics screen. PeerInfo Metrics Card is enabled in v0.3C. Toggles and runtime modules will be added in later builds."
)
gb_screen_p.write_text(gb)
print("patched", gb_screen_p)

s = profile_p.read_text()

if "case ghostbase" not in s:
    s = re.sub(
        r"(enum InfoSection: Int, CaseIterable \{\n)",
        r"\1    case ghostbase\n",
        s,
        count=1
    )

if "case ghostbase" not in s:
    raise SystemExit("failed to add InfoSection.ghostbase")

for marker in [
    "    // MARK: GhostBase v0.3C peer metrics card\n",
    "    // MARK: GhostBase v0.3B peer id card\n",
]:
    while marker in s:
        start = s.index(marker)
        end = s.index("    let bioContextAction:", start)
        s = s[:start] + s[end:]

block = '''
    // MARK: GhostBase v0.3C peer metrics card
    do {
        var ghostBaseItemId = 990000
        var ghostBasePeerIdText = ""

        if let peer = data.peer {
            if case let .channel(channel) = peer {
                ghostBasePeerIdText = "-100" + String(channel.id.id._internalGetInt64Value())
            } else {
                ghostBasePeerIdText = String(peer.id.id._internalGetInt64Value())
            }
        }

        if !ghostBasePeerIdText.isEmpty {
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "id: \\(ghostBasePeerIdText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
            ghostBaseItemId += 1
        }

        if let peer = data.peer, let smallProfileImage = peer.smallProfileImage, let cloudResource = smallProfileImage.resource as? CloudPeerPhotoSizeMediaResource {
            let ghostBaseDcText = String(cloudResource.datacenterId)
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "dc: \\(ghostBaseDcText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
            ghostBaseItemId += 1
        }

        var ghostBaseRegDateString = ""
        if let cachedData = data.cachedData as? CachedUserData, let registrationDate = cachedData.peerStatusSettings?.registrationDate {
            let components = registrationDate.components(separatedBy: ".")
            if components.count == 2, let first = Int32(components[0]), let second = Int32(components[1]) {
                let month = first - 1
                let year = second - 1900
                ghostBaseRegDateString = stringForMonth(strings: presentationData.strings, month: month, ofYear: year)
            }
        }

        if !ghostBaseRegDateString.isEmpty {
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "registered:", text: ghostBaseRegDateString, textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
            ghostBaseItemId += 1
        }
    }

'''

needle = '''    for section in InfoSection.allCases {
        items[section] = []
    }
'''

if needle not in s:
    raise SystemExit("items init insertion point not found")

s = s.replace(needle, needle + block, 1)
profile_p.write_text(s)
print("patched", profile_p)

profile = profile_p.read_text()
gb = gb_screen_p.read_text()

marker = "    // MARK: GhostBase v0.3C peer metrics card\n"
end_marker = "    let bioContextAction:"

if marker not in profile:
    raise SystemExit("GhostBase v0.3C block marker missing")

start = profile.index(marker)
end = profile.index(end_marker, start)
block = profile[start:end]

for forbidden in [
    "data.channelCreationTimestamp",
    "data.regDate",
    "data.peer as? TelegramUser",
    "data.peer as? TelegramChannel",
    "data.peer as? TelegramGroup",
    "openPeerInfoContextMenu(.copy",
]:
    if forbidden in block:
        raise SystemExit("FORBIDDEN in GhostBase block: " + forbidden)

checks = [
    ("ghostbase section", "case ghostbase" in profile),
    ("v0.3C block", "GhostBase v0.3C peer metrics card" in block),
    ("channel -100", '"-100" + String(channel.id.id._internalGetInt64Value())' in block),
    ("id row", 'label: "id: \\(ghostBasePeerIdText)"' in block),
    ("dc row", 'label: "dc: \\(ghostBaseDcText)"' in block),
    ("registered row", 'label: "registered:"' in block),
    ("no created row", 'label: "created:"' not in block),
    ("screen v0.3C", "Version: v0.3C" in gb),
    ("screen note", "PeerInfo Metrics Card is enabled in v0.3C" in gb),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase PeerInfo Metrics Card v0.3C patch OK")
