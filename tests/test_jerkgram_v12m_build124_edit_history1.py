from pathlib import Path
import importlib.util
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_edit_history1.py"


class Build124EditHistoryTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_edit_history", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def state_fixture(self) -> str:
        return '''                        // The stored text belongs to the previous version, so its
                        // timestamp must also come from the previous version.
                        let previousVersionDate = (
                            previousMessage.attributes.first(
                                where: { $0 is EditedMessageAttribute }
                            ) as? EditedMessageAttribute
                        )?.date ?? previousMessage.timestamp
                        if let updatedAttribute = attribute?.withAddedEditVersion(
                            text: previousMessage.text,
                            date: previousVersionDate,
                            entities: previousEntities,
                            inlineStickerFiles: previousInlineStickerFiles
                        ) {'''

    def menu_fixture(self) -> str:
        return '''        if result.isEmpty, let originalText = attribute.originalText, originalText != message.text {
            result.append(GhostBaseEditHistoryVersion(index: result.count, text: originalText, timestamp: 0.0, entities: attribute.originalEntities, inlineStickerFiles: []))
        }
    }

    if result.isEmpty {
        result = ghostBaseLoadEditHistoryVersions(messageId: message.id)
    }

    // MARK: Jerkgram v1.2K BUILD122_EDIT_HISTORY_CURRENT1
    // History must show the result of the latest text/caption edit as well.
    if !result.isEmpty, result.last?.text != message.text {
        result.append(GhostBaseEditHistoryVersion(
            index: result.count,
            text: message.text,
            timestamp: Double((message.attributes.first(where: { $0 is EditedMessageAttribute }) as? EditedMessageAttribute)?.date ?? message.timestamp),
            entities: message.textEntitiesAttribute?.entities ?? [],
            inlineStickerFiles: (message.attributes.first(where: { $0 is EmbeddedMediaStickersMessageAttribute }) as? EmbeddedMediaStickersMessageAttribute)?.files ?? []
        ))
    }

    return result
}'''

    def test_history_uses_edit_event_date_not_previous_message_date(self):
        module = self.load_patch()
        result = module.patch_state_text(self.state_fixture())
        self.assertIn("BUILD124_EDIT_EVENT_DATE1", result)
        self.assertIn("message.attributes.first", result)
        self.assertIn("date: editEventDate", result)
        self.assertNotIn("previousVersionDate", result)

    def test_one_edit_produces_one_history_version_not_old_plus_current(self):
        module = self.load_patch()
        result = module.patch_menu_text(self.menu_fixture())
        self.assertIn("BUILD124_HISTORY_NO_CURRENT_DUP1", result)
        self.assertNotIn("BUILD122_EDIT_HISTORY_CURRENT1", result)
        self.assertNotIn("History must show the result of the latest text/caption edit as well", result)
        self.assertNotIn("result.last?.text != message.text", result)

    def test_original_fallback_has_real_date_for_native_chat_header(self):
        module = self.load_patch()
        result = module.patch_menu_text(self.menu_fixture())
        self.assertIn("BUILD124_HISTORY_NATIVE_DATE1", result)
        self.assertIn("EditedMessageAttribute", result)
        self.assertIn("timestamp: originalFallbackDate", result)
        self.assertNotIn("timestamp: 0.0, entities: attribute.originalEntities", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        state_once = module.patch_state_text(self.state_fixture())
        menu_once = module.patch_menu_text(self.menu_fixture())
        self.assertEqual(state_once, module.patch_state_text(state_once))
        self.assertEqual(menu_once, module.patch_menu_text(menu_once))


if __name__ == "__main__":
    unittest.main()
