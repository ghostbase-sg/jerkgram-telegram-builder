#!/usr/bin/env python3
"""Package an identified, hash-verified compiled recovery IPA without a build."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from package_jg13 import ROOT, require, sha256_file


def verify_recovery(directory, config, run_id, commit):
    directory = Path(directory).resolve()
    reports = list(directory.glob('*-RAW-UNVERIFIED.json'))
    require(len(reports) == 1, 'Expected exactly one compiled recovery report')
    report = json.loads(reports[0].read_text())
    require(str(report.get('ci_run_id')) == str(run_id), 'Recovery run provenance mismatch')
    require(report.get('ci_commit') == commit, 'Recovery commit provenance mismatch')
    require(report.get('status') == 'RAW COMPILED IPA; PACKAGING AND VERIFICATION NOT PASSED', 'Unexpected recovery status')
    for key in ('product_version', 'product_display_version', 'product_technical_version',
                'build_number', 'bundle_id', 'bundle_short_version', 'upstream_new_sha'):
        require(report.get(key) == config[key], 'Recovery product mismatch: ' + key)
    name = report.get('ipa')
    require(isinstance(name, str) and Path(name).name == name and name.endswith('-RAW-UNVERIFIED.ipa'), 'Unsafe recovery archive name')
    compiled = directory / name
    require(compiled.is_file() and compiled.resolve().parent == directory, 'Recovery archive unavailable')
    require(sha256_file(compiled) == report.get('ipa_sha256'), 'Recovery archive digest mismatch')
    return compiled, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    config = json.loads((ROOT / 'jerkgram-migration.json').read_text())
    compiled, source = verify_recovery(args.input, config, args.source_run, args.source_commit)
    subprocess.run([sys.executable, str(ROOT / 'scripts/package_jg13.py'), str(compiled)], check=True)
    name = f'Jerkgram-{config["product_version"]}-Build{config["build_number"]}'
    if config.get('artifact_suffix'):
        name += '-' + config['artifact_suffix']
    report_path = ROOT / 'artifacts' / (name + '.json')
    report = json.loads(report_path.read_text())
    report.update(compiled_source_run=source['ci_run_id'], compiled_source_commit=source['ci_commit'],
                  compiled_source_sha256=source['ipa_sha256'], packaging_commit=report['ci_commit'])
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('Recovered source provenance and final IPA verification passed; no compilation performed')


if __name__ == '__main__':
    main()
