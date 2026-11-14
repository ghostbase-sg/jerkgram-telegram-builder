# Profile observer storage verification

Run from the repository root with a materialized Telegram 13.2 source tree.
The source is read only; all compiled files and fixture databases are temporary.

Native production Swift store tests (requires Swift and a C compiler):

```sh
python3 tests/profile_observer_storage_native/run.py --source-root /absolute/path/to/materialized-source
```

This compiles `JerkgramProfileHistoryStore.swift` itself with the real SQLCipher
amalgamation. It checks field enrichment/change semantics, atomic migration
rollback/retry, exact legacy source preservation, targeted migration without a
full settings-domain read, changing legacy revisions, pagination, more than 1100
changes, Presence separation, wrong keys, reopening, account isolation, and
restored watch opt-ins. The macOS CI workflow requires this suite. It was not
executed in the Linux development environment because Swift was unavailable.
File protection attributes are applied only on iOS; macOS tests cannot establish
device protection behavior.

Independent Linux encryption/schema probe (C compiler and OpenSSL headers):

```sh
python3 tests/profile_observer_storage_cipher_probe.py --source-root /absolute/path/to/materialized-source
```

The reproducible probe compiles the actual SQLCipher source, executes the store's
production schema statements, then checks a fully encrypted database header and
WAL, isolation from Postbox's global plaintext-header default, wrong-key
rejection, and reopening with the original key. All values are dummy fixtures.
This probe supplements the native suite and does not compile Swift or establish
iOS client compatibility.

The Linux probe passed on 2026-11-14 with the Telegram 13.2 materialization's
`submodules/sqlcipher/Sources/sqlite3.c` SHA-256:

```
8640c653acadf665cce6331646f60b5b74a4690746f2c4a2d8f688a0570a0c0c
```

Its final output was:

```
Real SQLCipher probe passed: encrypted header/WAL, global-default isolation, wrong-key rejection, reopen preservation
```

SQLCipher prints expected decryption errors during the wrong-key assertion.
