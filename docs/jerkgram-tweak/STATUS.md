# Status

## M1-R4 Build138 materialization

- parity authority: Jerkgram 1.0.2 Stable / Build138 only;
- staged payload replaced by materialized sources;
- old M1 verifier state captured RED (12 failures and 1 error out of 14);
- first R4 device run: FAIL; its custom layout rebuilt only selected native sections,
  causing later Telegram rows to overlap the Jerkgram background and displacing Wallet;
- R4.1 device run: FAIL intermittently; correct geometry after a tab roundtrip proved a
  lifecycle/topology race rather than another static geometry defect;
- R4.2 main Settings geometry: DEVICE-RUNTIME PASS; all destinations then failed
  through one common improperly initialized Display host;
- current correction observes the concrete Settings scroll view's native content-size
  completion, refreshes a potentially partial `regularSections` cache, snapshots whole
  native section containers, and derives one bounded insertion from that baseline;
- Build138 main icons now use the exact 30 pt/radius-8 renderer contract, exact RGB values,
  production 12.9.4 source-named glyphs, and the tweak-owned Build138 Airplane artwork;
- R4.3 removes the inherited UIKit initializer and uses the exact exported
  production 12.9.4 Display designated allocating initializer with image and
  class validation;
- all eight main routes plus Stars, Data & Backup, Send Style and per-chat
  retention resolve through the one shared host factory;
- Build138-only lifecycle/layout/host/route verifiers are staged; Apple
  compilation and R4.3 device navigation validation remain pending;
- main route: eight rows, after My Profile and before the first following stock section;
- `.root`: not reachable and not implemented as a route;
- account resolution: semantic and fail-closed;
- Settings navigation: runtime Display.ViewController hosts only;
- settings inventory: exactly 46 active Build138 values; no Download Boost;
- compatibility dylib and carrier executable are frozen inputs;
- M2 runtime features: not started.

Build138 Data & Backup cleanup/export/import rows remain visible, but their
event/media archive operations are intentionally inert in M1. The complete
Build138 event/archive owners are not migrated yet, so R4.3 refuses to create
or consume a misleading partial archive.

See `M1_LAYOUT_RACE_RESEARCH.md` for the exact trace and acceptance contract.
M1 remains device-parity pending.
