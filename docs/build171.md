# Build171

Based on green Build170 (051cb0ad33d0a11686f857f56dd6629896cbb932), Telegram 13.1.1.

## Changes

- Settings corner resources clear their bitmap before drawing. Transparent sections use real row masks, including inset rectangular masks for middle rows; layout updates refresh mask geometry.
- Nested settings reuse a cached small blurred source image even while the source profile screen is hidden. Removed hierarchy capture on every presentation. Strengthened backdrop tint and profile footer/placeholder contrast.
- Profile bio delegates background and rounded edges to the outer card; its inner multiline input no longer overlays another rounded backing.
- Retained excluded chats preserve selection and outward forwarding. Text and complete cached media can be copied to accessible cloud chats; missing media cannot be fetched after exclusion. Existing copy restrictions still apply unless independently overridden by the existing setting. Low-level sends into retained excluded chats remain rejected.
- Viewing retained messages advances local read position and clears local unread state without server receipts. Nonmember tracking no longer resets this position. Topic badges update locally before network guards.
- Avatar DC shows USA (1/3), Netherlands (2/4), Singapore (5); unknown DCs keep their number. This is the avatar storage location, not a person's country. Mapping: https://docs.pyrogram.org/faq/what-are-the-ip-addresses-of-telegram-data-centers
- Message mapping reads hot settings once outside the message loop, removes persistent diagnostic writes, and caches the existing seconds-display preference with invalidation. Existing ListView selection is preserved. No measured performance equivalence to Swiftgram is claimed.

## Registration estimate

Unchanged: valid Telegram-provided registration month takes precedence; otherwise explicitly approximate offline observations are used. Additional public datasets did not provide authenticated per-account registration evidence and contained conflicting observations. No hardcoded personal account dates, external runtime ID requests, or artificially narrowed intervals were added. Existing provenance: patches/jg131-registration-data-provenance.md.

## Verification and device checks

Source contracts, exact stage apply/reverse/refusal tests and focused regressions pass locally. Native Swift fixtures cannot run on this Linux host; the workflow runs them, parses every changed Swift owner, then compiles IPA. Compilation and runtime behavior are not proven by local source checks.

After a successful build: inspect Profile Edit bio edges, footer and placeholders; leave nested settings open for several seconds, navigate back/forward, rotate, scroll, and toggle existing translucency. In a disposable group and supergroup, enable retention before exclusion, then read to bottom, reopen/restart and verify no repeated unread jump. Copy/select/forward text and cached media out; verify reactions, votes and sends into the excluded chat stay blocked. Check avatar DC labels and compare scrolling on the same device/history with Build170. Account registration remains approximate.

## Compile repair after first Build171 run

Run40265660738 passed source/native preflight, then failed full PeerInfoScreen compilation because CloudPeerPhotoSizeMediaResource.datacenterId is Int, while the new formatter expected Int32. The formatter now accepts Int directly. The native DC fixture also passes explicitly typed Int values, so preflight catches this API-boundary type mismatch. Regenerated profile metadata stage hashes. Other feature behavior and build number remain unchanged; full IPA compilation must be rerun.
