# BOTBRIDGE1 acceptance evidence map

Source gates Task1/Task2 are approved after scoped fixes. Local terminal/restored-view gates pass; **all15native checks and actual app integration remain pending macOS**. Prepared declarative cases are not passed behavioral tests. The tests below extract actual production policy/controllers/adapters with strict unavoidable boundary facades; they are not real DB, transport, UIKit or device integration.

`H` = `tests/test_jg131_botbridge1_history.py`; `D` = `tests/test_jg131_botbridge1_diagnostics.py`. Task3 runs H on the exact reconstructed accepted history view and D on final materialized source. Unchanged bodies are protected independently; actual final controller/Postbox fixtures are also in D. No whole-worker execution is claimed by the sender source proof.

| User scenario | Source / actual fixture | Evidence and remaining device check |
|---|---|---|
|1 Confirmed bot only|AccountStateManager admission after validated auth/user/generation; H actual controller, D scope-before-requests|Portable wiring guards pass; native bot/user branch pending; login with real bot pending|
|2 Ordinary user unaffected|D observer fast path + actual worker context factory|No recorder/context UUID/event/wrapper in unregistered path; native lifetime/disposal pending; user switching pending|
|3 Historical import|Current StoreMessage converter, historical Postbox entry; H real storage helper/D final controller|Reviewed absent-only conversion/insertion; native helper pending; real server availability pending|
|4 No duplicates|H policy/storage/controller repeat and dedup cases|Existing cloud IDs skipped, progressing dedup slice continues; native pending; compare known history samples|
|5 Archive/pins intact|Existing inclusion function byte equality; H storage inclusion sentinels|Source proof plus pending native boundary checks; real archive/pin/cutoff comparison pending|
|6 Modern live messages retained|Absent-ID/peer checks, no generic historical mutations; H/D controller/storage|Edited/live/deleted-placeholder samples protected in fixture; actual DB/device samples pending|
|7 Live updates continue|Exact native pollDifference/custom body; actual-controller interleaving/watchdog fixture|Source body equality passes; native queue interleaving pending; real incoming updates pending|
|8 Modern text send|D exact whole-file worker/Network projection and actual request boundary|Modern algorithm recovered byte-for-byte after additive observers/contexts; native boundary pending; intended user send pending|
|9 Modern replies|Explicit original reply intent, resolved broadcast type; D actual context/request fixture|Reply versus forum and broadcast versus megagroup asserted in native fixture; whole sender/device interaction pending|
|10 Modern reactions|Protected unchanged reaction worker; central exact method category|Source owner unchanged, request fixture pending; intended real reaction pending|
|11 Modern media send|Modern upload/send algorithms retained; additive media/album/standalone context|Source proof plus pending request fixture; actual media/album send pending; upload failures before terminal RPC unobserved|
|12 No legacy mutations|Bridge getState/getDifference allowlist, no live setters/generic replay, narrow callback bypass|Source guards pass; actual Postbox mixed-call fixture pending; no claim all external observers are proven passive|
|13 Modern handoff|Actual controller once-finish/late-cancel guards; D actual serialized history adapter|Source reviews closed queue/lifecycle defects; native timeout/handoff/export assertions pending; real error flow pending|
|14 Persistence/restart|Atomic insertion+progress, persisted reservation/cursor/deadline; actual controller crash/resume|Unit boundary cases present, native pending; real Postbox/index/restart proof remains device work|
|15 Account isolation|Per-Postbox generation; weak manager/record/generation/epoch targets; D lifecycle fixture|Source review closes stale cleanup targeting; native namespace/replacement tests pending; A/B/C/user interleaving pending|

## Additional acceptance boundaries

- R1reservation hang, nested delete vectors, otherUpdates/messages/peers, original deadline/clock change,32attempt cap, timeout/cancel/late callbacks: actual production-controller/storage/policy/lease fixtures.
- Cold unsubscribed/resubscribed requests and logout, result/dispose race, original policy/error/dependency semantics, lazy parameter-loader sentinel and ordinary-user fast path: actual Network/registry fixtures.
- Ring/context/pending overflow, lifecycle reserve, physical per-record TTL despite fresh mtime, distinct capacity/duplicate/invalid-generation admission losses, rotation, single export/cleanup and throwing directory enumeration: actual recorder/sink/filesystem fixtures.
- Actual history adapter exact exported start/end/restored fields, finite reasons, four numeric tuples/counters and forbidden private/progress/parameter keys: serialized export fixture.
- Exact13-owner application, repeat no-op, corrupt-parent refusal before mutation, reverse C view/new-owner absence, provenance tamper, partial-owner refusal and symlink-cycle-bounded key scan: terminal stage/integration tests. Local413-file proof is not a full source checkout; CI must enforce full inventory and literal-key scan.

See [audit matrix](audit-matrix.md), [cost map](cost-map.md) and [BotA/B/C experiment](runtime-experiment.md). No FPS/thermal/Settings latency,14-hour survival, all-time history, server causality or Swiftgram parity is inferred from source/native/build evidence.
