from pathlib import Path
import re
import unittest


REPO = Path(__file__).resolve().parents[1]
STORE = REPO / "scripts/jerkgram_v12g_build118_core1_payload/JerkgramStore.swift"
INDEX = REPO / "scripts/jerkgram_v12g_build118_core1_payload/JerkgramIndex.swift"
RETENTION = REPO / "scripts/jerkgram_v12g_build118_storage1_payload/JerkgramRetention.swift"
SINCE_LAST_OPEN = REPO / "scripts/apply_jerkgram_v12g_build118_since_last_open1.py"
TIME_MACHINE_UI = REPO / "scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramTimeMachineController.swift"


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError(f"unterminated method: {signature}")


class Build118PerformanceContractTests(unittest.TestCase):
    def test_capture_append_never_loads_or_rewrites_the_account(self) -> None:
        source = STORE.read_text(encoding="utf-8")
        body = method_body(source, "public func append(_ event: JerkgramCanonicalEvent) throws")
        self.assertNotIn("loadAccount", body)
        self.assertNotIn("writeAccount", body)
        self.assertIn("appendBatch", body)

    def test_store_has_byte_range_index_and_bounded_chat_query(self) -> None:
        index = INDEX.read_text(encoding="utf-8")
        store = STORE.read_text(encoding="utf-8")
        for token in (
            "byteOffset: UInt64",
            "byteLength: UInt64",
            "messageNamespace: Int32?",
            "messageId: Int32?",
        ):
            self.assertIn(token, index)
        self.assertNotIn("searchKey", index)
        self.assertIn('"events.index.jsonl"', store)
        self.assertIn("private static var sharedIndexStates", store)
        self.assertIn("accountScopeMismatch", store)
        self.assertIn("public func indexRecords(", store)
        self.assertIn("public func eventPage(", store)
        ready_body = method_body(store, "public func readyIndexRecords(")
        self.assertIn("readyIndexLocked", ready_body)
        self.assertNotIn("ensureIndexLocked", ready_body)
        recovering_body = method_body(store, "public func appendBatchRecovering(")
        self.assertIn("allowExistingIdentical: true", recovering_body)
        self.assertIn("readEvent(accountPeerId:", store)

    def test_recovery_append_writes_canonical_data_before_skipping_index(self) -> None:
        source = STORE.read_text(encoding="utf-8")
        body = method_body(source, "private func appendLocked(")
        self.assertLess(
            body.index("canonicalHandle.write(contentsOf: canonicalAppend)"),
            body.index("guard maintainsIndex else { return }"),
        )

    def test_event_paging_uses_presorted_chat_records(self) -> None:
        source = STORE.read_text(encoding="utf-8")
        body = method_body(source, "public func eventPage(")
        self.assertIn("recordsByChat[chatPeerId]", body)
        self.assertIn(".reversed()", body)
        self.assertIn("pageUpperBound", body)
        self.assertNotIn(".filter", body)
        self.assertNotIn(".sorted", body)

    def test_capture_chat_index_has_append_fast_path(self) -> None:
        source = STORE.read_text(encoding="utf-8")
        body = method_body(source, "private func appendLocked(")
        self.assertIn("mergeAscending", body)
        self.assertNotIn("recordsByChat[chatPeerId]?.sort", body)

    def test_capture_recorder_reuses_one_store_and_batches(self) -> None:
        source = STORE.read_text(encoding="utf-8")
        recorder = source[source.index("public enum JerkgramCaptureRecorder"):]
        self.assertRegex(recorder, r"private static let store\s*=\s*JerkgramJSONLEventStore")
        self.assertIn("private static let maximumBatchSize = 32", recorder)
        self.assertIn("private static let maximumBatchDelay: Double = 0.25", recorder)
        self.assertIn("store.appendBatchRecovering", recorder)
        self.assertIn("Dictionary(grouping: events, by: { $0.accountPeerId })", recorder)
        self.assertIn("failedEvents.append(contentsOf: accountEvents)", recorder)
        self.assertIn("pendingEvents.insert(contentsOf: failedEvents, at: 0)", recorder)
        self.assertIn("private static let maximumPendingEvents = 4_096", recorder)
        self.assertIn("retryBackoffActive", recorder)
        self.assertIn("public static func flushSynchronously()", recorder)
        synchronous = method_body(recorder, "public static func flushSynchronously()")
        self.assertIn("while !self.pendingEvents.isEmpty", synchronous)
        self.assertNotRegex(recorder, r"JerkgramJSONLEventStore\(rootURL: rootURL\)\.append")

    def test_since_last_open_uses_index_interval_not_full_events(self) -> None:
        source = SINCE_LAST_OPEN.read_text(encoding="utf-8")
        self.assertIn("JerkgramCaptureRecorder.readyIndexRecords(", source)
        self.assertIn("afterSequence:", source)
        self.assertNotIn("eventStore.events(accountPeerId:", source)
        self.assertIn("records: records", source)

    def test_retention_runtime_caches_account_snapshot_and_chat_lookup(self) -> None:
        source = RETENTION.read_text(encoding="utf-8")
        runtime = source[source.index("public enum JerkgramRetentionRuntime"):source.index("public struct JerkgramCleanupPlan")]
        self.assertIn("private static var snapshots", runtime)
        self.assertIn("chatOverridesByPeerId", runtime)
        self.assertIn("snapshots[accountPeerId]", runtime)
        save_body = method_body(runtime, "public static func save(")
        self.assertIn("snapshots[configuration.accountPeerId]", save_body)

    def test_time_machine_loads_canonical_events_off_main_and_reuses_one_handle(self) -> None:
        ui = TIME_MACHINE_UI.read_text(encoding="utf-8")
        store = STORE.read_text(encoding="utf-8")
        self.assertIn("Queue.concurrentDefaultQueue().async", ui)
        self.assertIn("store.eventPage(", ui)
        self.assertIn("limit: 250", ui)
        self.assertIn("eventsPromise.set(JerkgramTimeMachinePageState", ui)
        self.assertIn("loadNextPage", ui)
        self.assertNotIn("while let page", ui)
        self.assertIn("case .loadMore: return Int32.max", ui)
        chat_branch = store[store.index("if let chatPeerId {"):store.index("return try self.loadAccount")]
        self.assertEqual(chat_branch.count("FileHandle(forReadingFrom:"), 1)


if __name__ == "__main__":
    unittest.main()
