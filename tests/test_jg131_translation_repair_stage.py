"""Exercise the real terminal materializer on small byte-exact source trees."""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class RepairStage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.before = {'submodules/A.swift': b'let a = 1\n', 'submodules/Z.swift': b'let z = 1\n'}
        self.after = {'submodules/A.swift': b'let a = 2\n', 'submodules/Z.swift': b'let z = 2\n', 'submodules/New.swift': b'let added = true\n'}
        for name, data in self.before.items():
            p = self.source / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        patch = ''
        for name in sorted(self.after):
            old = self.before.get(name)
            patch += 'diff --git a/{0} b/{0}\n'.format(name)
            if old is None:
                patch += 'new file mode 100644\n'
            patch += ''.join(difflib.unified_diff((old or b'').decode().splitlines(True), self.after[name].decode().splitlines(True), fromfile='a/' + name if old is not None else '/dev/null', tofile='b/' + name))
        self.patch = self.root / 'repair.patch'
        self.patch.write_text(patch)
        sha = lambda data: hashlib.sha256(data).hexdigest() if data is not None else None
        self.manifest = self.root / 'repair.json'
        self.manifest.write_text(json.dumps({'upstream_sha': 'fb0e62ba8a147f0821da6aa63c09da7d79a10111', 'patch_sha256': sha(self.patch.read_bytes()), 'owners': {n: {'before_sha256': sha(self.before.get(n)), 'after_sha256': sha(d)} for n, d in self.after.items()}}))
        spec = importlib.util.spec_from_file_location('repair_under_test', ROOT / 'scripts/materialize_jg131_translation_repair.py')
        self.stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.stage)
        self.stage.PATCH, self.stage.MANIFEST = self.patch, self.manifest

    def test_apply_and_reapply_are_byte_exact(self):
        self.stage.apply_repair(self.source)
        self.stage.apply_repair(self.source)
        self.stage.verify_repair(self.source)
        for n, d in self.after.items():
            self.assertEqual((self.source / n).read_bytes(), d)

    def test_corrupt_last_parent_leaves_first_untouched(self):
        (self.source / 'submodules/Z.swift').write_bytes(b'unknown\n')
        with self.assertRaises(RuntimeError):
            self.stage.apply_repair(self.source)
        self.assertEqual((self.source / 'submodules/A.swift').read_bytes(), self.before['submodules/A.swift'])
        self.assertFalse((self.source / 'submodules/New.swift').exists())

    def test_mixed_parent_and_result_rejected_before_mutation(self):
        (self.source / 'submodules/A.swift').write_bytes(self.after['submodules/A.swift'])
        with self.assertRaises(RuntimeError):
            self.stage.apply_repair(self.source)
        self.assertEqual((self.source / 'submodules/Z.swift').read_bytes(), self.before['submodules/Z.swift'])

    def test_reverse_view_restores_parent_and_omits_new_owner(self):
        self.stage.apply_repair(self.source)
        with self.stage.parent_source_view(self.source) as prior:
            for n, d in self.before.items():
                self.assertEqual((prior / n).read_bytes(), d)
            self.assertFalse((prior / 'submodules/New.swift').exists())
        self.stage.verify_repair(self.source)

    def test_tampered_patch_rejected_without_mutation(self):
        self.patch.write_text(self.patch.read_text() + '\n#tampered\n')
        with self.assertRaises(RuntimeError):
            self.stage.apply_repair(self.source)
        for n, d in self.before.items():
            self.assertEqual((self.source / n).read_bytes(), d)


if __name__ == '__main__':
    unittest.main()
