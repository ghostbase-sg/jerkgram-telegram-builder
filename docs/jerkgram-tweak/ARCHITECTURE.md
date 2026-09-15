# Jerkgram tweak architecture

## M1 boundary

M1 contains only bootstrap, Telegram 12.9.4 Settings integration, Build138
Settings pages and local actions, localization, and persistence. It contains
no Ghost Mode, message, protected-content, notification, or other runtime
feature hooks.

## Components

- `Bootstrap/JerkgramBootstrap.m` installs the Settings adapter once.
- `Adapters/Telegram1294/JGRuntimeIntrospection.swift` owns semantic,
  fail-closed Swift reflection.
- `Adapters/Telegram1294/JGTelegramSettingsAdapter.m` owns the production
  Settings hook, eight-row main section, layout, and Display host navigation.
- `UI/JGSettingsViewController.m` owns only reachable Build138 routes and
  settings-local actions. `.root` is absent.
- `JGCreateSettingsHost(accountPeerId,page)` is the sole navigation boundary.
  It invokes the exported production 12.9.4 Swift allocating initializer for
  `Display.ViewController`, verifies the export image and returned class, then
  embeds Jerkgram UIKit content as a child. It never calls an inherited UIKit
  initializer on the Display class.
- `Settings/JGSettingsStore.m` owns a cached typed inventory of exactly 46
  Build138 values. Account keys use
  `jerkgram.account.<peerId>.setting.<baseKey>`; active-account canonical keys
  are retained as Build138 compatibility projections.
- `Localization/JGStrings.m` owns complete English and Russian tables.
- retention uses the separate Build138 key
  `jerkgram.retention.account.<peerId>` and JSON schema version 1.
- telemetry remains separate at `jerkgram.telemetry.anonymous.enabled`.

All Jerkgram routes use a real Display host. UIKit child controllers are never
placed directly on Telegram's navigation stack.
