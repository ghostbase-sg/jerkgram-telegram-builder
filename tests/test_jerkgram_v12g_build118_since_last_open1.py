from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
ENGINE = REPO / "scripts/jerkgram_v12g_build118_time_machine1_payload/JerkgramTimeMachineIndex.swift"
OVERLAY = REPO / "scripts/apply_jerkgram_v12g_build118_since_last_open1.py"
UI = REPO / "scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramTimeMachineController.swift"


class Build118SinceLastOpenTests(unittest.TestCase):
    def test_first_visit_is_baseline_and_later_events_are_id_scoped(self):
        engine = ENGINE.read_text()
        self.assertIn("if previousValue == nil", engine)
        self.assertIn("eventIds: []", engine)
        self.assertIn("events: [JerkgramCanonicalEvent]", engine)
        self.assertIn("eventIds: matching.sorted", engine)
        ui = UI.read_text()
        self.assertIn("eventIds: Set<JerkgramEventId>? = nil", ui)
        self.assertIn("eventIds.contains(event.eventId)", ui)
        overlay = OVERLAY.read_text()
        self.assertIn("BUILD118_SINCE_LAST_OPEN1", overlay)
        self.assertIn("Set(changes.eventIds)", overlay)
        self.assertIn("changesSinceLastOpening", overlay)
        self.assertNotIn("message.text", overlay)


if __name__ == "__main__":
    unittest.main()
