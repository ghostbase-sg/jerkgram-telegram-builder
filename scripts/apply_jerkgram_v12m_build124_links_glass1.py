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
        // The Links pane itself must remain transparent. A pane-sized color
        // layer darkens the whole profile; the material belongs only behind
        // the loaded Links list, exactly like Groups in Common.
        if self.jerkgramLinksReadabilityEnabled {
            self.backgroundColor = .clear
            self.listNode.backgroundColor = .clear
            if self.ghostBaseGlassEnabled {
                let effectView: UIVisualEffectView
                if let current = self.glassBackgroundView.subviews.first as? UIVisualEffectView {
                    effectView = current
                } else {
                    let created = UIVisualEffectView()
                    created.autoresizingMask = [.flexibleWidth, .flexibleHeight]
                    self.glassBackgroundView.addSubview(created)
                    effectView = created
                }
                effectView.effect = UIBlurEffect(style: presentationData.theme.overallDarkAppearance ? .systemMaterialDark : .systemMaterialLight)
                effectView.frame = self.glassBackgroundView.bounds

                var distanceToTop: CGFloat = -100.0
                if case let .known(topOffset) = self.listNode.visibleContentOffset() {
                    distanceToTop = -CGFloat(topOffset) + self.listNode.insets.top
                }
                distanceToTop = max(-100.0, distanceToTop)
                let linksFrame = CGRect(
                    x: sideInset + 16.0,
                    y: distanceToTop,
                    width: max(1.0, self.listNode.bounds.size.width - (sideInset + 16.0) * 2.0),
                    height: max(1.0, self.listNode.bounds.size.height - distanceToTop - self.listNode.insets.bottom)
                )
                transition.updateFrame(view: self.glassBackgroundView, frame: linksFrame)
                self.glassBackgroundView.layer.cornerRadius = 16.0
                self.glassBackgroundView.layer.borderWidth = 0.5
                self.glassBackgroundView.layer.borderColor = presentationData.theme.list.itemPlainSeparatorColor.withAlphaComponent(presentationData.theme.overallDarkAppearance ? 0.30 : 0.20).cgColor
                self.glassBackgroundView.isHidden = false
            } else {
                self.glassBackgroundView.isHidden = true
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
    updated = text.replace(OLD, NEW, 1)
    # The Build123 geometry branch used to hide every Links card after the
    # owner above laid it out. Preserve that policy for non-Links panes only.
    geometry_marker = "BUILD123_LINKS_INTRINSIC_GLASS1"
    owner_marker = "BUILD115_LINKS_READABILITY_OWNER1"
    geometry_start = updated.index(geometry_marker)
    geometry_end = updated.find(owner_marker, geometry_start)
    if geometry_end < 0:
        geometry_end = len(updated)
    geometry = updated[geometry_start:geometry_end]
    require(geometry.count("        } else {") == 1, "Build123 Links hide branch missing")
    geometry = geometry.replace(
        "        } else {",
        "        } else if !self.jerkgramLinksReadabilityEnabled {",
        1,
    )
    return updated[:geometry_start] + geometry + updated[geometry_end:]


def main() -> None:
    require(LIST.is_file(), "PeerInfoListPaneNode.swift missing")
    original = LIST.read_text(encoding="utf-8")
    updated = patch_text(original)
    LIST.write_text(updated, encoding="utf-8")
    print("[Build124 Links glass] GREEN")
    print("[Build124 Links glass] intrinsic geometry kept; non-zero translucent material restored")


if __name__ == "__main__":
    main()
