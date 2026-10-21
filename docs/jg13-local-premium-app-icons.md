# Local Premium: App Icons — Build164

Product parent: `dev/release-1.1.0-163`, `b584175486af87a2c3dc3b98893c83f2947ad741`.
Official source of truth: Telegram iOS 13.0, `f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838`.
Release identity: About `1.2.0 Beta 1`; telemetry `1.2.0-beta.1`; build `164`.

## Historical experiment

Source-based Build140 experiment remains in `dev/build133-native-push-type1-probe` and other experimental descendants:

- `f3dba331b5deeede4e2697bff187b48fafe82433`: `scripts/apply_jerkgram_build140_premium_icons1.py`.
- `48a4bf78413c5a011ee15fe492ba753470be6662`: materialized-source verifier.
- `f62a62adc5578523432878ab334d4a4ede2011b1`: hooks source apply/verify before Build140 identity.
- `ab5b8fc33df2af9cebbae0771f1481ee10018f95`: wiring regression test / experimental branch head.

It set the lock badge to `false` and appended `&& false` to the Premium upsell branch. It checked that Premium icon metadata and Jerkgram default survived. It had no user toggle and did not address 13.0's visibility filter. No historical commit or unrelated Web Push code was cherry-picked.

## Official 13.0 owners

| Responsibility | Owner |
| --- | --- |
| Appearance list, available/current icons, account Premium read, selection/upsell | `submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift` |
| Grid, previews, lock badge, tap callback | `submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift` |
| `PresentationAppIcon` list and system alternate-icon binding | `submodules/TelegramUI/Sources/AppDelegate.swift` |
| Alternate-icon declarations and primary Jerkgram icon | `Telegram/BUILD` |
| Premium bitmap resources | `Telegram/Telegram-iOS/{Premium,PremiumBlack,PremiumTurbo}.alticon/` |

Three gates: filter Premium icons when Premium is disabled/testing environment; badge `!item.isPremium && icon.isPremium`; selection branch `icon.isPremium && !isPremium` leading to PremiumDemoScreen/PremiumIntroScreen.

The tap reads the existing account peer via engine data, then calls `requestSetAlternateIconName(icon.isDefault ? nil : icon.name, ...)`. AppDelegate binds that directly to `UIApplication.setAlternateIconName`. There is no Telegram API mutation, purchase receipt or server entitlement in the icon-changing path. iOS still controls whether the system icon change succeeds.

## Bounded implementation

Only three materialized owners change: the two App Icons files and `GhostBaseSettingsController.swift`.
`JerkgramAppIconAccess` is internal to SettingsUI. Its persisted device-wide switch `jerkgram.LocalPremium.AppIcons` defaults off. The same capability gates visibility, badge and upsell. Account Premium values and icon metadata retain their real values.

Location: Jerkgram → Appearance → Interface. Label uses normalized Telegram interface language from `JerkgramStrings.languageCode`: Russian “Разблокировать Premium-иконки”; English/fallback “Unlock Premium App Icons”. Setting off restores stock gates; it does not forcibly reset the current SpringBoard icon. Accounts share this switch because the application icon is device/app-wide.

The guarded stage runs in `configure_jg13.py` after the Build163 About cleanup and before identity configuration. It validates every parent and output hash before writing, rejects repeated application, and reverses each complete owner to its exact parent during verification. Unrelated Premium checks therefore remain byte-for-byte unchanged in those owners. AppDelegate and Telegram/BUILD are locked, as are all six Premium PNG resources. Existing source contracts continue to verify recovery, forwarding and Settings diagnostics.

## Validation and device matrix

Python preflight covers exact transformation/reversal, repeat refusal, tampered owner/resource rejection, canonical configure/verify wiring, previous About cleanup and existing recovery contracts. The macOS gate compiles the actual extracted capability and exercises default off, persisted toggle, all eight combinations of icon Premium/account Premium/toggle, and RU/EN fallback. Full app compilation is separate evidence; neither test establishes SpringBoard runtime success.

On device, use a non-Premium account: enable switch, reopen Telegram Appearance/App Icons, verify Premium/Black/Turbo visibility and absent locks/upsell, select each icon, inspect SpringBoard, relaunch, return to Jerkgram/default, disable switch and inspect stock gates. Check normal icons and a real Premium account for regression. Verify About and received telemetry version. No Download Boost or other Local Premium feature is included.
