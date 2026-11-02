# APP-FIX2 round 1 independent review

Verdict: prior P2 ADDRESSED in the gate implementation. No new actionable finding in the scoped correction. Native execution remains PENDING macOS CI.

The updated command includes `-warnings-as-errors` for both variants. It first requires the actual extracted fixed admission to typecheck. It then checks that the explicit outer capture occurs exactly once, removes only that capture, and requires the same fixture and compiler command to fail with self, weak/strong ownership, and explicit-capture guidance in the diagnostics. This supplies the missing native sensitivity check without substituting a modeled admission or fabricated Signal attribute.

The correction changes only the test and its report. It introduces no production capture, ownership, manifest, stage-chain, or downstream patch mutation. The diagnostic checks allow wording variation while requiring the relevant failure category.

Reviewed APP-FIX2-ROUND1.patch and updated APP-FIX2.md. Parent-reported portable results are 9 tests with 2 native skips, with Python compilation and diff checks passing. No tests or builds were rerun during this scoped rereview. The correction implements the required native RED/GREEN gate; its results have not yet been observed on this Linux host and are not claimed GREEN.
