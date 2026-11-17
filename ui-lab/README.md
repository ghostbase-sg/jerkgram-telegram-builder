# Jerkgram UI Lab · Settings 2.0

Standalone NATIVE SwiftUI design sandbox for Jerkgram. No TelegramCore, Bazel, signing keys, session secrets, live accounts, or interaction with production Jerkgram.

## First native iteration
- Main Settings page with routes to all eight sections. Only Ghost Mode has implemented UI; the others are clearly marked placeholders.
- Ghost Mode master switch with a separate chevron opening child toggles INLINE in the same card. Lower content is pushed down. There is no bottom sheet.
- Child toggles retain their values when the master switch is off.
- Contact, non-contact, and single-peer example rules have a proposed precedence of peer > category > global. Filtering is conceptual, not connected to Telegram.
- Settings translucency can be turned off. The opacity switch changes native SwiftUI materials, not web CSS.

## Preview / simulator
On pushes to the UI Lab branch, the dedicated macOS workflow builds this small app and uploads five native iPhone Simulator PNG screenshots as the Jerkgram-UI-Lab-SwiftUI-Screenshots artifact.

Screens: 01-home, 02-ghost-collapsed, 03-ghost-expanded, 04-ghost-filters, 05-ghost-opaque. It does not produce a signed IPA.

On a Mac, install XcodeGen, run xcodegen generate inside ui-lab, open JerkgramUILab.xcodeproj, and press Run.

This is not proof of working Telegram functionality. Integration must later bind components to real source owners with independent compile and device runtime gates.
