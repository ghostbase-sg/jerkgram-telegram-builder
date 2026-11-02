# Build178 CI fixture correction 1 review

Reviewed the three fixture changes against HEAD `701c469`, the supplied exact diff, `ci-fix1-errors.md`, `ci-fix1-report.md`, the relevant native extraction drivers, the existing portable log, and the production cursor validation used by these fixtures. Scope is this correction only; no fresh broad audit or test rerun was performed.

## Spec compliance: PASS

- The lease binding and all five affected storage page bindings are now private. This addresses the reported Swift visibility errors while retaining verbatim extraction of the private production types. No production access level or extraction driver changes appear in the tracked diff.
- The controller helper preserves date 21 as its default and permits an explicit date. The rejection scenario now supplies the unchanged tuple `(90,4,20,6)`, retains the `.nonadvancing` terminal assertion, and retains the zero-mutation assertion despite carrying a message.
- The added scenario supplies `(90,4,21,6)`, which advances only date under the unchanged production full-tuple comparison. It checks saved retrieval progress, the next actual request, continued nonterminal pagination, and later final-page import/completion. It therefore preserves the behavior that exposed the mistaken original expectation.
- The tracked change set contains only these three fixtures. Production code, patch, manifests, workflows, and native drivers are unchanged. The inspected drivers retain all 15 native execution calls: five history and ten diagnostics, including both consumers of the shared controller fixture. No skip, success bypass, or weakened existing assertion was added.

## Quality verdict: APPROVE for publication and revised CI

No concrete findings within the correction scope. The changes address both recorded root causes and add focused coverage for the date-only advancement behavior.

The existing portable log records 54 discovered cases with 15 native cases skipped (39 executed), plus an explicit native parsing skip because xcrun is unavailable. This review inspected that evidence and did not rerun it. It is not revised macOS native GREEN; actual revised native compilation/execution remains pending CI. The earlier official full-checkout scan and the later local 413-file source scan remain distinct claims.

No code changes were made by this review. The untracked release note was outside the three-fixture review scope.
