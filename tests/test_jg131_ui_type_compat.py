"""Catch Postbox names introduced by product overlays after upstream UI import removal."""
from pathlib import Path
import json
import re
import subprocess
import unittest
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/swiftgram-src'

class UITypeCompatibilityTests(unittest.TestCase):
    def test_product_ui_additions_do_not_reintroduce_unimported_postbox_types(self):
        owners = json.loads((ROOT / 'patches/jg13-stable.product.sha256.json').read_text())
        symbols = ('PeerId', 'MessageId', 'MessageIndex', 'MediaId', 'ValueBoxEncryptionParameters')
        violations = []
        for name in owners:
            if not name.startswith('submodules/TelegramUI/') or not name.endswith('.swift'):
                continue
            source = (SOURCE / name).read_text()
            if re.search(r'^import Postbox\b', source, re.M):
                continue
            original = subprocess.run(['git', 'show', 'HEAD:' + name], cwd=SOURCE, capture_output=True, text=True)
            stock = original.stdout if original.returncode == 0 else ''
            for symbol in symbols:
                token = r'(?<![\w.])' + symbol + r'\b'
                if re.search(token, source) and not re.search(token, stock):
                    violations.append(name + ': ' + symbol)
        self.assertEqual(violations, [], 'overlay introduced a type whose upstream UI import was removed')

    def test_exact_stage_refuses_tamper_and_repeat(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import materialize_jg131_ui_type_compat as stage
        m = stage.manifest()
        final = (SOURCE / m['owner']).read_text()
        parent = final
        for old, new in reversed(stage.REPLACEMENTS):
            parent = parent.replace(new, old, 1)
        self.assertEqual(stage.digest(parent.encode()), m['before_sha256'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / m['owner']
            path.parent.mkdir(parents=True)
            path.write_text(parent + '\n// unexpected change\n')
            before = path.read_bytes()
            with self.assertRaises(RuntimeError): stage.apply_ui_types(root)
            self.assertEqual(path.read_bytes(), before)
            path.write_text(parent)
            stage.apply_ui_types(root)
            stage.verify_ui_types(root)
            self.assertEqual(path.read_text(), final)
            with self.assertRaises(RuntimeError): stage.apply_ui_types(root)
            path.write_text(final + '\n// unexpected change\n')
            with self.assertRaises(RuntimeError): stage.verify_ui_types(root)

if __name__ == '__main__': unittest.main()
