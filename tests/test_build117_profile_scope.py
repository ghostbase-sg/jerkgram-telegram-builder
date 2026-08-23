import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build117ProfileScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load_script(
            "apply_jerkgram_v12f_build117_profile_scope1.py"
        )

    def test_settings_route_keeps_stock_panes_while_user_profiles_keep_history(self):
        source = '''
// MARK: Jerkgram v1.2E BUILD116_PROFILE_SCOPE1
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

final class PeerInfoScreenData {
    init(
        peer: EnginePeer?,
        availablePanes: [PeerInfoPaneKey],
        personalChannel: PeerInfoPersonalChannelData?,
        businessConnectedBot: EnginePeer?
    ) {
        self.availablePanes = ghostBaseAppendingProfilePanes(
            availablePanes,
            peer: peer,
            personalChannel: personalChannel
        )
    }
}

func peerInfoScreenSettingsData() -> PeerInfoScreenData {
    return PeerInfoScreenData(
        peer: peer,
        availablePanes: availablePanes,
        personalChannel: personalChannel,
        businessConnectedBot: businessConnectedBot
    )
}

func peerInfoScreenData() -> PeerInfoScreenData {
    return PeerInfoScreenData(
        peer: peer,
        availablePanes: availablePanes,
        personalChannel: personalChannel,
        businessConnectedBot: businessConnectedBot
    )
}
'''

        patched = self.overlay.patch_profile_scope(source)

        self.assertEqual(patched.count("BUILD117_SETTINGS_PROFILE_SCOPE1"), 1)
        self.assertIn("isSettings: Bool", patched)
        self.assertIn("if isSettings {\n        return availablePanes", patched)
        self.assertIn("isSettings: isSettings", patched)
        settings_function = patched[
            patched.index("func peerInfoScreenSettingsData"):
            patched.index("func peerInfoScreenData")
        ]
        ordinary_function = patched[patched.index("func peerInfoScreenData"):]
        self.assertIn("isSettings: true", settings_function)
        self.assertNotIn("isSettings: true", ordinary_function)
        for pane in (
            "ghostBaseProfileHistory",
            "ghostBasePresence",
            "ghostBaseGiftHistory",
            "ghostBasePersonalChannel",
        ):
            self.assertIn(pane, patched)


if __name__ == "__main__":
    unittest.main()
