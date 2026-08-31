import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12r_build129_protected_chat_forward1.py"


class Build129ProtectedChatForwardTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build129 protected-chat forward correction is missing")
        spec = importlib.util.spec_from_file_location("build129_protected_chat_forward", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def forward_fixture(self):
        return '''// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1
private func jerkgramRequiresPortableForward(_ message: Message) -> Bool {
    if message.isCopyProtected() {
        return true
    }
    if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
        return sourcePeer.isCopyProtectionEnabled
    }
    return false
}
'''

    def menu_fixture(self):
        return '''// MARK: Jerkgram v1.2O BUILD126_FORWARD_MENU_OWNER1
        let jerkgramPortableForwardTargets = selectAll || isImage ? messages : [message]
        let jerkgramNeedsPortableForward = jerkgramPortableForwardTargets.contains { message in
            if message.isCopyProtected() {
                return true
            }
            if let sourcePeer = message.forwardInfo?.author ?? message.effectiveAuthor {
                return sourcePeer.isCopyProtectionEnabled
            }
            return false
        }
        let jerkgramPortableForwardIsSafe = true
'''

    def test_carries_chat_level_protection_to_the_sender_and_menu(self):
        module = self.load_patch()
        forward, menu = module.patch_texts(self.forward_fixture(), self.menu_fixture())
        self.assertIn(module.MARKER, forward)
        self.assertIn("message.peers[message.id.peerId]", forward)
        self.assertIn("chatPeer.isCopyProtectionEnabled", forward)
        self.assertIn("chatPresentationInterfaceState.copyProtectionEnabled", menu)
        self.assertIn("message.peers[message.id.peerId]", menu)

    def test_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_texts(self.forward_fixture(), self.menu_fixture())
        self.assertEqual(once, module.patch_texts(*once))


if __name__ == "__main__":
    unittest.main()
