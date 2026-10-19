# Build162 — bounded cache optimization

Base: isolated Build161 product branch. Same Telegram pin and guarded recovery owner chain. CoreList experiments remain frozen. Only EnqueueMessage changes in source; no UI pipeline, network boost or animation-setting changes.

Public peer names: one locked lazy snapshot of private persisted name/order keys, same 256-entry LRU bound. Repeated unchanged latest entry skips persistence entirely; an order-only change rewrites only order. These keys have one in-process writer in the reviewed source.

Deleted media: preserve, remove, resolve-copy and retention cleanup share the existing serial utility queue. Queue-specific guard avoids sync recursion; resolvePath's only production caller runs on a utility queue. Empty immediate child directories are pruned atomically with rmdir; nonempty directories and symlinks survive. Retention/quota and media filenames/bytes remain unchanged. This removes persistent directory accumulation from repeated whole-tree scans. Global five-minute cleanup throttle remains as before.

Validation:32 focused Python tests pass on a clean CI-style tree. Native fixture extracts both actual cache owners with bounded model facades, real files and counted preferences:1000 unchanged store/read cycles, recency-only update, eviction bound, preserved bytes/nonempty directories/symlinks, empty directory pruning and same-queue reentrancy. Independent review found no critical/important issue. Native macOS gate/full compilation tracked separately.

These changes remove proven redundant operations; no device FPS or global-lag improvement is claimed. Build159 report still identifies heavy history/row/send work on main; that source pipeline is unchanged. Swiftgram review found analogous settings caching and optional network/effect controls, not a ready history scheduling fix. UI effect options require their own small product change and validation; network speed boost is unrelated to the observed main-thread spans.
