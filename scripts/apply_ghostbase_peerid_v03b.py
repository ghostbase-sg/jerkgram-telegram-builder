from pathlib import Path
import re
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_settings_v03a.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    candidates = [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]
    for c in candidates:
        if (c / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()
ROOT = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"

profile_p = ROOT / "PeerInfoProfileItems.swift"
gb_screen_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

if not profile_p.exists():
    raise SystemExit(f"missing file: {profile_p}")
if not gb_screen_p.exists():
    raise SystemExit(f"missing file: {gb_screen_p}")

gb = gb_screen_p.read_text()
gb = gb.replace("Version: v0.3A", "Version: v0.3B")
gb = gb.replace(
    "GhostBase diagnostics screen. Toggles and runtime modules will be added in later builds.",
    "GhostBase diagnostics screen. PeerInfo ID card is enabled in v0.3B. Toggles and runtime modules will be added in later builds."
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

block = '''
    // MARK: GhostBase v0.3B peer id card
    do {
        var ghostBasePeerIdText = ""

        if let user = data.peer as? TelegramUser {
            ghostBasePeerIdText = String(user.id.id._internalGetInt64Value())
        } else if let channel = data.peer as? TelegramChannel {
            ghostBasePeerIdText = "-100" + String(channel.id.id._internalGetInt64Value())
        } else if let group = data.peer as? TelegramGroup {
            ghostBasePeerIdText = String(group.id.id._internalGetInt64Value())
        } else if let peer = data.peer {
            ghostBasePeerIdText = String(peer.id.id._internalGetInt64Value())
        }

        if !ghostBasePeerIdText.isEmpty {
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: 990000, label: "id: \\(ghostBasePeerIdText)", text: "", textColor: .primary, action: nil, longTapAction: { sourceNode in
                interaction.openPeerInfoContextMenu(.copy(ghostBasePeerIdText), sourceNode, nil)
            }, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
        }

        var ghostBaseDcText = ""
        if let peer = data.peer, let smallProfileImage = peer.smallProfileImage, let cloudResource = smallProfileImage.resource as? CloudPeerPhotoSizeMediaResource {
            ghostBaseDcText = String(cloudResource.datacenterId)
        }

        if !ghostBaseDcText.isEmpty {
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: 990001, label: "dc: \\(ghostBaseDcText)", text: "", textColor: .primary, action: nil, longTapAction: { sourceNode in
                interaction.openPeerInfoContextMenu(.copy(ghostBaseDcText), sourceNode, nil)
            }, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
        }
    }

'''

if "GhostBase v0.3B peer id card" not in s:
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

checks = [
    ("ghostbase section", "case ghostbase" in profile),
    ("ghostbase card block", "GhostBase v0.3B peer id card" in profile),
    ("id card", 'label: "id: \\(ghostBasePeerIdText)"' in profile),
    ("dc card", 'label: "dc: \\(ghostBaseDcText)"' in profile),
    ("screen v0.3B", "Version: v0.3B" in gb),
    ("screen note", "PeerInfo ID card is enabled in v0.3B" in gb),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase PeerInfo ID Card v0.3B patch OK")
