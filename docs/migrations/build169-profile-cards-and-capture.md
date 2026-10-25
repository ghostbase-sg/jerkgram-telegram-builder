# Build169: profile cards and Swift capture repair

Parent: 950894f0a44fb8396dc172ceb4f6f4bf739ce8b5 (Build168), same Telegram 13.1.1 pin and ListView history backend.

Build168 run 40137304744 passed source/native preflight but failed full Swift compilation in SettingsUI/JerkgramDataAndBackupController.swift:181. Swift 27 diagnosed weak inner capture of controller conflicting with its implicit outer strong capture. The picker callback now spells the weak snapshot explicitly: `[weak picker, weak controller = controller]`. The outer variable remains captured by reference, so a controller assigned after arguments construction is available when the picker is opened. No global warning suppression or compiler downgrade.

User screenshot pairs show missing shared cards in profile color and Chat Automation, and incorrect profile editing card corners. The shared ListSectionComponent is restored byte-for-byte to pinned upstream; its global GhostBaseGlassStyle override had substituted almost invisible tint for the section background. Profile single/multiline field owners retain upstream opaque block colors and all text/editing behavior. Only their corner-image call differs from upstream: the actual card layer clips the appropriate first/last corners at the same 26-point radius. This avoids painting theme-black corner fillers over the existing blurred profile backdrop. The backdrop itself is unchanged.

The four-owner final stage follows the Build167 Stars/gift fixes and ListView backend stage. Before/after SHA-256 hashes and exact patch SHA guard all four owners; unexpected input is rejected before mutation, repeat apply is refused, reverse restoration is tested. No changes to account Premium state, download boost, ad suppression, Stars or gifts.

Validation: observed missing-stage RED before implementation, observed corner-contract RED before layer clipping, then three repair tests GREEN. Fresh separate source worktree materialized/configured the full canonical chain and passed the root source verifier. Focused migration, history backend and Stars/gift checks pass. Broader current-source discovery retains the same 108 tests with four historical failures and one historical error documented in the Build168 migration report.

A macOS Swift fixture compiles the actual picker callback in its nested capture shape with warnings-as-errors, then checks navigation, dismissal and release of its weak controller. The fixture plus syntax parsing of all four changed owners run before IPA compilation. These native checks and full application compilation await the new CI run. Screenshot parity and performance still require iPhone validation in both themes, toggles and repeated edit/open/close flows.


## TelegramUI follow-up after the full Build169 compilation

Run 40176153336 passed all native preflight checks and compiled SettingsUI, then failed in TelegramUI/Chat/ChatControllerLoadDisplayNode.swift:133 and :4970: `cannot find type PeerId in scope`. Upstream 13.1.1 removed that file's Postbox import, but two injected helper signatures retained bare PeerId. Both now use TelegramCore's public EnginePeer.Id alias (defined as PeerId by upstream). No message, unread policy, scheduling or storage behavior changes.

A separate exact one-owner final stage follows the UI repair. The new type-compatibility test was observed RED on the failing source and GREEN after repair, and audits all Stable TelegramUI overlay owners for newly introduced unimported Postbox ID types. An independent broader public-Postbox-type scan found no additional instances. Parent/output hashes, repeat/tamper refusal, root source verification and application to the independently materialized source tree pass. None of these replace whole-module compilation. Full IPA success remains unproven until a new CI build completes.
