#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
MODULE = ROOT / "submodules/JerkgramCore"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build118 core] " + message)


def main():
    models = (MODULE / "Sources/JerkgramModels.swift").read_text(encoding="utf-8")
    index = (MODULE / "Sources/JerkgramIndex.swift").read_text(encoding="utf-8")
    store = (MODULE / "Sources/JerkgramStore.swift").read_text(encoding="utf-8")
    build = (MODULE / "BUILD").read_text(encoding="utf-8")
    for token in (
        "BUILD118_CORE_MODELS1",
        "public struct JerkgramEventId",
        "public let accountPeerId: Int64",
        "public let chatPeerId: Int64",
        "public let eventId: JerkgramEventId",
        "public let payload: JerkgramEventPayload",
    ):
        require(token in models, "model invariant missing: " + token)
    for token in (
        "BUILD118_REFERENCE_INDEX1",
        "public let locator: JerkgramCanonicalLocator",
        "public let byteOffset: UInt64",
        "public let byteLength: UInt64",
    ):
        require(token in index, "index invariant missing: " + token)
    for forbidden in ("messageText", "mediaBytes", "authKey", "accessToken"):
        require(forbidden not in index, "index contains payload/secret field: " + forbidden)
    for token in (
        "BUILD118_EVENT_STORE1",
        "options: .atomic",
        "events.jsonl",
        "events.index.jsonl",
        "public func appendBatch",
        "public func indexRecords",
        "public func eventPage",
        "public func readyIndexRecords",
        "private static var sharedIndexStates",
        "appendBatchRecovering",
    ):
        require(token in store, "store invariant missing: " + token)
    append_body = store.split("public func append(_ event: JerkgramCanonicalEvent) throws", 1)[1].split("\n    }", 1)[0]
    require("loadAccount" not in append_body and "writeAccount" not in append_body, "append regressed to full rewrite")
    require('name = "JerkgramCore"' in build, "Bazel target missing")
    print("[verify Build118 core] GREEN: append-only account log + byte-range reference index")


if __name__ == "__main__":
    main()
