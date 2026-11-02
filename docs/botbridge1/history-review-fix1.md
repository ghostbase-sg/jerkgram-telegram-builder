### Finding Verdicts

- **R1 — Reservation wait lacked an independent watchdog — ADDRESSED.** `source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift:530–564` arms the lease timer before subscribing to the reservation transaction. The timer uses the smaller of ten seconds and the generation's remaining wall/monotonic time. The reservation callback no longer creates or renews it. Closing the lease gate prevents a subsequently released reservation from mutating progress or dispatching transport. `builder/tests/fixtures/botbridge1/controller.swift:195` and the following held-reservation scenarios exercise timeout, modern-operation release, stale transaction rejection, and reservation wait consuming the original lease window. Native execution remains pending.
- **R2 — Policy fixture committed the wrong, unreserved value — ADDRESSED.** `builder/tests/fixtures/botbridge1/policy.swift:26–32` now commits `afterCommit`, which reserved the next request, and separately verifies that the unreserved copy is rejected as corrupt. The production reservation invariant was not weakened.
- **R3 — Complete production-controller behavioral harness missing — ADDRESSED.** `builder/tests/test_jg131_botbridge1_history.py:148` assembles the complete unchanged production controller, lease, policy, response adapters and storage helpers. `builder/tests/fixtures/botbridge1/controller.swift:1–369` supplies controllable serial scheduling, clocks/timers, transport subscriptions/disposal, and suspended transaction boundaries. Its scenarios cover response shapes, first-payload consumption, progressing empty/deduplicated slices, modern work between pages, timeout/error/cancellation, stale callbacks and transactions, generation/account isolation, crash/resume boundaries, request/deadline limits, and oversized updates. This addresses the missing source fixture; it does not establish successful native compilation or execution.
- **R4 — Repeated chat-vector parsing on the shared database queue — ADDRESSED.** `source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift:365–374` builds a bounded first-occurrence lookup and ordered parsed list once; the per-message lookup uses current transaction metadata first, and peer insertion reuses the parsed objects at `:430`. `builder/tests/fixtures/botbridge1/storage.swift:115–121` exercises 5,000 messages with absent user destinations and 10,000 chats and requires exactly one parser invocation per chat. This removes the previous message-count × chat-count parsing behavior while preserving current-peer and first-occurrence precedence.

### New Breakage in the Fix Diff

- **Minor — Already-terminal progress no longer emits the previous terminal/handoff events on startup.** `source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift:548–552` now routes an already-terminal record through `fail` before reservation. The existing `persistTerminal` guard at `:512–513` returns for terminal progress, so this path does not emit either event. Previously the reservation callback emitted both when it obtained no request. The operation still completes and sends no network request, so this does not reopen R1 or block this fix round. During Task 2, preserve an explicit terminal/handoff notification for this path if diagnostics need to observe the persisted outcome; add an event assertion to the completed-generation restart scenario. This observation concerns the new early-exit path, not a broader review of unchanged event machinery.
- **Critical/Important:** None introduced by the reviewed fix diff.

### Out-of-Scope Observations

- None. No fresh review of untouched product code was performed.

### Checks and Remaining Gates

- Reviewed the appended fix report and the five-file scoped diff against the frozen review-0 inputs. No suite was rerun; no product, fixture, baseline, index or branch was changed. This report is the only written artifact.
- The report names the focused command and records `Ran 14 tests; OK (9 passed, 5 skipped)`, with all five native fixtures explicitly skipped because Swift is unavailable. The added native harness and conversion-count assertions were inspected as source, not represented as executed behavior.
- Native fixture compilation/execution, generated-checkout key collision scan, authoritative stage inclusion, application build and device/server proof remain Task 3 gates. Explicit logout/removal registry and diagnostic integration remain Task 2 work.
- The controller independently resolved the earlier provenance uncertainty: 403 genuine product files and 142 copied Git metadata files match, the ten added official Git blobs match, and the frozen BASELINE SHA256 is `fa557c77f423de18ccce8747e9e279091628c8de319488cf39788faf09ac4746`. This is controller-supplied verification; I did not repeat that audit.

### Verdict

**Fix round:** All findings addressed, no new Critical/Important breakage.

**Spec compliance:** Approved for this scoped Task 1 source-review gate, with the explicitly pending native and integration gates above.

**Code quality:** Approved with the nonblocking terminal-event observation. R1–R4 are closed; no additional fix round is required for these findings.

Paths beginning `source/` refer to `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task1/`. Paths beginning `builder/` refer to `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder/` with that prefix removed.
