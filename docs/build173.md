# Build173 — cancel obsolete archive checks during chat navigation

Based on Build172 b33c9a305a844a9f4fae06b907e82e26dc4bed88, Telegram 13.1.1.

## Reproduction and evidence

User reports severe typing latency accumulating with chat navigation/time and a large improvement after process restart, still below Swiftgram. The capture controls were removed from the release UI; restart alone is not evidence that diagnostic recording caused it. There is no automatic performance-capture start in this source. Deeper comparison of current Swiftgram editor dependencies found 399 byte-identical rich-editor source files and four differences for Return-key appearance. Pinned Bazel Swift rules enable whole-module optimization by default; the missing explicit WMO flag is not a demonstrated build defect. None of those findings proves the user's installed beta matches repository master.

## Concrete correction

Previously every chat appearance queued an archive-visit check on a concurrent worker, promoted the controller to a strong reference, and synchronously waited for the recorder queue. The task had no cancellation when the chat disappeared. Rapid navigation could retain departed screens and queue obsolete work behind archive I/O.

The chat now owns a cancellable request. Work runs directly on the existing serial utility recorder queue, with a weak request until execution and a weak controller only in the main-thread UI completion. Disappear/deinit cancels it; queued canceled requests perform no archive reads, and canceled in-flight results cannot present UI. Cancellation is cooperative at I/O boundaries, not an attempt to interrupt an active file read. Existing record capture, archive files, watermark/count logic, chat history backend and editor selection remain unchanged.

## Verification

New tests first failed against Build172. Local exact stage apply/reverse/refusal and source contracts pass; no local Swift compiler is installed. The CI gate compiles all actual JerkgramCore Foundation sources and exercises the actual request scheduler: 200 queued cancellations, released screen/request, in-flight cancellation and exactly one successful main-thread completion. Full IPA compilation follows preflight.

This removes demonstrated obsolete work and controller retention; the contribution to the reported end-to-end typing delay is not measured yet. No claim of a complete lag fix, native keyboard timing or Swiftgram performance parity.

## Device check

Compare the same short text in Saved Messages immediately after launch and after opening/closing 15–20 chats, then continue ordinary chat switching. Check whether the large degradation returns. Check that returning to a chat with new archive changes still shows the existing notification/action, and that leaving a chat promptly never shows its archive notification over another chat. No recording or exported message history is needed.
