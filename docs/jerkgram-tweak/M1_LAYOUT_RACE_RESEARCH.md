# M1-R4.1 main Settings layout race

## Checkpoint

Device evidence shows that the R4.1 geometry can be correct after a Settings →
Chats → Settings roundtrip, but is intermittently merged on first entry. This
rules out a purely static row-height or spacing error. No Build138 geometry,
icons, routes, settings, or M2 hooks are changed at this checkpoint.

## Root cause in R4.1

R4.1 finalized from `PeerInfoScreenImpl.viewDidLayoutSubviews`. That callback is
not the owner of Telegram's section geometry. In the final Build138 source,
`PeerInfoScreenNode.containerLayoutUpdated` creates/updates every
`PeerInfoScreenItemSectionContainerNode`, assigns each section frame, and then
writes `scrollNode.view.contentSize`. The node method is called by asynchronous
data and state updates after the controller UIKit callback.

R4.1 also cached a reflected `regularSections` array as soon as the cached
`myProfile` node remained attached. On first entry this allowed an early,
incomplete topology (for example, before the `payment`/Wallet section existed)
to remain authoritative for all later passes. A roundtrip recreated the context
after Telegram's sections had stabilized, explaining why the same geometry
could then appear correct.

## Narrow production boundary

The adapter now observes `setContentSize:` only on the concrete Settings scroll
view instance, using a runtime subclass of that instance's actual Objective-C
class. It does not globally swizzle `UIScrollView`, call a private Swift method,
construct a Swift value, or use a binary address.

At that boundary it:

1. lets Telegram's original setter return;
2. invalidates the potentially partial semantic section cache;
3. reflects the current completed `regularSections` topology;
4. captures current Telegram-owned section frames and content size;
5. derives the bounded Jerkgram section from that new baseline;
6. applies one guarded Jerkgram content-size mutation.

Jerkgram-owned content-size writes carry an instance-local recursion guard and
cannot be mistaken for a Telegram completion. There is no `dispatch_after` and
the former next-run-loop `dispatch_async` retry was removed.

## Runtime trace

The diagnostic build records JSON Lines at these boundaries:

- `viewDidAppear.afterOriginal`;
- `viewDidLayoutSubviews.enter`;
- `viewDidLayoutSubviews.afterOriginal`;
- `viewDidLayoutSubviews.afterApply`;
- `scroll.setContentSize.beforeOriginal`;
- `scroll.setContentSize.afterOriginal`;
- `scroll.setContentSize.afterApply`.

Each record contains a monotonic timestamp, controller identity, Jerkgram
existence/frame, current semantic native-section count/order and identities,
`myProfile` index, `payment` (Wallet) identity/frame, every native section frame,
captured Telegram baseline content size, requested native content size, and
final content size. The bounded log is stored in the app caches directory and
is included by the existing Debug / Research “Copy Extension Diagnostics”
action without adding a route or visible row.

## Device proof still required

Static verification can prove the ordering and recursion/idempotence contract,
but cannot prove the production callback sequence. Before M1 can pass, collect
traces for:

- fresh launch → first Settings entry;
- close/reopen Settings;
- Settings → Chats → Settings;
- rapid tab switching;
- scroll before leaving/returning;
- a theme/state refresh.

Acceptance is zero merged occurrences and, for every Telegram completion,
`scroll.setContentSize.afterApply` must show exactly eight Jerkgram rows bounded
before `payment`/Wallet with final content size equal to that native baseline
plus one insertion delta.
