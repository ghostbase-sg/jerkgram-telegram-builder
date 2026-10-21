# Download Boost — Telegram iOS 13.0 / Build165

Source baseline: Official Telegram-iOS `f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838`.
Product parent: Build164 `e2ca8607462bc675ad6f619a4e643136598ad898`.
Product identity remains 1.2.0 Beta 1 / telemetry 1.2.0-beta.1; build165.
This is a client scheduling optimization, not a Telegram Premium entitlement.

## Historical evidence (not the 13.0 source of truth)

The old Build140 Boost1→Boost2 chain, dated12 September2026, survives in
`origin/dev/build133-runtime-repair` and later branches including
`origin/dev/build141-jank-probe`. The original creation branch cannot be established
from branch containment alone. Commits: `c93f39a` tests, `27c6ae8` patcher,
`7a189e7` verifier, `dedc122` build hook; `075a4d7`/`0489db8`/`aa4e612` completed
four-owner pending wiring; `c28930b` semantic renderer; `17438c3` navigation regression
test; `00515a6` native pushed picker; `eb96ff6`/`d4b4418` verifier repair.

Historical source owners were FetchV2.swift, GhostBaseSettingsController.swift and
JerkgramStrings.swift. Network.swift was checked, not patched. Off returned stock;
Medium512KiB/pending8, Maximum1MiB/pending12. The part-size helper required known
size>1MiB; the pending helper did not check size or CDN. All four old pending6
constructor sites were replaced, including CDN. Only CDN part size128KiB was
explicitly preserved. Global storage was `jerkgram.global.DownloadBoost`, deliberately
excluded from account-scoped state. Build165 uses the current canonical per-account
contract instead. Historical source/build-hook evidence does not establish successful
compilation, native test execution, measured speed or device runtime. No such outcome
is claimed, and no deeper historical CDN rationale was found beyond retaining stock
part size.

Swiftgram reference: `Swiftgram/Telegram-iOS` commit
`cf8b23beaaac4126a396337ac2d5be13f9f76b66`, specifically
`Swiftgram/SGSimpleSettings/Sources/SimpleSettings.swift` helpers
`getSGDownloadPartSize` and `getSGMaxPendingParts`, plus FetchV2.swift call sites.
It uses512KiB/8 and1MiB/12, preserves known<=1MiB part sizes and stock CDN128KiB,
but boosts unknown sizes and CDN pending too. Its older FetchV2 lacks the current
13.0 Rust adaptive machinery. Build165 therefore adopts only the bounded size/window
idea, retaining all CDN scheduling and unknown-size behavior as stock.

## Bounded owner map

| Owner | Responsibility | Changed? |
|---|---|---|
| TelegramCore/Network/FetchedMediaResource.swift | public fetch initiation through MediaBox | No |
| Postbox/MediaBox.swift | resource/range contexts, priority and disposal | No |
| TelegramCore/Account/Account.swift | installs MediaBox fetch closure; auxiliary resource routing | No, regression locked |
| TelegramCore/State/Fetch.swift | secret/cloud/HTTP/local and other resource dispatch | No |
| TelegramCore/Network/MultipartFetch.swift | selects V2 for experimental downloads and TelegramCloudMediaResource; V1 otherwise | No, locked |
| TelegramCore/Network/Network.swift | engine kind, useExperimentalDownload (default true), ios_killswitch_disable_downloadv2; transport configuration | No, locked |
| TelegramCore/Network/FetchV2.swift | DC/CDN scheduling, alignment, adaptive window/size, hashes, retry, fallback, cancellation | Only policy injection, three DC state constructors, adaptive upper target and bounded debug summaries |
| TelegramCore/Network/MultiplexedRequestManager.swift | shared transport queue, priorities, bounded workers, request disposal | No, locked |
| TelegramCore/Network/Download.swift | network execution helpers, including unrelated upload helpers | No, locked |
| TelegramCore/Network/FetchHttpResource.swift | separate HTTP resource fetch | No, locked |
| TelegramCore/Network/MultipartUpload.swift | upload pipeline | No, locked |

Paths in this table are under `submodules/`. Secret-file decryption, local resources,
HTTP and V1 do not acquire Boost. A settings label cannot establish which path a
particular resource actually used. The server kill switch can select V1.

## Official stock parameters

V2 `fastDownloads` means **Rust engine**, not Premium account.

| V2 parameter | Ordinary engine | Rust engine |
|---|---|---|
| DC part, initial | 128 KiB (stories 512 KiB) | 128 KiB (stories 512 KiB) |
| DC max pending | 6 | 16 |
| CDN initial part / max aligned part | 128 / 256 KiB | 128 / 256 KiB |
| CDN max pending | 6 | 32 |
| adaptive initial window | unused by non-Rust scheduler | 6, minimum2, maximum state's pending cap |
| adaptive DC size | fixed initial | 128 / 512 KiB |

Rust raises its window by one below1s request latency and halves it above2s,
with a2s adjustment interval. The size estimator uses recent2s, at least4parts:
at least4MiB/s promotes512KiB; below1.5MiB/s retreats128KiB. Unknown size initially
limits scheduling to one request. Stock V2 has no small-file size threshold.

DC requests retain4KiB alignment, maximum1MiB and1MiB boundary constraints.
CDN retains128KiB alignment/hash blocks,1MiB hash-query boundaries, AES-CTR
offset/16 counter, key32/IV16 validation and all short-result/hash checks.
No CDN request flag, key, token, reupload generation or retry counter changes.

V1 stock is distinct: known non-story files<=512KiB use16KiB/parallel16;
larger files use512KiB/parallel8; unknown files128KiB/parallel1.
Stories use512KiB, parallel4 when known>512KiB, otherwise1. V1 is untouched.

The shared ordinary transport has3 requests/worker ×4 workers per target key;
Rust CDN uses4×8. These limits and priorities remain unchanged. A pending-parts
cap is a scheduler limit, not a promise of that many simultaneous sockets.

## Build165 policy

Only unencrypted V2 DC sessions whose size is already known and exceeds1MiB
are eligible. This conservative threshold avoids extra overhead on small files;
unknown-size eligibility is fixed for the session, even if size becomes known.

| Mode | Eligible DC initial part | non-Rust pending cap | Rust pending cap | Rust initial window | Rust adaptive upper target |
|---|---|---|---|---|---|
| Off | stock128KiB / story512KiB | 6 | 16 | 6 | 512KiB |
| Medium | 512KiB | 8 | 16 | 8 | 512KiB |
| Maximum | 1MiB | 12 | 16 | 12 | 1MiB |

All CDN modes, small/unknown/encrypted sessions retain stock values. Stock Rust
slow-link backoff is preserved. Maximum does not increase the already-high Rust
pending ceiling; it increases the initial window and allowed fast-link part size.
DC1MiB is within the existing alignment/request contract. CDN sizes are deliberately
not increased because decryption/hash validation and smaller alignment limits
are separate contracts. Active sessions keep an immutable policy snapshot;
settings affect **new fetch sessions**, not necessarily an already-existing MediaBox
resource context on cancel/resume.

Memory remains bounded per session, but is higher in enabled modes. At the largest
DC part size, pending payload envelopes are12MiB non-Rust /16MiB Rust; an additional
similarly bounded ready buffer may coexist. These are not total RSS limits.
Multiple concurrent resources add memory pressure. No throughput guarantee is made.

## Settings, storage and logs

Jerkgram → Media & Stories → Download Boost; RU equivalents and all three option
labels use the existing JerkgramStrings architecture. Footer explains server limits
and new-session semantics. A native pushed ItemListController reuses the existing
option-row renderer. No new popup/navigation framework.

Per-account canonical storage key:
`jerkgram.account.<peerId>.setting.jerkgram.DownloadBoost.Mode`.
The existing changed-settings persistence owns writes and synchronous runtime
projection. The new setting deliberately does **not** migrate a global projection
into a new account: missing/invalid scoped values mean Off. An NSLock-protected,
bounded32-account cache avoids per-part defaults/file/JSON reads. Cold fetch-session
lookup reads just this one scoped string. UI changes update the same cache.
Debug summaries are capped at32 per process across all accounts, with no resource
IDs and no per-part logging added. They report mode/path/part/pending/initial window.

No isPremium check or account entitlement changes. No new Telegram API request.
Existing upload.getFile/getCdnFile requests continue through normal transport.
Server allocation, priority, bandwidth, Premium throttling/FLOOD_PREMIUM_WAIT and
entitlement decisions remain under Telegram control. The client can reduce request
round-trip idle time and start with a larger bounded window; it cannot override
those server decisions or create bandwidth unavailable on the connection.

## Production delta and integration

Exactly four final source owners differ from Build164:

1. `submodules/TelegramCore/Sources/Network/FetchV2.swift`.
2. New `submodules/TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift`.
3. `submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift`.
4. `submodules/TelegramPresentationData/Sources/JerkgramStrings.swift`.

Canonical chain: materialize current product → configure release UI → apply Build164
App Icons → apply Boost → configure identity → full source verifier → native tests →
Bazel → IPA packaging. TelegramCore's existing Sources glob includes the helper.
The App Icons payload, UI gates, icon resources, declarations and runtime logic are
unchanged. Its verifier only recognizes and removes the exact reviewed Boost delta
before comparing the Build164 parent hash. The same applies to release UI checks.

Builder additions: materializer, Swift payload, four-owner/eleven-lock manifest,
Python stage tests, native policy runner, preflight workflow, this report.
Integration updates configure/verify/build scripts, release identity build number,
existing verifier descendant support and telemetry fixture build165.

## Verification and limitations

The manifest validates complete before/after owner hashes, not a marker. Exact reverse
transforms recover all Build164 parent bytes. All inputs and outputs are validated
before writes; reapplication fails without a duplicate. Eleven independent locks
protect transport/upload, Account, App Icons owners, AppDelegate and Core BUILD.
The root verifier checks the normal release identity and existing product contracts.

Local: Python compile, stage2 tests and full source contracts pass. Existing recovery,
portable forwarding, cache, release UI and App Icons contracts were also run. Review
found and fixed global-to-account migration; a dedicated native regression covers it.
macOS CI separately performs clean materialization, Swift syntax parsing and executes
the real policy/settings payload over288 cases (3modes ×6sizes ×2engines ×2story
×2encryption ×2CDN), real stock alignment including>4GiB offsets, account isolation,
immutable snapshots and debug budget. Full build runs all existing native regressions.
CI links and final build outcome are reported with the delivery commit; compile
success is never device/runtime success.

## Device matrix (required after IPA)

Use the same large uncached document/video and the same network for comparisons.
Cached downloads do not measure Boost. Repeat runs and compare duration/average
throughput; do not infer improvement from an isolated peak. Check real account remains
non-Premium and all unaffected server-gated functions retain their normal status.

| Test | Expected checks |
|---|---|
| Off | large file, progress/completion, cancel/resume, redownload, no crash; stock policy |
| Medium | large file, progress, cancel/resume, sequential and simultaneous resources, no stuck progress |
| Maximum | same plus a long large transfer, heat, memory pressure, no OOM/crash |
| Types | video, document, original photo/media, audio; CDN and non-CDN when reproducible |
| Regression | streaming seek/playback, gallery, chat media, upload/send file, Build164 App Icons |
| Storage | relaunch; Off→Medium→Maximum→Off on new sessions; account A/B isolation and B defaultOff |
| In-flight switch | existing fetch keeps old parameters; new resource/session gets selected mode |
| Network failure | disconnect/reconnect, cancel/resume, background/foreground, file-reference refresh |

Unverified until device: actual speed, battery/heat, multi-file RSS, background lifecycle,
all server-driven CDN redirects/hash/reupload failures, engine-specific runtime behavior.
CDN remains stock, so its speed may be unchanged. V1/HTTP/secret/local paths are out
of Boost scope. No other Local Premium feature is part of this change.
