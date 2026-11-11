# Beta 2 Recovery Implementation Plan

> Latest user steering: retain this recovery as a reviewed local base. Do not publish or launch a separate recovery IPA. Implement Local Premium (TASK A) and Saved Messages Tags (TASK B) as separate descendant commits, then review and build one combined release. This supersedes the earlier recovery-first delivery order below. Native/device gates remain pending.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Parent owns publication/CI. No per-task heavy builds.

**Goal:** Recover retained bot accounts from Build178 startup crash, remove reported UI/policy regressions, and publish Beta2 recovery179 before Local Premium/Tags work.

**Architecture:** Explicit Postbox-compatible progress codec preserves the same live manager/storage. New strict terminal source stage composes after BOT and exposes reversed parent views. Existing Settings/native row renderers and canonical preferences remain.

**Tech Stack:** Official Telegram13.1.2, Swift/Postbox/ItemList, Python exact materializers, GitHub macOS/xcode27.

**Spec:** docs/superpowers/specs/2026-11-05-beta2-recovery.md

## Global Constraints

- Base33fffd93b5d3cc207a5ce2492b43292fe09ea6b8; exact upstream279f89e4d4f63f17227bf877dc3d8990f22ecd58; nextbuild179 checkedbeforepublish.
- No account/history/preferences reset, global Premium spoof, second settings store/state loop, new external service, global theme darkening or translation rewrite.
- Draft before immutable; source-based final patch/manifests authoritative. Unknown parent refuses beforemutation, reapplynoop, exactreverse and historicalgates mandatory.
- Real production Postbox codec tests; native unavailableLinux remainsSKIP, mandatorymacOS gate cannot acceptskips.
- Same Work Local chat/current dedicated checkout, original178/Projects source immutable; userpublication/implementation authorization persists.

## Review Focus

- Retained initial record from optimized178 decodes same owner/peer/generation after upgrade; no forced reauthorization.
- Every terminal reason persists/reloads without unsupported singleValueContainer; malformed input yields safely persisted corrupt progress.
- Stored DefaultFolder ON/stale proposal/account switching never reenables local order or prunes saved prefs.
- Scoped card alpha survives live theme/push transitions without changing profiles/other Settings sections or accessibility behavior.
- Beta2 display/telemetry/build identity and every exact stage/chain owner hash agree after release identity derivation.

### Task 1: Explicit progress codec and real Postbox regression

**Files:** draft ../jerkgram-next/beta2/recovery/source/submodules/TelegramCore/Sources/State/JerkgramBotBridgeHistory.swift; new tests/test_jg131_beta2_bot_codec.py, tests/fixtures/beta2_bot_codec/ and pinned official codec dependencies/provenance as needed.
**Interfaces:** Keep BotBridgeHistoryProgress public/in-memory fields, initializer, schema1/key0x4A470002 and policy APIs. Produce explicit CodingKeys/init(from:)/encode(to:), no Int or raw enum calls to unsupported adapter methods. Task3 consumes final owner bytes and native test entrypoint.
- [ ] Read exact source crash evidence and actual Postbox adapters. Record old optimized negative reproduction design before changing code.
- [ ] Add actual PreferencesEntry/codec native subprocess tests using pinned implementation sources/module: old Int read fails and old terminal traps; fixed initial/reserved/cursor/page/all-terminal roundtrips; release-shaped legacy Int32 record preserves identity; malformed/unknown/negative/out-of-policy data failsclosed; safe corrupt fallback roundtrip and repeatedprepare/read/write.
- [ ] Implement smallest explicit keyed wire codec with checked Int32 conversions and terminal String. Preserve Int64/Bool/Double/nestedCursor and all existing policy/lifecycle/network/storage algorithms.
- [ ] Run portable guards/quality and prepare mandatory native compile/run for -O and -Onone. No sourcefacade/JSON test may stand in for actual Postbox persistence. Native unexecuted stayspending.
- [ ] Report exact changedowner/provenance/commands; independent task review and scoped fixes before Task2. No commit/push/build byworker.

### Task 2: Disable Default Folder and targeted UI cleanup

**Files:** draft TelegramCore/TelegramEngine/Peers/ChatListFiltering.swift; SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift; TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift and PeerInfoScreenItemSectionContainerNode.swift; focused tests/fixtures.
**Interfaces:** Consume acceptedTask1source. Preserve existing DefaultFolder storage types/keys and nativewrappers; add one effective disabled capability at snapshot/proposal/prune boundaries. Carry scoped dark0.44 override through existing section update/reconciliation for .ghostbase only.
- [ ] Add tests for storedtrue/order/staleproposal/defaultfalse/no localwrites, nativeprojection/entitlements unaffected, oldprefsretained.
- [ ] Disable runtime and hidecontrol/hint; do not globallydisable native folder reorder.
- [ ] Add narrowly scoped dark material override (lightunchanged) and same-section Media footer; preserve lifecycle/theme reconciliation/accessibility and existing renderer.
- [ ] Run covering portable/nativefixtures whereavailable; report no screenshot/deviceproof. Review independently and fixscoped.

### Task 3: Exact stage, Beta2 identity and recovery release

**Files:** patches/jg131-beta2-recovery.{patch,sha256.json}, scripts/materialize_jg131_beta2_recovery.py, scripts/verify_jg131_beta2_recovery.py, tests/run_jg131_beta2_recovery.py +stage/integrationtests; configure/releasemetadata/workflows/sourceverifier; docs/recovery reports.
**Interfaces:** Consume acceptedTask1/2 finalsource. Latestverifier peels recovery→BOT→C so historicalpositiveDefaultFolder/sourcehashchecks see exactoldparent. Newtests see finaldisabledpolicy/fixedcodec.
- [ ] Generate exact terminalpatch for changedowners only; apply415filefidelity/reapply/corruptlastparent refusal/no partialwrite/reverseexactoldsource.
- [ ] Set Beta2 display/technical and179 build coherently. Derive required Strings identity parents/outputs from verified178 bytes and unchangedfeaturepatchreversals for profile-metadata and translation-repair; changeonlyidentitylinevalues and associatedexacthashfields/chainrows, preserveoldhistory/featurepatchbytes. No blanketmanifestregeneration.
- [ ] Wire mandatory realcodec/native/fullsource gates before app; existing historicalrunner onreversedparent and migrationchain regressions mustallpass. No global gateweakening or fake sourceHEAD/fullcheckoutclaim.
- [ ] Run correct composedportable and requiredmacOSsource/native. One wholebranchreview then scopedfixes; publish exactreviewedtree to recoverybranch with expectedheadlease.
- [ ] Start IPA build afterrequiredgate and monitoronlyfirstfewminutesperuser. Captureactualrun/commit/status; do notwaitfullIPA orclaimdeviceresolved prematurely. Then continue remaining LocalPremiumA/TagsB on descendantfeaturebranch, separatecommits.
