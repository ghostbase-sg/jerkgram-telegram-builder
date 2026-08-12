#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

P = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources"
)

names = [
    "GhostBaseProfileFullscreenBackground.swift",
    "PeerInfoHeaderNode.swift",
    "PeerInfoScreenItemSectionContainerNode.swift",
    "PeerInfoPaneContainerNode.swift",
    "PeerInfoScreen.swift",
    "GhostBaseProfileReportPaneNode.swift",
    "PeerInfoProfileItems.swift",
]

files = {}

for name in names:
    path = P / name

    if not path.is_file():
        raise SystemExit(
            f"[V11I FINAL VERIFY] missing: {path}"
        )

    files[name] = path.read_text(
        encoding="utf-8"
    )


bg = files[
    "GhostBaseProfileFullscreenBackground.swift"
]
header = files[
    "PeerInfoHeaderNode.swift"
]
section = files[
    "PeerInfoScreenItemSectionContainerNode.swift"
]
pane = files[
    "PeerInfoPaneContainerNode.swift"
]
screen = files[
    "PeerInfoScreen.swift"
]
report = files[
    "GhostBaseProfileReportPaneNode.swift"
]
profile = files[
    "PeerInfoProfileItems.swift"
]


errors = []


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        errors.append(
            message
        )


require(
    "GhostBase v1.1I PROFILEFINAL1"
    in bg,
    "final background marker missing",
)

require(
    "cache.countLimit = 20"
    in bg,
    "background cache is not bounded",
)

require(
    "// 3) Premium profile color / gift decoration."
    in bg,
    "Premium source missing",
)

require(
    "// 4) Avatar fallback uses the actual avatar pixels."
    in bg,
    "avatar fallback missing",
)

premium_position = bg.find(
    "// 3) Premium profile color / gift decoration."
)

avatar_position = bg.find(
    "// 4) Avatar fallback uses the actual avatar pixels."
)

require(
    premium_position >= 0
    and avatar_position > premium_position,
    "Premium/avatar source priority is wrong",
)

require(
    ".systemUltraThinMaterialDark"
    in bg
    and ".systemUltraThinMaterialLight"
    in bg,
    "global UltraThin material missing",
)

require(
    "private let imageView: UIImageView"
    in bg,
    "single source UIImageView missing",
)

require(
    "private let blurView: UIVisualEffectView"
    in bg,
    "single persistent blur missing",
)

require(
    "private let tintView: UIView"
    in bg,
    "separate tint layer missing",
)


# Stock Telegram action buttons.
require(
    "GhostBase v1.1H ACTIONGLASS1"
    not in header,
    "V11H custom action material survived",
)

require(
    "let regularContentButtonBackgroundColor: UIColor"
    in header,
    "stock content button declaration missing",
)

require(
    "let regularHeaderButtonBackgroundColor: UIColor"
    in header,
    "stock header button declaration missing",
)


# Known triangle source gone.
require(
    "ghostBaseGlassEffectView"
    not in section,
    "per-section effect still exists",
)

require(
    "UIVisualEffectView("
    not in section,
    "per-section UIVisualEffectView still exists",
)

require(
    "GhostBase v1.1I SECTIONFINAL1"
    in section,
    "final section material missing",
)


# Full profile continuity.
require(
    "GhostBase v1.1I FULLPANEFINAL1"
    in pane,
    "full-pane material missing",
)

require(
    "withAlphaComponent("
    in pane,
    "pane material is not translucent",
)

require(
    "self.paneContainerNode.backgroundColor = .clear"
    not in screen,
    "global pane clear override survived",
)

require(
    "frame: CGRect(origin: .zero, size: layout.size)"
    in screen,
    "fullscreen visual source is not layout-sized",
)


# Detailed histories.
for token in (
    "История изменений профиля",
    "Зафиксировано изменений:",
    "Имя:",
    "Username:",
    "BIO:",
    "Аватар:",
    "Emoji-status:",
    "Старый журнал PROFILEINTEL2",
    "История личного канала",
    "Подписчики:",
    "Ссылка:",
):
    require(
        token in report,
        f"history token missing: {token}",
    )


# Bounded/lazy/async.
require(
    "static let maximumEvents = 200"
    in report,
    "history bound missing",
)

require(
    "self.queue.async"
    in report,
    "async history writer missing",
)

require(
    "if visibleHeight > 0.0"
    in report,
    "lazy report loading missing",
)


# Profile metrics/copy survive.
for token in (
    'label: "Telegram ID"',
    'label: "DC"',
    'label: "Дата регистрации"',
    "UIPasteboard.general.string",
):
    require(
        token in profile,
        f"profile metric missing: {token}",
    )


# Forbidden architecture stays dead.
all_peer = "\n".join(
    path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    for path in P.rglob("*.swift")
)

for token in (
    "PROFILEHUB2",
    "PROFILEHUB4",
    "GhostBaseProfileHubItem",
    "История и сведения",
):
    require(
        token not in all_peer,
        f"forbidden profile architecture returned: {token}",
    )


if errors:
    print(
        "[V11I FINAL VERIFY] FAILED"
    )

    for error in errors:
        print(
            " -",
            error,
        )

    raise SystemExit(1)


print("[V11I FINAL VERIFY] OK")
print("  stock Telegram action buttons preserved")
print("  single fullscreen source/blur/tint retained")
print("  per-section blur/masks removed")
print("  background continues through native panes")
print("  detailed profile history restored")
print("  detailed Personal Channel history restored")
print("  legacy PROFILEINTEL2 preserved")
print("  history remains bounded/lazy/async")
