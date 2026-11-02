# Finding verdicts

- **R1 — deferred lifecycle must identify the original generation/epoch: ADDRESSED.** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:261` introduces a non-Codable target containing a weak manager namespace and immutable record/generation/epoch. Registry matching at `:308` checks all four identities and invokes the resolved scope only after unlocking. `submodules/TelegramCore/Sources/Account/AccountManager.swift:452` captures this target before cleanup start and uses the same target in the deferred completion. An old callback cannot re-resolve a replacement generation or replacement epoch. `tests/fixtures/botbridge1/diagnostic_lifecycle.swift:52` adds both replacement cases and the later weak-namespace case; the assertions exercise the actual registry implementation.

- **R2 — deletion scheduling must correspond to the excluded directory: ADDRESSED.** `submodules/TelegramCore/Sources/Account/Account.swift:1876` supplies the real `accountRecordIdPathName(id)` output, avoiding signed-ID/path reconstruction. `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:325` preserves the original predicate exactly: `account-` prefix and absence from `validPaths`. `submodules/TelegramCore/Sources/Account/AccountManager.swift:471` captures bounded generation/epoch targets before dispatch; `:475` calls the predicate/observation immediately before the existing removal attempt. The old `beginList` event and the inferred deletion event in `reconcile` are removed. `tests/fixtures/botbridge1/diagnostic_lifecycle.swift:71` covers retained versus excluded paths and stale targets after replacement. The event remains explicitly a scheduled attempt, not a claim that filesystem deletion succeeded.

- **R3 — enumeration failure must stop append/export: ADDRESSED.** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:419`, `:422`, and `:427` propagate enumeration errors through retained-file listing, stale-export cleanup, and pruning. `:444` requires successful enumeration before appending, propagates subsequent rotation/read/write failures, increments storage failure, and returns false. `:480` and the surrounding export error handler return `.storage` and release the busy slot on preparation/listing failures. The prior empty-array fallback is gone. `tests/fixtures/botbridge1/diagnostic_filesystem_failure.swift:1` exercises the actual sink with real writable storage and an injected throwing enumeration boundary, checks repeated denied drains create no additional files, covers each export listing position, and inspects loss labels after recovery.

- **R4 — execute the actual history-to-export mapping and exact serialized fields: ADDRESSED.** `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift:527` extracts the unchanged production mapping into a pure helper; the real owner delegates to it at `:541`. `tests/test_jg131_botbridge1_diagnostics.py:126` extracts the actual policy/event types, tuple mapper, history mapper, recorder, and sink. `tests/fixtures/botbridge1/diagnostic_history_export.swift:1` routes start/end/restored-terminal events through that mapping into asynchronous JSON export and asserts exact history key sets, distinct tuple components and counters, phases/reasons, coverage flags, and forbidden private/progress/parameter/error keys. This closes the former fixture boundary gap without introducing a fixture mapping.

# New breakage in the fix diff

- None found. The registry retains its maximum-entry/no-live-eviction policy and weak scope ownership; callbacks remain outside its lock. Directory deletion eligibility and its original removal attempt remain unchanged. Filesystem errors remain finite exported loss metadata rather than raw error strings. The adapter refactor preserves its former field mapping.

# Out-of-scope observations

- None added. Untouched code was not reopened as a new review.

# Checks and limitations

- Read the scoped re-review instructions, the full fix diff in passes, and the appended fix report at `task-2-report.md:206`. Compared each of R1–R4 against the actual changed source and fixture extraction boundaries.
- One focused check outside the diff: `submodules/TelegramCore/Sources/Account/Account.swift:293` confirms `accountRecordIdPathName` returns `account-` followed by the unsigned bit-pattern representation, and the native account path uses that function at `:304`. The fix calls that exact function; it does not assume decimal signed-ID spelling.
- The appended report names the covering command `python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v` and shows `Ran 20 tests ... OK (skipped=8)`: **12 portable passes, eight native skips**, not 20 executed behavioral tests. It also reports the regenerated source patch dry-run. These reported commands were not rerun, and no 761-test discovery was performed.
- **Cannot verify here:** native compilation/runtime of the eight fixtures, actual framework/UI integration, and authoritative stage/native/app delivery. Those remain mandatory Task 3 gates. No Swift execution or passing native/app build is claimed by this review.
- Source files, fixtures, index, HEAD, and branches were not modified; only this requested review report was written.

# Verdict

**Spec compliance for the reviewed findings: Approved.** R1, R2, R3, and R4 are addressed in the source and fixture definitions.

**Task quality for this fix round: Approved.** All findings addressed; no new Critical/Important breakage found. Task 3 native and integration validation remains required before final delivery.
