import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12o_build126_forward_menu_owner1.py"


class Build126ForwardMenuOwnerTests(unittest.TestCase):
    def load_patch(self):
        self.assertTrue(PATCH.is_file(), "Build126 forward-menu owner patch is missing")
        spec = importlib.util.spec_from_file_location("build126_forward_menu", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self):
        return '''        let ghostBaseForwardWithoutAuthor = true
        // MARK: Jerkgram v1.2M BUILD124_SINGLE_FORWARD_TARGET_SCOPE1
        ) {
            actions.append(.action(ContextMenuActionItem(text: "Переслать без автора", action: { _, f in
                f(.dismissWithoutContent)
            })))
        }
        if data.messageActions.options.contains(.sendScheduledNow) {
        }

        // MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1
        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
           }) {
            actions.append(.action(ContextMenuActionItem(text: "Переслать без автора", action: { _, f in
                f(.dismissWithoutContent)
            })))
        }

        var messageText: String = ""
        var isImage = true
        let isCopyProtected = false
        let isMigrated = false
        let isUnremovableAction = false
        let resourceAvailable = true

        if data.messageActions.options.contains(.forward) {
            if !isCopyProtected {
                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuForward, action: { _, f in
                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])
                    f(.dismissWithoutContent)
                })))
            }
        }
'''

    def test_protected_source_receives_portable_forward_entry_before_native_gate(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn(module.MARKER, result)
        self.assertIn("jerkgramPortableForwardTargets", result)
        self.assertIn("message.forwardInfo?.author ?? message.effectiveAuthor", result)
        self.assertIn("sourcePeer.isCopyProtectionEnabled", result)
        self.assertIn("interfaceInteraction.forwardMessages(jerkgramPortableForwardTargets)", result)

    def test_single_long_press_action_uses_exact_pressed_target_and_force_hides_author(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn("jerkgramBuild126ForwardWithoutAuthorTargets = selectAll ? messages : [message]", result)
        self.assertIn("let jerkgramBuild126ChatController = interfaceInteraction.chatController() as? ChatControllerImpl", result)
        self.assertIn("if ghostBaseForwardWithoutAuthor,\n           let jerkgramBuild126ChatController", result)
        self.assertNotIn("forceHideNames: true", result)
        self.assertIn("messageIds: jerkgramBuild126ForwardWithoutAuthorTargets.map", result)
        self.assertNotIn("BUILD125_SINGLE_FORWARD_DIRECT_ACTION1", result)
        self.assertNotIn("BUILD124_SINGLE_FORWARD_TARGET_SCOPE1", result)

    def test_preserves_the_declarations_between_the_old_action_and_native_gate(self):
        module = self.load_patch()
        result = module.patch_text(self.owner_fixture())
        self.assertIn('var messageText: String = ""', result)
        self.assertIn("var isImage = true", result)
        self.assertIn("let isCopyProtected = false", result)
        self.assertLess(result.index(module.MARKER), result.index(module.NATIVE_FORWARD))

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.owner_fixture())
        self.assertEqual(once, module.patch_text(once))

    def test_legacy_owner_is_optional_after_its_broken_predecessor_is_removed(self):
        module = self.load_patch()
        source = self.owner_fixture().replace(module.OLD_MARKER + "\n", "")
        source = source.replace("        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]\n", "")
        source = source.replace("        if ghostBaseForwardWithoutAuthor,\n", "        if true,\n", 1)
        result = module.patch_text(source)
        self.assertIn(module.MARKER, result)


if __name__ == "__main__":
    unittest.main()
