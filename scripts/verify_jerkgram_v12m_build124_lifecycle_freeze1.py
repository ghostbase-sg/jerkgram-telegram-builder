#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/JerkgramCore/Sources/JerkgramStore.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1"
COOPERATIVE_MARKER = "// MARK: Jerkgram v1.2M BUILD124_COOPERATIVE_LIFECYCLE_DRAIN1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 lifecycle freeze verify] " + message)


def request_lifecycle_block(text: str) -> str:
    signature = "private static func requestLifecycleFlush()"
    start = text.index(signature)
    brace = text.index("{", start + len(signature))
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise RuntimeError("[Build124 lifecycle freeze verify] request function is unbalanced")


def main() -> None:
    require(TARGET.is_file(), f"target missing: {TARGET}")
    text = TARGET.read_text(encoding="utf-8")
    require(MARKER in text, "Build124 lifecycle marker missing")
    require(COOPERATIVE_MARKER in text, "cooperative lifecycle drain marker missing")

    observer_start = text.index("private static let lifecycleObservers")
    request_start = text.index("private static func requestLifecycleFlush()", observer_start)
    observer_block = text[observer_start:request_start]
    require(observer_block.count("requestLifecycleFlush()") == 2, "both lifecycle observers must use the async request")
    require("flushSynchronously()" not in observer_block, "lifecycle observer still performs synchronous flush")

    request_block = request_lifecycle_block(text)
    require("self.queue.async" in request_block, "lifecycle request is not dispatched to capture queue")
    require("guard !self.pendingEvents.isEmpty, !self.flushScheduled else { return }" in request_block, "lifecycle request is not bounded")
    require("self.flushScheduled = true" in request_block, "lifecycle request does not hand off a normal flush")
    require("_ = self.flush()" in request_block, "lifecycle request does not start a bounded flush")
    require("while !self.pendingEvents.isEmpty" not in request_block, "lifecycle request still drains an unbounded backlog")
    require("self.queue.sync" not in request_block, "async lifecycle request still blocks its caller")

    require(text.count("public static func flushSynchronously()") == 1, "explicit synchronous bridge changed unexpectedly")
    print("[Build124 lifecycle freeze verify] GREEN")
    print("[Build124 lifecycle freeze verify] UIKit lifecycle callbacks cannot wait on capture disk I/O")


if __name__ == "__main__":
    main()
