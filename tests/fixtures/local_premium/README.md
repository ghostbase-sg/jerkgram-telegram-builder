# Local Premium native fixture

Extracts the production canonical state, account readers, complete delta writer,
policy caches, App Icon gate, localized strings and appearance callback verbatim.
The list/controller lifecycle, state signal containers and external visual sinks
are synchronous fixture boundaries. This is not a UIKit integration test, native
SwiftSignalKit scheduler test, translation test, or screenshot verification.

Runs with `swiftc -Onone` and `-O` on macOS / Apple Foundation, with a temporary
`CFFIXED_USER_HOME`. Linux reports native execution as pending. Required native
mode fails closed instead of skipping. Baseline hashes were captured from exact
recovery parent `ce7fc4cc67a8dc036c51aa33de762e5e29ddabec` / integration source.

Covered: pure open/appearance, retained alias back navigation and reopen, reverse
alias edits, unrelated edit retention, canonical setters/cache publication,
device-global Icons versus account-scoped other settings, two accounts,
defaults, invalid Boost read fallback, selected RU/EN and fallback strings.
