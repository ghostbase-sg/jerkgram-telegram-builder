# Bounded recovery / optimization checkpoint

User replaced the asynchronous CoreList project with optimization of Jerkgram's
own runtime/build code and localized deleted-message reply expansion.
CoreList work remains frozen, excluded from this branch and any new IPA.

Product baseline: Build157, 7be71232f9b723dafe4c771ec57e90f26fe29a59.
Dedicated remote branch: dev/portable-reply-158, based on that product commit.
Pinned Telegram: f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838.

Implemented three-owner delta:

- Poll question/options/solution and todo title/items/completion state.
- Contact name/phone, venue/address/coordinates, dice result and invoice text.
- Rich entities shifted using UTF-16 offsets; nested quote excluded as before.
- RU/EN semantic labels selected from current app localization, English fallback.
- Captionless recovered media now has a type label instead of author-only text.
- Ordinary sends without replies skip recovery defaults reads, Postbox transaction
  and worker dispatch. Non-deleted reply plans skip language read and worker.
- Packaging digest streams 1 MiB chunks instead of reading the entire IPA.
  No signing, entitlement or packaging-content behavior was changed.

Evidence:

- Four new source-contract tests observed RED before product changes, then GREEN.
- Four materialization fixture tests observed missing stage, then GREEN: exact
  apply/repeat refusal, tampered-parent no mutation, existing-helper preservation,
  each of five original regression locks.
- Two digest tests observed missing function, then GREEN: exact digest and <3 MiB
  traced allocation for a 12 MiB file, plus empty-file digest.
- Native run38205484165 GREEN: actual Foundation helper, actual extracted
  quote-body functions against explicitly bounded Telegram model facades.
  https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/38205484165
- Earlier native attempts failed because of a Bash empty-array fixture issue and
  private global fixture declarations; neither was a demonstrated product defect.

Long-context behavior approved by user on 2026-10-12 and implemented:

- Fit only the recovered quote, keeping user text unchanged and no automatic
  text splitting. Existing album recovery behavior remains unchanged.
- Reserve actual account message/caption limits via UserLimitsConfiguration,
  including Premium app configuration. Snapshot once for deleted plans only.
- Mark shortening in RU/EN; use an ellipsis if only a minimal notice fits.
  If valid user input fills the whole limit, omit quote rather than trim input.
- End the retained prefix at a composed-character boundary. Clip quote entity
  ranges to that prefix before appending the marker and unchanged user entities.
- Native RED run38206325835 demonstrated missing fittedQuote. GREEN
  run38206511578 executes both the real helper and final portable builder with
  bounded model facades: text/caption limits, full user text, exact-boundary
  caption, Premium limit, retained attributes and UTF-16 clipping.
  https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/38206511578
- Focused independent re-review resolved the Important length finding and found
  no new Important/Critical issues. Nine local source/stage and two digest tests
  pass. Full device Build158 is the next verification gate.

Coverage limits: native facades do not compile real Telegram model types,
Account/AccountManager integration. Outgoing-message assembly is now covered
against bounded facades, not the actual Telegram model classes. Whole-app
compilation, transport and device behavior remain UNVERIFIED. Generic unknown
attachments remain a localized fallback; this is not a claim that every service
action/story/giveaway/paid-media subtype has a full snapshot representation.

Historical product patches/manifests and all five regression locks remain intact.
