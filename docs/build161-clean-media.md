# Build161 — clean recovered media and sticker association

Base: Build160 branch; same upstream pin and bounded four-owner patch chain, no CoreList experiment changes. Only EnqueueMessage changes from160.

Recovered native attachments now retain their original caption only, suppressing generated type labels, duplicate filenames/contact/map details. Deleted sticker replies use TelegramMediaFile.stickerDisplayText (associated emoji) from the source metadata, with localized Sticker fallback if absent. Original caption offset/entities retained. Text fallback for unavailable media retains useful descriptions; poll/todo/service text unchanged.

Validation:30 focused Python tests pass in a clean CI-style tree. Native Swift fixtures cover attachment suppression, source captions, associated emoji/missing-emoji fallback; macOS gate tracked separately before full build.

Performance investigation: user reports lag survives process restart. Deleted-media cleanup removes files but leaves empty per-message directories, increasing later recursive scans. Public-name persistence rewrites genuinely unchanged values/order. These are source-proven unnecessary operations, not established causes of severe UI lag. Opt-in performance sampling is off by default; release V11G record already no-op. No appropriate new Swiftgram performance backport found in inspected master changes; checked Telegram story-layer optimization already exists in our pin. Need a short device performance report before choosing a lag fix. No speculative cache deletion or CoreList rebuild applied.
