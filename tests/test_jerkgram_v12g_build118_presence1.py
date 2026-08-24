from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "scripts/ghostbase_v11g_unified_recovery1_payload/PresenceHelper.swift.fragment"


class Build118PresenceTests(unittest.TestCase):
    def test_presence_has_id_and_rejects_stale_until(self):
        text = SOURCE.read_text()
        self.assertIn("public var eventId: String?", text)
        self.assertIn("UUID().uuidString.lowercased()", text)
        self.assertIn("identities.insert(eventId)", text)
        self.assertIn("Int64(until) >= event.observedAt", text)
        self.assertNotIn("transitionKey(previous) == self.transitionKey(event)", text)
        self.assertNotIn(".hashValue", text)


if __name__ == "__main__":
    unittest.main()
