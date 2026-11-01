# TASK B final integration review

Spec verdict: PASS at source-review scope.
Code-quality verdict: PASS at source-review scope.
Actionable findings: none identified in the reviewed delta.

Reviewed the default-folder design first, followed by the implementation, earlier source review and native-success evidence. Inspected the product REVIEW-DIFF.patch and relevant physical owners under replay-final, plus the canonical builder diff 0479229..fd2f615. This review did not edit implementation, run builds, use the network or repeat passed tests.

## Material integration evidence

- `ChatListFiltering.swift` — `_internal_updatedJerkgramChatListFilters` reads filters, local order, entitlement and configuration from a combined Postbox view; computes allowed visible IDs before permutation; and publishes the matching policy generation and proposal. `JerkgramFolderOrder.effective` preserves the locked suffix and resolves an unavailable configured first ID to All.
- `ChatListFiltering.swift` — `_internal_updateJerkgramChatListFilterOrder` validates database identity, generation, actual entitlement, native membership and allowed membership inside the transaction. Enhanced proposals cannot fall through to stock persistence after a toggle change. Separate local storage and server-compatible order avoid synthesizing All into synchronized state. Both interactive writers and the central state writer prune authoritative membership removals transactionally, resetting a removed default to All.
- `ChatListController.swift` — `reloadFilters` consumes the matching snapshot/unread result and gates the existing startup one-shot on readiness. Enhanced missing or disallowed selections resolve to All before the native predecessor expression. Header reorder captures its proposal on entry and completion releases reorder mode even after rejection.
- `ChatListFilterPresetListController.swift` — editor presentation uses the same snapshot and normalizes tentative enhanced order before native ordinal checks. Reorder retains the originating proposal across policy changes; Done clears editing state after either acceptance or rejection. Stock save closures remain separately branched, with real Premium and OFF retaining the original entitlement behavior.
- `TabBarChatListFilterController.swift`, `TelegramEnginePeers.swift`, `SyncCore_Namespaces.swift` and `GhostBaseSettingsController.swift` provide the bounded integration: existing unread implementation, narrow facade, separate local key, account-scoped default-OFF toggle and explanatory footer. No new global entitlement hook or unrelated feature unlock appears in the delta.
- `scripts/materialize_jg131_default_folder.py` validates patch scope and exact owner parents before mutation, verifies outputs, supports an already-applied stage and reconstructs hash-verified TASK A parents for earlier gates. `verify_jg13_source.py` restores SOURCE after recursive parent verification.
- `scripts/build_jg13.sh` and `.github/workflows/no-ads-native.yml` place B after materializing and checking A. `tests/run_jg131_default_folder.py` checks B outputs and owners, then invokes A against the restored parent; inherited stage tests exercise materializer failure/idempotence behavior. Prior patch files are outside the builder delta.

## Evidence boundary

The supplied native-success record reports run 40898713432 on fd2f615fb5d93a92556cffce1a7c7ba297f071e5: B 13/13 and A 24/24, no skips. This is existing evidence, not a newly executed result. Seven-owner Swift parsing and extracted production Foundation fixtures do not establish whole-app type checking, UIKit behavior, RPC success or device visuals.

The planned combined app build and device checks remain necessary delivery gates: both native reorder surfaces, ON/OFF and Premium, relaunch/offline, hidden/limited folders, deletion/ID reuse, account/logout isolation, and notification/deep-link navigation with subsequent user selection. Their pending status is a validation limitation, not a source defect established by this review.
