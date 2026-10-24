# Build167 — currency isolation and gift readability

Parent: Build166 `bf1a00483e0c1b10d290371a6223d0954094f8ab`, IPA workflow39637411733
completed successfully. Official13.0 pin remains
`f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838`.
Version stays1.2.0 Beta1 / telemetry1.2.0-beta.1; build167.

## Stars leaking into Gram Earnings

The existing StarsContext serves both Stars and TON/Gram via its `ton` flag.
Jerkgram's local Stars override was unconditionally replacing its balance in
StarsContextImpl.updateState. StarsTransactionsScreen independently applied that
override again when passing the balance to its currency-aware card. The card and
top header already format/branch by currency, but received contaminated values.

Fix exactly those two owners: skip the Core override when `self.ton`; skip the UI
override when `component.starsContext.ton`. Both guards short-circuit before calling
the defaults-reading helper for TON. Stars mode preserves its existing override,
parser and settings. Real TON balance, transactions, server requests, accounting,
withdrawal and purchase actions are untouched. No settings schema change.

## Gift sheet showing the profile gift grid through its body

GiftViewScreen lowered its theme sheet background opacity to0.56 dark /0.64 light.
GiftPagerComponent further reduced profile-gift dimming to0.28 instead of native0.4.
The artwork header paints its own background, while the lower attributes table
exposed the grid behind it, matching the supplied screenshot.

Restore the full-opacity theme background for the sheet and assign the same color
to the existing content-container UIView behind its children. Restore pager dim0.4,
removing its profile-glass condition and repeated item scan. Dark/light theme colors
are preserved. No new overlay, observer, preference or touch interception. Gift
artwork, glass controls, actions, layout, scroll/paging, dismissal and global glass
remain unchanged. hasDimView remains false because the pager owns the dim.

## Exact runtime owners

- TelegramCore/Sources/TelegramEngine/Payments/Stars.swift.
- TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift.
- TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift.
- TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift.

Paths are under submodules/. A separate four-owner manifest/stage follows the
Build166 stages before identity configuration. It validates complete parent/output
hashes, reversible exact transforms, regression locks, canonical apply/verify and
repeat rejection. Reverse validation occurs before writes. No App Icons, Download
Boost, No Ads, protected forwarding, deleted replies or profile-capture runtime
source is modified.

## Validation and device checks

Local: Python compilation, three stage/regression tests and canonical source verifier
pass. Independent reviews found no critical/important issue. Native macOS runner
executes actual extracted Core updateState/helper and UI count/helper over32 cases:
override Off/On ×Stars/TON ×decimal/zero/spaced-comma/invalid ×two real updates;
also verifies missing UI state, emitted state and retained history marker. It is a
model facade, not full network/account/UI execution. Existing App Icons, Download
Boost, No Ads/profile native gates remain required. The four changed Swift owners
are syntax-parsed before the normal IPA job; no Bazel starts if preflight fails.

After installing Build167:

1. Record actual Gram Earnings; enable fake Stars with a distinct amount; Gram top
   header/card remain real while Stars shows the selected local balance.
2. Change fake amount, toggle Off/On, reopen and relaunch; repeat for zero/decimals.
3. Check gifts in dark/light themes, own/other profiles, collectible/ordinary gifts;
   lower attributes table and footer no longer reveal the profile grid.
4. Check gift scroll, paging, transfer/wear/sell/menu/add-to-profile and dismissal.
5. Smoke App Icons, Download Boost, No Ads and profile screenshots.

Remaining device-only checks: actual iOS27 compositor/theme rendering, gift action
touch behavior, real account refresh and screenshot comparison. No runtime success
is claimed from compilation. Direct execution on the user's computer was unavailable
in this session; source edits used the connected cloud workspace and normal GitHub CI.
