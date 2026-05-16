from pathlib import Path
import runpy

# Apply v0.3A baseline first.
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

screen_p = ROOT / "PeerInfoScreen.swift"
profile_p = ROOT / "PeerInfoProfileItems.swift"

for p in (screen_p, profile_p):
    if not p.exists():
        raise SystemExit(f"missing file: {p}")

s = screen_p.read_text()

s = s.replace(
    "private(set) var showProfileId: Bool = SGSimpleSettings.shared.showProfileId // MARK: Swiftgram",
    "private(set) var showProfileId: Bool = true // MARK: GhostBase v0.3B always show peer IDs"
)

s = s.replace(
    "strongSelf.showProfileId = SGSimpleSettings.shared.showProfileId",
    "strongSelf.showProfileId = true // MARK: GhostBase v0.3B always show peer IDs"
)

screen_p.write_text(s)
print("patched", screen_p)

s = profile_p.read_text()

s = s.replace(
    "if SGSimpleSettings.shared.showDC {",
    "if true { // MARK: GhostBase v0.3B always show DC"
)

s = s.replace(
    "if SGSimpleSettings.shared.showCreationDate {",
    "if true { // MARK: GhostBase v0.3B always show creation date"
)

s = s.replace(
    "if SGSimpleSettings.shared.showRegDate {",
    "if true { // MARK: GhostBase v0.3B always show registration date"
)

profile_p.write_text(s)
print("patched", profile_p)

screen = screen_p.read_text()
profile = profile_p.read_text()

checks = [
    ("showProfileId init true", "var showProfileId: Bool = true" in screen),
    ("showProfileId refresh true", "strongSelf.showProfileId = true" in screen),
    ("profile id card exists", 'label: "id: \\(idText)"' in profile),
    ("dc forced", "GhostBase v0.3B always show DC" in profile),
    ("creation forced", "GhostBase v0.3B always show creation date" in profile),
    ("reg forced", "GhostBase v0.3B always show registration date" in profile),
    ("v03a screen still exists", "ghostBaseSettingsController" in (BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text()),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase PeerInfo ID Card v0.3B patch OK")

# Update GhostBase diagnostics screen version for v0.3B
gb_screen_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
gb_screen = gb_screen_p.read_text()
gb_screen = gb_screen.replace("Version: v0.3A", "Version: v0.3B")
gb_screen = gb_screen.replace(
    "GhostBase diagnostics screen. Toggles and runtime modules will be added in later builds.",
    "GhostBase diagnostics screen. PeerInfo ID card is enabled in v0.3B. Toggles and runtime modules will be added in later builds."
)
gb_screen_p.write_text(gb_screen)
print("patched", gb_screen_p)

# Final v0.3B screen verification
gb_screen = gb_screen_p.read_text()
if "Version: v0.3B" not in gb_screen:
    raise SystemExit("GhostBase screen version was not updated to v0.3B")
if "PeerInfo ID card is enabled in v0.3B" not in gb_screen:
    raise SystemExit("GhostBase v0.3B note missing")

print("GhostBase v0.3B screen marker OK")
