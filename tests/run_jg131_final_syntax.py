"""Parse every changed Swift owner on the real pinned iOS build host."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from jg131_final_stages import STAGES
owners=set()
for stage, _, _ in STAGES: owners.update(stage.manifest()['owners'])
from materialize_jg131_performance_wave1 import manifest
owners.update(manifest()['owners'])
from materialize_jg131_translation_repair import MANIFEST as repair_manifest, manifest as translation_repair_manifest
if repair_manifest.exists():
    owners.update(translation_repair_manifest()['owners'])
from materialize_jg131_default_folder import MANIFEST as folder_manifest, manifest as default_folder_manifest
if folder_manifest.exists():
    owners.update(default_folder_manifest()['owners'])
for name in sorted(owners):
    if name.endswith('.swift'):
        subprocess.run(['xcrun','swiftc','-frontend','-parse',str(ROOT/'work/swiftgram-src'/name)],check=True)
print('Changed Swift owners PARSED; not type-checked or fully compiled')
