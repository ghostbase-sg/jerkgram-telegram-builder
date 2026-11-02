# BOTBRIDGE1 source integration (local review candidate)

The authoritative product change is `patches/jg131-botbridge1.patch`, applied
strictly after TASK C against official Telegram `279f89e4d4f63f17227bf877dc3d8990f22ecd58`.
It combines the accepted Task1 history and Task2 diagnostic sources in 13 owners;
it adds exactly two owners. Patch SHA256 is
`caf968f6071b440ba757977e8eec78f5cef617521c683240230147a36032a5d8`.
The Task1/2 drafts and modern Build177 source remain immutable.

The materializer checks the patch digest, upstream pin, exact owner scope and
all before hashes before any write. Exact after hashes make repeat application
a no-op. Its disposable reversed view restores C, including absence of both new
BOT owners. Earlier C/B/A/wave1/175 contracts run on their exact restored views.
No product owner outside the accepted combined diff is regenerated.

## Portable provenance and native fixtures

`tests/fixtures/botbridge1/provenance` contains the exact protected 16-owner
baseline, modern poll case, ordered allowed-edit proof, and accepted Task1 patch
with owner hashes. Their digests are pinned in the terminal manifest. The runner
reconstructs the accepted Task1 source from C in a disposable view so the original
policy/storage/lease/controller fixtures retain their original production input.
Task2 fixtures use the actual final controller, response mapper, diagnostics,
request boundary and Postbox. Its before input is the accepted Task1 view.
No machine-specific path, credential configuration, copied Git directory, or
555-record local snapshot is required by these portable fixtures.

The 555 original Task1 baseline records mean 403 genuine product files plus 10
verified official inputs and 142 copied Git metadata records. The independent
original provenance check remains separate from portable source gates. It does
not promise that generated credentials or release identity hash identically in
all configured builds. The terminal verifier checks all 16 whole modern owners
on exact C; final outputs are pinned in full, while the Task2 proof reverses only
the explicitly accepted observer/context edits. The modern poll case is retained
verbatim. Bridge RPCs are restricted to getState/getDifference; forbidden live
setters, generic replay and logging are checked separately.

`verify_preference_key_available` scans every regular product file in the supplied
C tree, follows restored-view directory links, excludes `.git`, and visits each
physical directory once to bound aliases/cycles. It streams file contents and reports the
visited-file count. It checks case-insensitive hex `0x4A470002` and decimal
`1246167042` literal spellings. The local proof subset contains 413 files; this is
not evidence that the full official source has no collision. The required CI
runner uses `--require-full-source`: it verifies the official Git pin, a full
tracked-file inventory and presence of every tracked non-gitlink input before
scanning the actual generated product tree.

The workflow and app entrypoint require `--require-native --require-full-source`.
Missing Swift/xcrun fails this required gate. Linux native skips cannot satisfy it.
Swift parsing and extracted native fixtures remain distinct from a whole app
compile and device/server behavior.

## Build178 identity dependency

The proposed experimental artifact is
`Jerkgram-1.2.0-Build178-BOTBRIDGE1.ipa` with its matching JSON report. Configuration,
Bazel build number, artifact naming and workflow identity agree. Recheck the next
build number immediately before publication.

`configure_jg13.py` writes release identity before the final stages. Therefore
profile-metadata and translation-repair each hash the whole JerkgramStrings owner
with the selected build number. Only that owner's before/after hashes in those
two manifests and stage-chain rows are adapted. Both feature patches stay exact.
The existing stage-chain Strings rows were older than the reviewed Build177
terminal manifests; their previous values and historical old-before/old-after
fields are preserved explicitly. Exact Build177 bytes were verified first;
Build178 derives from replacing the single `public static let build = "177"`
line with `178`. The derived hashes are in `metadata-identity-adaptation.json`.
No protected modern source owner depends on that metadata line.

## Publication and remaining evidence

These are local changes on `dev/botbridge1-legacy-history-modern-write`. The local
workflow prepares this branch's push trigger, with the required source/native
job as the app job dependency; no remote trigger is enabled by local edits.
Parent review and publication own the next steps. No commit, push, CI dispatch,
heavy app build, IPA artifact, native GREEN, device result or server-history
availability is claimed here. Existing modern stable branch remains unchanged.

## Final whole-branch fix wave

The initial Task3 patch `8c0e5554f636fbf40807c3da4f03e3869171176969a8eead7d7b69f2ef53f021` is historical evidence. The current hash above includes only the reviewed diagnostic retention/admission-loss amendments. All thirteen parent hashes, other twelve patch sections and twelve original Swift fixture files remain unchanged. Two new actual-production native fixture files cover fresh-mtime/old-record physical expiry and distinct registry admission losses. Scoped local evidence:54 cases,15 native skips; exact415-file application/no-op reapply/corrupt-parent refusal and413-file reversal pass. [Fix report](whole-branch-fix.md). Native execution and app evidence remain pending.
