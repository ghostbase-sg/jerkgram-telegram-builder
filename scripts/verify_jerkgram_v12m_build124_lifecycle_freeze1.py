#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/JerkgramCore/Sources/JerkgramStore.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 lifecycle freeze verify] " + message)


def main() -> None:
    require(TARGET.is_file(), f"target missing: {TARGET}")
    text = TARGET.read_text(encoding="utf-8")
    require(MARKER in text, "Build124 lifecycle marker missing")

    observer_start = text.index("private static let lifecycleObservers")
    request_start = text.index("private static func requestLifecycleFlush()", observer_start)
    observer_block = text[observer_start:request_start]
    require(observer_block.count("requestLifecycleFlush()") == 2, "both lifecycle observers must use the async request")
    require("flushSynchronously()" not in observer_block, "lifecycle observer still performs synchronous flush")

    request_end = text.index("@discardableResult", request_start)
    request_block = text[request_start:request_end]
    require("self.queue.async" in request_block, "lifecycle request is not dispatched to capture queue")
    require("while !self.pendingEvents.isEmpty" in request_block, "async request does not drain pending capture events")
    require("self.queue.sync" not in request_block, "async lifecycle request still blocks its caller")

    require(text.count("public static func flushSynchronously()") == 1, "explicit synchronous bridge changed unexpectedly")
    print("[Build124 lifecycle freeze verify] GREEN")
    print("[Build124 lifecycle freeze verify] UIKit lifecycle callbacks cannot wait on capture disk I/O")


if __name__ == "__main__":
    main()
