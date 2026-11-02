# Task 3 review, round 0

## Spec compliance

- ✅ Spec compliant for the delegated **local integration/source-stage scope**. No missing, extra, or misunderstood implementation requirement found in that scope. This approves a review candidate, not completion of the brief's native/app/IPA delivery requirement.
- Scope: base builder `5ba6add985d6995ca102d4e40d8da66e98f443c1`; local package `task-3-review-0.md`; requirements `task-3-brief.md`, accepted-input division `task-3-context.md`, and concrete `task-3-integration-notes.md`. Accepted Task1/2 product gates are inputs to this review; whole-branch architecture review is separate.
- ⚠️ Cannot verify native execution, a real full-checkout scan, compiler success, run/artifact identity or IPA bytes from this diff. `docs/botbridge1/stage-integration.md:47` distinguishes native fixtures from app/device proof, and `docs/botbridge1/stage-integration.md:71` explicitly leaves publication and those results pending. Parent must obtain required macOS gate and app GREEN, then record commit/run/artifact bytes/digest. Reported Linux results (151 cases/19 native skips; production 196 tests/21 skips) do not establish native GREEN.
- ⚠️ The minimum fifteen scenario mapping, architecture/legacy map, user Bot A/B/C instructions and final whole-branch review are outside this integration package and assigned to the parent. Check those before final delivery; this local gate does not waive `task-3-brief.md:8` or its final delivery requirement.
- ⚠️ Build178 availability and unchanged remote stable/original Projects state require the parent's publication checks. The proposed local identity and pending recheck are explicit at `docs/botbridge1/stage-integration.md:54`.

## Strengths and verified implementation checks

- `scripts/materialize_jg131_botbridge1.py:23`: validates the fixed Telegram pin, patch digest, safe owner paths and exact `git apply --numstat` owner set. `patches/jg131-botbridge1.sha256.json:2` retains Telegram `279f89e4d4f63f17227bf877dc3d8990f22ecd58`; its thirteen owner records and two null parents match the package's product patch scope.
- `scripts/materialize_jg131_botbridge1.py:57`: checks all actual owner bytes before mutation, admits only the complete before set or complete after set, uses an application check before writing, and verifies every final owner. Mixed before/after states cannot be treated as idempotent success.
- `scripts/materialize_jg131_botbridge1.py:72`: reversal copies only owned final bytes into a disposable location, reverses the pinned patch, checks every restored parent digest and represents the two newly introduced owners as absent. The existing `source_view` helper preserves that absence. The original source is only read.
- `tests/test_jg131_botbridge1_stage.py:6`: inherits real apply/reapply, corrupt-last-parent, mixed-state, tampered-patch and exact-reversal/new-owner-absence tests, then adds escaping-path and owner-scope rejection. These execute the production materializer rather than a replacement algorithm.
- `scripts/verify_jg131_botbridge1.py:55` and `:84`: portable baseline/proof/Task1 patch artifacts are digest checked before use; all sixteen protected modern whole-file hashes are checked on the exact reversed C view. `tests/test_jg131_botbridge1_diagnostics.py:43` retains deterministic allowed-edit normalization, and `:55` retains byte-exact Network recovery and its frozen hash.
- `scripts/verify_jg131_botbridge1.py:93` and `tests/run_jg131_botbridge1.py:36`: construct the accepted Task1 source from exact C for historical fixtures, provide it as the Task2 before view, run Task2 against the actual final source, and run the C historical runner against restored C. Earlier contracts are not pointed at incompatible final BOT bytes.
- `tests/test_jg131_botbridge1_history.py:122` and `tests/test_jg131_botbridge1_diagnostics.py:109`: five history native tests and eight diagnostic/final-source native tests remain present and invoked. The final controller and final Postbox extractions remain at diagnostics lines 152 and 146. No native tests were skipped or weakened by the portability changes.
- `tests/run_jg131_botbridge1.py:18`: the required native mode fails before suites when Swift/Swift compiler/xcrun are missing. With those tools present the fixture methods compile and execute their extracted production code; their only platform skip is the unavailable compiler path. The runner also parses all final Swift owners and aggregates failing subprocesses into a nonzero result.
- `scripts/verify_jg131_botbridge1.py:23`: the preference-key scan streams regular product files, follows directory links, excludes Git metadata, refuses unreadable inputs and bounds directory cycles through resolved-directory visitation. Hex case and decimal literal forms are covered. This is accurately documented as a literal scan, not semantic evaluation of constant expressions.
- `scripts/verify_jg131_botbridge1.py:63`: required full-source mode checks the upstream HEAD and tracked inventory and then demands every non-gitlink tracked input be present in the supplied tree. A correct external Git HEAD alone cannot bless the local 413-file subset. Its call precedes the collision scan at `tests/run_jg131_botbridge1.py:20`; test coverage includes the missing-tracked-input case and valid directory symlinks at `tests/test_jg131_botbridge1_integration.py:64` and `:96`.
- `scripts/verify_jg131_botbridge1.py:117`: pins final owner bytes and separately checks the bridge getState/getDifference RPC allowlist and forbidden live setters, replay, logging and alternate history APIs. This preserves the accepted product boundaries without reinterpreting unrelated modern authorization code.
- `scripts/verify_jg13_source.py:83`: detects newly introduced BOT owners before historical fallback, verifies final BOT outputs, restores C, and then recursively enters existing historical verification. The partial-BOT regression test at `tests/test_jg131_botbridge1_integration.py:81` covers the new entrypoint behavior.
- `.github/workflows/no-ads-native.yml:99` and `scripts/build_jg13.sh:70`: apply BOT after C and run `--require-native --require-full-source` before preservation checks/app compilation. The existing `.github/workflows/build.yml:36` reusable source-preflight and `:39` required app dependency remain intact. The newly prepared experimental push trigger becomes effective only when the parent publishes this reviewed branch.
- `jerkgram-migration.json:17`, `scripts/build_jg13.sh:86`, `scripts/package_jg13.py:65`, and `.github/workflows/build.yml:205`: build number178, Bazel identity, optional artifact suffix and explicit BOTBRIDGE1 upload filenames agree. No compiler flags or credential handling are changed by this task.
- `patches/jg131-profile-metadata.sha256.json:15`, `patches/jg131-translation-repair.sha256.json:46` and `docs/botbridge1/metadata-identity-adaptation.json:5`: only the two Strings before/after dependencies are adapted to the single177→178 identity-line change, with the translation parent-build metadata and matching chain rows. Feature patch digests remain unchanged; stale historical chain values are retained as evidence instead of silently rewritten away.

## Issues

### Critical

- None found in the reviewed scope.

### Important

- None found in the reviewed scope.

### Minor

- None requiring a change for this gate.

## Review evidence and limits

- Read the brief, context, integration notes, implementer report and bounded sections of the supplied review package. Reviewed new integration code, portability drivers, metadata/workflow changes and portable provenance directly. Nested product patches are accepted Task1/2 inputs; their prior semantic gates and the parent's independent thirteen-owner before/after fidelity check were used rather than repeating their product architecture review.
- Named outside check — **restored views could leak newly added owners or mutate accepted source**: read `scripts/jg131_final_stages.py:57`. Its helper omits `None` replacements, copies replacement bytes and links only unchanged inputs; Task3 applies its Task1 patch to copied owners, not the linked read-only view.
- Named outside check — **inherited tests might not exercise the claimed materializer edges**: read `tests/test_jg131_translation_repair_stage.py:16`. Its five inherited tests use isolated real byte-exact patches and assert application, refusal and restoration results.
- Named outside check — **native/app workflow ordering could bypass a clean pinned source or the required gate**: inspected the previously omitted workflow setup/dependency context, `scripts/prepare_source_official.sh:12`, and `scripts/materialize_jg13.py:21`. Preparation checks out the exact upstream; initial materialization refuses a wrong or dirty parent; the app job requires source-preflight. The full-source checker explicitly covers the main repository's non-gitlink tracked inputs; dependency gitlinks are populated later by the existing build flow and are not claimed as scanned dependency contents.
- Parent supplied additional accepted-input evidence: all twelve Swift fixture files reconstruct byte-for-byte from their accepted review/fix packages (`task3/ACCEPTED-FIXTURE-PROOF.json`), thirteen composite owner before/after digests match accepted inputs, and all403 original modern177 product files are unchanged. These are provenance checks, not native execution evidence.
- No reported test suite was rerun. No build, Git command, publication, product/source edit, index edit or HEAD change was performed. Only this requested review report was written. Actual macOS/full-source/app evidence remains the required next gate, as stated above.

## Assessment

**Task quality: Approved for the delegated local integration scope.**

The new stage is small, strict about byte identity, and composes accepted fixtures through explicit restored source views. Its required workflow gate preserves the distinction between portable source proof, native fixture execution and final app/device evidence; remaining release requirements are explicit pending work for the parent.
