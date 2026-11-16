from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from repackage_jg13_recovery import verify_recovery


class RecoveryProvenanceTests(unittest.TestCase):
    def test_exact_source_is_accepted_and_mismatches_are_blocked(self):
        config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'test-RAW-UNVERIFIED.ipa'
            archive.write_bytes(b'compiled recovery fixture')
            original = dict(config, ci_run_id='123', ci_commit='source-commit', ipa=archive.name,
                            ipa_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                            status='RAW COMPILED IPA; PACKAGING AND VERIFICATION NOT PASSED')
            report = root / 'test-RAW-UNVERIFIED.json'
            report.write_text(json.dumps(original))
            self.assertEqual(verify_recovery(root, config, '123', 'source-commit')[0], archive)
            for change in ({'ci_run_id': 'wrong'}, {'ci_commit': 'wrong'}, {'ipa_sha256': 'wrong'},
                           {'build_number': 0}, {'product_version': 'wrong'}, {'ipa': '../outside.ipa'}):
                report.write_text(json.dumps(dict(original, **change)))
                with self.assertRaises(RuntimeError, msg=str(change)):
                    verify_recovery(root, config, '123', 'source-commit')


if __name__ == '__main__':
    unittest.main()
