# Telegram13.1.2 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move existing source-based Jerkgram to genuine Official Telegram13.1.2 while retaining all reviewed features.

**Architecture:** Sequentially rebase existing source stages onto exact target parents, preserving upstream bugfixes and strict verification. Full native checkout is authoritative; local selected source projection is a bounded audit artifact.

**Tech Stack:** Swift/Objective-C, Git source patches, Python materializers, existing macOS native workflow.

**Spec:** docs/superpowers/specs/2026-11-01-telegram-1312-migration.md

## Global Constraints

Target279f89e4d4f63f17227bf877dc3d8990f22ecd58/app13.1.2; Xcode27.1/Bazel9.2.0 unchanged.
Preserve all JG features and every upstream fix, including target tlottie gitlink.
No fake pin/HEAD/archive digest, full-owner overwrite, verification bypass or compiler flag changes.
No heavy app build during migration preparation, no BOTBRIDGE1 changes.
Preserve old17ff source/evidence and historical docs; update active metadata intentionally.

## Review Focus

Media diagnostics must coexist with rotation/seek/timing fixes, including tuple shape.
Every create-bot and state-manager constructor/conformer must forward the new explicit flags.
Bot-storage completion must retain upstream quota/removal semantics.
Stage parents/reverse views must reflect target, not stale old whole-file hashes.
Selected local source must not be presented as complete checkout or runtime proof.

## Task 1 — Coupled upstream/stage migration

- [ ] Read audited compare and exact chain; preserve original digests and source parents.
- [ ] Obtain verified target parent bytes; label projection vs complete checkout honestly.
- [ ] Add focused RED preservation tests for signature/media/bot-storage clusters.
- [ ] Rebase stable port then each stage in actual order; resolve media conflict hunks explicitly.
- [ ] Update active pins/manifests/config/prepare and tests, preserving strict guards.
- [ ] Replay twice, verify reverse/tamper/idempotence and scoped A/B/C/regression tests.
- [ ] Report exact changed owners, merge evidence and native gaps; no commit/push/app build by implementer.
- [ ] Independent review, fix concrete findings, publish separate migration commit/source-only gate.

## Task 2 — Real native proof and combined app artifact

- [ ] Actual macOS clean target checkout/source gates, resolve real failures within scope.
- [ ] Verify latest successful real IPA and choose next build coherently across identities/hashes.
- [ ] One combined app build, scoped compiler/link fixes, require GREEN artifact metadata.
- [ ] Device limitations and next isolated BOTBRIDGE1 scope reported explicitly.
