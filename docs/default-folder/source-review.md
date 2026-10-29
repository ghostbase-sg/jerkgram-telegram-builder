# TASK B review

Spec verdict: PASS at source-review scope. Code quality verdict: PASS at source-review scope. No actionable findings in the seven changed owners and their scoped fixtures.

Reviewed the design requirements first, then IMPLEMENTATION.md, REVIEW-DIFF.patch and the relevant production and fixture code. This review did not run a build, network requests or repeat the reported tests.

Evidence:

- `ChatListFiltering.swift`, `JerkgramFolderOrder` and `_internal_updatedJerkgramChatListFilters`: effective order is capability scoped to enabled, known actual nonPremium; allowed custom IDs are calculated from the native visible prefix before permutation; locked members retain their suffix. Snapshot carries preference readiness, actual entitlement, limits, generation and proposal together.
- `ChatListController.swift`, `reloadFilters` and `reorderingDonePressed`: the root consumes startup only when the snapshot is ready; missing/ineligible enhanced selections explicitly resolve to All before the native predecessor expression. Header proposal is captured at reorder entry; the original stock save closure remains separately branched. No foreground, deep-link or notification enforcement was introduced.
- `ChatListFilterPresetListController.swift`, reorder entry/completion and Done: shares the snapshot and scoped commit facade; clamps tentative enhanced order before rendering native ordinal limit gates; retains the original proposal through policy changes; rejected commits still clear editing state. Shared Premium flags and count/tag gates remain native.
- `ChatListFiltering.swift`, `_internal_updateJerkgramChatListFilterOrder`: checks database identity, generation, known entitlement, native membership and allowed set in the transaction. Obsolete enhanced proposals complete without falling through to a stock RPC. Local order is a separate Postbox preference; synchronized order preserves All-first compatibility and includes original residual members.
- Both interactive native writers and `updateChatListFiltersState` prune by authoritative old/new membership independently of the feature toggle and UI lifetime. Removing the saved first custom ID inserts All first; later numeric ID reuse cannot restore that deleted default. Projection changes do not prune storage.
- `GhostBaseSettingsController.swift` and `SyncCore_Namespaces.swift`: canonical account-scoped default-OFF setting, bounded policy cache, scoped/disposed policy notifications, separate reserved Postbox key, requested native toggle/footer. No global Premium or unrelated unlock was added.
- `TelegramEnginePeers.swift` and `TabBarChatListFilterController.swift`: facade is narrow; root unread output retains its originating snapshot and the existing unread implementation is reused.
- Scoped Foundation fixtures cover normalization, bounded storage, policy admission/readiness, locked suffix, compatible server order, authoritative deletion/ID reuse, generation and distinct database lifetime rejection. Source fixtures additionally protect native closures/gates and owner integration.

Validation boundary: parent reports portable gate13B and gate24A passed, with four total Swift-dependent skips. Actual Swift execution, macOS type/build checks and the specified iPhone navigation/account/relaunch matrix remain pending. This verdict does not claim those runtime gates passed.
