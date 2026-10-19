import os
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))
class RecoveryCacheTests(unittest.TestCase):
    def setUp(self):
        self.source = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift").read_text()
    def test_names_use_loaded_snapshot_and_skip_unchanged(self):
        body = self.source.split("private enum GhostBasePublicPeerNameStore", 1)[1].split("func ghostBaseStorePublicPeerName", 1)[0]
        self.assertIn("loadIfNeeded", body)
        self.assertIn("self.values?[key] == name && self.order.last == key", body)
        self.assertIn("self.values?[String(peerId.toInt64())]", body)
    def test_media_cache_serializes_its_own_copy_and_cleanup(self):
        body = self.source.split("private enum GhostBaseDeletedMediaCache", 1)[1].split("func ghostBasePreserve", 1)[0]
        self.assertIn("DispatchQueue.getSpecific(key: self.queueKey)", body)
        self.assertIn("self.queue.sync", body)
        self.assertIn("self.queue.async", body)
        self.assertIn("ghostBasePruneEmptyDeletedMediaDirectories(root: root)", body)
if __name__ == "__main__": unittest.main()
