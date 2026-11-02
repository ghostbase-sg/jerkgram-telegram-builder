# Botbridge CI fix2 report

## Scoped change

- `docs/migrations/telegram-13.1.2-stage-chain.json`: updated only the `jg131-botbridge1` `regenerated_patch_sha256` and `JerkgramBotBridgeDiagnostics.swift` owner `after` value. The stage's `original_patch_sha256` remains `8c0e5554f636fbf40807c3da4f03e3869171176969a8eead7d7b69f2ef53f021`.
- `tests/test_jg1312_migration.py`: added `test_botbridge_chain_owners_match_terminal_manifest`, comparing all BOT terminal stage owner before/after values to `patches/jg131-botbridge1.sha256.json`.
- The patch and manifest were not edited. Actual patch SHA-256 and manifest `patch_sha256` both equal `caf968f6071b440ba757977e8eec78f5cef617521c683240230147a36032a5d8`.

## Red / green evidence

Focused test before metadata fix:

`python3 -m unittest tests.test_jg1312_migration.Migration1312.test_botbridge_chain_owners_match_terminal_manifest`

Result: failed as expected on `submodules/TelegramCore/Sources/State/JerkgramBotBridgeDiagnostics.swift`: chain had `2acd698c5056f8576a410cf0204dad14186279d52a5df2918860706c0d6f1da3`; authoritative manifest has `5a8df32804333ebf18d9dacfb3dd4c63a9af5eb720f40f7d0026a0ee7b53077b`.

Migration tests after the two metadata updates:

`python3 -m unittest discover -s tests -p 'test_jg1312*.py'`

Result: 10 tests passed.

`git diff --check` passed.

## Native CI context

Previously observed on actual macOS run `41510332117`, native job `125500238048`: all 14 history and 24 diagnostics tests passed, including 15 native tests, and the full 33,732 source key scan passed. The later migration test failed on the stale hash-chain value described above. No native build or workflow rerun was performed for this metadata/test-only fix; revised CI status is pending.
