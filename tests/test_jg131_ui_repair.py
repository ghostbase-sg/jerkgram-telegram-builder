"""Regression checks for shared card backgrounds, profile masks and Swift capture compatibility."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/swiftgram-src'

class UIRepairTests(unittest.TestCase):
    def stage(self):
        path = ROOT / 'scripts/materialize_jg131_ui_repair.py'
        self.assertTrue(path.exists(), 'four-owner UI and capture repair stage is missing')
        spec = importlib.util.spec_from_file_location('ui_repair', path)
        stage = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stage)
        return stage

    def test_restored_components_equal_official_source(self):
        stage = self.stage()
        for name in stage.CARD_OWNERS:
            expected = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=SOURCE)
            actual = (SOURCE / name).read_bytes()
            if name.endswith('TextFieldNode.swift'):
                text = actual.decode()
                self.assertTrue('self.backgroundNode.cornerRadius = hasCorners ? 26.0 : 0.0' in text)
                self.assertTrue('self.maskNode.image = nil' in text)
                text = re.sub(r'        // JG169 field corners begin\n.*?        // JG169 field corners end', '        self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil', text, flags=re.S)
                actual = text.encode()
            self.assertEqual(actual, expected, name)

    def test_capture_uses_explicit_weak_snapshot_after_controller_creation(self):
        stage = self.stage()
        text = (SOURCE / stage.DATA).read_text()
        self.assertTrue('picker.peerSelected = { [weak picker, weak controller = controller]' in text)
        self.assertFalse('picker.peerSelected = { [weak picker, weak controller]' in text)
        self.assertTrue('controller?.push(jerkgramChatRetentionController(' in text)
        self.assertTrue('controller = ItemListController(context: context, state: signal)' in text)

    def test_stage_rejects_repeat_and_tamper_without_partial_mutation(self):
        stage = self.stage()
        m = stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            subprocess.run(['git', 'init', '-q', str(target)], check=True)
            for name in m['owners']:
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                parent = stage.parent_bytes(name, (SOURCE / name).read_bytes())
                path.write_bytes(parent)
            name = stage.DATA
            path = target / name
            parent = path.read_bytes()
            path.write_bytes(parent + b'\n// unexpected change\n')
            before = {n: (target / n).read_bytes() for n in m['owners']}
            with self.assertRaises(RuntimeError): stage.apply_ui_repair(target)
            self.assertEqual(before, {n: (target / n).read_bytes() for n in m['owners']})
            path.write_bytes(parent)
            stage.apply_ui_repair(target)
            stage.verify_ui_repair(target)
            with self.assertRaises(RuntimeError): stage.apply_ui_repair(target)
            path.write_bytes(path.read_bytes() + b'\n// unexpected change\n')
            with self.assertRaises(RuntimeError): stage.verify_ui_repair(target)

if __name__ == '__main__': unittest.main()
