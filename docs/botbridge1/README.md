# BOTBRIDGE1 delivery and evidence index

## Current state

Modern **Build177 is GREEN**, exact compiled code `5ba6add985d6995ca102d4e40d8da66e98f443c1`, Telegram13.1.2 pin `279f89e4d4f63f17227bf877dc3d8990f22ecd58`. [Verified modern release](../releases/build177-result.md).

Experimental **Build178 BOTBRIDGE1 is not released yet**. History, diagnostics and terminal source-stage task reviews approved local code. Whole-branch review, macOS required native/full-source preflight and actual app build remain delivery gates. Linux skipped native cases are not passes. Device/server behavior is not established by compilation.

Earlier research documents preserve their then-current checkpoint wording. Their “Build177 pending” statements describe the research snapshot, not the current release state above.

## Architecture

One current Account, Network, Postbox and AccountStateManager remain. The finite history importer runs serialized custom operations, yields between pages and never replaces live pts/qts/date/seq. Imported absent messages use current storage/converters/inclusion, bypassing only interactive callbacks for this historical call. Existing messages and peers are retained. Outbound operations keep the modern runtime; passive diagnostics add opaque context and observed outcomes.

Build82 source is exactly `2d120ab4a72dd2217269d7b6a7142a8ef0ce3cd3`. Retained semantics: current server snapshot, unread-based clamped PTS candidate, getDifference retrieval. Adaptation: consume the first payload directly, use a private bounded cursor for existing/new accounts, import absent content without generic historical replay or live-state seeding. This is best-effort backlog retrieval, not an all-time-history guarantee.

No legacy source file is copied wholesale. Adapted symbols live in new `JerkgramBotBridgeHistory.swift` with narrow current Account/authorization/manager/Postbox integration. New `JerkgramBotBridgeDiagnostics.swift` observes current paths. Old UI/badges/global bot markers, old outbound stack, old account lifecycle, zero-cursor pager, second live loop and account-wide history logout suppression are excluded. See [historical classification](history-audit.md), [modern write proof](write-audit.md), [exact stage integration](stage-integration.md).

## Reports

- [Audit matrix and exact risks](audit-matrix.md)
- [Module and path cost map](cost-map.md)
- [Fifteen acceptance scenarios and proof boundaries](scenario-matrix.md)
- [Bot A/B/C device experiment and JSON field guide](runtime-experiment.md)
- [Decisions, costs and coverage limits](decisions.md)
- [History implementation](history-implementation-report.md), [accepted scoped review](history-review-fix1.md)
- [Diagnostics implementation](diagnostics-implementation-report.md), [accepted scoped review](diagnostics-review-fix1.md)

First-wave performance A/B1/B2/C, translation repair, default folder and Settings/device-detail glass are already combined in modern177. This experiment adds no unrelated UI/performance changes. Deferred D–H/S7 work is not represented as complete.
