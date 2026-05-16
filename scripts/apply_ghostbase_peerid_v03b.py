from pathlib import Path
import re
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_settings_v03a.py")))

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

# Add a separate GhostBase card section.
if "case ghostbase" not in s:
    s = re.sub(
        r"(enum InfoSection: Int, CaseIterable \{\n)",
        r"\1    case ghostbase\n",
        s,
        count=1
    )

if "case ghostbase" not in s:
    raise SystemExit("failed to add InfoSection.ghostbase")

# Remove old broken GhostBase block if it exists.
marker = "    // MARK: GhostBase v0.3B peer id card\n"
if marker in s:
    block_start = s.index(marker)
    block_end_marker = "    let bioContextAction:"
    block_end = s.index(block_end_marker, block_start)
    s = s[:block_start] + s[block_end:]

block = '''
    // MARK: GhostBase v0.3B peer id card
    do {
        if let peer = data.peer {
            let ghostBasePeerIdText = String(peer.id.id._internalGetInt64Value())
            items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: 990000, label: "id: \\(ghostBasePeerIdText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                interaction.requestLayout(false)
            }))
        }
    }

'''

needle = '''    for section in InfoSection.allCases {
        items[section] = []
    }
'''

if needle not in s:
    raise SystemExit("items init insertion point not found")

if "GhostBase v0.3B peer id card" not in s:
    s = s.replace(needle, needle + block, 1)

profile_p.write_text(s)
print("patched", profile_p)

profile = profile_p.read_text()
gb = gb_screen_p.read_text()

marker = "    // MARK: GhostBase v0.3B peer id card\n"
end_marker = "    let bioContextAction:"
if marker not in profile:
    raise SystemExit("GhostBase block marker missing")
block_start = profile.index(marker)
block_end = profile.index(end_marker, block_start)
ghostbase_block = profile[block_start:block_end]

checks = [
    ("ghostbase section", "case ghostbase" in profile),
    ("ghostbase id block", "GhostBase v0.3B peer id card" in ghostbase_block),
    ("id card", 'label: "id: \\(ghostBasePeerIdText)"' in ghostbase_block),
    ("no invalid TelegramUser cast in GhostBase block", "data.peer as? TelegramUser" not in ghostbase_block),
    ("no invalid TelegramChannel cast in GhostBase block", "data.peer as? TelegramChannel" not in ghostbase_block),
    ("no invalid TelegramGroup cast in GhostBase block", "data.peer as? TelegramGroup" not in ghostbase_block),
    ("no unavailable copy context in GhostBase block", "openPeerInfoContextMenu(.copy" not in ghostbase_block),
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
