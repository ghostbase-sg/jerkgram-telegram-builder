# History backend and upstream implementation plan

**Goal:** Keep Build167 Stars/gift fixes, restore ListViewImpl as the default history backend, and port to Telegram 13.1.1 without losing existing features.

**Architecture:** A bounded reversible final source stage selects the existing backend. Full output hashes and restoration retain earlier regression contracts. Upstream migration is checked separately before changing the product pin.

**Constraints:** Work in the existing Projects checkout. No commit, push or expensive build without authorization. No runtime performance claims without device evidence.

- [x] Test the backend transform against actual materialized source, including tamper/reapply rejection and exact restoration.
- [x] Add a final backend stage after Build167 fixes; wire application, verification and native parsing.
- [x] Run source regression gates and report compile/device limits.
- [x] Evaluate the complete Stable patch against 13.1.1 and resolve migration conflicts before changing canonical metadata/toolchain.

- [ ] macOS native gates, full IPA compilation, and device validation.
