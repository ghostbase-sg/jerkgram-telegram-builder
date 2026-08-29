import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12n_build125_single_forward1.py"


class Build125SingleForwardTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build125_single_forward", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def build124_owner(self) -> str:
        return '''        let ghostBaseForwardWithoutAuthor = true

        if ghostBaseForwardWithoutAuthor,
           data.messageActions.options.contains(.forward) {
            actions.append(.action(ContextMenuActionItem(
                text: "Переслать без автора",
                action: { _, f in
                    let targetMessages = selectAll ? messages : [message]
                    f(.dismissWithoutContent)
                }
            )))
        }
'''

    def test_direct_single_message_action_does_not_require_native_forward_permission(self):
        module = self.load_patch()
        result = module.patch_text(self.build124_owner())
        self.assertIn("BUILD125_SINGLE_FORWARD_DIRECT_ACTION1", result)
        self.assertIn("let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]", result)
        self.assertNotIn("data.messageActions.options.contains(.forward)", result)
        self.assertIn("jerkgramForwardWithoutAuthorTargets.allSatisfy", result)

    def test_unsupported_message_kinds_stay_excluded(self):
        module = self.load_patch()
        result = module.patch_text(self.build124_owner())
        self.assertIn("Namespaces.Peer.SecretChat", result)
        self.assertIn("TelegramMediaPaidContent", result)
        self.assertIn("TelegramMediaExpiredContent", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.build124_owner())
        self.assertEqual(once, module.patch_text(once))

    def test_accepts_direct_owner_when_legacy_gate_is_only_a_comment(self):
        module = self.load_patch()
        direct_owner = '''        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
           }) {
            // data.messageActions.options.contains(.forward) survived portable gate
            actions.append(.action(ContextMenuActionItem(text: "Переслать без автора", action: { _, f in
                f(.dismissWithoutContent)
            })))
        }
'''
        result = module.patch_text(direct_owner)
        self.assertIn("BUILD125_SINGLE_FORWARD_DIRECT_ACTION1", result)
        self.assertEqual(result.count("let jerkgramForwardWithoutAuthorTargets"), 1)


if __name__ == "__main__":
    unittest.main()
