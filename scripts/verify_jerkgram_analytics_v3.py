#!/usr/bin/env python3
"""Verify exact materialized v3 source owners and the hard disabled production gate."""
import argparse
import json
from pathlib import Path
from apply_jerkgram_analytics_v3 import ROOT, MANIFEST, PAYLOADS, digest, verify_pin


def verify(source):
    source = verify_pin(source)
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get('production_v3_delivery') is not False:
        raise RuntimeError('Analytics v3 production delivery approval has not been granted')
    for name, hashes in manifest['owners'].items():
        if digest((source / name).read_bytes()) != hashes['after_sha256']:
            raise RuntimeError('Analytics v3 materialized owner changed: ' + name)
    for name in PAYLOADS:
        path = source / 'submodules/TelegramUI/Sources' / name
        if digest(path.read_bytes()) != manifest['payloads'][name]:
            raise RuntimeError('Analytics v3 materialized payload changed: ' + name)
    core = (source / 'submodules/TelegramUI/Sources/JerkgramAnalyticsV3.swift').read_text()
    if core.count('static let productionTransportEnabled = false') != 1:
        raise RuntimeError('Analytics v3 production transport must remain hard-disabled')
    print('Analytics v3 exact materialized source VERIFIED; production transport OFF; native/app/device results separate')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT / 'work/swiftgram-src')
    verify(parser.parse_args().source_root)
