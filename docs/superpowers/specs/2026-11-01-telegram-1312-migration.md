# Official Telegram13.1.2 source migration

User requested continuation and noted new release. Confirmed official master
279f89e4d4f63f17227bf877dc3d8990f22ecd58, versions.json app13.1.2,
Xcode27.1/Bazel9.2.0 unchanged; old pin fb0e62 (13.1.1), four commits/41files.
Current candidate C17ff4f1 passed macOS41318834444, C9/B13/A24 tests; actual
latest successful IPA is still Build176 (recheck before next build).

## Design and constraints

Use a genuine clean target checkout in production, exact HEAD and app version
assertions. Rebase the feature stages sequentially; do not relabel an old base,
copy old whole feature owners onto new upstream, undo upstream fixes to satisfy
old hashes, add compatibility defaults that hide omitted arguments, or bypass
verification. No compiler flag/toolchain changes. Full app build only after
source/native gate; source preparation/replay is permitted.

Source of truth: upstream-13.1.2/compare.json and MIGRATION-AUDIT.md under
jerkgram-next. Seven existing feature owners overlap target; fourteen content
hash manifests cascade. Old historical stable patch can remain immutable;
regenerate its reviewed port delta/effective patch and truthful target parents.
Other active patch/manifests may be regenerated as reviewed migration deltas;
record original digests and changed hunks. Never bless arbitrary current bytes
after a failed gate. Preserve old17ff replay/evidence without modification.

Preserve all upstream changes, especially create-bot viaDeeplink protocol and
conformer/call propagation; Account/StateManager/UpdateMessageService
ignoresShortSentMessages; bot storage postbox signatures and completion;
video rotation tuple/seek/rearm/timing fixes around retained JG diagnostics.
Preserve target tlottie92df98dc209bc39b1e567ec74a8c86a0af5239de; existing
explicit rlottie override is a separate dependency. All other target files
including new upstream tests must come from target checkout unchanged except
reviewed feature scopes. No mechanical Swiftgram import/global Premium/hooks.
Retain all JG features, A translation, B local folder and C glass semantics.

Root materialization prepares/configures multiple stages, not only final
patches. Update actual prepare/config source pin/version, stable-port and all
active upstream-tagged contracts/materializer constants. Preserve historical
docs and earlier test evidence. Keep Jerkgram1.2.0Beta1 product identity; defer
actual next build number until the real successful artifact check.

Local direct Git transport is unavailable (DNS); GitHub connector raw/API
reads work. A selected source projection is acceptable for bounded local
replay only if each clean parent is traced to exact official blob evidence.
Do not claim it is a complete deployable checkout or fabricate its Git HEAD.
Production native gate must fetch actual full target with exact HEAD before
materialization. Missing clean files must be fetched, not recovered by copying
patched final owners. Do not mutate existing immutable replay directories.

source_snapshot_sha256 is unused by current scripts/tests. Establish whether
it denotes the historical baseline export before changing it; do not assign
a guessed current-upstream archive digest. Preserve historical provenance or
compute a real archive only if a newly claimed artifact is actually produced.

## Proof

For every stage: exact new parent/output hashes and patch scope; dry-run,
all-parent-before-write rejection, idempotence, reverse restoration. Two fresh
target replays must produce equal final owners. Compare old→new final against
upstream diff plus explicit merge resolutions. Record media overlap decisions
and changed protocol clusters. New focused tests assert retained upstream
rotation/seek semantics, bot-storage completion and complete factory/state
signature forwarding, beyond updated golden hashes. Run bounded migration,
media/history/profile/stage and A/B/C tests; historical full-suite failures
are not new defects and must not trigger unrelated rewrites.

Require independent source/merge review and real macOS source/native gate.
Whole app/extensions build later confirms full type/link compatibility.
Siri/bot-storage upstream test execution, media behavior and device matrix
must be reported honestly if harness unavailable. Source parse is not app
typecheck, and compile is not runtime success. Keep BOTBRIDGE1 for later
isolated branch from latest actual GREEN modern base.
