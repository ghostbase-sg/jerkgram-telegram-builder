from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_deleted_entities1.py"


class Build124DeletedEntityTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_deleted_entities", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def helper_fixture(self) -> str:
        return '''private func ghostBaseOriginalQuoteableEntities(
    source: Message
) -> [MessageTextEntity] {
    guard !source.text.isEmpty,
          let attribute = source.attributes.first(
            where: { $0 is TextEntitiesMessageAttribute }
          ) as? TextEntitiesMessageAttribute else {
        return []
    }
    let length = (source.text as NSString).length
    guard length > 0 else {
        return []
    }
    return messageTextEntitiesInRange(
        entities: attribute.entities,
        range: NSRange(location: 0, length: length),
        onlyQuoteable: true
    ).filter { entity in
        if case .BlockQuote = entity.type {
            return false
        }
        return true
    }
}'''

    def call_fixture(self) -> str:
        return '''        entities.append(contentsOf: ghostBaseShiftEntities(
            ghostBaseOriginalQuoteableEntities(source: source),
            by: originalTextStart
        ))'''

    def test_source_entities_are_not_limited_to_telegram_quoteable_subset(self):
        module = self.load_patch()
        result = module.patch_helper(self.helper_fixture())
        self.assertIn("BUILD124_DELETED_FULL_ENTITIES1", result)
        self.assertIn("onlyQuoteable: false", result)
        self.assertNotIn("onlyQuoteable: true", result)

    def test_deleted_snapshot_is_fallback_when_live_text_entities_are_missing(self):
        module = self.load_patch()
        result = module.patch_helper(self.helper_fixture())
        self.assertIn("GhostBaseMessageAttribute", result)
        self.assertIn("originalEntities", result)
        self.assertIn("liveEntities.isEmpty ? storedEntities : liveEntities", result)

    def test_nested_block_quotes_are_the_only_entity_removed(self):
        module = self.load_patch()
        result = module.patch_helper(self.helper_fixture())
        self.assertIn("if case .BlockQuote = entity.type", result)
        for entity_type in (".TextUrl", ".Url", ".TextMention"):
            self.assertNotIn(f"case {entity_type}", result)

    def test_builder_calls_full_entity_helper_and_keeps_offset_shift(self):
        module = self.load_patch()
        result = module.patch_call(self.call_fixture())
        self.assertIn("ghostBaseOriginalPortableEntities(source: source)", result)
        self.assertIn("by: originalTextStart", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        helper = module.patch_helper(self.helper_fixture())
        call = module.patch_call(self.call_fixture())
        self.assertEqual(helper, module.patch_helper(helper))
        self.assertEqual(call, module.patch_call(call))


if __name__ == "__main__":
    unittest.main()
