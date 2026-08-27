#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
LIST = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1"

OLD = '''        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1
        // PeerInfoListPaneNode is the actual visible owner for Links.
        // Keep dark profile sources transparent. On bright sources,
        // add one local neutral black readability surface only here.
        if self.jerkgramLinksReadabilityEnabled {
            let luminance = (
                UserDefaults.standard.object(
                    forKey: "Jerkgram.ProfileBackdrop.SourceLuminance"
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
        }
'''

NEW = '''        // MARK: Jerkgram v1.2D BUILD115_LINKS_READABILITY_OWNER1
        // MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1
        // Links must keep the Build123 intrinsic geometry fix: never restore
        // the viewport-height rounded glass plate. Instead the actual list
        // owner receives a bounded, theme-aware translucent material. The
        // alpha has a non-zero floor so dark profile sources do not collapse
        // to a visually opaque/absent material state.
        if self.jerkgramLinksReadabilityEnabled {
            if self.ghostBaseGlassEnabled {
                let luminance = (
                    UserDefaults.standard.object(
                        forKey: "Jerkgram.ProfileBackdrop.SourceLuminance"
                    ) as? NSNumber
                )?.doubleValue ?? 0.0

                let lightness = max(
                    0.0,
                    min(
                        1.0,
                        (CGFloat(luminance) - 0.55) / 0.45
                    )
                )

                let materialAlpha: CGFloat = presentationData.theme.overallDarkAppearance
                    ? 0.20 + 0.06 * lightness
                    : 0.14 + 0.04 * lightness
                let readabilityColor = UIColor(
                    white: presentationData.theme.overallDarkAppearance ? 0.0 : 1.0,
                    alpha: materialAlpha
                )

                self.backgroundColor = readabilityColor
                self.listNode.backgroundColor = readabilityColor
            } else {
                // GBGlass off returns this pane to the normal Telegram-owned
                // transparent surface; the parent profile background remains
                // the only owner, exactly like the other list panes.
                self.backgroundColor = .clear
                self.listNode.backgroundColor = .clear
            }
        }
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 Links glass] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    require(text.count(OLD) == 1, f"expected one Build115 Links owner, found {text.count(OLD)}")
    require("BUILD123_LINKS_INTRINSIC_GLASS1" in text, "Build123 intrinsic Links geometry owner missing")
    return text.replace(OLD, NEW, 1)


def main() -> None:
    require(LIST.is_file(), "PeerInfoListPaneNode.swift missing")
    original = LIST.read_text(encoding="utf-8")
    updated = patch_text(original)
    LIST.write_text(updated, encoding="utf-8")
    print("[Build124 Links glass] GREEN")
    print("[Build124 Links glass] intrinsic geometry kept; non-zero translucent material restored")


if __name__ == "__main__":
    main()
