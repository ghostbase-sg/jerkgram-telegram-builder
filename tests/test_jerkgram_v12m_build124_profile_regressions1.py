from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_profile_regressions1.py"


class Build124ProfileRegressionTests(unittest.TestCase):
    def make_tree(self, root: Path, *, groups: str, links: str, profile_items: str) -> None:
        files = {
            "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift": groups,
            "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift": links,
            "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift": profile_items,
        }
        for relative, text in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def good_sources(self) -> tuple[str, str, str]:
        groups = '''// MARK: Jerkgram v1.2L BUILD123_COMMON_GROUPS_SURFACE1
self.ghostBaseGlassEffectView.isHidden = false
self.ghostBaseGlassTintView.backgroundColor = UIColor(white: isDark ? 0.0 : 1.0, alpha: isDark ? 0.26 : 0.18)
self.listBackgroundView.isHidden = true
self.listMaskView.isHidden = true
'''
        links = '''// MARK: Jerkgram v1.2L BUILD123_LINKS_INTRINSIC_GLASS1
if self.ghostBaseGlassEnabled && !self.jerkgramLinksReadabilityEnabled { }
else {
    self.glassBackgroundView.isHidden = true
    transition.updateFrame(view: self.glassBackgroundView, frame: self.jerkgramLinksReadabilityEnabled ? .zero : self.glassBackgroundView.frame)
}
// MARK: Jerkgram v1.2M BUILD124_LINKS_INTRINSIC_MATERIAL1
let materialAlpha: CGFloat = 0.20 + 0.06 * lightness
'''
        profile_items = '''// MARK: Jerkgram v1.2L BUILD123_REMOVE_PRIVATE_LINK_PROBE1
var result: [(AnyHashable, [PeerInfoScreenItem])] = []
'''
        return groups, links, profile_items

    def run_verify(self, *, groups: str, links: str, profile_items: str):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_tree(root, groups=groups, links=links, profile_items=profile_items)
            env = os.environ.copy()
            env["JERKGRAM_SOURCE_ROOT"] = str(root)
            return subprocess.run(
                [sys.executable, str(VERIFY)],
                cwd=REPO,
                env=env,
                capture_output=True,
                text=True,
            )

    def test_accepts_build123_accepted_surfaces_after_build124_overlays(self):
        groups, links, profile_items = self.good_sources()
        result = self.run_verify(groups=groups, links=links, profile_items=profile_items)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_common_groups_becoming_hidden_or_transparent_again(self):
        groups, links, profile_items = self.good_sources()
        groups = groups.replace("isHidden = false", "isHidden = true")
        result = self.run_verify(groups=groups, links=links, profile_items=profile_items)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_short_links_viewport_plate_regression(self):
        groups, links, profile_items = self.good_sources()
        links = links.replace("self.jerkgramLinksReadabilityEnabled ? .zero : self.glassBackgroundView.frame", "self.glassBackgroundView.frame")
        result = self.run_verify(groups=groups, links=links, profile_items=profile_items)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_experimental_private_get_link_owner_returning(self):
        groups, links, profile_items = self.good_sources()
        profile_items += "\n// MARK: GhostBase v1.0ZG PRIVATELINK1 cached exported invite\n"
        result = self.run_verify(groups=groups, links=links, profile_items=profile_items)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
