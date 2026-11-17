# Jerkgram native Settings · Telegram 1:1 overlay v1

**This replaces the rejected SwiftUI UI Lab approach.** No alternative SwiftUI cards, gradients, fake profile or new navigation system.

This stage only adds an optional chevron to the real Telegram ItemListSwitchItem node. Existing callers continue to render the stock control. When tapped, the same ItemList list animates insertion/removal of existing ItemListSwitchItem rows, preserving Telegram glass masks, section geometry, colors, typography, navigation and native switches.

## First production-safe scenario: Profile Information

On **Jerkgram → Основные функции** the existing "Показывать сведения" row becomes the parent. Its real account-scoped toggle is unchanged. A small downward chevron to the RIGHT of the switch reveals the existing Telegram ID, DC, and registration-date rows immediately beneath. Their original keys, toggles, order, account isolation and persistence remain unchanged. The section starts **expanded** so the initial screen retains all existing Telegram rows; tapping the arrow collapses/expands them without changing values or persistence. Closing the section does not change values.

The first v1 code is intentionally NOT a Ghost Mode master switch. Ghost Mode currently has independent runtime flags; inventing a global master without runtime gating and value preservation would be unsafe. That scope requires a separate source audit and implementation.

## Actual sources
- submodules/ItemListUI/Sources/Items/ItemListSwitchItem.swift
- submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift

## Apply only to pinned materialized Jerkgram source
    python3 scripts/apply_jerkgram_native_settings_inline_v1.py --source-root /path/to/final-source --apply
    python3 scripts/apply_jerkgram_native_settings_inline_v1.py --source-root /path/to/final-source --verify

Script is intentionally non-idempotent for apply, marker+structure verified and exact-anchor bounded. No blind global replace. Never apply to upstream Official source before materializing Jerkgram overlays.

## Evidence and release safeguards

- Reproducible source patch, tested on published Build183 native Settings owners.
- **Not a Build184 final-source proof** until audited after the complete current Build184 patch-chain.
- **Not compiled as Jerkgram IPA**, and no iPhone runtime claim. Do not distribute it as finished UI.
- No GitHub workflow of the two-hour product build is modified.
- Standalone SwiftUI Lab remains an isolated rejected experiment, not part of this native patch.

Next gates: exact Build184 final materialization → apply verifier → compile → device runtime screenshot/interaction → iteration.
