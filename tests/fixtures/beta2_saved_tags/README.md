# Saved Tags storage fixture

This fixture compiles the actual `LocalSavedTagsTable.swift`, the exact marked
Transaction API from the patched `Postbox.swift`, and its exact existing
`PostboxImpl.setPreferencesEntry` sink. It does not copy or reimplement the
store algorithms. Complete pinned Table, ValueBox protocol, ValueBoxKey and
PreferencesTable execute unchanged. PeerId, MessageId and MediaResourceId are
extracted as complete declarations from exact pinned files to avoid unrelated
application dependencies. Complete Postbox Coding/PreferencesEntry/adapters,
logging and Objective-C MurMurHash32 come from the existing immutable
`beta2_bot_codec` fixture. Both provenance manifests are checked with SHA-256
and Git blob SHA-1 before compilation, including in portable checks.

The complete pinned `submodules/Postbox/BUILD` is declaration evidence only;
it is not compiled and does not turn a partial source proof into a full checkout.
The allocation/source-glob check reads the selected source's BUILD when present,
otherwise it verifies and reads this checked-in pinned declaration. It honors
`JG_SAVED_TAGS_BEFORE` for the exact Hub parent supplied by the composed runner.
Preference-key enumeration is limited to that parent's Postbox/Sources and follows
unchanged directory symlinks in reverse views. A clean-layout child regression
uses actual final source inputs and an actual reversed parent, without sibling
research or SDD inputs; it also checks collision, sink, glob and fixture refusals.

`SQLiteValueBox.swift` is a boundary adapter implementing the actual pinned
ValueBox protocol with SQLite BLOB keys, exclusive range bounds and real SQL
transactions. Unsupported protocol operations trap. Its SQL uses the same
key comparisons and directions as pinned SqliteValueBox. It uses plain system
SQLite/WAL, not production SQLCipher, statement caches, encryption, account
queues, recovery handling or cross-process view delivery. Fixture operations
prove use of the real PreferencesTable operation sink; they cannot prove the
full ViewTracker/signal lifecycle or app behavior.

Portable command from the builder:

```
python3 -m unittest discover -s tests -p test_jg131_beta2_saved_tags_store.py -v
```

Mandatory macOS command against the final materialized source:

```
JG_SAVED_TAGS_REQUIRE_NATIVE=1 JG_SAVED_TAGS_SOURCE=/absolute/final/source python3 tests/test_jg131_beta2_saved_tags_store.py
```

`--require-native` is an equivalent direct-script switch. Missing swiftc/xcrun
is a failure in required mode. Native compilation/execution runs both `-Onone`
and `-O` in Swift language mode5. A second process then opens the committed
transaction database and verifies catalogue, full Saved identity and matching
table/preference revisions. No dictionary or JSON persistence substitutes for
Swift/SQLite execution. Linux assembly checks are not a native pass.

Native cases cover name normalization/bounds, CRUD, multi-tag/idempotence,
copy identity, account path isolation, invalid self/namespace/pending IDs,
atomic batch and all four quotas, removal at quota, inclusive ID/time/thread
ranges, full clear, direct uncached numeric deletion, confirmed metadata moves,
real keyed revision codec and malformed binary/schema records, preflight
corruption rejection, a wrong secondary-key regression, exhausted-revision preflight and creation-order rollover. Missing content
cannot purge relations here because the table has no content/cache loader;
provider/retry behavior belongs to Task3.

Pages traverse1001 associations in both directions with <=45 returned rows and
<=47 fetched reverse-index rows per page. A real100000-edge seed tests oldest
page reachability, SQL query plan and explicit deletion without data eviction.
Native `MEASURE` lines report elapsed time, SQL operation/row counts and maximum
range request size. The heavy delete stays in one transaction on the Postbox
queue and performs O(affected edges) work; its memory bound does not establish
acceptable UI latency. No measurement exists until this native command runs.
