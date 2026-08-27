#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ENQUEUE = ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 deleted entities verify] " + message)


def main() -> None:
    text = ENQUEUE.read_text(encoding="utf-8")

    require("BUILD124_DELETED_FULL_ENTITIES1" in text, "portable full-entity owner missing")
    require("ghostBaseOriginalPortableEntities(source: source)" in text, "portable builder still calls reduced entity helper")
    require("let liveEntities" in text and "TextEntitiesMessageAttribute" in text, "live source entities are not read")
    require("let storedEntities" in text and "GhostBaseMessageAttribute" in text and ".originalEntities" in text, "deleted snapshot entity fallback missing")
    require("liveEntities.isEmpty ? storedEntities : liveEntities" in text, "stored entity fallback is not selected")

    start = text.index("// MARK: Jerkgram v1.2M BUILD124_DELETED_FULL_ENTITIES1")
    end = text.index("private func ghostBaseBuildPortableDeletedReply(", start)
    helper = text[start:end]
    require("onlyQuoteable: false" in helper, "Telegram quoteable filter still strips embedded links")
    require("onlyQuoteable: true" not in helper, "reduced quoteable entity filter survived")
    require("if case .BlockQuote = entity.type" in helper, "nested source BlockQuote exclusion missing")

    builder_start = text.index("private func ghostBaseBuildPortableDeletedReply(")
    builder_end = text.index("private func ghostBaseReconstructedMedia(", builder_start)
    builder = text[builder_start:builder_end]
    require("ghostBaseShiftEntities(" in builder and "by: originalTextStart" in builder, "entity offsets are not shifted into recovered quote")
    require("TextEntitiesMessageAttribute(entities: entities)" in builder, "rebased source entities are not emitted")

    print("[Build124 deleted entities verify] GREEN")
    print("[Build124 deleted entities verify] embedded links + full source formatting survive portable deleted reproduction")


if __name__ == "__main__":
    main()
