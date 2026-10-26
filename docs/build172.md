# Build172

Based on Build171 repair a0c55a6911f707975c67196addfa004ae9db4ba5 and Telegram 13.1.1.

## Settings appearance

Nested settings own an independent native backdrop using the main Settings image, blur effect and alpha, background color and adaptive tint. Removed the separate low-resolution Gaussian rendering and fixed dark/light overlays. Each child retains its backdrop across appearance and back transitions; explicit style/provider changes invalidate it. Main Settings keeps its existing backdrop instead of adding a duplicate. Restored the pre-Build171 adaptive tint. Nested cards use the same black/white surface colors and alpha as the main settings cards.

## Profile DC

The visible row and setting are labelled DC. Country formatting and the Int API boundary are preserved. This remains a storage DC sourced from the profile photo; no numeric-user-ID-to-home-DC formula was invented. Checked current Swiftgram, AyuGram, Nekogram and TeleBox implementations: they resolve profile/photo or cached connection data rather than deriving a home DC from decimal user ID.

## Performance status

The additional source audit did not identify a verified fix for severe typing latency. Input behavior and the Build171 performance changes remain unchanged. Do not describe this release as a typing-lag fix or Swiftgram performance parity. Device comparison of actual editor selection remains necessary to resolve that issue.

## Verification

Local exact-source, stage apply/reverse/refusal and regression checks are required before publication. Linux has no Swift compiler or iPhone renderer; source checks do not prove compilation or visual behavior. CI must parse changed Swift files and compile the IPA.

Device check: enter a nested settings page, wait several seconds, scroll, open another page and return both by button and interactive swipe. Check that the background and card surfaces persist without a brightness jump. Repeat with the existing translucency switch off/on and check main Settings brightness against the earlier accepted version. Confirm profile DC label and country. Animated avatar playback remains owned by main Settings; subsection backdrops use its still image and native material without an additional video decoder.
