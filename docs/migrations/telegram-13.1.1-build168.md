# Telegram 13.1.1 / Build168

Working repository: existing Projects checkout, branch dev/telegram-13.1.1-168.
Parent: Build167 a34071d. Upstream: release-13.1.1, fb0e62ba8a147f0821da6aa63c09da7d79a10111.
Product version remains 1.2.0 Beta 1; bundle version 13.1.1; build 168.

## Behavior

The existing ListViewImpl backend is now the default for chat history, matching the inspected Swiftgram implementation. Explicit experimental CoreList and the upstream rollback override remain supported; rotation and factory behavior are unchanged. This avoids the default CoreList synchronous row-host path identified in earlier device captures. Device performance improvement is not yet established.

Build167 fixes are retained: fake Stars do not override TON/Gram Earnings, gift sheets use opaque background and 40% dimming. App Icons, Download Boost, sponsored-only suppression, profile capture, deleted-message recovery and existing product layers remain in the canonical materialization chain.

## Upstream port

Rebased all 15 source stages. Resolved 16 initial conflicting owners plus subsequent diagnostic conflicts, retaining new upstream layout insets, accountId initialization, wallet/music header changes, pinned-message skeleton behavior and ServerMessageMerge semantics. Edit retention operates on the upstream merged attributes and returns mergedMessage.withUpdatedAttributes, preserving server flags, local tags, translations, fact checks and unlocked paid media.

TelegramApi now generates API wrappers during builds. Bot-token diagnostic redaction moved from obsolete Api43.swift to TLObjectSupport.swift; wire function implementation remains byte-equivalent to upstream. Existing exact hash locks were regenerated for the new source, retaining the stage chain. Upstream removed updateNavigationExpansionPresentation and renamed topPinnedScrollMessage to topPinnedScrollMessageState; survival declarations follow those verified upstream changes.

Independent review identified removed PeerInfoHeaderNode.navigationTransition property use in two calls. Calls now use upstream direct transition and animateHeader arguments. A regression test was observed failing before this fix and passing afterward; no further important issue was found in the reviewed merges. Review was static, not a compilation claim.

## Validation

Clean canonical materialization, configuration with non-secret syntactic API fixtures, root source verifier, Python compilation and shell syntax checks pass. Backend stage tests demonstrate exact restoration, repeat refusal, tamper refusal and no mutation on parent failure. Native 8-case backend factory/selection fixture is wired before IPA compilation and awaits macOS execution.

Current source test discovery: 108 tests, same four failures and one error before and after migration. Existing failing tests:
- test_jg13_performance_capture.CaptureTests.test_bounded_session_and_shutdown
- test_jg13_performance_capture.CaptureTests.test_internal_capture_actions_and_export_remain_available
- test_jg13_performance_capture.CaptureTests.test_timing_and_native_output_routed_into_capture
- test_jg13_profile_cleanup.ProfileCleanupTests.test_full_hash_gate_rejects_marker_preserving_tamper
- test_jg13_profile_cleanup.ProfileCleanupTests.test_scene_lifecycle

These standalone tests target older intermediate diagnostics/profile ownership; the canonical stage gates and focused current feature checks pass. Two additional migration compatibility tests pass. Full application compilation and iPhone runtime remain pending CI/device evidence.

CI uses the documented xcode-27 runner image and Xcode_27.1.app alias. Reference: https://github.com/actions/runner-images/blob/main/images/macos/xcode-27-arm64-Readme.md

## Device matrix

After IPA: cold open/reopen chats, rapid scroll, unread jump, pagination, sending/replying, pinned messages, media/gallery, switching accounts, relaunch, Stars versus TON/Gram Earnings, profile gifts in light/dark themes, App Icons, Download Boost and No Ads toggles. Compare with Swiftgram on the same account/chat; do not equate source verification or successful compilation with measured smoothness.
