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

    def test_carries_chat_level_protection_in_the_sender_owner(self):
        module = self.load_patch()
        forward = module.patch_text(self.forward_fixture())
        self.assertIn(module.MARKER, forward)
        self.assertIn("message.peers[message.id.peerId]", forward)
        self.assertIn("chatPeer.isCopyProtectionEnabled", forward)
        self.assertIn("message.forwardInfo?.author ?? message.effectiveAuthor", forward)

    def test_does_not_depend_on_or_mutate_the_retired_build126_menu_owner(self):
        source = PATCH.read_text(encoding="utf-8")
        self.assertNotIn("ChatInterfaceStateContextMenus.swift", source)
        self.assertNotIn("BUILD126_FORWARD_MENU_OWNER1", source)
        self.assertNotIn("patch_menu", source)

    def test_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.forward_fixture())
        self.assertEqual(once, module.patch_text(once))


if __name__ == "__main__":
    unittest.main()
