# Jerkgram Build116 Specification

## Evidence baseline

- GitHub Build115 artifact `Jerkgram-build115.ipa` compiled successfully at `e990b3b8072166f04d25da57a31817ca7b7e0dda`.
- Device runtime failed for Broadcast, Share content, Widget data, and textual numeric mentions.
- `tg://openmessage?user_id=8405914445` passed on device.
- The post-ESign IPA has seven bundles. Every embedded profile and code-signature entitlement carrier exposes the same five App Groups; the Build115 selection model resolves all seven to `group.4a348a9b186b700c.1`.
- Build115 globally removed four profile history panes although the requested release cleanup concerned raw Runtime/logging content in Jerkgram Settings.
- The send-style page still owns hardcoded Russian labels independently from the Build115 Settings localizer.

## Build116 deliverables

1. Restore `.ghostBaseProfileHistory`, `.ghostBasePresence`, `.ghostBaseGiftHistory`, and conditional `.ghostBasePersonalChannel` panes for user profiles. Remove the raw Runtime/event buffer presentation from Jerkgram Settings without deleting persisted research/history data.
2. Normalize `@N` and `@idN` in the actual chat owner, `ChatController.openPeerMention`, to Official Telegram's `https://t.me/@idN` resolver. Keep ordinary usernames on `resolvePeerByName`. Do not fabricate access hashes. Bare decimal text must not silently replace Telegram phone-number semantics; it is accepted only through explicit URL/deep-link input.
3. Localize the send-style title, current-style label, preview prefix/body, and seven style names via `JerkgramStrings`, following Telegram's selected language.
4. Add a native About community row for `https://t.me/JerkgramApp`, localized as a Jerkgram community/channel credit, while retaining concise base/version information and removing the raw Bundle ID from visible About copy.
5. Add bounded per-process extension stage diagnostics. Record one atomic JSON file per process in the selected shared container after successful container resolution. Stages cover profile parsing/group selection, `containerURL`, shared root, encryption/account opening, and Broadcast coordination selection. No raw log list is shown in Settings; one localized `Copy Extension Diagnostics` action copies the bounded report for device testing.
6. Add typed `JerkgramSettingsV1` and `JerkgramArchiveV1` foundations. Archive content is versioned and semantic; it excludes auth keys, tokens, keychain data, sessions, and signing material. Build116 provides encoding/validation/merge primitives. User-facing import/export flow remains the Build117 deliverable.
7. Publish the next artifact as `Jerkgram-build116.ipa` under workflow `Jerkgram 12.9.2 Build116`.

## Global constraints

- Official Telegram iOS 12.9.2 remains the API and geometry source of truth.
- Patchers are bounded, assert exact anchors/counts, and fail before Bazel on ambiguity.
- Each production overlay has a verifier and a failing unit fixture written first.
- Build green is not runtime success; device runtime closes runtime defects.
- Existing deleted-message, recovery, profile, transcription, protected-content, Gifts, and performance regression locks remain intact.
