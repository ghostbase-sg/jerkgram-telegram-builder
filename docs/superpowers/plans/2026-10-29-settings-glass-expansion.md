# Settings Glass Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend translucent Settings to native device detail cards and improve readable separation.

**Architecture:** Reuse Settings material policy and native card fill. Explicit opt-in from the Settings session flow; no generic modal or blur changes. Append one exact terminal source stage.

**Tech Stack:** Swift/UIKit/ComponentFlow, Python materialization and native Foundation fixtures.

**Spec:** docs/superpowers/specs/2026-10-29-settings-glass-expansion.md

## Global Constraints

Official13.1.1 fb0e62 pin; preserve TASK A/B and Build176 source-based features.
Dark item0.34/light0.26; cardblack0.60/white0.70; no low-power tint substitution.
Reduce Transparency or master/translucency OFF = native. Native outer dim0.4,
card bounds/corners, clipping, hit testing and gestures unchanged.
No global hooks/observers/swizzling, extra blur, premium/unrelated changes.
Do not edit generic ResizableSheet/ViewController/ComponentContainer owners.

## Review Focus

Toggle/accessibility change while card open must refresh both cached component levels.
New style must not leak into non-Settings callers or full-screen outside area.
Reduced effects must not create old0.90 darkening; native text contrast remains.
Terminate/checkbox/form/scroll state must survive visual updates.
Prior B/A reverse views and exact source parents must survive terminal stage.

## Task 1 — Coupled material policy and native card adoption

- [ ] Read spec and current four before/source owners in task-c; research file is pristine evidence only.
- [ ] Add focused RED tests/production Swift policy fixture; observe portable failure before implementation.
- [ ] Implement four owners, default-false public parameter, two component equality updates, existing lifecycle observer routing.
- [ ] Run scoped tests; native absence is an explicit skip; report changed symbols and API evidence. No build/commit/push.
- [ ] Independent task review of source diff and fixtures, fix concrete findings.

## Task 2 — Exact terminal materialization and source gate

- [ ] Generate patch/manifest against immutable task-c/before matching TASK B replay.
- [ ] Add strict idempotent materializer and reverse parent view, stage fixtures and terminal runner.
- [ ] Wire build/native/old-verifier recursion after B; include changed owners in final syntax gate.
- [ ] Fresh replay apply/reapply, C fixtures + reverse B/A/source contracts; source-only macOS publication.
- [ ] Separate C commit, evidence and broad review of C changes/integration.

## Task 3 — Combined app artifact

- [ ] Verify latest real successful IPA/build number; update all identity/hash dependencies coherently.
- [ ] Enable candidate branch app build once; retain its own source gate; no speculative compiler flags.
- [ ] Resolve actual compiler errors within scope, require GREEN and artifact metadata; distinguish device checks still pending.
