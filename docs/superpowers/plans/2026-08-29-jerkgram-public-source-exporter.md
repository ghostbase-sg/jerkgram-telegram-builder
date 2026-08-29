# Jerkgram Public Source Exporter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone deterministic, fail-closed public-source exporter/verifier for final materialized Jerkgram release trees.

**Architecture:** Copy the materialized tree by default, reject secrets before exclusions, apply only explicit generated-state exclusions, preserve safe symlinks and modes, generate sorted manifests, verify retained files byte-for-byte, and package the public tree as deterministic `tar.xz`. Keep this tooling standalone until Build124's exact final materialization boundary is frozen.

**Tech Stack:** Python 3 standard library (`argparse`, `hashlib`, `json`, `os`, `pathlib`, `shutil`, `stat`, `tarfile`, `tempfile`, `unittest`).

**Spec:** `docs/superpowers/specs/2026-08-29-jerkgram-public-source-exporter-design.md`

## Global Constraints

- Upstream is Telegram iOS `release-12.9.2` at `6ad963e5b62d354da79040f388ae2b9132fb17b8`.
- Do not modify Swift/ObjC/C/C++/Bazel production source during export.
- Scan the complete materialized tree for secrets before applying exclusions.
- No auto-redaction.
- Copy-all-by-default; exclusions are explicit generated/VCS state only.
- Public metadata must not expose builder commit, internal server paths, signing identity, or patch-chain history.
- Do not wire the exporter into `.github/workflows/build.yml` in v1.

---

### Task 1: Public-source policy and manifest primitives

**Files:**
- Create: `scripts/jerkgram_public_source.py`
- Create: `scripts/jerkgram_public_source_policy.json`
- Test: `tests/test_jerkgram_public_source_exporter.py`

**Interfaces:**
- Produces `load_policy(path)`, `scan_materialized_tree(root, env)`, `build_manifest(root)`, `classify_exclusion(relpath, policy)`, `safe_symlink_target(root, path)`.

- [x] **Step 1: Write failing tests** for deterministic manifest ordering, file hash/mode capture, safe symlink preservation, absolute/escaping symlink rejection, and explicit exclusion classification.
- [x] **Step 2: Run** `python3 -m unittest tests.test_jerkgram_public_source_exporter -v` and verify failures are caused by missing implementation.
- [x] **Step 3: Implement minimal manifest/policy primitives** in `scripts/jerkgram_public_source.py` and initial JSON policy with `.git`, root `bazel-*`, `ghostbase-final`, and `build-input/configuration-repository` classifications.
- [x] **Step 4: Re-run tests** and verify all Task 1 cases pass.
- [x] **Step 5: Commit** implementation to the isolated exporter branch.

### Task 2: Fail-closed secret scanning

**Files:**
- Modify: `scripts/jerkgram_public_source.py`
- Test: `tests/test_jerkgram_public_source_exporter.py`

**Interfaces:**
- `scan_materialized_tree(root: Path, env: Mapping[str, str]) -> list[Finding]`
- `Finding` contains relative path + reason only; never prints secret values.

- [x] **Step 1: Add failing tests** for PEM private keys, `.p12`, `.pfx`, `.mobileprovision`, `.key`, GitHub token prefixes, and exact secret values passed in supported environment names.
- [x] **Step 2: Run the focused tests** and confirm RED.
- [x] **Step 3: Implement scanner** that walks all files including paths later excluded and reports only redacted finding metadata.
- [x] **Step 4: Add test** proving a secret under `build-input/configuration-repository` still fails export.
- [x] **Step 5: Run all exporter tests** and confirm GREEN.
- [x] **Step 6: Commit** implementation to the isolated exporter branch.

### Task 3: Byte-identical public tree export

**Files:**
- Create: `scripts/jerkgram_export_public_source.py`
- Modify: `scripts/jerkgram_public_source.py`
- Test: `tests/test_jerkgram_public_source_exporter.py`

**Interfaces:**
- `export_public_tree(materialized_root, public_root, policy) -> ExportResult`
- CLI arguments exactly as specified in the design doc.

- [x] **Step 1: Add failing fixture test** with retained source files, excluded generated state, executable mode, and safe relative symlink.
- [x] **Step 2: Verify RED.**
- [x] **Step 3: Implement copy-all-by-default exporter** with explicit exclusions only, preserving mode and safe symlink target.
- [x] **Step 4: Add mutation/deletion tests** proving retained source bytes are unchanged and unknown internal-looking names are not silently excluded.
- [x] **Step 5: Run tests** and verify GREEN.
- [x] **Step 6: Commit** implementation to the isolated exporter branch.

### Task 4: Manifests and standalone verifier

**Files:**
- Create: `scripts/verify_jerkgram_public_source.py`
- Modify: `scripts/jerkgram_public_source.py`
- Test: `tests/test_jerkgram_public_source_exporter.py`

**Interfaces:**
- `verify_export(materialized_root, public_root, policy) -> VerificationResult`
- JSON outputs: `internal-materialized-manifest.json`, `public-source-manifest.json`, `excluded-paths.json`.

- [x] **Step 1: Add failing tests** showing verifier detects missing retained file, added unexpected file, changed bytes, changed mode, and changed symlink target.
- [x] **Step 2: Verify RED.**
- [x] **Step 3: Implement verifier** using path-set equation `internal - exclusions == public` and retained-entry equality.
- [x] **Step 4: Implement sorted JSON manifest writers** with stable formatting.
- [x] **Step 5: Run tests** and confirm GREEN.
- [x] **Step 6: Commit** implementation to the isolated exporter branch.

### Task 5: Deterministic archive and release provenance

**Files:**
- Modify: `scripts/jerkgram_public_source.py`
- Modify: `scripts/jerkgram_export_public_source.py`
- Test: `tests/test_jerkgram_public_source_exporter.py`

**Interfaces:**
- `create_deterministic_tar_xz(public_root, archive_path, arc_prefix) -> sha256_hex`
- `write_release_metadata(...) -> JERKGRAM_RELEASE.json`

- [x] **Step 1: Add failing test** exporting the same fixture twice into separate archives and asserting identical archive SHA-256 and bytes.
- [x] **Step 2: Verify RED.**
- [x] **Step 3: Implement sorted tar creation** with uid/gid `0`, empty user/group names, mtime `0`, preserved mode, and safe symlinks.
- [x] **Step 4: Add failing metadata test** for Jerkgram version/build, public source tag, exact Telegram upstream, source archive hash, public manifest hash, and optional IPA SHA-256.
- [x] **Step 5: Implement release metadata and `.sha256` output.**
- [x] **Step 6: Run all exporter tests** and confirm GREEN.
- [x] **Step 7: Commit** implementation to the isolated exporter branch.

### Task 6: Final standalone verification and current-tree dry run gate

**Files:**
- Modify only if failures reveal defects in exporter/verifier/tests.

**Interfaces:**
- No CI workflow changes.

- [x] **Step 1: Run** `python3 -m py_compile scripts/jerkgram_public_source.py scripts/jerkgram_export_public_source.py scripts/verify_jerkgram_public_source.py`.
- [x] **Step 2: Run** `python3 -m unittest tests.test_jerkgram_public_source_exporter -v` — verified 23 tests, 0 failures on a byte-identical copy of the GitHub branch files.
- [x] **Step 3: Perform fixture CLI export twice** and compare archive hashes — both produced `e0397059af21e4e6eac38dfcb003ae06719c1fd34f57d7a1b14ebbab7fff2bc`; both standalone verifier runs returned OK.
- [ ] **Step 4: If a real `work/swiftgram-src` tree is available locally, run scanner/export in audit mode only; do not publish its output as Stable source.** Not executed because no real final Stable materialized tree is available in the current environment. This remains a Stable-candidate gate, not a standalone-v1 blocker.
- [x] **Step 5: Review branch diff** and verify `.github/workflows/build.yml` is untouched — blob SHA remains `963087d0cb1f8f13f849bec92ae41e36a37e703d`.
- [x] **Step 6: Record final integration blocker** in the design: current Build124 private Telegram API credential injection must be moved outside the materialized tree or the exact pre-injection immutable source boundary must be proven before release integration.

## Verification status

Standalone exporter v1 is complete and verified against fixtures. It is intentionally **not** integrated into Build124 CI and has intentionally **not** produced a public Stable source archive, because neither a final Stable IPA nor the corresponding final materialized source tree exists yet.

The remaining unchecked real-tree audit is mandatory before the first Stable public-source release.

## Self-review

- Spec coverage: copy policy, secrets, symlinks, manifests, deterministic archive, provenance, and no-CI v1 boundary are covered.
- Placeholder scan: no implementation behavior depends on `TBD`/`TODO` placeholders.
- Type consistency: exporter and verifier share policy/manifest primitives from `scripts/jerkgram_public_source.py`.
