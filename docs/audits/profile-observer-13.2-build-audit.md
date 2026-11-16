# Actual Telegram 13.2 product build integration audit

The user's explicit correction supersedes the earlier 12.9.2 attachment. The experimental observer must extend the current 13.2 product. The old observer materializer/workflow work is suspended and has not been dispatched.

## Verified product and source

- Stable builder (read only): `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/jerkgram-telegram-builder`.
- Branch: `perf/build182-wave2b1-ui-jank`.
- Local HEAD: `243e367a3d5fa7cf353e11bb58db677525df31cf`.
- Local HEAD tree: `c7b85c10a49144dc0baf7f82cc183fdb849acdf6`.
- Build183 CI report: `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/release-1.2.0/build183-ci-report.json`; records published CI commit `636decefd426586118c0a06de03d2d3c2cc24cde`, run `43516752691`, status `COMPILED, NOT RUNTIME TESTED`. The published commit itself is not available in the local builder object database, so tree equivalence needs an independent recorded/API comparison before claiming it.
- Genuine official source Git checkout: `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/release-1.2.0/source`, HEAD `24638bc69bd083981b178dd1e7f921eebbf7fc46`. This is a dirty materialized product; preserve it. Read official API files via `git show HEAD:path` and current product files via ordinary reads.
- A nongit official source export also exists at `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/jerkgram-next/upstream-13.2/official-target`.
- Pinned official `versions.json`: app **13.2**, Xcode **27.1**, Bazel **9.2.0**, macOS **27**. The current workflow uses custom runner label **xcode-27**, not macos-26.

## Real active route

The stable `.github/workflows/build.yml` invokes:

1. `scripts/prepare_source_official.sh`: new exact Git checkout of `24638bc69bd083981b178dd1e7f921eebbf7fc46`, verifies app/toolchain and new tlottie tree. This script removes `work/swiftgram-src`, so only invoke in an isolated experimental builder.
2. `scripts/build_jg13.sh`: calls `scripts/materialize_jg132_product.py`.
3. The product materializer requires pristine genuine upstream, applies 32 reviewed port boundaries, verifies complete baseline, then applies Beta3, post180, and post181 stages, and configures current build inputs from `jerkgram-migration.json`.
4. `tests/run_jg132_post181.py --require-native --require-full-source` runs the current product gate once.
5. `scripts/pin_jg13_dependencies.py`, recursive submodule initialization, dependency verification, and `scripts/prepare_jg13_build_rules.py` preserve current unsigned app/extension semantics.
6. Full Bazel `//Telegram:Telegram` for arm64, opt, extensions enabled, provisioning disabled, legacy signing disabled, buildNumber183.
7. Existing release script then preserves/packages the IPA. An observer compile-only workflow should stop after successful Bazel and omit the release preservation/package actions.

The old `bazel_build_probe_official.sh` and Build133 installer remain in the repository but are not the active product route. Replaying their old Python chain would reconstruct the wrong product.

## Proposed experimental integration

Create/reuse an isolated experimental checkout based on the verified current product tree, then clone fresh official 13.2 source in that experimental checkout's work directory. Materialize the entire current product with the existing 13.2 product materializer unchanged. Apply the observer as one narrow successor after the final current product stage. Verify source hashes/guarded anchors and run observer native tests plus the existing current product gate. Use the pinned current custom xcode-27 runner, Xcode27.1 and Bazel9.2.0 for the single full app compilation. Do not edit the stable branch/source, change product identity/notifications, run release packaging, or dispatch CI before root review.

The observer patch anchors and import dependencies must be rechecked against both the pinned official 13.2 files and final current product owners. Storage and portable scheduler/admission logic can be retained if their production API integrations are adapted and compiled against this actual baseline.

## Old work retained for reference only

The old uncommitted files `materialize_profile_observer_foundation.py`, `build_profile_observer_foundation.sh`, `test_profile_observer_materialization.py` and the modified observer workflow currently target 12.9.2 and must not be committed/dispatched as the 13.2 solution. Their only real local materialization stopped at historical Build110's macOS-only sips requirement. No native app build has been run in this Linux session.

## Experimental setup and verified local result

Current experimental checkout: `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/profile-time-machine-13.2`, branch `dev/profile-time-machine-13.2`, based on local current product commit243e367. An independent source clone at `/home/pixi/Projects/Jerkgram/iOS/_chatgpt-work/iOS DEV/profile-observer-source-13.2` was created from the genuine released Git object database without hardlinks; its origin is the official public repository. No edits were made to the released checkout. Experimental `work/swiftgram-src` points to this independent clone.

The unchanged current product materializer completed successfully locally: all32 baseline boundaries, Beta3, post180, post181 and post182 final successor chain source checks passed on genuine HEAD24638bc69bd083981b178dd1e7f921eebbf7fc46. This run supplied only a deliberately invalid all-zero compile fixture API hash with the existing approved public API ID; no credential was read from the released checkout and no app was launched or published. The result is source/materialization evidence, not native compilation. Its generated `artifacts/profile-observer-materialization.json` explicitly records native gate and app compilation as `not-run`.

The new dedicated manual workflow uses the current custom xcode-27 runner with Xcode27.1/Bazel9.2.0. `scripts/materialize_profile_observer_foundation.py` first invokes the unchanged current product materializer; when native is required it invokes the existing current product source/native gate before applying the observer successor (existing source ownership hashes describe the parent product). `scripts/build_profile_observer_foundation.sh` then uses unchanged dependency pin/build-rule preparation and full app Bazel flags, and stops after compilation. Neither the stable build workflow nor build script was edited. No CI has been dispatched.

Local checks: materializer contract tests (wrong pin rejection, failed native parent gate blocks observer, unchanged build route and absence of release packaging), Python compilation, shell syntax, and whitespace checks. Actual current toolchain compiler success remains pending the reviewed CI run.
