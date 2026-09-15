# M1 Settings owner research

## Authority

The sole parity authority is Jerkgram 1.0.2 Stable / Build138 from
`release/source-export-1.0.2` at
`1d2b7cf728fe63bc82f0dac8abdf27701d53f44d`. Build139–141 and earlier
historical implementations are not product authority.

## Production Telegram 12.9.4 seam

The controller runtime owner is `_TtC14PeerInfoScreen18PeerInfoScreenImpl`. The
adapter adds class-local hooks for `viewDidAppear:` and
`viewDidLayoutSubviews` without patching code addresses. Build138 source and
R4.1 device behavior prove that the section-layout owner is the nested
`PeerInfoScreenNode.containerLayoutUpdated`, whose last native section-flow
write is the Settings scroll view's `setContentSize:`. The adapter observes that
UIKit boundary on the concrete Settings scroll instance and reapplies after the
original setter returns. A Swift `Mirror` bridge resolves the semantic
`isSettings`, `peerId.namespace`, `peerId.id`, presentation language, and the
named `regularSections` dictionary. The section topology is refreshed at every
native completion so an early partial first-entry dictionary cannot remain
cached. Resolution is fail-closed; zero or an
unresolved account never activates storage or creates the section.

No private Swift item is constructed. The injected eight-row section is a
Jerkgram-owned UIKit view hosted in the existing Settings scroll hierarchy.
Telegram's current completed native section frames, native My Profile row height,
colors, type, and separators are sampled on layout. The adapter recomputes the
whole section sequence from the current native baseline, inserts after
`myProfile`, and leaves Wallet (`payment`) and all following native sections
after it. Jerkgram's content-size writes are recursion-guarded. There is no
arbitrary delay and no cumulative frame delta.

## Navigation boundary

Every pushed page is an actual runtime `_TtC7Display14ViewController`. The
Jerkgram UITableView controller is a child view controller only; it is never
pushed directly through Telegram's `Display.NavigationController`.

## Explicitly rejected paths

- no `UIBarButtonItem` entry;
- no image or function offsets;
- no Swift object byte reads or guessed ivar offsets;
- no manually fabricated Swift existential values;
- no stripped `settingsItems` invocation;
- no localized text search for My Profile or Proxy;
- no account ID 0 fallback.
