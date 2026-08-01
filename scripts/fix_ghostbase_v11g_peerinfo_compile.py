#!/usr/bin/env python3

import os
from pathlib import Path


SOURCE_ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

PEER_ROOT = (
    SOURCE_ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)

BACKGROUND = PEER_ROOT / "GhostBaseProfileFullscreenBackground.swift"
REPORT = PEER_ROOT / "GhostBaseProfileReportPaneNode.swift"


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)

    if count == 1:
        return text.replace(old, new, 1)

    if count == 0 and new in text:
        print(f"[V11G PEERINFO FIX] already repaired: {label}")
        return text

    raise RuntimeError(
        f"{label}: expected one old anchor, found {count}"
    )


# ------------------------------------------------------------
# 1. Give SwiftSignalKit.deferred an explicit generic type.
# ------------------------------------------------------------
background = BACKGROUND.read_text(encoding="utf-8")

background = replace_once(
    background,
    "            self.sourceDisposable.set((deferred {\n"
    "                guard let image = Self.generatedGradientImage(\n",
    "            self.sourceDisposable.set((deferred { "
    "() -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> in\n"
    "                guard let image = Self.generatedGradientImage(\n",
    "premium gradient deferred signal type",
)

BACKGROUND.write_text(background, encoding="utf-8")

print(
    "[V11G PEERINFO FIX] fixed premium gradient "
    "deferred signal type"
)


# ------------------------------------------------------------
# 2. CachedPeerData and CachedUserData live in Postbox.
# ------------------------------------------------------------
report = REPORT.read_text(encoding="utf-8")

if "import Postbox\n" not in report:
    anchor = "import SwiftSignalKit\n"

    if report.count(anchor) != 1:
        raise RuntimeError(
            "GhostBaseProfileReportPaneNode SwiftSignalKit "
            f"import count={report.count(anchor)}"
        )

    report = report.replace(
        anchor,
        anchor + "import Postbox\n",
        1,
    )

    print(
        "[V11G PEERINFO FIX] added Postbox import "
        "for CachedPeerData"
    )
else:
    print(
        "[V11G PEERINFO FIX] Postbox import already present"
    )

REPORT.write_text(report, encoding="utf-8")


# ------------------------------------------------------------
# 3. Exact final checks.
# ------------------------------------------------------------
background_check = BACKGROUND.read_text(encoding="utf-8")
report_check = REPORT.read_text(encoding="utf-8")

required_signal = (
    "deferred { () -> "
    "Signal<GhostBaseProfileBackgroundCacheEntry?, NoError> in"
)

if background_check.count(required_signal) != 1:
    raise RuntimeError(
        "typed premium gradient deferred count="
        f"{background_check.count(required_signal)}"
    )

if report_check.count("import Postbox\n") != 1:
    raise RuntimeError(
        "Postbox import count="
        f"{report_check.count('import Postbox\\n')}"
    )

print("[V11G PEERINFO FIX] PeerInfo compile repair OK")
