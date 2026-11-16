# Profile Time Machine foundation implementation plan

> **For agentic workers:** use executing-plans for root integration; independent storage, requests and build audits already delegated.

**Goal:** preserve actually observed profile changes without UI work or added unbounded hot-path work.
**Architecture:** account-scoped SQLCipher append history; fixed-memory membership filter and event ingress; selective foreground BIO scheduler; retain legacy stores and writers.
**Tech Stack:** Telegram 13.2, Swift/SwiftSignalKit, Postbox, existing SQLCipher, Bazel9.2.0/Xcode27.1.
**Spec:** user attachment63fe99b7 plus six critical requirements; user's subsequent correction explicitly supersedes its stale12.9.2 pin.

## Global constraints

- Telegram13.2 commit24638bc69bd083981b178dd1e7f921eebbf7fc46, productBuild183; experimental branch dev/profile-time-machine-13.2 from243e367 (published equivalent636dece).
- No changes to released product branches, notifications, release identity, UI or stories.
- No invented BIO values, false snapshots, all-user polling, global SQLCipher configuration changes, destructive migrations or capped disk history.
- Python/static checks, native component execution, full app compilation and real-device performance are separate evidence levels.

## Review focus

- Unknown BIO becoming known must enrich, never imply an earlier BIO change.
- In-flight invalidation and FLOOD_WAIT must not trigger concurrent requests or unlimited retries.
- Account disposal/logout and reactivation must reject stale work and isolate files.
- Overflow and unreadable storage must be visible failures, never silently recreate history.
- Wrong key, WAL crash recovery and interrupted/changed legacy source migration must preserve original bytes.

## Tasks

1. **Encrypted store:** create JerkgramProfileHistoryStore.swift and actual native SQLCipher runner. Test baseline/enrichment/change, atomicmulti-field, paging beyond500, semanticPresence, account paths, keyerrors, migration retry/rollback/raw fidelity. Implement only after failing fixtures; retain source stores. Commit separately.
2. **Admission/model:** create JerkgramProfileObserverAdmission.swift + Foundation executable tests for no-watch fastpath, FIFO bounded capacity, single drain, overflow reporting and stalegeneration rejection. Rewrite main observer to project native user fields only after admission on utilityqueue, stable encodings, weak Account lifecycle. Verify hooks on genuine currentproduct. Commit.
3. **BIO:** dedicated invalidation events through current13.2 state pipeline without changing existing external-ID subscribers. Add one-inflight foreground scheduler with4096pending, monotonic spacing, actualFLOOD_WAIT, finitefailure policy and cancellation. Pure productionpolicy native tests + pinnedsource patch tests. Commit.
4. **Integration:** atomicfail-closed installer precomputes every edit/payload/dependency before writes; idempotence/rejection tests. Register existing per-device key at authorized Account creation; keep old historywriters; separatePresence journal. Audit with exactsourceowners.
5. **Build evidence:** dedicated experimentalworkflow uses actualBuild183 source materialization + observer overlay, existing13.2 toolchain and realfullBazel target. One current componentgate, preserve diagnostics; no release or stablepipeline changes. Run localsourcechecks; dispatch experimentalCI after review. Never call Python/parse green a workingiOS feature.
