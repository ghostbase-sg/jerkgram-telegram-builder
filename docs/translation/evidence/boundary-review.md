# TASK A native UTF16 boundary fix — scoped review

Scope: the two helper changes from `native-boundary-before` to `source`, the corresponding core and UI native fixture assertions/extraction logic, and `NATIVE-BOUNDARY-FIX.md`. This does not repeat the whole TASK A review. No production edits, subagents or builds were performed.

## Verdict

**Both native findings ADDRESSED by source inspection. No new actionable breakage found in this fix. Native GREEN remains pending.**

The parent reported actual native CI failures at commit `2843fd0`, run `40889023877`: `Range(NSRange, in: String)` accepted an endpoint inside a UTF16 surrogate pair. That disproved the earlier review's assumption that successful Foundation range conversion established this boundary property. The original failing assertions are retained.

- `jerkgramValidTranslatedEntities` now explicitly rejects an endpoint if its preceding NSString code unit is a high surrogate and its following code unit is a low surrogate. Both lower and upper endpoints are checked. The preceding short-circuit guards establish `0 <= lower < upper <= count`, so every interior code-unit read is in bounds; zero/end return before accessing adjacent units. The failed `1..<2` case and newly added `0..<1` / `1..<3` cases are consequently rejected, while the whole emoji `0..<2` and following text `2..<3` remain valid.
- `jerkgramTranslationRecognitionSample` checks the same explicit condition on the immutable sampled NSString. Its guards establish `0 <= lower < clippedEnd <= count` before either endpoint check. Upper clipping remains at the complete 256-Character sample boundary. Replacements contain one ASCII space per removed UTF16 unit, so subsequent overlapping ranges retain their offsets; boundary checks always reference the original sample. An interior lower or upper endpoint skips the mask rather than splitting an emoji.
- Both helpers permit Unicode scalar boundaries within a combining sequence, as required for UTF16 entity ranges. Neither unnecessarily imposes extended-grapheme boundaries or scans the entire text per endpoint. The fix leaves routing, request lifetime, settings, policy and asynchronous behavior untouched.

## Test logic and evidence

The native fixtures still extract and execute the production helpers verbatim. No test-side implementation of the surrogate-boundary algorithm was introduced and no failing expectation was weakened. Expanded assertions distinguish lower/upper invalid endpoints, whole emoji, post-emoji text, combining base/mark boundaries and clipping around the sample's final emoji. Existing overlapping-mask and invalid negative-range cases remain.

Independently reran the two focused suites against the current physical `source`:

- Core: 7 tests, 6 passed, 1 explicit native Swift skip.
- UI: 11 tests, 9 passed, 2 explicit native Swift skips.

Swift is absent on this Linux host. These results confirm source contracts and fixture integration only. The parent-provided earlier CI failures supply native RED; a new macOS run must establish native GREEN, including admission/queue cases that were not reached after the earlier core fixture fatal assertion. No new native parsing, full compilation, backend, quality or device success is claimed here.
