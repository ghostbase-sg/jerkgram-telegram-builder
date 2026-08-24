#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()

def require(value, message):
    if not value: raise RuntimeError("[verify Build118 glass] " + message)

def main():
    files = [
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift",
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift",
        ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoVisualMediaPaneNode/Sources/PeerInfoVisualMediaPaneNode.swift",
    ]
    for path in files: require(path.is_file(), "missing " + str(path))
    text = "\n".join(path.read_text() for path in files)
    list_source = files[1].read_text()
    visual = files[2].read_text()
    frame_marker = "private final class FrameSequenceThumbnailNode"
    pane_marker = "public final class PeerInfoVisualMediaPaneNode"
    require(frame_marker in visual and pane_marker in visual, "visual class markers missing")
    frame_section = visual[visual.index(frame_marker):visual.index(pane_marker)]
    pane_section = visual[visual.index(pane_marker):]
    require("ghostBaseGlassEnabled" not in frame_section, "FrameSequenceThumbnailNode contaminated by pane flag")
    require("private let ghostBaseGlassEnabled: Bool" in pane_section, "pane flag property missing")
    require("self.ghostBaseGlassEnabled = ghostBaseGlassEnabled" in pane_section, "pane flag assignment missing")
    require("import ComponentFlow\n" in list_source, "ComponentTransition owner import missing from list pane")
    for token in ("BUILD118_GLASS1", "withAlphaComponent(0.075)", "withAlphaComponent(0.035)", "cornerRadius: 16.0", "ghostBaseGlassEnabled"):
        require(token in text, "missing " + token)
    print("[verify Build118 glass] GREEN: reference material and stock fallback present")

if __name__ == "__main__": main()
