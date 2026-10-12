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

Important release blocker found by focused independent review:

Expanded content plus author and user text may exceed message/caption limits.
Current delta does not budget or split final portable text. Original source text
could already be too long, but newly included media-internal text creates more
affected cases. User must choose explicit long-context behavior before shipping:
bounded marked shortening or multiple messages, with no silent extra paid sends.
Do not bump Build158 or launch the device IPA until resolved and tested against
the real final portable-message builder, including user-attached media.

Coverage limits: native facades do not compile real Telegram model types,
Account/AccountManager integration or outgoing-message assembly. Whole-app
compilation, transport and device behavior remain UNVERIFIED. Generic unknown
attachments remain a localized fallback; this is not a claim that every service
action/story/giveaway/paid-media subtype has a full snapshot representation.

Historical product patches/manifests and all five regression locks remain intact.
