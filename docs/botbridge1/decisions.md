# BOTBRIDGE1 decisions and limits

These execution decisions supplement the user spec. Implementation and native/app integration are still in progress; this document does not assert a released experimental IPA.

| Decision | Reason | Cost or limitation if wrong |
|---|---|---|
| Reuse the dedicated current checkout on `dev/botbridge1-legacy-history-modern-write`; keep the original Projects checkout and stable remote unchanged | Existing suitable checkout; user requested this same Work Local chat | Isolation relies on branch/source ownership discipline; exact bases and immutable source packages are retained |
| Reuse the exact GREEN Build177 checkpoint instead of repeating its expensive build | Required native/source and app evidence already exists for commit5ba6add | Baseline evidence must refer to that exact commit; independent owner/provenance checks guard drift |
| Tasks1/2 produce reviewed drafts; Task3 terminal patch/manifests/materialization are authoritative | Existing source-based builder architecture | Draft-only completion would leave product unshipped; final IPA/CI remains mandatory |
| Extract actual production code with strict unavoidable boundary facades for native unit evidence; do not invent a full DB/device gate | User permits static/unit tests and final app build; Linux has no Swift compiler | Facades cannot establish actual database/index/UI/transport behavior; unexecuted/device cases stay explicitly pending |
| Keep the Telegram13.1.2 base and first-wave A/B1/B2/C scope fixed during BOT | User prohibited unrelated migration/UI/performance work in the experiment | Deferred performance waves D–H, including S7 race/cleanup, are not claimed fixed |
| Cap aggregate historical delete-ID inspection at20,000/page before mutation | An otherUpdates count cap does not bound nested vectors | Unusually large history responses terminate incomplete; live deletion/update behavior is unchanged |
| Fix repeated response-chat parsing within Task1 | At permitted bounds it allowed up to50million parse attempts on the shared Postbox queue | A bounded one-pass index uses additional bounded memory; actual device timing remains unmeasured |
| Exercise the actual history-to-export adapter in Task2 fixtures | The brief explicitly requires exact exported tuples/counters/privacy assertions | Adds a focused native unit fixture; it still does not establish device/server behavior |
| Propagate Build178 identity through both exact Strings-owning stages only | Composed restored-view runner exposed translation-repair and profile-metadata identity dependencies | Incorrect derivation fails strict hashes/identity gates; unchanged feature patches and old hash evidence are retained |
| Show a dedicated experimental export action unconditionally in Data & Backup | Retained bot diagnostics must remain reachable from another active account; page construction must avoid file scans | An empty report truthfully states no captured sessions; zero-account login UI export is not provided |

## Evidence boundaries

Modern177 is compiled and metadata verified, not device-tested. BOT source-gate approval is not macOS fixture execution or a successful app build. Declarative prepared cases and Linux native skips are never counted as behavioral passes. The full generated-source preference-key scan, production fixture execution on macOS, protected modern-write proof and experimental IPA remain required before delivery.

Build82's unread-based candidate is retained; the adapter consumes the first difference payload and imports absent messages directly while never replacing live update state. This supports existing accounts and avoids a second live state loop. It is an adaptation, not a literal transplant or an all-time-history guarantee. Server retention/channel coverage and physically deleted messages without durable tombstones remain runtime/coverage limits.

Operation ordering near logout is correlation. Submission is not wire execution, acknowledgement is not successful RPC completion, and RPC success is not proof of local update application. Reading may generate native read acknowledgements. Internal retries/upload failures outside the observed request entry points must be labeled unknown rather than inferred.

## Whole-branch review boundary dispositions

| Review boundary | Disposition and consequence |
|---|---|
| macOS native/full-source/app/IPA | Required delivery gates, still pending; no skipped test or reviewed source substitutes for them |
| Full Postbox/index/hole/pending-worker integration | Keep extracted production fixtures and full app compile; actual database/device preservation remains a stated runtime check, not an asserted pass |
| Server candidate/slices/channels/all-time history/14h survival | User Bot A/B/C experiment; report partial coverage and do not claim server success from compilation |
| Physical deletion without tombstones or later-page deletion evidence | Retain explicit incomplete deletion coverage; no unrequested tombstone subsystem |
| Internal transport retries/uploads/local application | Preserve exported unobserved markers; no inference of success or causation |
| Zero-account login export | Existing agreed active-account entry only; document the limitation |
| Deferred D–H/S7/archive/device UI and thermal parity | Preserve deferred scope; no BOT-time unrelated cleanup or parity claim |
| Remote build identity/stable branch/publication | Recheck remote immediately before publishing the reviewed experimental branch; verify actual compiled commit/artifact after CI |
| Computed preference-key expressions/dependency gitlinks | Describe the literal full main-source scan accurately; no semantic-expression or dependency-content scan claim |

Accepting these boundaries can leave a device/server/database defect undiscovered until runtime testing. None waives the required macOS or IPA delivery gates. The final review's R1 retention and R2 admission-loss findings are assigned to one scoped fix wave before publication, rather than deferred.
