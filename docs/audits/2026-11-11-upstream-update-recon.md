# Official Telegram 13.2 update reconnaissance

Read-only source reconnaissance on 2026-11-11. No product, patch, manifest, dependency, workflow, Git reference, or build changes were performed. This report is not migration completion or native compatibility evidence.

## Exact release and toolchain

Official repository: `TelegramMessenger/Telegram-iOS`. Annotated `release-13.2` tag object `8ae8dcd1132cbf8ecf5bf4cd285484c901535207`, dated `2026-11-06T19:57:09Z`, peels to **`24638bc69bd083981b178dd1e7f921eebbf7fc46`**. Use the peeled release commit rather than a moving branch.

Exact-release [versions.json](https://github.com/TelegramMessenger/Telegram-iOS/blob/24638bc69bd083981b178dd1e7f921eebbf7fc46/versions.json), blob `01ad887a3eb867ece3a4a0127062e92291e4254c`, declares:

| Field | Official release value |
| --- | --- |
| app | 13.2 |
| xcode / deploy_xcode | 27.1 / 27.1 |
| bazel | `9.2.0:dd466352a3e4d3581b8898740ee1ff208866ccbe25f8d367c5dcb950219587e6` |
| macos | 27 |

The app version changes; these toolchain declarations match the existing preparation contract. This does not establish that every dependency gitlink remains unchanged.

The [official comparison](https://github.com/TelegramMessenger/Telegram-iOS/compare/279f89e4d4f63f17227bf877dc3d8990f22ecd58...24638bc69bd083981b178dd1e7f921eebbf7fc46) reports **897 commits ahead, zero behind**, with merge base exactly the current upstream `279f89e4d4f63f17227bf877dc3d8990f22ecd58` (13.1.2). The connector returns exactly 300 file records and stops alphabetically in ChatPresentationInterfaceState. **300 is a truncated listing, not the changed-path total. The full repository changed-path count was not established.** Root recursive tree requests exceeded connector transport capacity; no clone or full source download was substituted.

## Bounded, verified stage intersection

The current checked-in `docs/migrations/telegram-13.1.2-stage-chain.json` has **32 stages**, including identity and the four additions after the original migration. The production ordering is also visible in `scripts/build_jg13.sh`.

Existing scratch owner inventories were recovered, then corrected against exact-release tree metadata. Cached selected subtree entries were verified by rebuilding Git tree objects from immediate child names, modes and SHAs; missing root entries, unrelated changed root inventories and three executable-mode discrepancies were resolved using official GitHub tree responses. Every expanded directory hash then matched (zero mismatches). Unexpanded changed submodules were deliberately left unexpanded. Owner and guard paths lie within the verified selected subtrees; two additional guard paths in PeerAvatarGalleryUI were fetched and confirmed unchanged. Consequently this establishes the following selected-path counts, without establishing a global upstream file count.

| Selected path set | Unique paths | Upstream changed | Old upstream path removed | Unchanged upstream | Jerkgram-only |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stage owners | 339 | 131 | 2 | 93 | 113 |
| Explicit parent/lock/regression guards | 84 | 42 | 0 | 31 | 11 |
| Union | 357 | 134 | 2 | 108 | 113 |

These are pristine upstream blob comparisons, not generated Jerkgram parent digests. A stage may require regeneration when a preceding stage changes its parent even if its own pristine upstream path did not change. Removed paths require an explicit owner remap; they must not be restored wholesale from 13.1.2.

The four later production stages are `jg131-botbridge1` (13 owners), `jg131-beta2-recovery` (5), `jg131-local-premium` (2 plus 5 guarded parents), and `jg131-saved-tags` (12 plus 45 guarded parents). Respectively, 8, 1, 0 and 6 owner paths changed or disappeared upstream. The Local Premium Hub has no directly changed upstream owner, but its preceding source and guarded parents still require validation.

## Two removed owners require semantic ports

1. `submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift` no longer exists. Its responsibilities were split under `submodules/TelegramCore/Sources/State/Sync/`. Exact-release symbol evidence:

   - `finalStateWithUpdateGroups` is in `SyncSequencing.swift`.
   - `finalStateWithUpdatesAndServerTime` is in `UpdateInterpreter.swift`, which constructs an `UpdateInterpreter` and applies sorted updates.
   - `resolveMissingPeerChatInfos` is in `SyncResolve.swift`.
   - `StateReplay+Messages.swift` owns `applyAddMessages`, `applyDeleteMessagesWithGlobalIds`, `applyDeleteMessages`, `applyUpdateMinAvailableMessage`, and `applyEditMessage` (blob `cf1ab15d9cfae956abcb53bf5060db525b32448d`).

   The stable retention patch, excluded-history bot persistence changes, and Saved Tags deletion/edit cleanup all modify the removed owner today. Reapply each behavior to its new actual transaction/interpreter boundary. In particular preserve local-tag cleanup on global-ID deletes, explicit deletes, range truncation and edits; preserve bot chat-list inclusion only after message storage and avoid introducing bot-only user RPCs. A successful text merge elsewhere cannot prove these hooks survived.

2. `submodules/TelegramUI/Sources/CoreListChatHistoryBackend.swift` moved to [Components/Chat/ChatHistoryListViewBackend/Sources/CoreListChatHistoryBackend.swift](https://github.com/TelegramMessenger/Telegram-iOS/blob/24638bc69bd083981b178dd1e7f921eebbf7fc46/submodules/TelegramUI/Components/Chat/ChatHistoryListViewBackend/Sources/CoreListChatHistoryBackend.swift), blob `db09e9433ae6d2db905ad1acea9f5432c7a243c0`.

   It is now part of the separate `ChatHistoryListViewBackend` Swift module. The class remains internal `final class CoreListChatHistoryBackend: ASDisplayNode, ChatHistoryListViewBackend`; its documented public entry point is `makeCoreListChatHistoryBackend(rotated:scrollTrace:)`. The sibling BUILD declares this module with public target visibility, which does not make the internal Swift class publicly accessible. Port existing backend selection/retention behavior through the real factory/protocol boundary and update ownership/dependencies explicitly. Do not recreate the obsolete source path to satisfy its previous hash guard.

## Native tags and wallet observations

`submodules/TelegramCore/Sources/State/SavedMessageTags.swift` is byte-identical at the two exact release commits: blob **`5ab1286047257f8f3c93b40d5014b452d29e6184`**. The `SavedMessageTags` reaction/title/count model, cached access, managed synchronization and tag-title operation remain present. This bounded result says that implementation file has no API drift; it does not establish that all call sites, eligibility checks or UI integration are compatible. The current local-tag stage still touches six changed/removed owners and must survive the state-replay split above.

The parallel native-tag reconnaissance found the native tag panel structurally unchanged. Any typed local override for chat-history source selection needs to respect its private immutable source property and current ownership rather than broad source replacement.

Root-agent exact-release WalletScreen inspection found empty-state benefits/legal text using `environment.theme.actionSheet.secondaryTextColor` around line 3760 in `submodules/TelegramUI/Components/Wallet/WalletScreen/Sources/WalletScreen.swift`. The wallet inherits the current BaseViewController settings-glass behavior, so underlying imagery can reduce text contrast. Treat a wallet contrast adjustment as a separate explicit source delta after migration; the inspection is not a tested fix.

## Minimal execution strategy for a genuine 13.2 port

1. Freeze the current Build179 source chain and its exact active manifests/patch bytes as the old side. Preserve baseline successful build provenance separately. The reusable `../jerkgram-next/upstream-13.1.2/candidate/{regenerate.py,replay.py,stages,original-inputs}` and parent `IMPLEMENTATION.md` provide the prior algorithm and review evidence, but their Python stage lists stop at **28**. Extend the engine to replay the current **32-stage** contracts and their real parent-guard semantics before changing the target pin. Never reuse old original-inputs as if they contained the four later stages.

2. Acquire pristine 13.2 parents for every selected owner, parent guard, new replacement owner and relevant BUILD/API boundary. Verify bytes against exact-release Git blob SHAs and dependency gitlinks. Either import cryptographically verified genuine commit/tree metadata for a clearly labelled sparse review projection, or use a genuine exact-target checkout. Do not fabricate a target HEAD or claim a partial projection is a complete deployable checkout.

3. Replay each existing feature stage against its real 13.1.2 parent/output, checking its original digests first. Three-way merge only that feature delta onto the preceding 13.2 stage. Stop on actual conflicts and review their semantics. Explicitly remap the two removed owners to the state-sync and backend modules before generating manifests. Record old/new owner mappings and why hooks moved; preserve upstream state ordering and factory visibility.

4. Regenerate stage patches, before/after hashes and guard hashes from those reviewed boundaries. Hashes are outputs of the port, not a compatibility workaround. Preserve unchanged patch bytes when possible. Apply product identity/version changes at their declared boundary; Beta3/Build180 identity must not be silently folded into historical feature provenance. Align genuine source pin, app/base version and active entrypoints only once the candidate chain is coherent.

5. Prove all 32 actual boundaries: clean-parent apply and verification, exact output, reverse restoration, repeated-delta refusal, corrupt/mixed-parent refusal with no writes, and two fresh deterministic production replays. Verify untouched selected upstream owners remain byte-identical and every changed final owner is attributable to an explicit stage. Run focused moved-state/native-tag/backend regression checks at their declared source boundaries. A global literal SHA replacement cannot replace these proofs.

6. Then run the existing macOS native/full-source gates and full app/extensions build against a genuine complete target checkout. Review affected dependency gitlinks and target module BUILD changes first. Linux source checks and sparse replay do not establish Swift module access, whole-app linking, wallet rendering, native tag behavior or bot history behavior.

## Evidence and limits

Official evidence used: release tag metadata from the preceding recon; exact-ref versions and selected source files through GitHub connector; comparison metadata; target root/submodule/third-party tree inventories and selected recursive trees. Current local evidence: stage ledger, active patch manifests, production build ordering, existing migration engine and implementation record. Temporary inventory/hash-check work is under `/tmp/jg180-*`; those scratch files are not product inputs.

No build, native parse/typecheck, dependency fetch, migration regeneration, Git mutation, CI dispatch or runtime test was performed here. No full global changed-path count is claimed. The concrete release pin, verified owner intersection, removed-owner map and 32-stage replay plan are ready for implementation review.
