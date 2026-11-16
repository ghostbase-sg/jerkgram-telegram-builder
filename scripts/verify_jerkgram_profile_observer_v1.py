#!/usr/bin/env python3
"""Source integrity/ownership check only; not proof of compilation or device behavior."""
import hashlib
import json
import os
from pathlib import Path
from apply_jerkgram_profile_observer_v1 import MANIFEST, PAYLOAD, PAYLOAD_NAMES, PREFIX, ROOT


def verify(root=ROOT):
    root = Path(root)
    if (root/(MANIFEST+'.pending')).exists():
        raise RuntimeError('Interrupted observer installation')
    manifest = json.loads((root/MANIFEST).read_text())
    for name, digest in manifest['after'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Observer source integrity mismatch: '+name)
    for name in PAYLOAD_NAMES:
        if (root/(PREFIX+name)).read_bytes() != (PAYLOAD/name).read_bytes():
            raise RuntimeError('Observer payload differs from builder: '+name)
    main = (root/(PREFIX+'JerkgramProfileObserver.swift')).read_text()
    for forbidden in ('String(describing:', 'Timer.scheduledTimer', 'DispatchQueue.main', 'BGAppRefreshTask', 'updateUserStatus'):
        if forbidden in main:
            raise RuntimeError('Unexpected observer operation: '+forbidden)
    if 'knownAbout' in main or 'cachedData as? CachedUserData' in main:
        raise RuntimeError('Unknown cached BIO treated as known')
    requests = (root/(PREFIX+'JerkgramProfileObserverRequests.swift')).read_text()
    for forbidden in ('retryRequest', 'forceUpdateCachedPeerData', 'updateCurrentPeerNotificationSettings', 'updateUserStatus'):
        if forbidden in requests:
            raise RuntimeError('Broad or unrelated BIO request work: '+forbidden)
    store = (root/(PREFIX+'JerkgramProfileHistoryStore.swift')).read_text()
    for required in ('cipher_plaintext_header_size=0', 'cipher_version', 'journal_mode=WAL', 'synchronous=FULL'):
        if required not in store:
            raise RuntimeError('Missing reviewed SQLCipher contract: '+required)
    print('[Profile observer13.2] SOURCE INTEGRITY PASS; native Swift/Bazel/device results are separate')


if __name__ == '__main__':
    verify()
