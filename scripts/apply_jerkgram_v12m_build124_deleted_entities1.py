#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ENQUEUE = ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_DELETED_FULL_ENTITIES1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 deleted entities] " + message)


OLD_HELPER = '''private func ghostBaseOriginalQuoteableEntities(
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

NEW_HELPER = '''// MARK: Jerkgram v1.2M BUILD124_DELETED_FULL_ENTITIES1
private func ghostBaseOriginalPortableEntities(
    source: Message
) -> [MessageTextEntity] {
    guard !source.text.isEmpty else {
        return []
    }

    let liveEntities = (
        source.attributes.first(where: { $0 is TextEntitiesMessageAttribute })
        as? TextEntitiesMessageAttribute
    )?.entities ?? []
    let storedEntities = (
        source.attributes.first(where: { $0 is GhostBaseMessageAttribute })
        as? GhostBaseMessageAttribute
    )?.originalEntities ?? []
    let sourceEntities = liveEntities.isEmpty ? storedEntities : liveEntities

    let length = (source.text as NSString).length
    guard length > 0, !sourceEntities.isEmpty else {
        return []
    }

    // Telegram's `onlyQuoteable` filter deliberately drops Url/TextUrl and
    // TextMention. A portable deleted reply must reproduce the source text,
    // not Telegram's reduced quote-format subset, so preserve every entity
    // whose range belongs to the source text. The outer recovered quote owns
    // its BlockQuote entity; nesting a source BlockQuote is the sole exclusion.
    return messageTextEntitiesInRange(
        entities: sourceEntities,
        range: NSRange(location: 0, length: length),
        onlyQuoteable: false
    ).filter { entity in
        if case .BlockQuote = entity.type {
            return false
        }
        return true
    }
}'''

OLD_CALL = '''        entities.append(contentsOf: ghostBaseShiftEntities(
            ghostBaseOriginalQuoteableEntities(source: source),
            by: originalTextStart
        ))'''

NEW_CALL = '''        entities.append(contentsOf: ghostBaseShiftEntities(
            ghostBaseOriginalPortableEntities(source: source),
            by: originalTextStart
        ))'''


def patch_helper(text: str) -> str:
    if MARKER in text:
        return text
    require(text.count(OLD_HELPER) == 1, f"portable entity helper count is {text.count(OLD_HELPER)}")
    return text.replace(OLD_HELPER, NEW_HELPER, 1)


def patch_call(text: str) -> str:
    if "ghostBaseOriginalPortableEntities(source: source)" in text:
        return text
    require(text.count(OLD_CALL) == 1, f"portable entity call count is {text.count(OLD_CALL)}")
    return text.replace(OLD_CALL, NEW_CALL, 1)


def main() -> None:
    text = ENQUEUE.read_text(encoding="utf-8")
    text = patch_helper(text)
    text = patch_call(text)
    ENQUEUE.write_text(text, encoding="utf-8")
    print("[Build124 deleted entities] GREEN")
    print("[Build124 deleted entities] Url/TextUrl/TextMention and formatting survive deleted portable reproduction")


if __name__ == "__main__":
    main()
