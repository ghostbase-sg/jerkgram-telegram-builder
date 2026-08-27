#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/JerkgramCore/Sources/JerkgramStore.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1"


OLD_OBSERVERS = '''    private static let lifecycleObservers: [NSObjectProtocol] = [
        NotificationCenter.default.addObserver(
            forName: Notification.Name("UIApplicationDidEnterBackgroundNotification"),
            object: nil,
            queue: nil,
            using: { _ in JerkgramCaptureRecorder.flushSynchronously() }
        ),
        NotificationCenter.default.addObserver(
            forName: Notification.Name("UIApplicationWillTerminateNotification"),
            object: nil,
            queue: nil,
            using: { _ in JerkgramCaptureRecorder.flushSynchronously() }
        ),
    ]
'''

NEW_OBSERVERS = '''    // MARK: Jerkgram v1.2M BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1
    // UIKit lifecycle notifications are normally posted on the main thread.
    // Never wait there for JSONL/index disk I/O: the capture queue can be busy
    // rebuilding or appending its index and a queue.sync here freezes the whole UI.
    private static let lifecycleObservers: [NSObjectProtocol] = [
        NotificationCenter.default.addObserver(
            forName: Notification.Name("UIApplicationDidEnterBackgroundNotification"),
            object: nil,
            queue: nil,
            using: { _ in JerkgramCaptureRecorder.requestLifecycleFlush() }
        ),
        NotificationCenter.default.addObserver(
            forName: Notification.Name("UIApplicationWillTerminateNotification"),
            object: nil,
            queue: nil,
            using: { _ in JerkgramCaptureRecorder.requestLifecycleFlush() }
        ),
    ]

    private static func requestLifecycleFlush() {
        _ = self.lifecycleObservers
        self.queue.async {
            while !self.pendingEvents.isEmpty {
                guard self.flush(scheduleContinuation: false) else { break }
            }
        }
    }
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 lifecycle freeze] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text
    require(text.count(OLD_OBSERVERS) == 1, f"expected one Build118 lifecycle observer owner, found {text.count(OLD_OBSERVERS)}")
    require("public static func flushSynchronously()" in text, "Build118 synchronous flush bridge missing")
    updated = text.replace(OLD_OBSERVERS, NEW_OBSERVERS, 1)
    require(MARKER in updated, "marker missing after patch")
    return updated


def main() -> None:
    require(TARGET.is_file(), f"target missing: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")
    updated = patch_text(original)
    TARGET.write_text(updated, encoding="utf-8")
    print("[Build124 lifecycle freeze] GREEN")
    print("[Build124 lifecycle freeze] background/terminate capture flush no longer blocks the lifecycle caller")


if __name__ == "__main__":
    main()
