# Native UTF16 boundary fix

## Observed cause and failing evidence

Parent-provided native CI evidence: commit2843fd0, GitHub Actions run40889023877. The actual extracted production core fixture failed `reject split surrogate` for text `😀x`, entity range1..<2. The actual extracted UI mask fixture failed its unchanged-input assertion for a surrogate-interior mask range. These native failures are the RED evidence for this focused fix; expected outcomes were retained.

`Range(NSRange(...), in: text)` was assumed to reject every surrogate-interior endpoint. On the CI Swift6.4/Foundation runtime it accepted the failing range, so neither core validation nor recognition masking guaranteed valid scalar boundaries. A Foundation conversion success is not a substitute for checking UTF16 code units.

## Exact repair

Only two production owners changed:

- TelegramCore/Sources/TelegramEngine/Messages/Translate.swift: jerkgramValidTranslatedEntities.
- TranslateUI/Sources/ChatTranslation.swift: jerkgramTranslationRecognitionSample.

Both now inspect the original NSString UTF16 representation explicitly. An endpoint strictly inside the text is rejected when its immediately preceding code unit is a high surrogate0xD800...0xDBFF and its next code unit is a low surrogate0xDC00...0xDFFF. Zero/end endpoints are accepted; ordinary range bounds and nonempty range checks still run before code-unit access. Both lower and upper endpoints are checked. The test permits scalar boundaries inside combining graphemes; it does not require a Character/grapheme boundary.

The UI helper still takes the same prefix256-character sample, clips an entity's upper endpoint to that sample's UTF16 length, and validates the clipped endpoints before NSMutableString.replaceCharacters. It checks against immutable original sample code units, preserving offset stability for overlapping masks. A clipped range covering the final complete emoji is accepted; a lower/upper endpoint inside that emoji is skipped. No additional scans, arrays, history reads or asynchronous work were introduced; checking each endpoint uses at most two NSString code-unit reads.

Snapshots of both owners before the fix are at task-a/native-boundary-before. task-a/before remains the Build176 parent. Settings, routing, protocol, queue and shared footprint were not changed. Parent will regenerate patch/replay and rerun native CI. No commit, push, backend request or build was performed here.

## Actual-production fixture coverage

The existing extraction mechanisms remain: core fixture extracts production validation with the existing policy/admission owners; UI fixture extracts the real recognition helper verbatim. No test-side boundary algorithm was added and no existing expected assertion was relaxed.

Added core cases cover an invalid lower endpoint, invalid upper endpoint, valid whole emoji, valid range after emoji, full combining sequence and each scalar of a combining sequence. Added UI cases cover both invalid endpoints, whole emoji masking, full/individual combining-scalar masking, and upper clipping at a sample ending in an emoji—including lower/upper interior endpoints that must leave the sample unchanged. The supplemental UI source gate now checks the explicit code-unit guard in place of requiring the old Foundation range conversion.

## Scoped verification

```
JERKGRAM_TRANSLATION_REPAIR_SOURCE='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/task-a/source' python -m unittest discover -s jerkgram-telegram-builder/tests -p 'test_jg131_translation_core.py'
JERKGRAM_TRANSLATION_REPAIR_SOURCE='/home/pixi/ChatGPT/iOS DEV/jerkgram-next/task-a/source' python -m unittest discover -s jerkgram-telegram-builder/tests -p 'test_jg131_translation_ui_repair.py'
```

Core:7 tests,6 passed,1 native skip. UI:11 tests,9 passed,2 native skips. Swift is absent from this Linux environment, so the expanded native cases have not executed locally and no native GREEN, new Swift parse result or device-runtime result is claimed. The existing CI failures establish native RED; the parent CI rerun must establish native GREEN. Historical full-suite discovery was not rerun.

## Scoped owner hashes

- `submodules/TelegramCore/Sources/TelegramEngine/Messages/Translate.swift`: before `dc28c6c4b0e10c471e3c1bc3e2c2bad54bc81361d1a22e27ab3a519072c48b19`, after `1289237c2f91f0cd154a4b36c6fbb39dfb2ca3ea50fdabeb94d15565ec2367c5`.
- `submodules/TranslateUI/Sources/ChatTranslation.swift`: before `1583bf34b542920c36d72ba21e86958d6852dc0c5fb62c345b22298b2ec3e40e`, after `6fc860ae083057ed2d5ba16e428ab2247271a2697bebe6d9387f83801a5afdd3`.
