# Beta 2 actual Postbox codec regression

Before owner edits (2026-11-05), portable codec guard was run against the unchanged release owner and failed because explicit decoding was absent. This is source-contract RED only; no Swift compiler exists on the Linux worker.

Native negative design, recorded before the repair: compile the frozen old policy separately with the actual pinned PreferencesEntry, complete Coding.swift and adapters, actual MurMurHash32 dependency. In -O, the old initial record must encode but decode nil (Int primitive mismatch); a second subprocess must read that record, construct corrupt fallback and terminate in the raw terminal single-value encoder. In -Onone, the old initial Int write must terminate at assertionFailure. Expected fatal processes are isolated and must never be accepted as successful fixed roundtrips.

The fixed harness will compile the production policy unchanged with those same actual codec sources under both -O and -Onone, then exercise initial/reservation/cursor/page/all terminal states, legacy primitive fields, malformed semantic records and repeated prepare/read/write. Missing native tooling is a pending result, and JG_BETA2_REQUIRE_NATIVE=1 must turn it into a failed gate.

## Mandatory native entrypoint

On macOS with Xcode Swift/Clang:

```
JG_BETA2_REQUIRE_NATIVE=1 JG_BETA2_CODEC_OWNER=/absolute/final/source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift python3 tests/test_jg131_beta2_bot_codec.py
```

The native test compiles both `-O` and `-Onone`, with Swift language mode 5 to match the pinned source conventions. It builds the exact official Objective-C hash implementation as a Clang module, then compiles complete pinned `Coding.swift`, all eight encoder/decoder adapter files, complete `PreferencesEntry.swift`, and complete `PostboxLogging.swift`. `MediaResourceId` is the only supporting declaration extracted verbatim from its pinned file, avoiding unrelated media/peer/message/cache subsystems. No codec method is replaced, extracted partially, or stubbed. `PROVENANCE.json` records Git blob SHA-1 and SHA-256 for all 14 official files; portable tests verify every byte.

The frozen old policy is compiled separately. Its optimized executable saves actual release-shaped PreferencesEntry bytes, demonstrates nil old Int decode, and traps in a separate corrupt-terminal subprocess. The same actual old bytes are passed to the fixed executable under both optimization settings and must preserve owner, peer and authorization generation through the actual production prepare/read/write helpers. The old debug executable must assert on its initial Int write.

The fixed harness also tests complete valid initial/reservation/cursor/page records with nonzero counters, all 15 terminal strings on fresh and active records, no-candidate state, required-field omissions, wrong schema/primitive width, unknown terminal, negative/oversized/out-of-policy counters, invalid timestamps/cursor, owner/peer/environment mismatch, empty bytes, safe serialization of corrupt fallback, and repeated relaunch-like prepare/read/write. Invalid in-memory counters are checked outside the `try!` boundary and sanitized by the production write helper before actual Postbox encoding.

## Scope and current result

Linux worker result: three portable guards PASS; native compile/execution SKIPPED because Swift/Xcode are unavailable. Mandatory-native mode FAILS in this environment as intended. Neither native reproduction nor device recovery is claimed.

The transaction/account objects in `native.swift` only supply byte storage and a valid account identity to unchanged production helpers; every persisted byte uses the actual codec. This is a codec boundary regression, not a real Postbox database, importer, queue, network, authorization, or device test. Corruption cases use valid Postbox framing with malformed values plus empty data; arbitrary hostile byte-stream fuzzing of global Postbox memory readers is outside this owner repair. Historical Any/JSON fixtures remain unchanged and are not treated as persistence evidence.

## CI dependency correction (2026-11-11)

Run42973251252 reached the actual codec compilation and failed in both optimization modes because complete Coding.swift calls `mdb_cmp_memn`, defined in official ValueBoxKey.swift. The standalone codec compile omitted that owner. The complete pinned file is now included from `support/ValueBoxKey.swift`, with independent Git blob and SHA-256 provenance and a portable check on actual compiler inputs. Its separate location avoids duplicating the independent Saved Tags fixture owner. No comparator or codec is stubbed; runtime source and fatal/roundtrip expectations remain unchanged. The successful Saved Tags SQLite/Core fixtures from that run do not establish bot-codec or app success; the replacement CI must execute this corrected closure.
