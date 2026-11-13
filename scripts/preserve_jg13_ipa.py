"""EXIT-trap recovery for an IPA emitted before a failed Bazel/package action."""
from pathlib import Path
import json, sys
from package_jg13 import ROOT, preserve_raw_ipa
if __name__ == '__main__':
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    name = f'Jerkgram-{config["product_version"]}-Build{config["build_number"]}'
    if config.get('artifact_suffix'): name += '-' + config['artifact_suffix']
    out = ROOT / 'artifacts'
    compiled = Path(sys.argv[1])
    if compiled.is_file() and not (out / (name + '-RAW-UNVERIFIED.ipa')).exists():
        out.mkdir(exist_ok=True)
        preserve_raw_ipa(compiled, out, name, config)
