from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_single_forward1.py"


class Build124SingleForwardTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_single_forward", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def state_fixture(self) -> str:
        return '''        GhostBaseKey.showEditHistory: .bool(state.showEditHistory),
        ghostBaseSendTextStyleKey: .string(state.sendTextStyle),'''

    def menu_fixture(self) -> str:
        return '''        let ghostBaseForwardWithoutAuthor = (
            UserDefaults.standard.object(
                forKey: "GhostBase.Messages.ForwardWithoutAuthor"
            ) as? Bool
        ) ?? true

        // MARK: Jerkgram v1.2L BUILD123_PORTABLE_MENU_RESTRICTIONS1
        if ghostBaseForwardWithoutAuthor,
           messages.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
               && !message.media.contains(where: {
                   $0 is TelegramMediaPaidContent
                   || $0 is TelegramMediaAction
                   || $0 is TelegramMediaExpiredContent
               })
           }) {
            // data.messageActions.options.contains(.forward) survived portable gate'''

    def test_forward_toggle_returns_to_build123_account_projection(self):
        module = self.load_patch()
        result = module.patch_state_text(self.state_fixture())
        self.assertIn("BUILD124_FORWARD_SETTING_OWNER1", result)
        self.assertIn("GhostBaseKey.forwardWithoutAuthor: .bool(state.forwardWithoutAuthor)", result)

    def test_single_context_menu_reads_current_account_scope_first(self):
        module = self.load_patch()
        result = module.patch_menu_text(self.menu_fixture())
        self.assertIn("BUILD124_SINGLE_FORWARD_ACCOUNT_SCOPE1", result)
        self.assertIn("context.account.peerId.toInt64()", result)
        self.assertIn("jerkgram.account.", result)
        self.assertIn("GhostBase.Messages.ForwardWithoutAuthor", result)
        scoped_lookup = "defaults.object(forKey: scopedForwardWithoutAuthorKey)"
        legacy_lookup = "defaults.object(forKey: legacyForwardWithoutAuthorKey)"
        self.assertIn(scoped_lookup, result)
        self.assertIn(legacy_lookup, result)
        self.assertLess(result.index(scoped_lookup), result.index(legacy_lookup))

    def test_single_action_remains_independent_of_telegram_forward_permission(self):
        module = self.load_patch()
        result = module.patch_menu_text(self.menu_fixture())
        self.assertNotIn("data.messageActions.options.contains(.forward)", result.replace("// data.messageActions.options.contains(.forward) survived portable gate", ""))
        self.assertIn("messages.allSatisfy", result)
        self.assertIn("Namespaces.Peer.SecretChat", result)
        self.assertIn("TelegramMediaPaidContent", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        state = module.patch_state_text(self.state_fixture())
        menu = module.patch_menu_text(self.menu_fixture())
        self.assertEqual(state, module.patch_state_text(state))
        self.assertEqual(menu, module.patch_menu_text(menu))


if __name__ == "__main__":
    unittest.main()
