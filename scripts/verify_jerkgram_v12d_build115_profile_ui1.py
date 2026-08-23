#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import os

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))).resolve()
BUILDER = Path(__file__).resolve().parent.parent
APPLY = BUILDER / "scripts/apply_jerkgram_v12d_build115_profile_ui1.py"
PEER = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
DATA = PEER / "PeerInfoData.swift"
PANE = PEER / "PeerInfoPaneContainerNode.swift"
LINKS = PEER / "Panes/PeerInfoListPaneNode.swift"
REPORT = PEER / "GhostBaseProfileReportPaneNode.swift"
SCREEN = PEER / "PeerInfoScreen.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build115 profile UI] " + message)


def alpha(luminance):
    lightness = max(0.0, min(1.0, (luminance - 0.55) / 0.45))
    return 0.26 * lightness


require(alpha(0.20) == 0.0, "dark source must remain transparent")
require(alpha(0.55) == 0.0, "threshold source must remain transparent")
require(abs(alpha(0.775) - 0.13) < 0.000001, "mid source alpha mismatch")
require(abs(alpha(1.0) - 0.26) < 0.000001, "bright source alpha mismatch")

require(APPLY.is_file(), "apply script missing")
spec = importlib.util.spec_from_file_location("build115_profile_ui", APPLY)
require(spec is not None and spec.loader is not None, "cannot load apply module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

for path in (DATA, PANE, LINKS, REPORT, SCREEN):
    require(path.is_file(), "owner missing: " + str(path))

data = DATA.read_text(encoding="utf-8")
require(data.count(module.PROFILE_MARKER) == 1, "profile marker count != 1")
start = data.index("private func ghostBaseAppendingProfilePanes(")
end = data.index("\n}\n", start) + 3
policy = data[start:end]
require("return availablePanes" in policy, "stock pane return missing")
for token in ("ghostBaseProfileHistory", "ghostBasePresence", "ghostBaseGiftHistory", "ghostBasePersonalChannel", "result.append("):
    require(token not in policy, "raw research pane still published: " + token)

report = REPORT.read_text(encoding="utf-8")
screen = SCREEN.read_text(encoding="utf-8")
require("GhostBaseObservedProfileHistoryV11G" in report, "profile history storage lost")
require("profileReport" in report, "profile report core lost")
require("ghostBaseRecordObservedProfileV11G" in screen, "profile observation call lost")

pane = PANE.read_text(encoding="utf-8")
require(pane.count(module.OUTER_MARKER) == 1, "outer marker count != 1")
out = pane[pane.index(module.OUTER_MARKER):pane.index(module.OUTER_MARKER) + 900]
require("self.backgroundColor = .clear" in out, "outer pane not clear")
require("0.26 * lightness" not in out, "outer duplicate scrim survived")

links = LINKS.read_text(encoding="utf-8")
require(links.count(module.LIST_MARKER) == 2, "Links marker count != 2")
for token in (
    "private let jerkgramLinksReadabilityEnabled: Bool",
    "self.jerkgramLinksReadabilityEnabled = tagMask == .webPage",
    module.LUMINANCE_KEY,
    "(CGFloat(luminance) - 0.55) / 0.45",
    "0.26 * lightness",
    "self.backgroundColor = readabilityColor",
    "self.listNode.backgroundColor = readabilityColor",
):
    require(token in links, "Links owner token missing: " + token)

print("[verify Build115 profile UI] GREEN")
print("[verify Build115 profile UI] raw profile research panes hidden")
print("[verify Build115 profile UI] history/observation core retained")
print("[verify Build115 profile UI] Links owner = PeerInfoListPaneNode")
print("[verify Build115 profile UI] Links alpha dark=0 bright<=0.26")
