# Build155 history/input investigation plan

Native execution in the current isolated worktree, authorized by user. No additional approval round.

Goal: localize synchronous history/keyboard/send work beyond Build154's broad timers; remove two proven temporary-array allocations without changing results.

Constraints: upstream f1dd7a2dbd02cbbf513e75d5695d8d36d1cf5838, product1.1.0Beta1/com.jerkgram.ios/short13.0, Build155. Five locks and Stable/history/signing untouched. No change to backend choice, synchrony, animation, blur or playback. RAM512/timings32/slow96/utility1Hz/600s remain.

- [ ] RED: history/send boundary, bounded entered-operation bitmap and actual single-pass source contracts fail against154.
- [ ] Capture core: fixed <=64-bit entered-operation mask; reset/off/stale-token/privacy contracts, main/worker detail tags. No extra timing dictionary.
- [ ] History: preparation/mapping/application/completion boundaries, actual CoreList transaction and row layout/build; preserve all original calls and scheduling.
- [ ] Input/send: real panel send handler, state update, sendMessages and scheduled-dispatch callback. No network/message content.
- [ ] Single-pass old-history ID/max index bounds; actual production fragment macOS fixture against former algorithm for empty/duplicates/unordered/random cases. Gate all other source bytes unchanged.
- [ ] Exact ten-owner patch/hash/function-survival/five-lock gates; fresh chain/repeat refusal/Python compile/full-suite comparison; publish currentHEAD CI.

Review: inclusive timers overlap; callback bodies may execute asynchronously; missing slow event does not prove hook entered; CoreList default is retained; no claim that two-array optimization fixes seconds of UI blocking.
