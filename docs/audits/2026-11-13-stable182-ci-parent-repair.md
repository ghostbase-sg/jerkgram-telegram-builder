# Stable182 CI parent-byte repair

Failed run: https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/43429358656
Commit: ba18c1397850b876bf9330508a223f2cd0cd1d59 (local tree-equivalent66747c0).
Failure: source-preflight, `materialize_jg132_post181.py` before app compilation; `build-probe` SKIPPED.

The latest GRAM successor's native parent fixture files each contained one extra trailing LF introduced while preparing the selected source projection through Add File. Hashes and patch parents were thus consistent locally, but not equal to the genuine pinned Telegram13.2 checkout. Specifically:

| Native owner | Correct SHA256 |
|---|---|
| GiftStoreScreen/BalanceComponent.swift | 8997f49582c8b51e560f5caaf9dc8cc48cdc1325d4b86d147e524a798a7ff631 |
| GiftStoreScreen/GiftStoreScreen.swift | 79de32135c6b7a699ffb06b0b758d6fc6153e2031f54bc0345464e620ef37c97 |
| StarsBalanceOverlayComponent.swift | b7b2f9e2f0a01276c01b27e878c04cbd1b3b8699d7abb9decbd8c45c2ca32ffb |

Re-fetched exact raw files at upstream24638bc69bd083981b178dd1e7f921eebbf7fc46, verified old local bytes == official bytes + one LF for all3. Corrected only this unaccepted successor's parent hashes and regenerated diff from genuine originals. All4 output SHA256 values remain exactly equal to failed candidate outputs: no feature/runtime source change, no rollback of bot/LocalPremium/GRAM/performance.

Added `gram-native-provenance.json` with official SHA256/Git blob IDs/byte lengths; new regression compares successor native parents against independently pinned original bytes, including EOF. RED on previous candidate; GREEN after correction. Combined apply/reapply/reverse/corruption-refusal and focused source/assembly runner PASS locally. Six Swift execution tests still require macOS; they were not reached in failed run. No new IPA/device runtime claim.

Historical accepted patches and manifests remain unchanged. Source-preflight remains mandatory and strict; no hashes relaxed, no check disabled, no toolchain or upstream changes. Replacement combined CI is required to verify native execution and app compilation.
