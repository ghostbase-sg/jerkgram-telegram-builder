# Spec compliance: ❌ Issues found

- The ten product owners are represented in the supplied diff. The requested architecture, finite diagnostic schema, cold request observation, additive worker contexts, bounded recorder, restored-terminal history status, and dedicated Settings export are present. Three important gaps remain: generation-safe deferred lifecycle targeting, truthful deletion scheduling, and failure-closed directory enumeration.
- ⚠️ Native Swift compilation/runtime and real framework/UI integration cannot be verified from this package. The report explicitly records eight portable passes and six native skips; `tests/test_jg131_botbridge1_diagnostics.py:81` skips when Swift is unavailable. Task 3 must execute these fixtures with Swift and the correct stage/native/app gates. The reported 37 failures and 40 errors from naive repository discovery remain unresolved evidence, not a passing regression gate; the report explains their historical-view limitation, which this task review does not independently establish.

# Strengths

- `submodules/TelegramCore/Sources/Network/Network.swift:1376`, `:1425`, and `:1473`: observation starts inside the cold Signal; closures retain the independent registration box and request service; ordinary requests return the original disposable. Existing parser, policy, dependency, result/error forwarding, and acknowledgement availability remain intact in the inspected methods.
- `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:139`, `:162`, `:208`, and `:423`: fixed event/context bounds, independent terminal arbitration, cancellation before lifecycle snapshot, soft-reset continuation, and a single asynchronous export slot are implemented without payload/parameter inspection.
- `submodules/TelegramCore/Sources/State/AccountStateManager.swift:1572` and `State/JerkgramBotBridgeHistory.swift:506`: diagnostic admission precedes controller creation, and restored terminal progress emits a truthful status without restarting the import. The history changes observe numeric live state through existing transactions; the diff introduces no live-state replacement.
- `tests/test_jg131_botbridge1_diagnostics.py:41` and `:53`: exact reversible worker insertions and whole-file Network normalization are checked against the independent modern baseline. The supplied product hunks preserve modern request operators, update application, and error policy rather than exempting whole functions.
- `submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift:639` and `JerkgramDataAndBackupController.swift:141`: export is reachable without creating a recorder or scanning files during page construction, presentation holds the controller weakly, and a URL-only lease releases the export.

# Issues

## Critical

- None found in the reviewed scope.

## Important

1. **Deferred lifecycle lookup is not bound to authorization generation or epoch.** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:262`, `:275`, and `submodules/TelegramCore/Sources/Account/AccountManager.swift:455`. Registry entries and `notify` matching use only manager identity plus record ID; the generation stored on the scope is never part of lookup. The asynchronous cleanup completion re-resolves that record when it finishes. If the original scope has been unregistered/deallocated and a replacement has registered for the same manager/record, the old completion targets the replacement and `lifecycle(.cleanupResult)` freezes it and clears its Network registration. The old-deinit epoch guard does not protect this separate path. This also misses the explicit generation-key requirement. Bind deferred lifecycle callbacks to an immutable generation/epoch token obtained for their original operation, and reject stale tokens while retaining weak ownership. Add a fixture that replaces the scope before invoking the old cleanup completion and verifies the replacement remains active.

2. **`deletionScheduled` is emitted while the same closure explicitly preserves that directory.** `submodules/TelegramCore/Sources/Account/AccountManager.swift:470`. `beginList` contains logged-out records still present in `view.records`; those records are added to `validPaths` at line 463. The queued filesystem pass deletes only paths absent from that set, so the newly emitted event does not correspond to scheduling deletion of that account directory. It can precede the eventual removal by the entire cleanup RPC duration or be emitted even if cleanup never completes. Emit the event only at the actual path-exclusion/deletion scheduling boundary, bound to the appropriate scope token; do not label cleanup initiation as directory deletion scheduling. Add a fixture showing a logged-out record still in `validPaths` receives cleanup-start but no deletion-scheduled event until its path is excluded.

3. **Directory-enumeration errors bypass the fixed resource policy and truthful export state.** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:374`, `:377`, and `:429`. `files()` converts every listing failure into an empty array. `prune()` consequently reports success without knowing the retained files/count/bytes, and `drain()` may create another file when the directory permits creation but enumeration fails. Repeated drains can exceed the eight-file/global byte cap. Export can likewise encode `no_captured_sessions` without recording that stored sessions could not be enumerated; the separate stale-export listing has the same suppression. Make enumeration failure explicit, count the storage failure, stop appending when retention cannot be established, and return `.storage` for export preparation. Add a focused filesystem-failure fixture; current resource fixtures cover successful enumeration only.

## Minor

- **The history-to-export adapter is not executed by the new fixtures.** `tests/test_jg131_botbridge1_diagnostics.py:90`, `:118`, and `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:474`. Foundation fixtures extract only the `BEGIN/END BOTBRIDGE DIAGNOSTICS` block, which excludes the typed `BotBridgeHistoryEvent` adapter; the final-controller fixture checks raw events rather than the serialized history records. The mapping looks correct in the diff, but the brief's exact exported history-field/privacy assertions do not currently protect it. Include the actual adapter in a focused fixture and inspect one exported start/end/restored-terminal record with distinct numeric counters and tuples.

# Checks and scope

- Read the task brief, prior-interface context, implementation report, and complete supplied product/test diff in sequential passes. No reported test suite was rerun; no native compilation result is claimed.
- Focused inspection beyond diff context: `Account/AccountManager.swift:398`–`:486`, because the deletion-scheduling hunk ended before its filtering/deletion loop; this confirmed finding 2. Read the continuation of `cleanupAccount` at `:510`–`:543` to establish the asynchronous completion/removal boundary relevant to finding 1. No broader call-site crawl was performed.
- Focused inspection beyond diff context: `State/PendingMessageManager.swift:1200`–`:1385`, because the grouped context hunk ended before the worker's reply-attribute selection; the existing worker uses the same first message's attributes, so no grouped reply-selection discrepancy was found.
- Focused inspection beyond diff context: `Network/Network.swift:1376`–`:1480`, because the request hunks omitted their parser/progress sections; these remain unchanged and the fixture's extraction targets both complete production methods.
- Product source, index, HEAD, branch, and fixtures were not modified. Only this requested review report was written.

# Assessment

**Task quality: Needs fixes.** The architecture and source-preservation approach are disciplined, but lifecycle records must identify the correct generation and describe actions that were actually scheduled, and storage failures must not silently disable resource enforcement. Native compilation and Task 3 integration remain separate mandatory gates after these fixes.
