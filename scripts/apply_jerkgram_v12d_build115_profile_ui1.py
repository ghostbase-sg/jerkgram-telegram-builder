#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd())
    )
).resolve()

PEER = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources"
)

DATA = PEER / "PeerInfoData.swift"
PANE_CONTAINER = PEER / "PeerInfoPaneContainerNode.swift"
LIST_PANE = PEER / "Panes/PeerInfoListPaneNode.swift"

LUMINANCE_KEY = (
    "Jerkgram.ProfileBackdrop.SourceLuminance"
)

PROFILE_MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_HIDE_RESEARCH_PANES1"
)

OUTER_MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_LINKS_INNER_OWNER1"
)

LIST_MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_LINKS_READABILITY_OWNER1"
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 profile UI] "
            + message
        )


def replace_once(text, old, new, label):
    count = text.count(old)

    require(
        count == 1,
        (
            f"{label}: expected 1 anchor, "
            f"found {count}"
        )
    )

    return text.replace(
        old,
        new,
        1
    )


def patch_profile_panes(text):
    require(
        PROFILE_MARKER not in text,
        "research-pane suppression already applied"
    )

    old = '''// MARK: GhostBase v1.1G NATIVEPANES1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    guard let peer, case .user = peer else {
        return availablePanes
    }
    var result = availablePanes
    for key in [
        PeerInfoPaneKey.ghostBaseProfileHistory,
        PeerInfoPaneKey.ghostBasePresence,
        PeerInfoPaneKey.ghostBaseGiftHistory
    ] where !result.contains(key) {
        result.append(key)
    }
    if personalChannel != nil,
       !result.contains(.ghostBasePersonalChannel) {
        result.append(.ghostBasePersonalChannel)
    }
    return result
}
'''

    new = '''// MARK: GhostBase v1.1G NATIVEPANES1
// MARK: Jerkgram v1.2D BUILD115_HIDE_RESEARCH_PANES1
private func ghostBaseAppendingProfilePanes(
    _ availablePanes: [PeerInfoPaneKey],
    peer: EnginePeer?,
    personalChannel: PeerInfoPersonalChannelData?
) -> [PeerInfoPaneKey] {
    // Keep PROFILEINTEL/history recording and persisted data intact,
    // but do not publish raw research/report panes in the normal
    // Telegram profile UI.
    return availablePanes
}
'''

    return replace_once(
        text,
        old,
        new,
        "raw profile pane policy"
    )


def build114_outer_block():
    return f'''        // MARK: Jerkgram v1.2C BUILD114_LINKS_ONLY_READABILITY1
        // Files / Voice / Music are transparent.
        //
        // Links alone receives a LOCAL black scrim,
        // and only when the actual profile source is light.
        //
        // No scene-wide tint.
        // No per-cell blur.
        // No geometry changes.
        if self.ghostBaseGlassEnabled {{
            if self.currentPaneKey == .links,
               let value = UserDefaults.standard.object(
                   forKey: "{LUMINANCE_KEY}"
               ) as? NSNumber {{
                let luminance =
                    CGFloat(value.doubleValue)

                let lightness = max(
                    0.0,
                    min(
                        1.0,
                        (luminance - 0.55)
                            / 0.45
                    )
                )

                self.backgroundColor =
                    UIColor.black
                        .withAlphaComponent(
                            0.26 * lightness
                        )
            }} else {{
                self.backgroundColor = .clear
            }}
        }} else {{
            self.backgroundColor =
                backgroundColor
        }}
'''


def patch_outer_links_owner(text):
    require(
        OUTER_MARKER not in text,
        "Links outer-owner suppression already applied"
    )

    old = build114_outer_block()

    new = '''        // MARK: Jerkgram v1.2D BUILD115_LINKS_INNER_OWNER1
        // The outer pane container is not the visible owner of the
        // Links list. Keep it transparent and let PeerInfoListPaneNode
        // own the single adaptive readability surface.
        if self.ghostBaseGlassEnabled {
            self.backgroundColor = .clear
        } else {
            self.backgroundColor = backgroundColor
        }
'''

    return replace_once(
        text,
        old,
        new,
        "Build114 outer Links readability block"
    )


def patch_links_list_owner(text):
    require(
        LIST_MARKER not in text,
        "Links inner owner already applied"
    )

    text = replace_once(
        text,
        '''    private let chatControllerInteraction: ChatControllerInteraction
''',
        '''    private let chatControllerInteraction: ChatControllerInteraction
    // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1
    private let jerkgramLinksReadabilityEnabled: Bool
''',
        "Links owner property"
    )

    text = replace_once(
        text,
        '''        self.chatControllerInteraction = chatControllerInteraction
''',
        '''        self.chatControllerInteraction = chatControllerInteraction
        self.jerkgramLinksReadabilityEnabled = tagMask == .webPage
''',
        "Links owner init"
    )

    anchor = '''        self.currentParams = (size, topInset, sideInset, bottomInset, deviceMetrics, visibleHeight, isScrollingLockedAtTop, expandProgress, navigationHeight, presentationData)
'''

    readability = f'''        self.currentParams = (size, topInset, sideInset, bottomInset, deviceMetrics, visibleHeight, isScrollingLockedAtTop, expandProgress, navigationHeight, presentationData)

        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1
        // PeerInfoListPaneNode is the actual visible owner for Links.
        // Keep dark profile sources transparent. On bright sources,
        // add one local neutral black readability surface only here.
        if self.jerkgramLinksReadabilityEnabled {{
            let luminance = (
                UserDefaults.standard.object(
                    forKey: "{LUMINANCE_KEY}"
                ) as? NSNumber
            )?.doubleValue ?? 0.0

            let lightness = max(
                0.0,
                min(
                    1.0,
                    (CGFloat(luminance) - 0.55) / 0.45
                )
            )

            let readabilityColor = UIColor.black.withAlphaComponent(
                0.26 * lightness
            )

            self.backgroundColor = readabilityColor
            self.listNode.backgroundColor = readabilityColor
        }}
'''

    text = replace_once(
        text,
        anchor,
        readability,
        "Links owner update"
    )

    return text


def main():
    for path in (
        DATA,
        PANE_CONTAINER,
        LIST_PANE,
    ):
        require(
            path.is_file(),
            "owner missing: " + str(path)
        )

    data = patch_profile_panes(
        DATA.read_text(encoding="utf-8")
    )

    pane = patch_outer_links_owner(
        PANE_CONTAINER.read_text(
            encoding="utf-8"
        )
    )

    links = patch_links_list_owner(
        LIST_PANE.read_text(
            encoding="utf-8"
        )
    )

    DATA.write_text(
        data,
        encoding="utf-8"
    )

    PANE_CONTAINER.write_text(
        pane,
        encoding="utf-8"
    )

    LIST_PANE.write_text(
        links,
        encoding="utf-8"
    )

    print(
        "[Build115] raw profile research panes hidden; "
        "history/core retained"
    )

    print(
        "[Build115] Links readability moved from outer "
        "container to PeerInfoListPaneNode"
    )


if __name__ == "__main__":
    main()
