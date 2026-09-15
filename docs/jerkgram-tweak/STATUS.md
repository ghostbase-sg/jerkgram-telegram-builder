# Status

## M1-R4 Build138 materialization

- parity authority: Jerkgram 1.0.2 Stable / Build138 only;
- staged payload replaced by materialized sources;
- old M1 verifier state captured RED (12 failures and 1 error out of 14);
- first R4 device run: FAIL; its custom layout rebuilt only selected native sections,
  causing later Telegram rows to overlap the Jerkgram background and displacing Wallet;
- corrected main integration restores Telegram's prior baseline before each native layout,
  snapshots whole native section containers afterward, inserts one bounded eight-row block,
  and translates every following container by one common delta;
- Build138 main icons now use the exact 30 pt/radius-8 renderer contract, exact RGB values,
  production 12.9.4 source-named glyphs, and the tweak-owned Build138 Airplane artwork;
- corrected Build138-only verifier: GREEN, 19/19;
- main route: eight rows, after My Profile and before the first following stock section;
- `.root`: not reachable and not implemented as a route;
- account resolution: semantic and fail-closed;
- Settings navigation: runtime Display.ViewController hosts only;
- settings inventory: exactly 46 active Build138 values; no Download Boost;
- compatibility dylib and carrier executable are frozen inputs;
- M2 runtime features: not started.

The corrected Apple/Xcode build and second device-runtime validation are recorded
separately in the M1 checkpoint after the build artifact is produced. M1 remains
device-parity pending.
