"""Execute account retention/backward compatibility against production Swift sources."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG_EXCLUDED_SOURCE', ROOT/'work/swiftgram-src'))

class ExcludedHistoryNativeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; native retention execution pending macOS CI')
    def test_policy_compatibility_and_account_isolation(self):
        fixture = r'''
let legacy = Data(#"{"historyDuration":"days30","mediaByteLimit":"gigabytes1","archiveSecretChats":false}"#.utf8)
let old = try JSONDecoder().decode(JerkgramRetentionPolicy.self, from: legacy)
assert(!old.retainExcludedChats)
var p = old
p.retainExcludedChats = true
let encoded = try JSONEncoder().encode(p)
let decoded = try JSONDecoder().decode(JerkgramRetentionPolicy.self, from: encoded)
assert(decoded.retainExcludedChats)
let config = JerkgramRetentionConfiguration(accountPeerId: 1, accountPolicy: p, chatOverrides: [JerkgramChatRetentionOverride(chatPeerId: 10, captureEnabled: false)])
assert(config.effectivePolicy(chatPeerId: 20).1.retainExcludedChats)
let defaults = UserDefaults(suiteName: "jg170-test-" + UUID().uuidString)!
try JerkgramRetentionRuntime.save(config, userDefaults: defaults)
assert(JerkgramRetentionRuntime.shouldRetainExcludedHistory(accountPeerId: 1, chatPeerId: 20, userDefaults: defaults))
assert(!JerkgramRetentionRuntime.shouldRetainExcludedHistory(accountPeerId: 1, chatPeerId: 10, userDefaults: defaults))
assert(!JerkgramRetentionRuntime.shouldRetainExcludedHistory(accountPeerId: 2, chatPeerId: 20, userDefaults: defaults))
// Retain only an actual exclusion; voluntary leaves and unknown forbidden peers stay excluded.
for mask in 0 ..< 16 {
    let excluded = mask & 1 != 0
    let member = mask & 2 != 0
    let retained = mask & 4 != 0
    let enabled = mask & 8 != 0
    let result = JerkgramRetainedChatPolicy.keep(excluded: excluded, wasMember: member, wasRetained: retained, enabled: enabled)
    assert(result == (excluded && (retained || (member && enabled))))
}
// Known member -> kicked while enabled -> retain across refresh and restart.
assert(JerkgramRetainedChatPolicy.keep(excluded: true, wasMember: true, wasRetained: false, enabled: true))
assert(JerkgramRetainedChatPolicy.keep(excluded: true, wasMember: false, wasRetained: true, enabled: false))
// Rejoin clears retention. A subsequent kick must obey the current setting.
assert(!JerkgramRetainedChatPolicy.keep(excluded: false, wasMember: false, wasRetained: true, enabled: true))
assert(!JerkgramRetainedChatPolicy.keep(excluded: true, wasMember: true, wasRetained: false, enabled: false))
// Explicit deletion clears retained state; an old forbidden refresh must not resurrect it.
assert(!JerkgramRetainedChatPolicy.keep(excluded: true, wasMember: false, wasRetained: false, enabled: true))
print("native retained-chat policy/account scope PASS")
'''
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)/'main.swift';main.write_text('import Foundation\n'+fixture)
            sources=[str(SOURCE/'submodules/JerkgramCore/Sources'/n) for n in ['JerkgramModels.swift','JerkgramRetention.swift','JerkgramIndex.swift']]
            # Retention references the index/store types: use all real Foundation-only core sources.
            sources=[str(p) for p in (SOURCE/'submodules/JerkgramCore/Sources').glob('*.swift')]
            subprocess.run(['swiftc','-warnings-as-errors',*sources,str(main),'-o',d+'/check'],check=True)
            subprocess.run([d+'/check'],check=True)
if __name__=='__main__': unittest.main()
