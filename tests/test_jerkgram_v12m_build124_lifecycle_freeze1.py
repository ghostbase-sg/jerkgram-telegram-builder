from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_lifecycle_freeze1.py"


class Build124LifecycleFreezeTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_lifecycle_freeze", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''public enum JerkgramCaptureRecorder {
    private static let queueKey = DispatchSpecificKey<Void>()
    private static let queue: DispatchQueue = {
        let queue = DispatchQueue(label: "jerkgram.capture.recorder", qos: .utility)
        queue.setSpecific(key: JerkgramCaptureRecorder.queueKey, value: ())
        return queue
    }()
    private static var pendingEvents: [JerkgramCanonicalEvent] = []
    private static let lifecycleObservers: [NSObjectProtocol] = [
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

    @discardableResult
    private static func flush(scheduleContinuation: Bool = true) -> Bool {
        return true
    }

    public static func flushSynchronously() {
        _ = self.lifecycleObservers
        let drain: () -> Void = {
            while !self.pendingEvents.isEmpty {
                guard self.flush(scheduleContinuation: false) else { break }
            }
        }
        if DispatchQueue.getSpecific(key: self.queueKey) != nil {
            drain()
        } else {
            self.queue.sync(execute: drain)
        }
    }
}
'''

    def test_lifecycle_observers_never_sync_flush(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        start = result.index("private static let lifecycleObservers")
        end = result.index("private static func requestLifecycleFlush()", start)
        observer_region = result[start:end]
        self.assertIn("BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1", result)
        self.assertNotIn("flushSynchronously()", observer_region)
        self.assertEqual(observer_region.count("requestLifecycleFlush()"), 2)

    def test_lifecycle_flush_is_dispatched_to_utility_queue(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        start = result.index("private static func requestLifecycleFlush()")
        end = result.index("@discardableResult", start)
        block = result[start:end]
        self.assertIn("self.queue.async", block)
        self.assertIn("while !self.pendingEvents.isEmpty", block)
        self.assertNotIn("self.queue.sync", block)

    def test_existing_explicit_sync_bridge_is_not_broadened(self):
        module = self.load_patch()
        result = module.patch_text(self.fixture())
        self.assertEqual(result.count("public static func flushSynchronously()"), 1)
        sync_start = result.index("public static func flushSynchronously()")
        self.assertIn("self.queue.sync(execute: drain)", result[sync_start:])

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_text(self.fixture())
        twice = module.patch_text(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count("BUILD124_NONBLOCKING_LIFECYCLE_FLUSH1"), 1)


if __name__ == "__main__":
    unittest.main()
