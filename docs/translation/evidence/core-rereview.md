# Core review round 1 — scoped resolution

Scope: compared only `core-review-before` to `source` for TelegramCore `Translate.swift`, reviewed the amended core test and `cases.swift`, and read the round 1 section of `CORE-REPORT.md`. The wrapper baseline correction and concurrent UI work were excluded. No production edits or builds were performed.

## Finding disposition

| Original finding | Result | Evidence |
| --- | --- | --- |
| P1 timer/job retention cycle | **ADDRESSED** | The timeout closure now captures both admission and job weakly. The identity-checked terminal handler cancels and sets `job.timer = nil` before disposing transport. The scheduled timeout cannot retain job/start/input/account through the former cycle. |
| P2 variable entity payloads bypass byte accounting | **ADDRESSED** | `jerkgramTranslationPayloadBytes` serializes the complete entity array, includes UTF8 text and structural overhead, checks arithmetic overflow, and is called before hashing/admission and before cache retention. Oversized input is rejected; oversized output is not cached. |

No additional actionable defect was identified in this fix diff.

## API and fixture evidence

Independently fetched the exact pinned [`SyncCore_TextEntitiesMessageAttribute.swift`](https://github.com/TelegramMessenger/Telegram-iOS/blob/fb0e62ba8a147f0821da6aa63c09da7d79a10111/submodules/TelegramCore/Sources/SyncCore/SyncCore_TextEntitiesMessageAttribute.swift), blob `db354b607912ccc651030003d8dc5c0f692b1681`. `MessageTextEntity` is `Codable`; its actual `encode(to:)` writes `.TextUrl` destination, `.Pre` language and the `.CustomEmoji` sticker-pack reference. Thus using `JSONEncoder().encode(text.1)` has a confirmed conformance and covers the previously uncounted strings. These are encoded-payload bounds with overhead, not exact process heap measurements.

The amended native fixture checks production start/transport capture release through weak probes after success, last-subscriber cancellation and timeout. It also checks giant TextUrl input rejection and repeated oversized-output requests to establish that the result is not retained in cache. Its entity shape is minimal and Encodable; it does not compile the real Telegram entity owner. Full production Swift compilation remains a separate gate.

Scoped Python verification: **7 tests, 6 passed, 1 explicitly skipped** because Swift is absent. Therefore weak-lifetime and giant-entity behavioral cases have been inspected but have **not executed** here. No native compilation, device, translation-quality or backend-success claim is made.
