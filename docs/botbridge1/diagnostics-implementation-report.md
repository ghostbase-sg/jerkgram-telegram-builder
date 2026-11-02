# Task 2 implementation report — BOTBRIDGE1

Status: DONE_WITH_CONCERNS. Source package is ready for independent review; native execution and authoritative final-stage/CI/device delivery remain pending Task 3. No commit, push, workflow edit, materializer execution, full native build, or IPA claim.

## Source package and immutable provenance

Builder branch remains `dev/botbridge1-legacy-history-modern-write`, HEAD `5ba6add985d6995ca102d4e40d8da66e98f443c1`. Product edits exist only in `/home/pixi/ChatGPT/iOS DEV/jerkgram-next/botbridge1/task2/source`.

`task2/before` is a separate complete copy of accepted Task1/source. A final inventory compared all **556 accepted Task1 files** against Task2/before and BASELINE.json with exact SHA256 equality. Task1/source, Task1/before, Task1 tests/fixtures, modern177 source, stable branch, and existing builder product files were not edited.

Review artifacts: `task2/BASELINE.json` (all before hashes), `task2/OWNER-MANIFEST.json` (all after hashes and the ten changed owners), `task2/SOURCE.patch` (exact source delta), `task2/MODERN-WRITE-PROOF.json` (reversible exact worker context edits), `task2/RESOURCE-POLICY.json` (fixed limits). All paths below are relative to Task2/source.

| Changed owner | Before SHA256 | After SHA256 |
| --- | --- | --- |
| `submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift` | 215ab9b5f4aab7968ec894c7cd54bdfc9d129ca6d3421438b14cf69b38835430 | dfac82d7280037f44147070e474ee05135d4a5d7f44f668094fb2f42537899ce |
| `submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift` | 8475280ce7f9be1102b1ef516e31dc6f77df296a11144701c11bc11b81cabbdf | 852a35db8f0d0c85443f60d2465d066073b3767c7e476aa24d287f2f6cc8d633 |
| `submodules/TelegramCore/Sources/Account/Account.swift` | 59632aa5256d5ec676c33922988131f4395d9f3f34bc0f668b47edff4781fa02 | 44c30eca89ef89ac2b96a687f7cabf1bcb7c0f20c39d9ecba3e4533230fcec1e |
| `submodules/TelegramCore/Sources/Account/AccountManager.swift` | 3b895522301c0b0f7aa7245d6217b96a5ad1b9f9ac4d614f5292f73ddcc56d64 | ad738b587a3f22cc742d9ae9ffbc08eadb023f9a162de39b66e39886a0c383f8 |
| `submodules/TelegramCore/Sources/Network/Network.swift` | b135376f7db35a77995d2c06dd92d1ba9b6acbe490cd339d8f745307c3ca812e | b3523f20406d2c076f29d4f9e46b47a13010f1fe686ceea856ef9ec8bb3b75d6 |
| `submodules/TelegramCore/Sources/PendingMessages/StandaloneSendMessage.swift` | ab8a7c29995eba1865880e3c5c6be2c367725d773cd8b3f0450d0ce69a040bd8 | b23dd503a2ea7c17b00198c7f67f591ee4d5594328d2d13011822ee53f5477a6 |
| `submodules/TelegramCore/Sources/State/AccountStateManager.swift` | 0ccaa08c55b54a8daad68a42651b1789464d7090d3525a65f18d341ff8d65290 | fb253699e027ae7cc0b1352b1e27afd43a8c698bc4c861cf08b963eec5913ceb |
| `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift` | new | 6f8aa906ba17d6b6b3654ff7a766f14ad94fa18da426b3efd0a5d1bff01f17bd |
| `submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift` | c75d0de635a02d2d1ae74ebbcc15282cf5df78571d921707b051c4f807cf6296 | a5c01bb8c596e5d42c7519b66803fcef31b7600591e3ed0ed2a3050ba97c0ff6 |
| `submodules/TelegramCore/Sources/State/PendingMessageManager.swift` | e5fd04ed9a3d11f615d9eee5f17fa184768fa1c51ced79103b0068f1ffbc92c2 | 1d1e8df4d65ae4d7f474c87a1e6e89439474e5ae21af723b0c5ebf5bafd43ae7 |

## Implemented behavior and ownership

The new focused `State/JerkgramBotBridgeDiagnostics.swift` owns finite typed diagnostic values, account scope/registration/owner, bounded teardown registry and asynchronous sink/export. Account owns its continuing scope through `BotBridgeDiagnosticOwner`; the existing sole AccountStateManager/history controller remains the history owner. No second Account, Network, Postbox, state manager, sender, polling loop or callback registry was introduced.

Admission occurs only after the existing confirmed-bot/auth/environment/preference transaction returns a generation, before constructing the history controller or any bridge request. AccountManager namespace is the actual weak manager object; internal keys retain only record id plus validated generation/epoch context. Admission validates UUID generation. The weak bounded registry purges dead entries, accepts at most 32 live targets, rejects an occupied live record/capacity instead of evicting its cancellation target, resolves under its lock and invokes lifecycle callbacks after unlocking. Old-epoch unregister cannot remove a replacement. Supplementary Accounts and ordinary users never admit a scope.

The existing two cold Network methods now take defaulted optional `diagnosticContext`. Each subscribed invocation observes finite method category, attempt/request UUID, acknowledgement where already provided, typed result, numeric RPC failure, local parse failure or cancellation. Acknowledgement availability, error instance, metadata, dependency tags, parse operators, policy functions, downstream callbacks and underlying request-service disposable are preserved. Terminal-versus-disposal races have an independent lock. Observer closures capture an independent box containing a weak scope and immutable finite context; they do not capture Account or Network. Unregistered requests return the original underlying disposable directly and allocate no recorder, UUID, event or diagnostic disposable wrapper. The worker context factory resolves registration before creating its logical UUID, so ordinary users create no context UUID either.

Modern single/group/standalone workers only receive finite context locals and optional arguments at their existing terminal request calls. Explicit reply attributes determine reply intent; topic/monoforum routing alone does not. The resolved TelegramChannel broadcast kind determines post intent; megagroups do not. Text is an additive positive flag; sendMedia/sendMultiMedia provide the finite media category/flag. Central exact finite method names cover normal/paid reaction, message/inline/ephemeral edit, delete variants and supported other mutations without touching those workers. `read_ack` remains distinct from mutations; native read policy is preserved. `updates.getState/getDifference` are honestly labeled `state_read` because modern manager requests use those same methods. Their names alone never claim bridge ownership.

Safe lifecycle hooks cover actual subscribed local/remote logout, server logout, soft reset/resetStateManagement, permanent-key-unknown observation without its identifiers, direct record absence in the existing cleanup stream, cleanup start, cleanup Signal completion, scheduled directory deletion and deinit. The existing sole manager is invalidated/cancelled before a lifecycle snapshot; terminal scopes are frozen before registration clearing/unregister. Soft reset cancels only finite history and retains the modern Network recorder. Cleanup completion is explicitly labeled Signal completion, not proof that an auth RPC succeeded; directory deletion is labeled scheduled. No auth/logout behavior is suppressed or rewritten.

History receives only the existing typed callback. Added phases distinguish started and restored-terminal status. Restored already-terminal progress produces one truthful restored-terminal status and no new import. Existing startup/reservation/store/terminal transactions return a numeric observed-live tuple alongside existing progress; there is no new read transaction, live state setter or progress owner. Start/page/end/handoff records include original/candidate/last retrieval/live tuples, reserved requests distinct from committed pages, inserted messages/peers/chats/users, examined/skipped/unsupported/delete-observation/missing-reference counters and finite reason. No progress object, private account/message/peer id, API object, raw error, token, payload or request parameters reaches the sink. Handoff explicitly says modern processing resumes and live state was never replaced.

Limits are **256 total retained events/account, consisting of 248 ordinary plus 8 reserved snapshots**, 64 active flights, 64 logical-attempt entries, 30 minute correlation TTL; **256 total pending sink records, 248 ordinary plus 8 reserved**; one drain task rather than an unbounded task per event. Per-record encoding is capped at 32 KiB. Sink writes batches only on its utility queue under Documents/Jerkgram/BotBridge1, outside removable account paths. It retains at most eight 256 KiB event files (2 MiB), applies 24 hour TTL on sink access/export, and fails closed when cleanup cannot enforce rotation. One temporary export is bounded at 2 MiB including its versioned envelope. Storage failures explicitly mean unknown storage loss. Ring/context expiry/eviction, sink/snapshot drops, rotation/retention losses and export truncation are explicit. Crash/restart durability, transport-internal retries, uploads, local update application and unknown methods are explicitly unobserved/limited; no server causality is inferred.

The experimental Data & Backup page always shows a clearly labeled BOTBRIDGE1 action, including from another active ordinary user after bot removal. Page construction adds no recorder, file scan or observer. On tap, an asynchronous public facade creates only dedicated redacted JSON. Empty export reports `no_captured_sessions`. Existing weak actionTarget ownership is preserved. Presentation captures controller weakly, presents on main, and releases the export if controller vanished; both picker callbacks and a URL-only lease deinit release it asynchronously/idempotently. No archive/canonical store/general log data is read by this feature.

## Modern byte preservation

`MODERN-WRITE-PROOF.json` contains the exact ordered before/after local/argument insertions for PendingMessageManager and StandaloneSendMessage. Reversing those specific edits recovers the exact modern protected SHA256 for each entire file; there are no whole-function exemptions. The focused test also checks each recovered digest against the independent MODERN-WRITE-BASELINE.json, rather than trusting the new proof alone.

Network has its own exact removal normalization in `test_exact_network_observer_normalization`: removing the explicitly named observer property/callback/local/defaulted argument/terminal notifications/disposable wrapper recovers the entire original Network.swift byte for byte and its independent protected modern digest. All remaining untouched modern owners are checked against the independent modern manifest. The already accepted four Task1 owners retain their separate provenance; the modern pollDifference case and addCustomOperation body are checked byte identical. Task1 policy, page adapter, import/storage helper, validation and lease bodies remain identical to accepted Task1.

## Tests and TDD evidence

Initial RED was run **before Task2 production edits**:

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v`

It ran 7 tests: 6 FAIL and 1 ERROR. Expected failures included `missing production bounded diagnostics recorder/request/lifecycle implementation`, missing exact worker proof, absent cold weak observer/fast path, and absent admission/restored-terminal boundary. The logout check initially raised ValueError because the cold Signal wrapper did not yet exist. Raw initial output remains local at `/tmp/botbridge2-red.txt`.

Final focused command, exit 0:

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v`

```
Ran 14 tests in 0.015s
OK (skipped=6)
```

This is **8 portable checks passed / 6 native fixtures skipped**, not fourteen behavioral tests executed. Native skip reason: `Swift unavailable on Linux: actual production native fixture pending macOS`. Native fixtures extract actual production implementations and replace only unavoidable transport/Signal/queue/Postbox scheduling boundaries. They are not a policy reimplementation. They cover the Foundation recorder and weak observer/registry, actual Network request functions with lazy-parameter/raw-error sentinels and concurrent cancellation/result race, actual worker context factory, actual subscribed logout, registry namespace/capacity/epoch/generation behavior, bounded sink saturation/rotation/TTL/single export/cleanup, final history controller plus all accepted Task1 controller scenarios and restored-terminal/live tuple assertions, and final actual Postbox mixed historical/ordinary callback behavior.

**Native RED/GREEN has not executed.** The initial recorder fixture was authored before the recorder implementation; additional native boundary/resource/lifecycle/race cases were authored while completing and self-reviewing the draft. Thus I cannot claim complete native test-first evidence or compiled Swift correctness. These are explicit required macOS gates, not skipped assertions represented as passes.

Immutable Task1 command, exit 0 (default source remains immutable Task1):

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_history.py -v`

```
Ran 14 tests in 0.150s
OK (skipped=5)
```

Task1 native fixtures remain pending Swift. Final actual controller/Postbox tests are separately extracted from **Task2/final SOURCE**, avoiding falsely testing only Task1 source after Task2 changes.

Patch applicability check, exit 0, all ten owners checked without writes:

`patch --dry-run --batch -p1 -d '../jerkgram-next/botbridge1/task2/before' < '../jerkgram-next/botbridge1/task2/SOURCE.patch'`

Final inventory check passed: 556 accepted Task1 files unchanged; ten Task2 owner differences, one new diagnostic owner. Builder HEAD and existing product/workflow files remain unchanged.

Repository-wide discovery was also run once after the final product changes (and once earlier while fixtures were being completed):

`python3 -m unittest discover -s tests -v > /tmp/botbridge2-full-suite-final.txt 2>&1`

```
Ran 761 tests in 4.752s
FAILED (failures=37, errors=40, skipped=36)
```

This naive discovery is **not an authoritative final-stage regression gate**: existing repository tests require restored prior-stage source views/runners. Concrete exception categories from the local output: 33 RuntimeErrors (expected stage anchors absent; e.g. Build133 ChatList preview owner found zero anchors), 3 ValueErrors (missing expected substring), 1 FileNotFoundError (missing work/swiftgram-src generated owner), 1 IndexError (missing expected fixture result), 2 other error reports, 37 assertions about workflow/prior-stage generated contracts. These failures are outside the Task2 production package and no related existing builder product/workflow files were edited. They have not been fixed or broadened into this task. All exact failing names are listed below. Raw tracebacks/output remain **local ignored evidence in `/tmp/botbridge2-full-suite-final.txt`**, not copied into public docs, fixtures or SOURCE.patch; that file may contain unrelated generated configuration/log output and must not be published.

## Self-review and concerns

Self-review checked all ten changed owners, exact protected-byte projections, closure ownership, registration/admission/logout ordering, ordinary fast path, privacy types, UI weak presentation/cancellation lease, fixed ring/pending/file/export bounds and lifecycle labels. It corrected finite state-read attribution (not bridge ownership), numeric live observations from existing transactions, generation validation, soft-reset continuity, race terminal recording, per-snapshot last completion metadata, exact loss accounting, bounded total pending slots, temp export cleanup and failure-closed rotation. No independent reviewer was spawned; that review belongs to the controller.

Material remaining concerns: Swift compiler/runtime execution is unavailable here. The six native fixtures themselves have **not compiled or executed**, actual Signal/Network/SDK/module integration and UIKit/file-picker lifetime behavior remain unverified. These narrow fixtures intentionally do not execute a full real DB, whole send worker, full native account manager or device auth/session. Complete native test-first RED/GREEN evidence is pending. Runtime/API method-name surface, actual engine callback order/internal retries, upload failure paths and local update application remain explicit coverage limits; no universal outbound coverage or server-causality claim is made. Media terminal sends are observed; upload failures before terminal RPC are unobserved. Exact modern worker source projection is evidence of algorithm preservation, not execution of those whole workers.

Retained event files (2 MiB) and the separate active temporary export (2 MiB) have distinct caps. TTL is enforced on initialization/append/export and per exported record; there is no polling timer, so idle files can physically remain past TTL until the next sink access and are excluded when exported. Lifecycle persistence is asynchronous best effort and cannot be guaranteed before crash or immediate process termination. Login-screen export with zero active accounts is outside the agreed Data & Backup action.

## Task 3 integration interface

Materialize from accepted Task1 then apply exactly Task2/SOURCE.patch to its ten owners, including the new diagnostics source. TelegramCore and SettingsUI BUILD source globs already include these paths; neither BUILD needed editing. Run the required production stage/source guards and native workflow on their correct restored/final views. Do not use naive full discovery as the sole regression gate and do not treat this draft package as an IPA delivery.

For the Task2 fixture runner, artifact provenance and actual tested source are independently selectable:

```
JERKGRAM_BOTBRIDGE_TASK2_ARTIFACTS=/absolute/path/to/task2 \
JERKGRAM_BOTBRIDGE_SOURCE=/absolute/path/to/final/materialized/source \
python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v
```

The artifact directory supplies immutable before/proof files; its parent supplies the independent modern baseline. Keep the existing Task1 runner on immutable Task1 by default; do not globally repoint it to Task2 where its historical C-before assertions would be invalid. Task2 contains actual final controller/Postbox extraction coverage separately. CI must have Swift and must reject/notice the six native skips rather than treating this Linux result as native GREEN.

Native/public source interfaces: `AccountStateManager.jerkgramStartBotBridgeHistory(recordId:admit:event:)`, validated `admit(String)->Bool` before controller creation; internal optional Network `diagnosticContext`; typed BotBridgeHistoryEvent phases started/reserved/committed/terminal/handoff/restoredTerminal; `jerkgramExportBotBridgeDiagnostics(completion:)` asynchronously returns Result<URL,BotBridgeDiagnosticExportError>; `jerkgramReleaseBotBridgeDiagnosticExport(URL)` is asynchronous/idempotent. No payload/Account reference enters operation context. No lifecycle adapter owns an extra progress store or history controller.

## Exact non-authoritative full-discovery failure/error names

```
ERROR: test_ci_runs_phase_two_after_phase_one_and_before_music (test_jerkgram_build137_performance2.Performance2Tests.test_ci_runs_phase_two_after_phase_one_and_before_music)
ERROR: test_glass_is_account_setting_gated_and_uses_reference_material (test_jerkgram_v12g_build118_glass1.Build118GlassTests.test_glass_is_account_setting_gated_and_uses_reference_material)
ERROR: test_chat_list_activity_uses_raw_tagged_evidence_not_filtered_preview (test_jerkgram_v12u_build133_blocked_activity1.Build133BlockedActivityContracts.test_chat_list_activity_uses_raw_tagged_evidence_not_filtered_preview)
ERROR: test_chat_list_filters_the_rendered_message_preview_with_explicit_chat_peer (test_jerkgram_v12u_build133_blocked_activity1.Build133BlockedActivityContracts.test_chat_list_filters_the_rendered_message_preview_with_explicit_chat_peer)
ERROR: test_chat_list_rebuilds_when_blocked_visibility_changes (test_jerkgram_v12u_build133_blocked_activity1.Build133BlockedActivityContracts.test_chat_list_rebuilds_when_blocked_visibility_changes)
ERROR: test_direct_block_api_updates_the_shared_policy_cache (test_jerkgram_v12u_build133_blocked_activity1.Build133BlockedActivityContracts.test_direct_block_api_updates_the_shared_policy_cache)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_excluded_history_stage.ExcludedHistoryStageTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_only_reviewed_transformations_change_original_source (test_jg131_performance_followup.PerformanceFollowupTests.test_only_reviewed_transformations_change_original_source)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_performance_followup_stage.PerformanceFollowupStageTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_profile_metadata_stage.ProfileMetadataStageTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_profile_polish.ProfilePolishTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_settings_transparency_stage.SettingsTransparencyStageTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_backdrop_preserves_native_material_and_transition_lifetime (test_jg131_settings_visual_followup.SettingsVisualSourceTests.test_backdrop_preserves_native_material_and_transition_lifetime)
ERROR: test_local_engine_path_precedes_server_rpc_and_never_falls_back (test_jg131_translation.TranslationTests.test_local_engine_path_precedes_server_rpc_and_never_falls_back)
ERROR: test_atomic_apply_restore_and_refuse_unknown_owners (test_jg131_translation_stage.TranslationStageTests.test_atomic_apply_restore_and_refuse_unknown_owners)
ERROR: test_stage_rejects_repeat_and_tamper_without_partial_mutation (test_jg131_ui_repair.UIRepairTests.test_stage_rejects_repeat_and_tamper_without_partial_mutation)
ERROR: test_bad_last_parent_refuses_before_first_mutation (test_jg131_wave1_stage.WaveStageTests.test_bad_last_parent_refuses_before_first_mutation)
ERROR: test_exact_parent_roundtrip (test_jg131_wave1_stage.WaveStageTests.test_exact_parent_roundtrip)
ERROR: test_reapply_is_rejected_without_mutation (test_jg131_wave1_stage.WaveStageTests.test_reapply_is_rejected_without_mutation)
ERROR: test_each_protected_file_remains_locked (test_jg13_deleted_reply_stage.DeletedReplyStageTests.test_each_protected_file_remains_locked)
ERROR: test_exact_application_and_repeat_refusal (test_jg13_deleted_reply_stage.DeletedReplyStageTests.test_exact_application_and_repeat_refusal)
ERROR: test_existing_helper_is_not_overwritten (test_jg13_deleted_reply_stage.DeletedReplyStageTests.test_existing_helper_is_not_overwritten)
ERROR: test_tampered_parent_leaves_all_files_unchanged (test_jg13_deleted_reply_stage.DeletedReplyStageTests.test_tampered_parent_leaves_all_files_unchanged)
ERROR: test_bounded_stage_exists_and_verifies_real_source (test_jg13_download_boost.DownloadBoostTests.test_bounded_stage_exists_and_verifies_real_source)
ERROR: test_repeat_and_tamper_are_rejected (test_jg13_download_boost.DownloadBoostTests.test_repeat_and_tamper_are_rejected)
ERROR: test_full_hash_gate_rejects_tamper_in_every_new_owner (test_jg13_expanded_diagnostics.ExpandedDiagnosticsTests.test_full_hash_gate_rejects_tamper_in_every_new_owner)
ERROR: test_real_owner_selects_existing_listview_and_restores_exactly (test_jg13_history_backend.BackendTests.test_real_owner_selects_existing_listview_and_restores_exactly)
ERROR: test_five_locks_each_reject_modification (test_jg13_portable_copy_stage.PortableCopyStageTests.test_five_locks_each_reject_modification)
ERROR: test_parent_apply_final_hashes_and_repeat_refusal (test_jg13_portable_copy_stage.PortableCopyStageTests.test_parent_apply_final_hashes_and_repeat_refusal)
ERROR: test_tampered_owner_does_not_partly_apply (test_jg13_portable_copy_stage.PortableCopyStageTests.test_tampered_owner_does_not_partly_apply)
ERROR: test_exact_roundtrip_repeat_and_tamper_refusal (test_jg13_premium_icons.PremiumIconsTests.test_exact_roundtrip_repeat_and_tamper_refusal)
ERROR: test_three_gates_are_scoped_to_app_icons (test_jg13_premium_icons.PremiumIconsTests.test_three_gates_are_scoped_to_app_icons)
ERROR: test_profile_capture_exact_delta (test_jg13_profile_capture.ProfileCaptureTests.test_profile_capture_exact_delta)
ERROR: test_round_trip_and_all_owner_tampering (test_jg13_profile_capture.ProfileCaptureTests.test_round_trip_and_all_owner_tampering)
ERROR: test_full_hash_gate_rejects_marker_preserving_tamper (test_jg13_profile_cleanup.ProfileCleanupTests.test_full_hash_gate_rejects_marker_preserving_tamper)
ERROR: test_settings_publish_before_deferred_persistence (test_jg13_profile_preferences.ProfilePreferencesTests.test_settings_publish_before_deferred_persistence)
ERROR: test_about_only_cleanup_is_exact_and_rejects_repeat (test_jg13_release_ui.ReleaseUiTests.test_about_only_cleanup_is_exact_and_rejects_repeat)
ERROR: test_exact_sponsored_stage (test_jg13_sponsored.SponsoredStageTests.test_exact_sponsored_stage)
ERROR: test_round_trip_repeat_tamper_and_atomic_parent_failure (test_jg13_sponsored.SponsoredStageTests.test_round_trip_repeat_tamper_and_atomic_parent_failure)
ERROR: test_exact_stage_and_all_tampering (test_jg13_stars_gift.StarsGiftTests.test_exact_stage_and_all_tampering)
FAIL: test_active_workflows_retain_build116_layer_under_build117 (test_build116_wiring.Build116WiringTests.test_active_workflows_retain_build116_layer_under_build117)
FAIL: test_active_workflows_publish_one_build117_artifact (test_build117_wiring.Build117WiringTests.test_active_workflows_publish_one_build117_artifact)
FAIL: test_release_verifier_protects_foundations_and_packaging (test_build117_wiring.Build117WiringTests.test_release_verifier_protects_foundations_and_packaging)
FAIL: test_localization_gate_is_wired_before_the_build (test_ghostbase_v10zb_seasonal_gifts_localization.SeasonalGiftLocalizationContracts.test_localization_gate_is_wired_before_the_build)
FAIL: test_workflow_publishes_build138_artifact (test_jerkgram_build134_release_contract.Build138ReleaseContract.test_workflow_publishes_build138_artifact)
FAIL: test_workflow_preserves_build119_gates_under_successor_builds (test_jerkgram_v12h_build119_hybrid_ui1.Build119HybridUIContractTests.test_workflow_preserves_build119_gates_under_successor_builds)
FAIL: test_workflow_retains_build120_contract_in_newer_builds (test_jerkgram_v12i_build120_profile_blur_lifecycle1.Build120ProfileBlurLifecycleTests.test_workflow_retains_build120_contract_in_newer_builds)
FAIL: test_overlay_and_verifier_are_wired (test_jerkgram_v12k_build122_edit_caption_history1.Build122EditCaptionHistoryTests.test_overlay_and_verifier_are_wired)
FAIL: test_build122_identity_and_artifact_are_wired_end_to_end (test_jerkgram_v12k_build122_settings_release1.Build122SettingsReleaseContractTests.test_build122_identity_and_artifact_are_wired_end_to_end)
FAIL: test_overlay_is_wired_after_build121_before_bazel (test_jerkgram_v12k_build122_settings_release1.Build122SettingsReleaseContractTests.test_overlay_is_wired_after_build121_before_bazel)
FAIL: test_build123_is_wired_after_build122_and_before_bazel (test_jerkgram_v12l_build123_release_recovery1.Build123ReleaseRecoveryTests.test_build123_is_wired_after_build122_and_before_bazel)
FAIL: test_new_api_ipa_gates_are_part_of_ci (test_jerkgram_v12m_build124_canary_publication1.Build124CanaryPublicationTests.test_new_api_ipa_gates_are_part_of_ci)
FAIL: test_workflow_uploads_private_actions_canary_artifact_only (test_jerkgram_v12m_build124_canary_publication1.Build124CanaryPublicationTests.test_workflow_uploads_private_actions_canary_artifact_only)
FAIL: test_workflow_can_advance_past_build125_with_a_successor_artifact (test_jerkgram_v12n_build125_canary_publication1.Build125CanaryPublicationTests.test_workflow_can_advance_past_build125_with_a_successor_artifact)
FAIL: test_workflow_uses_build125_installer_and_materialized_wiring_gate (test_jerkgram_v12n_build125_wiring1.Build125WiringTests.test_workflow_uses_build125_installer_and_materialized_wiring_gate)
FAIL: test_workflow_publishes_only_current_successor_artifact (test_jerkgram_v12o_build126_release_contract1.Build126ReleaseContractTests.test_workflow_publishes_only_current_successor_artifact)
FAIL: test_build_routes_apply_and_test_the_native_status_overlay_after_build126 (test_jerkgram_v12p_build127_onetime_native_status1.Build127OneTimeNativeStatusTests.test_build_routes_apply_and_test_the_native_status_overlay_after_build126)
FAIL: test_materialized_verifier_and_build_chain_include_owner (test_jerkgram_v12z_build134_context_localization1.Build134ContextLocalizationTests.test_materialized_verifier_and_build_chain_include_owner)
FAIL: test_workflow_stages_build137_scripts_and_runs_regression_contract (test_jerkgram_v12zd_build137_performance1.Build137PerformanceTests.test_workflow_stages_build137_scripts_and_runs_regression_contract)
FAIL: test_bio_outer_section_is_the_single_background_and_corner_owner (test_jg131_settings_visual_followup.SettingsVisualSourceTests.test_bio_outer_section_is_the_single_background_and_corner_owner)
FAIL: test_session_modal_declines_fullwindow_backdrop_and_keeps_native_sheet (test_jg131_surfaces_175.Settings175SurfaceTests.test_session_modal_declines_fullwindow_backdrop_and_keeps_native_sheet)
FAIL: test_chat_failure_is_localized_and_aggregated_without_canceling_successes (test_jg131_translation.TranslationTests.test_chat_failure_is_localized_and_aggregated_without_canceling_successes)
FAIL: test_completed_results_are_versioned_and_not_reused_after_source_changes (test_jg131_translation.TranslationTests.test_completed_results_are_versioned_and_not_reused_after_source_changes)
FAIL: test_composer_translation_keeps_native_apply_result (test_jg131_translation.TranslationTests.test_composer_translation_keeps_native_apply_result)
FAIL: test_failure_is_not_completed_pinned_cache_and_all_native_consumers_validate_source (test_jg131_translation.TranslationTests.test_failure_is_not_completed_pinned_cache_and_all_native_consumers_validate_source)
FAIL: test_background_preflight_before_apple_translation_and_manual_only_opt_in (test_jg131_translation_175.DownloadPolicyTests.test_background_preflight_before_apple_translation_and_manual_only_opt_in)
FAIL: test_capture_uses_explicit_weak_snapshot_after_controller_creation (test_jg131_ui_repair.UIRepairTests.test_capture_uses_explicit_weak_snapshot_after_controller_creation)
FAIL: test_restored_components_equal_official_source (test_jg131_ui_repair.UIRepairTests.test_restored_components_equal_official_source)
FAIL: test_exact_stage_refuses_tamper_and_repeat (test_jg131_ui_type_compat.UITypeCompatibilityTests.test_exact_stage_refuses_tamper_and_repeat)
FAIL: test_snapshot_catalog_preserves_49_keys (test_jg131_wave1_projection.ProjectionContracts.test_snapshot_catalog_preserves_49_keys)
FAIL: test_client_hooks_preserve_every_original_source_byte (test_jg13_expanded_diagnostics.ExpandedDiagnosticsTests.test_client_hooks_preserve_every_original_source_byte)
FAIL: test_bounded_session_and_shutdown (test_jg13_performance_capture.CaptureTests.test_bounded_session_and_shutdown)
FAIL: test_internal_capture_actions_and_export_remain_available (test_jg13_performance_capture.CaptureTests.test_internal_capture_actions_and_export_remain_available)
FAIL: test_timing_and_native_output_routed_into_capture (test_jg13_performance_capture.CaptureTests.test_timing_and_native_output_routed_into_capture)
FAIL: test_persistent_stack_and_layout_no_processing (test_jg13_profile_cleanup.ProfileCleanupTests.test_persistent_stack_and_layout_no_processing)
FAIL: test_scene_lifecycle (test_jg13_profile_cleanup.ProfileCleanupTests.test_scene_lifecycle)
FAIL: test_header_phone_preference_is_memory_only_and_fresh (test_jg13_profile_preferences.ProfilePreferencesTests.test_header_phone_preference_is_memory_only_and_fresh)
```


# Task 2 fixround 1 — R1/R2/R3/R4

Status: DONE_WITH_CONCERNS for scoped independent rereview. This appendix supersedes the original lifecycle-target, deletion-boundary and enumeration implementation details above. The authoritative current after hashes are in regenerated `task2/OWNER-MANIFEST.json`; original report hashes describe the frozen initial-review input in `task-2-fix1-before`.

Read and verified all verbatim findings in `task-2-review-report-0.md` before editing, using the receiving-code-review/TDD workflow. Scope was limited to those four findings. Product changes relative to the controller's frozen fixround input affect exactly **three** existing Task2 owners:

| Fixround product owner | Frozen review input SHA256 | Current SHA256 |
| --- | --- | --- |
| `submodules/TelegramCore/Sources/Account/Account.swift` | 44c30eca89ef89ac2b96a687f7cabf1bcb7c0f20c39d9ecba3e4533230fcec1e | 90af53fff47956875a48490f1299e6e6c60ed2f92b02ed04aeae6f8a72712fb8 |
| `submodules/TelegramCore/Sources/Account/AccountManager.swift` | ad738b587a3f22cc742d9ae9ffbc08eadb023f9a162de39b66e39886a0c383f8 | 19e13b217a98cbfae109d220fd38afaea09c5d00b6d4787c4b806b41bcc8ccf6 |
| `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift` | 6f8aa906ba17d6b6b3654ff7a766f14ad94fa18da426b3efd0a5d1bff01f17bd | 2acd698c5056f8576a410cf0204dad14186279d52a5df2918860706c0d6f1da3 |

`task2/FIXROUND1-OWNERS.json` preserves this delta separately. Regenerated `SOURCE.patch` still applies from the immutable accepted Task1 `task2/before`; there are still ten total Task2 changed owners and 557 final files. All **556 accepted Task1 files** again compared exactly to Task2/before/BASELINE.json. Task1 source and its fixtures were not modified. Modern worker context proof and Network normalization were unchanged and still pass against the independent modern manifest. RESOURCE-POLICY.json gained only the explicit enumeration-failure policy; numerical limits did not change.

## R1 — original authorization generation/epoch target

Registry entries now explicitly contain validated UUID authorization generation and runtime epoch alongside the actual weak AccountManager namespace and record id. `BotBridgeDiagnosticTarget` is an immutable non-Codable operation token: record/generation/epoch/directory name are `let`, and namespace is externally read-only weak storage. It owns no Account, scope or manager.

`target(namespace:record:)` captures the original operation token; `notify(target:kind:)` revalidates namespace identity **and record and generation and epoch** under the bounded registry lock, copies only that original matching scope, unlocks, then invokes lifecycle. A removed/replaced/dead token cannot resolve a later scope. Immediate subscribed logout still resolves at subscription; deferred cleanup captures one `diagnosticTarget` before cleanup-start and uses that same token in its completion, with no later record-only lookup.

The actual native lifecycle fixture now replaces the original target before invoking old cleanup completion and checks the replacement remains active. It covers both a new generation and a new epoch within the same generation. It also checks a held deferred token does not keep its namespace alive and cannot invoke lifecycle after namespace deallocation. These native assertions remain unexecuted pending Swift; portable checks protect the actual capture and bound-target call sites.

## R2 — truthful directory scheduling

Removed `deletionScheduled` from `beginList` and from `reconcile`. Record absence now records only removal; cleanup start says only cleanup start. Account admission passes the **actual `accountRecordIdPathName(id)` result** as an internal, non-exported directory name; no decimal/hex path decoding or reconstructed path spelling is used.

Before the existing utility-queue directory pass, the existing cleanup observer captures a bounded array of original weak target tokens. The utility pass now calls `botBridgeScheduleAccountDirectoryDeletion(directoryName:validPaths:targets:)`, which contains the exact original `account-` prefix / path-not-in-validPaths predicate and emits the matching token's finite scheduling event immediately before the existing removal attempt. Native deletion policy and removal attempt semantics are preserved. A late queued directory observation uses the captured generation/epoch and cannot freeze a replacement scope for a reused path.

The native fixture executes the actual predicate/hook: cleanup-start plus a path still in validPaths produces **no** deletion-scheduled event; excluding the path then produces one event. It additionally replaces the scope before a queued old-token scheduling callback and checks the replacement remains active. No supplementary registration or extra account-record observer was added.

## R3 — explicit directory errors / failure closed retention

The sink now has one injectable filesystem enumeration boundary, `(URL) throws -> [URL]`, whose default is the existing FileManager directory listing. This is used for every sink listing: startup/retention/rotation, stale temporary exports and retained export records. `files()`, `prune()` and stale-export cleanup propagate errors; no listing error is converted to an empty array.

`drain() -> Bool` performs successful retention enumeration before any append, propagates later rotation/listing/read/write failures, counts storage failure, and stops. Export requires a successful drain and all preparation/listing/read operations; any failure returns the finite public `.storage` result and releases its busy slot instead of generating `no_captured_sessions`. The loss counter and `storageLossCountUnknown` remain visible after a later successful recovery. Encoding and persistence still run only on the sink queue; no raw filesystem error is serialized.

New `diagnostic_filesystem_failure.swift` executes the actual sink with a throwing directory boundary while real file creation remains permitted. It seeds nine existing files, denies enumeration, performs repeated accepted batches/exports, and verifies no additional event files or misleading export JSON are created. It separately injects failure at each export enumeration position (retention, stale export, retained record listing), expects `.storage`, then recovers enumeration and checks storage failure/unknown-loss labels. It does not reimplement retention policy. This native test is present but has not compiled/executed on Linux.

## R4 — exact actual history adapter serialization

Extracted the existing mapping into the production pure helper `botBridgeDiagnosticHistory(_:) -> (history: BotBridgeDiagnosticHistory, phase: BotBridgeDiagnosticPhase)`; the real Owner callback delegates to that same helper. The mapping's fields/semantics remain unchanged.

New `diagnostic_history_export.swift` compiles the **actual** typed history event, policy types, numeric tuple helper, mapping helper, recorder and sink together. It sends start/end/restored-terminal events with distinct original/candidate/retrieval/live numeric tuples and distinct counters through that actual mapping and real recorder into a real asynchronous redacted JSON export. Assertions inspect exact history key sets, each numeric tuple field, every inserted/skipped/unsupported/deletion/missing counter, reserved attempts versus commits, finite reasons, live-state/handoff coverage flags, and absence of private/progress/parameter/error sentinel keys. No handwritten fixture mapping substitutes for the production adapter. Native execution remains a mandatory Task3 gate.

## Focused RED/GREEN evidence and verification

Before R1–R3 production fixes, added covering fixtures and portable boundary guards, then ran:

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v > /tmp/botbridge2-fix1-red.txt 2>&1`

```
Ran 17 tests in 0.017s
FAILED (failures=3, skipped=6)
```

The three failures were the missing immutable generation-bound lifecycle token, the false deletion scheduling boundary, and suppressed enumeration errors. Before extracting the R4 mapping helper, its covering native fixture/portable extraction guard also ran RED:

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v > /tmp/botbridge2-fix1-r4-red.txt 2>&1`

```
Ran 20 tests in 0.017s
FAILED (failures=1, errors=1, skipped=7)
```

The portable guard failed because the actual mapping helper was absent; fixture assembly raised ValueError for that missing production extraction anchor. This is source-boundary RED evidence, **not executed native behavioral RED**.

Final focused command, exit 0:

`python3 -m unittest discover -s tests -p test_jg131_botbridge1_diagnostics.py -v > /tmp/botbridge2-fix1-green.txt 2>&1`

```
Ran 20 tests in 0.017s
OK (skipped=8)
```

Result: **12 portable checks passed; 8 native fixtures explicitly skipped** because Swift is unavailable. The original six native gates remain; two new gates cover filesystem failure policy and exact serialized history mapping. Existing lifecycle fixture now covers original generation/epoch and retained/excluded/replaced directory behavior. No native compilation, full AccountManager worker execution, real DB, UIKit/app API or device result is claimed. Native RED/GREEN remains pending Task3.

Patch applicability was rerun, exit 0, all ten owners checked without writes:

`patch --dry-run --batch -p1 -d '../jerkgram-next/botbridge1/task2/before' < '../jerkgram-next/botbridge1/task2/SOURCE.patch'`

Self-review checked the three changed source owners, all enumeration paths, generation/epoch/weak ownership, capture-before-defer ordering, unchanged directory predicate, actual history helper extraction/serialization coverage, and exact modern projections. The fixed package retains the resource caps, no ordinary-user recorder, no payload/private-ID export, no synchronous hot-path filesystem work and no duplicate history owner. The earlier repository-wide discovery was **not rerun** or expanded in this fixround. Its local evidence and limitations above remain unchanged. No stage/workflow/full-build/commit/push actions occurred.

## Task3 interface changes from fixround 1

Public export facade/result and optional Network context interfaces are unchanged. Internal lifecycle adapters now use `BotBridgeDiagnosticTarget`, `target(namespace:record:)`, `targets(namespace:)` and `notify(target:kind:)` for deferred work. Account diagnostic admission receives the original `accountRecordIdPathName(id)` string as `directoryName`; it is only internal token metadata, never part of serialized diagnostic records. The exact original directory predicate/hook is `botBridgeScheduleAccountDirectoryDeletion(directoryName:validPaths:targets:)`.

The sink initializer gains a defaulted throwing `listDirectory` filesystem boundary, and the pure typed history mapper is now directly extractable as `botBridgeDiagnosticHistory(_:)`. New test fixture files are `tests/fixtures/botbridge1/diagnostic_filesystem_failure.swift` and `diagnostic_history_export.swift`; existing `diagnostic_lifecycle.swift` and the focused runner are extended. Artifact/source environment variables are unchanged; Task3 must run the current **20-test runner with all eight native fixtures executed**, retain independent artifact roots for immutable baselines, and apply the regenerated SOURCE.patch/current OWNER-MANIFEST. The unchanged worker proof still recovers exact protected modern bytes. Native/app/API compilation and final authoritative stage/CI/IPA delivery remain required.
