# BOTBRIDGE1 whole-branch review, round 0

## Scope and evidence

Reviewed the cumulative uncommitted candidate against builder base `5ba6add985d6995ca102d4e40d8da66e98f443c1`, the user specification and implementation plan dated 2026-11-02, design, decisions, progress ledger, scenario/cost/runtime documentation, and the requesting-code-review reviewer template. The authoritative change is `patches/jg131-botbridge1.patch` plus its manifest and builder integration. Reviewed all thirteen product-owner deltas, including the complete new history and diagnostic implementations, and inspected the final generated-source copies under `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task3/source` for surrounding manager/request/storage context. Also inspected the stage/verifier/runner, workflow and metadata changes, test extraction/proof boundaries and relevant native fixture definitions. README and the runtime JSON guide were read directly after the parent identified their later documentation-only additions.

Product file references below are relative to that generated source root; these files are delivered by the authoritative patch, not by checking in the draft tree. Builder file references are relative to `/home/pixi/ChatGPT/iOS DEV/jerkgram-telegram-builder`.

No reported test suite was rerun. No source, fixture, index, HEAD, branch or publication state was changed; this requested report is the sole written artifact. The parent supplied independent fidelity evidence for the thirteen owner inputs/outputs, all 403 unchanged modern product files and twelve accepted Swift fixture files. Those checks establish provenance, not execution of Swift or an app.

Reported local results remain overlapping evidence: composed 151 cases / 19 native skips; production 196 cases / 21 skips; BOT 50 cases / 13 skips. They must not be added or described as native behavioral passes. Required macOS fixture/full generated-source gates and the actual app/IPA are pending.

## Strengths

- The history adapter has a narrow ownership boundary. `JerkgramBotBridgeHistory.swift:251`, `:325` and `:614` validate the actual bot and authorization, import absent cloud IDs with current converters, and issue only getState/getDifference. It does not replace live AuthorizedAccountState, invoke generic historical replay, or construct another Account/Network/Postbox/update manager. The active old BotShadow pager and its dedicated logout suppression are removed.
- Durable reservation and commit are distinct. `JerkgramBotBridgeHistory.swift:109`, `:141`, `:585` and `:657` preserve the original generation budget and atomically commit imported messages and progress. Empty or entirely deduplicated slices can continue; terminal response kind controls completion. The activation watchdog at `:564` bounds reservation waits as well as transport, and lifetime/request gates are checked inside storage work.
- Current data is preserved deliberately: existing message IDs, including edited/live/retained deletion placeholders, are skipped; current peer metadata wins; same-response and known-session deletion evidence excludes absent candidates. The one-pass response chat index avoids the earlier message-by-chat conversion multiplication. The Postbox adapter changes only the two installed callback dispatch guards and retains the ordinary insertion default.
- Modern request algorithms remain recognizable and separately protected. Network additions observe cold subscription/result/error/disposal and use an independent weak scope box; worker additions pass explicit reply/post context without repurposing dependency tags or request payloads. The allowed-edit recovery checks supplement exact whole-owner provenance. Upload/internal retry/local-application gaps are explicitly disclosed.
- Diagnostic objects accept typed finite categories, counters and opaque identifiers. No diagnostic parameter loader, raw error description, message content or credential serialization was found. Weak namespace/record/generation/epoch targets prevent delayed cleanup callbacks from resolving a replacement account, and callbacks execute after registry unlocking. The exporter is separate from the general archive/log export and remains reachable from another active account.
- The terminal materializer validates the complete parent set before mutation, pins owner scope and output bytes, and reverses into a disposable parent view including absence of the new owners. The native/full-source requirements are wired before app compilation, and Build178/BOTBRIDGE1 identity is coherent across configuration, build and artifact naming. The scenario matrix correctly separates source proofs, extracted native fixtures and real device evidence.

## Issues

### Critical — Must Fix

None found.

### Important — Should Fix

**R1 / P2 — Continued appends defeat the promised 24-hour on-disk event retention.**

- **Files/symbols:** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:427` (`prune`), especially `:432`; `:444` (`drain`), especially active-file loading at `:453` and atomic rewrites at `:459` / `:468`; export filtering at `:491`. Covering fixture: `tests/fixtures/botbridge1/diagnostic_resources.swift`, the final TTL scenario.
- **What is wrong:** Pruning determines file age from `contentModificationDate`. Every drain reads the existing last event file, appends records, and atomically rewrites it, refreshing that date. With low steady activity before each 24-hour interval and insufficient volume to fill 256 KiB, the first records can remain physically stored for many days. The 24-hour per-record filter in export only omits them from the returned report; it never removes them from the retained JSONL file. The current TTL fixture manually makes the whole file's modification time old, so it does not exercise this case.
- **Why it matters:** The design and plan promise a 24-hour diagnostic retention limit, applied lazily on access. Access in this scenario actively extends old evidence retention instead. This is a bounded-storage/retention defect, not a claim that credentials are exposed or that export currently includes expired records.
- **Fix:** Enforce age using immutable file creation/rotation age or prune expired records before rewriting an active file. Keep fail-closed filesystem handling, byte/file caps and explicit retention-loss accounting. A lazy policy remains sufficient; no timer or broad storage refactor is needed.
- **Regression:** Seed a valid file containing an event older than 24 hours while keeping its modification time recent, append a fresh event, and inspect retained on-disk bytes after sink access. Assert that old evidence is purged, fresh evidence is retained when applicable, export remains correct, and loss accounting reflects the expiry. Exercise actual sink code, not only an export-filter assertion.

### Minor — Nice to Have

**R2 / P3 — Registry admission rejection produces no explicit diagnostic loss signal.**

- **Files/symbols:** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:285` (`BotBridgeDiagnosticRegistry.register`, guard at `:289`), `:337` (`BotBridgeDiagnosticOwner.admit`, return at `:341`); `submodules/TelegramCore/Sources/State/AccountStateManager.swift:1573` (failed admission returns before creating the controller).
- **What is wrong:** At the 32-live-target limit, or when a live target already occupies the namespace/record, registration correctly refuses admission. That Boolean failure disappears without a finite reason or sink-level loss counter. The new bot receives neither bridge work nor recorder events, leaving an operator unable to distinguish admission rejection from an account that was never observed.
- **Why it matters:** The plan explicitly requires fail-closed admission *and capacity-loss reporting*. Isolation is preserved, so this is a nonblocking observability omission, particularly unlikely in the intended small A/B/C experiment.
- **Fix:** Record a bounded, nonidentifying admission-loss counter/reason outside the rejected account recorder, or otherwise expose an explicit admission failure in the dedicated export. Keep the no-live-eviction policy and ordinary-user fast path. Cover capacity rejection separately from invalid-generation/duplicate-target cases; do not export record IDs or retain rejected Accounts.

## Recommendations

Address R1 before publication. R2 can be handled in the same small fix wave or explicitly deferred by the executor with its observability limitation retained. Add the focused retention regression and review only the resulting fix diff; no repeat whole-branch audit or rerun of already reported broad suites is warranted by these findings.

After the scoped source fix, run the already-required macOS native/full-source and app gates. Record the final commit/run/artifact bytes and digest, then update release documentation from pending to its observed state. A GREEN build still does not establish server history availability, sustained session behavior or device performance.

## Declined to judge / explicit limits requiring executor ruling

- **Actual macOS compilation, thirteen new native fixtures, complete official generated-source key scan, app build, IPA contents and runtime:** unavailable in this read-only Linux review and explicitly pending parent delivery gates; no success inferred from local skips.
- **Real Postbox/index/hole/pending-worker behavior beyond the extracted production adapter facades:** source insertion and callback boundaries were inspected, but the fixtures do not instantiate the full database or all downstream observers. This remains device/integration evidence, not an invented replacement test gate.
- **Server acceptance of the unread-based candidate, slice tuple behavior, channel coverage, all-time history and 14-hour session survival:** require the user's runtime experiment. The finite adapter deliberately differs from Build82's seed/refetch architecture and documents that difference.
- **Physically deleted history without durable tombstones, or deletion evidence arriving only on a later page:** the accepted preservation/partial-coverage policy explicitly cannot provide universal non-resurrection. No broad tombstone subsystem was added or demanded by this review.
- **Transport-internal retries, upload failures before terminal send RPC, and successful local application after RPC result:** explicitly marked unobserved coverage in the design/export; not silently counted as observed actions or successful application.
- **Zero-account login-screen export:** the accepted minimal UI entry requires another remaining active account. README/runtime instructions disclose this limit; it is not treated as implemented.
- **Deferred performance waves D–H/S7, canonical archive cleanup, device UI/performance parity and FPS/thermal behavior:** explicitly outside BOT scope in decisions/progress; unchanged defects or unmeasured performance are not represented as solved.
- **Fresh remote Build178 availability, stable remote/original checkout state and publication authorization sequencing:** parent publication responsibilities. This review inspected local identity/wiring but did not query or change remote state.
- **Preference-key semantic collisions through computed expressions or dependency gitlink contents:** the checked gate is a literal scan of the complete generated main source inventory, as documented. No claim of semantic constant evaluation or scanning unavailable dependency checkouts is made.

The earlier Task1 restored-terminal observation is addressed in the final source by `.restoredTerminal` and its typed export mapping. Previous task R1–R4 fixes were inspected in their integrated context and are not reopened; their native evidence remains pending as above.

## Assessment

**Ready to publish the reviewed source candidate? With fixes — address R1 first.** R2 is nonblocking but requires an explicit ruling if deferred. No Critical finding or additional Important architecture/outbound/state-isolation defect was found in this broad pass.

**Ready to deliver a released experimental IPA? No, not yet.** Besides R1, the required macOS native/full-source and actual app/artifact gates are still pending. The source architecture preserves the intended single modern account/state ownership and modern outbound paths; the retention defect is localized and does not require redesigning the bridge.
