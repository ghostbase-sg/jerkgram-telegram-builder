"""Mandatory checks collect independent errors and still block the app build."""
from pathlib import Path
import importlib.util,subprocess,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stable182_gate',ROOT/'tests/run_jg132_post181.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
class RequiredChecks(unittest.TestCase):
    def test_runs_remaining_checks_and_reports_all_failures(self):
        calls=[]
        def execute(command,**kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, {'first':1,'middle':0,'last':2}[command[0]])
        with self.assertRaisesRegex(RuntimeError,'first.*last'):
            gate.run_required_checks([(n,[n]) for n in ['first','middle','last']],env={'REQUIRED':'1'},execute=execute)
        self.assertEqual(calls,[['first'],['middle'],['last']])
    def test_all_successful_checks_return_normally(self):
        calls=[]
        def execute(command,**kwargs):
            calls.append(command);return subprocess.CompletedProcess(command,0)
        self.assertIsNone(gate.run_required_checks([('one',['one']),('two',['two'])],execute=execute))
        self.assertEqual(calls,[['one'],['two']])
if __name__=='__main__':unittest.main(verbosity=2)
