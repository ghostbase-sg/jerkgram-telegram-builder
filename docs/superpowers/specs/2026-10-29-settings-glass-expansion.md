# TASK C — Settings readability and detail-card translucency

User: expand semi-transparent Settings to missing regions, explicitly device
information, and darken enough to distinguish the content from its backdrop.
Continue the same local chat/workspace. TASK A and B source/native checks passed;
TASK B code fd2f615, run40898713432. Official13.1.1 pin fb0e62 remains unchanged.

## Decision

Keep the existing Settings backdrop and modestly strengthen item fills. Give
the native device/session detail card a scoped translucent fill. Do not use
generic full-screen backdrop inheritance for this floating card. Do not add
another blur layer or alter global modal components. The current sheet already
has native corners, clipping, transforms, independent outside dimming and hit
testing; those remain authoritative. This is a bounded first expansion to the
known missing device/website/connected-bot details in the same Settings flow.

Approaches rejected: removing the card's Settings opt-out installs an outside
backdrop; clearing all modal themes changes unrelated screens; adding another
full-screen blur increases rendering cost. A scoped existing color fill is the
smallest reviewable adjustment. Actual visual quality still requires a device.

## Scope and values

All values are independent of Low Power Mode: it may suppress animation/blur,
but must not substitute a much darker 0.90 tint. Reduce Transparency and master
glass/settings translucency OFF retain native backgrounds. No text/icon alpha
changes, no global background/theme/premium change.

Existing Settings item fill: dark0.26→0.34, light0.18→0.26. New floating-card
fill: black0.60 in dark theme, white0.70 in light theme, both theme-aware with
opaque native text. Child detail rows use the same scoped Settings item fill.
This stronger card fill preserves a visible separation from the underlying
list without clearing the native outside dimView alpha0.4.

Put pure admission/alpha policy beside existing Settings policy in
Display/Source/GhostBaseGlass.swift, under distinct extraction markers. Theme
mapping consumes the policy. Device card styling is opt-in through an appended
default-false initializer parameter from RecentSessionsController only; callers
outside that flow keep native behavior. Preserve
RecentSessionScreen.jerkgramAcceptsSettingsSurface=false. Use existing scoped,
disposed visibility/revision machinery (jerkgramTracksVisualSettings) for style
updates; include style state/revision in component equality so cached components
cannot retain obsolete colors. No polling, defaults reads per layout, new
global observers, runtime wrappers or swizzling. Do not force content/state
recreation on each layout; preserve current form/session actions and scrolling.

Expected four source owners: GhostBaseGlass.swift, PresentationTheme.swift,
RecentSessionScreen.swift, RecentSessionsController.swift. If additional owner
is necessary, establish its exact parent and report the reason first. Do not
change ResizableSheetComponent, ViewControllerComponentContainer or generic
ViewController. Existing full-screen Settings surfaces inherit their existing
policy; chat/profile/emoji-picker boundaries stay intact.

## Evidence / delivery

TDD actual pure production policy fixtures: light/dark fill bounds, all opt-in
flags, OFF/masterOFF/ReduceTransparency native admission, Low Power does not
change tint. Source tests cover both component equality levels, scoped caller,
unchanged opt-out/native sheet geometry/dimming/gesture sections, and live style
update wiring. A source fixture is not UIKit/device proof. Device matrix:
light/dark, toggle/master/accessibility/low-power, session/web/bot cards,
landscape/tablet bounds, terminate/cancel/drag-dismiss, repeated opening and
return navigation; compare readable text against bright/busy wallpaper.

Separate terminal materialization stage after TASK B: exact parent hashes,
idempotence, reverse C→B→A→176 contracts. Source-only macOS gate before app
build. One combined IPA only after all scoped reviews/gates and verification
of actual latest successful build number. No unrelated BOTBRIDGE1 changes;
that remains a later isolated branch.
