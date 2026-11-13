# Stable182: missing Postbox import in the selection panel

## Green baseline and observed failure

Last confirmed successful product build is Build181, published commit
`3b5d0b51e9289c14f595e097619b04ade70444d6`, Actions run
https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/43399202106.
The next Stable182 run, on `d8808db47c05f205ea86127e9542778acfe65408`, failed:
https://github.com/ghostbase-sg/jerkgram-telegram-builder/actions/runs/43456549671.

Actual Swift diagnostic:
`ChatInterfaceStateInputPanels.swift:38:8: cannot find JerkgramLocalPremiumPolicy in scope`.
The policy is public in Postbox/LocalSavedTagsTable.swift. The master-switch patch
added a policy call to a file that previously did not need Postbox. Swift imports
are file scoped; TelegramCore importing Postbox does not import it into this file.
Comparison with the green181 owner confirms the added condition is the only
behavioral delta in this owner. This is a new integration error, not a toolchain
change or a packaging/verifier error.

## Patch and evidence

New exact successor `post181-native-policy-import` adds only `import Postbox` to
that source owner. All existing successors, product features and optimizations
remain. A regression scans every current policy consumer for the owning module
import (excluding Postbox's own sources). It failed on this file before the fix
and passes afterward; no other current policy consumer lacked the import.
The six focused CI/recovery/source regressions pass locally. The complete current
source/component gate runs locally with native tests explicitly skipped on Linux;
actual Swift app typecheck and device success are not established by these checks.

## Pipeline observations

The shortened workflow reached app compilation. Mandatory current native tests
passed in macOS before the app compiler failure. The recovery upload steps ran,
but no IPA existed because the app did not finish compiling; they correctly did
not publish an older or invented archive. The always-uploaded build log is now in
the diagnostics artifact. Historical test duplication remains removed.
