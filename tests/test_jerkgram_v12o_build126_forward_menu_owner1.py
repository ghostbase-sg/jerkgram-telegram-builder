import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12o_build126_forward_menu_owner1.py"


class Build126ForwardMenuOwnerTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build126_forward_menu", PATCH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def owner_fixture(self):
        return '''        // MARK: Jerkgram v1.2N BUILD125_SINGLE_FORWARD_DIRECT_ACTION1
        let jerkgramForwardWithoutAuthorTargets = selectAll ? messages : [message]
        if ghostBaseForwardWithoutAuthor,
           jerkgramForwardWithoutAuthorTargets.allSatisfy({ message in
               message.id.peerId.namespace != Namespaces.Peer.SecretChat
           }) {
            actions.append(.action(ContextMenuActionItem(text: "Переслать без автора", action: { _, f in
                f(.dismissWithoutContent)
            })))
        }

        if data.messageActions.options.contains(.forward) {
            actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuForward, action: { _, f in
                interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])
                f(.dismissWithoutContent)
            })))
        }
'''

    def test_leaves_original_without_author_and_native_forward_owners_unchanged(self):
        module = self.load_patch()
        source = self.owner_fixture()
        self.assertEqual(source, module.patch_text(source))
        self.assertIn("Переслать без автора", module.patch_text(source))
        self.assertNotIn("jerkgramPortableForwardTargets", module.patch_text(source))


if __name__ == "__main__":
    unittest.main()
