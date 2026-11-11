# Beta 2 recovery and reported regressions

> Latest user steering: retain this recovery as a reviewed local base. Do not publish or launch a separate recovery IPA. Implement Local Premium (TASK A) and Saved Messages Tags (TASK B) as separate descendant commits, then review and build one combined release. This supersedes the earlier recovery-first delivery order below. Native/device gates remain pending.

## Authority and intent

User reports Build178 bot token login followed by a crash on every app launch. No crash report/export/screenshots are available because the app cannot open; do not request them again. Fix launch without deleting account data, history, bot authorization or preferences. Also disable experimental default folder, darken only the relevant Jerkgram Settings area, reduce Media & Stories explanatory gap, and show Beta 2 in Settings and telemetry.

Current verified product: builder33fffd93b5d3cc207a5ce2492b43292fe09ea6b8, dev/botbridge1-legacy-history-modern-write, Build178 GREEN run41512083073. Actual upstream13.1.2 pin279f89e4d4f63f17227bf877dc3d8990f22ecd58. Reuse dedicated checkout on dev/beta2-recovery-179; no new chat/project/worktree. Before/source drafts at ../jerkgram-next/beta2/recovery preserve415 genuine product files and exact13BOT owner outputs. Original178 and originalProjects checkouts stay immutable.

## Proven startup defect and chosen repair

Source evidence ../jerkgram-next/beta2/research/bot-crash/AUDIT.md: progress synthesized Int Codable writes Int32 under optimized Postbox, cannot decode Int via its adapter, then .corrupt raw enum asks unsupported single-value encoder and precondition-fails before diagnostics. Keep model Int policy and existing key/schema/field names; add explicit keyed Int32 schema/counter encoding and decoding plus keyed terminal String.rawValue. Preserve owner/peer Int64, Bool, Double, generation String, optional keyed Int32 cursors. Checked integer conversion and valid bounded production writes are mandatory because PostboxEncoder uses try!; invalid persisted input must fail closed into a safely serializable corrupt state. Initial Build178 release record must decode preserving its authorization generation. No new state machine, auth suppression, global encoder modification, JSON persistence blob or data reset.

Alternatives rejected: changing only Int fails terminal encoding; changing only enum fails every progress read; disabling bridge startup alone avoids a symptom without enabling history and does not address debug auth writes. Real pinned PreferencesEntry/PostboxEncoder/Decoder regression is required; Any and JSON facades cannot establish this fix. Expected old crashes isolated to subprocesses; no device-success claim from source evidence.

## Reported UI/policy regressions

Disable all effective default-folder behavior, not just its switch: snapshot always disabled, stale proposal transaction and pruning hooks no-op; retained local order and UserDefaults remain unchanged. Native folders/reorder/server/Premium behavior remain. Remove Default Folder control/hint.

Interpret screenshot-unavailable “Gram” as the Jerkgram card in main Settings, not Wallet/collectibles. Scope dark alpha0.44 (from0.26) to isSettings && .ghostbase; preserve light0.18, all neighboring cards/profiles, theme switches and accessibility policy. This numeric/area choice is an executor ruling, not a screenshot-approved result. Media & Stories Download Boost explanatory info belongs to section0 with its control, not section1. Native text/Dynamic Type and other footers unchanged.

Display1.2.0 Beta 2; technical1.2.0-beta.2; upstream/bundle short version13.1.2. Proposed next build179, recheck before publication. Settings and telemetry must use the same Strings constants, app/extensions/package179 agree. Authoritative new source stage after exact BOT; historical verifiers see disposable reversed178 parent views. Existing feature patch bytes remain fixed; only proven release-identity Strings hashes in two dependent manifests may be derived and propagated explicitly, preserving prior evidence.

## Delivery and remaining scope

Publish recovery before long feature work, source/native preflight then IPA. User explicitly wants launch and only first few minutes monitoring, not waiting for IPA completion. No runtime success until user opens retained installation. Follow with Local Premium Hub (TASK A) and Saved Messages Tags (TASK B) as separate commits on a descendant feature branch, audited owners/native assets/local indexed persistence, with Translation unchanged and no further Premium features. Those requests remain required after recovery and are not replaced by this plan. Optimization is restricted to proven costs/defects; no broad blind cleanup.

Existing user authorization covers implementation, routine technical choices, GitHub publication and builds. User repeatedly delegated execution/asked continue; no new design/order permission pause is needed.
