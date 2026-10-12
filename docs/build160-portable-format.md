# Build160 — device feedback on recovery and protected copies

Base: dev/portable-copy-159, tested by the user. Telegram pin unchanged; CoreList experiments remain excluded.

User requests: remove duplicated contact text when native contact is attached; stop native poll/todo recreation and retain original titled text; include parent poll/todo title in service descriptions; replace square addition symbol; style protected copies like recovered deleted replies with bold linked source title and preserve captions, custom emoji and rich entities.

Implementation: four-owner portable delta remains guarded against the immutable Build158 parent. Only EnqueueMessage changed from159. Static contact recovery returns original caption only. Poll/todo media entrypoints return nil and existing titled textual descriptions are retained. Service bodies prepend associated parent title and its entities when available; missing parent context is not invented. Additions use +; unchecked tasks use a hyphen. Protected copies add the outer blockquote, retain bold exact public/private source-message URL, use the current transaction source peer with snapshot fallback, reuse the portable rich entity selector and supply custom emoji files from associated media. Caption, thread, group, send option and fetch failure contracts retained.

Validation: new regression source assertions fail on159 and pass on160; all29 focused tests pass in a clean fixture without developer scratch dependencies. Independent review found no critical/important defect. Native Swift gate and full compilation are separate checks; device rendering of albums and custom emoji must be tested after installation.

Device retest: attached contact contains name/phone once; deleted poll/todo response is text only and retains title; task/option additions and task completion retain parent title; + renders normally; protected public/private channel name is bold and clickable; source message link opens exact message; captions/formatting/custom emoji survive in single media and albums. Protected cloud DM attribution uses profile link/mention because DMs have no source-message URL. User has not yet tested DMs.
