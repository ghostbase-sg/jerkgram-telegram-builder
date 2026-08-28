#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest

from tests.test_jerkgram_v12m_build124_onetime_remote_persistence1 import REMOTE_FIXTURE


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_persistence1.py"


def v08i2_clean(text: str) -> str:
    # apply_ghostbase_voice_circle_stars_v08i2.py rewrites the whole owner with
    # this exact cleanup, stripping indentation from whitespace-only lines.
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


class Build124OneTimeWhitespaceAnchorTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_onetime_persistence_whitespace", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_remote_consume_accepts_v08i2_cleaned_countdown_owner(self):
        module = self.load_patch()
        fixture = v08i2_clean(REMOTE_FIXTURE)
        self.assertNotEqual(fixture, REMOTE_FIXTURE)
        self.assertEqual(fixture.count(module.REMOTE_DECISION_ANCHOR), 0)

        updated = module.patch_remote_consumed_text(fixture)

        self.assertIn("BUILD124_PERSISTENT_ONETIME_REMOTE1", updated)
        self.assertEqual(updated.count("let jerkgramKeepOneTimeRemoteMedia = ("), 1)
        self.assertEqual(updated.count("if !jerkgramKeepOneTimeRemoteMedia && (attribute.timeout == viewOnceTimeout"), 2)


if __name__ == "__main__":
    unittest.main()
