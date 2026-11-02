# BOTBRIDGE1 independent design/plan preflight

2026-11-01. Research-only review of BOTBRIDGE1-SPEC.md, DESIGN-DRAFT.md, IMPLEMENTATION-PLAN-DRAFT.md, HISTORY-AUDIT.md, WRITE-AUDIT.md, FINITE-IMPORT-DESIGN-NOTES.md, API-VALIDATION.md, EXPORT-LIFECYCLE-NOTES.md and POSTBOX-ACTION-SEARCH.json. No product/source/builder edits, duplicate source audit, or build performed. Modern app run 41346030214 is still pending in the supplied checkpoint; source/native GREEN is not app GREEN.

## Verdict

Architecture is suitable with the bounded corrections below. It preserves the modern base, a single live state owner and current outbound algorithms, while documenting the intentional adaptation of Build82's seed/refetch behavior into finite direct import. The plan covers the fifteen requested scenarios and eventual exact commit/run/IPA delivery. It is not yet an implementation or proof of runtime history availability. Keep the existing exact modern app GREEN prerequisite; no additional user approval is needed for the corrections or routine integration choices.

## Required corrections before implementation claims

### 1. Persist request reservation separately from committed-page progress

The design promises getState plus at most 32 getDifference requests **per session generation**, but persists committed page counts and permits a crash before commit to repeat the page. Thus those counters bound committed pages, not actual requests. The same gap exists before initial getState/candidate persistence. The 120-second deadline reduces exposure but cannot establish the claimed request bound, especially if start/deadline themselves are not persisted before dispatch.

Remedy: transactionally create generation/start/deadline and reserve each request attempt before subscribing. Keep attempt count distinct from atomically committed message/page/cursor counters. On restart, an interrupted reservation consumes its attempt; retry the same cursor only with another reservation and remaining budget. If initial getState has an interrupted reservation with no persisted result, terminate incomplete rather than issue an unbudgeted second getState. Persist cursor/result and messages together as already planned. Add crash tests before dispatch, after response and before page commit, and after commit. An unused reservation may cost budget; that conservative behavior is acceptable. No new retry subsystem is required.

### 2. Make response kind, not insertion count, determine terminality

The current design correctly says final difference or differenceEmpty terminates. FINITE-IMPORT-DESIGN-NOTES.md step 7 also says “Store first page empty/dedup-only success as terminal too,” which could prematurely stop a differenceSlice whose messages already exist or whose newMessages list is empty. Later slices can still contain recoverable history.

Remedy: explicitly supersede that note. A progressing differenceSlice continues within budgets even with zero inserted messages; only final response/empty constructor, nonprogress, error or a limit terminates. Test an empty and a deduplicated slice followed by a slice containing a new message. Preserve the existing identical/regressing-cursor rejection.

### 3. Carry lifecycle registry safety and soft-reset behavior into the executable plan

EXPORT-LIFECYCLE-NOTES.md supplies necessary details that Task 2 reduces to “bounded weak registry by AccountRecordId.” AccountRecordId uniqueness across manager roots is unproved, and an active cancellation target must not be silently evicted. The plan's general “freeze before unregister” instruction also needs the note's explicit distinction between a soft reset and terminal teardown.

Remedy: key weak registrations by manager namespace plus record ID and generation; cap at 32 entries, purge dead entries, and fail closed for a new experimental bridge if no safe slot exists. Do not evict a live cancellation target. Resolve targets under lock and invoke callbacks after releasing it. On soft reset, cancel finite history and freeze an observation while keeping diagnostics available for the continuing modern Account; unregister only on terminal teardown or replacement. Verify old-generation deinit cannot remove a replacement and two manager namespaces cannot cancel one another. The actual reset/removal/authorization hook inspection remains a narrow source integration prerequisite, not a request for another design approval.

### 4. Specify the required history diagnostic fields and ancillary payload bounds

The spec requires original current state, selected legacy starting point, iterations, messages/chats and transition back to modern processing. Progress storage contains the tuples, but the recorder/export schema currently names only general typed events and counters. Persisted progress alone is not a user-exportable diagnostic result. Also, scanning otherUpdates for deletion IDs/counts needs a bound even though newMessages and peers already have caps.

Remedy: define allowlisted history start/end records containing numeric original/candidate/last retrieval tuples, attempted/committed pages, inserted message/peer counts, skipped counts and finite terminal/coverage reason. Record “modern processing resumed; live state never replaced,” rather than claiming a live-state reset occurred. Never export peer/message IDs or full serialized progress. Cap otherUpdates inspection and unsupported payload counting before additional allocation; on excess terminate incomplete without partially importing the page. Include oversized otherUpdates and tuple/counter export fixtures with forbidden content sentinels.

## Confirmed design strengths and retained integration obligations

- The Postbox adapter is necessary: .Random alone does not suppress installed message/store-update actions. The proposed two-block guard with default true and a bridge-only public entry is appropriately narrow. Keep mixed historical/ordinary insertion and open-chat behavioral tests; a source string check cannot prove callback safety. Agree on one public signature between design and plan (fixed .Random is simplest). Remaining MessageHistoryTable flags/pending actions and other observers must be inspected before a blanket no-indirect-mutation claim.
- Modern Network subscription observers plus explicit reply/broadcast context at modern send workers satisfy attribution more honestly than an enqueue-only or method-name-only approach. Additive worker modifications require allowed-diff and behavior proof; unchanged-file hashes alone cannot prove modified workers retain behavior. Preserve error object, retry policy, dependencies, ack availability and disposal semantics.
- FunctionDescription.name-only classification, finite errors, no payload capture, explicit lazy-loader sentinels, bounded queues/files and export outside account directories are sound. A finite unknown/uncovered method label must remain visible; do not imply universal upload/multiplexed coverage. Missing preterminal media failure evidence is a stated diagnostic limitation, not proof the user did no outbound action.
- Generic custom-operation subscription disposal is insufficient; explicit request ownership, invalidation, exactly-once completion, transaction revalidation and queued-page yielding are correctly required. Persist terminal cancellation where feasible; a crash before cancellation persistence may resume the same bounded generation, never a fresh budget.
- Physical deletes without durable tombstones remain a known experimental limitation. Existing-message preservation, same-page delete exclusion and session-local known deletes do not prove universal non-resurrection. No broad tombstone subsystem or new approval gate is warranted here.
- Dedicated export from another active account is adequate for the stated multi-account experiment, with the zero-account UI limitation disclosed. Do not claim Files access or no-account export without evidence.
- Actual modern app GREEN, exact builder/source provenance, branch-only stage, full generated-source/native tests and final experimental IPA remain required. Device testing alone can establish server backlog availability and session behavior. Keep these evidence levels distinct.

## Disposition

Apply the four small documentation/fixture requirements above during plan finalization. Proceed with the authorized implementation once the existing modern app GREEN checkpoint is real. No architectural rewrite, extra approval cycle, durable deletion subsystem, or extra heavy preflight build is requested.
