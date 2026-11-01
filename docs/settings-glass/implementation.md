# Settings glass expansion (TASK C)

Four owners extend Settings translucency to device/web/connected-bot detail
cards through an explicit Settings-only opt-in. The native full-screen boundary,
outer dimming, sheet geometry/gestures and session state remain unchanged.
No new blur or observer is added. Item fill is dark0.34/light0.26; detail card
fill black0.60/white0.70. OFF/masterOFF/Reduce Transparency retain native fill;
Low Power does not change opacity.

Portable terminal gate passed: C9tests (1Swift skip), restoredB13 (1skip),
restoredA24 (3skips), earlier source contracts. Fresh exact B parent replay
accepted four-owner patch; second apply unchanged. Independent source+builder
review passed both spec and quality. macOS run41318834444 passed on commit17ff4f1c8bbbc694d0ce54093c002c2dad56c9c7: all9C tests,13B tests and24A tests passed with no skips in those stages; no app,
visual/FPS/device validation or IPA success is claimed.

Review notes a minor conditional theme-cache miss: when native modal mapping
creates a temporary base theme, repeated content-body evaluations allocate a
transformed theme. No demonstrated hot-path cost; record for focused follow-up
rather than adding new caching architecture before measurement.

Upstream update discovered during work: Official13.1.2 SHA279f89e4d4f63f17227bf877dc3d8990f22ecd58,
four commits/41files ahead of current13.1.1. Existing JG overlaps include Account,
AccountStateManager, SharedAccountContext, AccountContext, TelegramEnginePeers,
ChunkMediaPlayerV2 and MediaPlayerNode. No pin or compiler flags changed in C.
Compatibility migration must precede the planned combined app build; do not
mix a new upstream with unverified old owner hashes or discard current features.
