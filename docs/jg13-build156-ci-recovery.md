# Build156 report-format compatibility recovery

Failed run: https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/38124771557
Job: 114426747208. Head: 0d0f1aafae8b50b10fb612cd363ccb1b2ce40472.

The full job log identifies the first failure at 2026-10-11T08:26:58Z:
`main/main.swift:481: Precondition failed`, from `tests/run_jg13_performance_capture.py`.
The existing native assertion requires the contiguous report prefix
`slowEvents=30 suppressedSlowEvents=2970 limit=96`.
Build156 inserted `nestedSlowEventsSuppressed` before `limit`, breaking that
format contract before application compilation or the expanded native tests.

Recovery restores the existing prefix and appends the new counter after `limit`.
No native assertion, test, cap, collection behavior, playback policy, or signing
configuration is changed. Build number remains 156.

Verification:

- The added structural prefix contract failed against the original Build156
  materialization, then passed against the recovery.
- Fresh bounded materialization passed source hashes, function survival checks,
  and five regression locks; 46 canonical structural contracts passed.
- Python compilation and `git diff --check` passed.
- Full legacy suite: 495 tests, 20 failures and 12 errors. The exact 32 failing
  test names match the original Build156 baseline (494 tests); this suite is
  NOT GREEN. Baseline names are recorded in jg13-build156-suite-results.md.
- Native Swift execution and application compilation remain pending in CI;
  no local Swift toolchain is available. No runtime freeze fix is claimed.
