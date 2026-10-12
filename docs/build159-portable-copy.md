# Build159 — native recovery and protected copies

Base: tested Build158 product branch, immutable Telegram pin f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838. CoreList experimental work is excluded.

User smoke test: Build158 broadly works; requested richer static locations/contacts, task/poll service descriptions and protected forwarding for owner-protected channels and cloud DMs.

Four-owner delta: EnqueueMessage, JerkgramDeletedReplyText, AccountStateManager, ChatControllerForwardMessages. Build158 Account owner remains unchanged. Five regression locks retained. Four obsolete private UI portable-forward helpers are intentionally removed; all other original functions retained.

Native static location/contact recovery, bounded fresh poll/todo creation, localized task/poll changes and preserved source snapshots. Protected copies resolve centrally at the public enqueue boundary across forward routes. Attribution uses actual source chat, exact public/private channel message links, or DM profile mentions. Binary media owns fresh local resource IDs and bytes; fetch failure aborts the batch with localized feedback. Normal forwards and disabled settings retain existing behavior. User quote limit policy remains unchanged.

Validation: 26 focused Python tests pass; clean final-tree reverse/apply fixtures pass (7 additional stage executions). macOS Swift production-function gate 38220233897 passes; previous RED 38218466562 fails for the absent protected helper as intended. Independent review found no critical/important defects. Helper fixtures cover pure model and text behavior, not actual asynchronous uploading or device behavior.

Device checks: static location and vCard; ordinary poll and todo (Premium/non-Premium fallback); append/completion/option change messages in RU/EN; public/private owner-protected channels and protected cloud DMs with text/photo/video/document; downloaded and not-yet-downloaded media; albums, comments, silent/scheduled/Saved forwarding; source links, captions/entities, spoilers; disabled protection settings and ordinary forwards; offline fetch failure without partial send or forbidden-forward fallback.

Full compilation and device smoke test remain separate validation gates.
