# Profile Time Machine foundation — Telegram13.2

## Baseline and scope

User correction explicitly supersedes the stale12.9.2 attachment. Actual product is Jerkgram1.2.0 Stable Build183, builder published636decefd426586118c0a06de03d2d3c2cc24cde (localtree-equivalent243e367), Telegram13.2 release24638bc69bd083981b178dd1e7f921eebbf7fc46. Work: `dev/profile-time-machine-13.2`, separate from released product. Initial observer62c62f68 was an older experimental implementation, **not an active observer in releasedBuild183**. Current product retains legacy ProfileHistory/ProfileIntel/Presence/gift stores. Do not attribute all existing product lag to a module absent from that product.

No UI, stories, notification settings, entitlement, release identity or Stable branch modifications. Original12.9.2 experiment retained for reference; no build was dispatched from it.

## Audit matrix / implemented successors

| Severity | Evidence / defect | Change | Remaining evidence |
|---|---|---|---|
| P1 privacy | Old `JerkgramProfileObserver.openIfNeeded`: SQLCipher import but no key, global observer-v1.sqlite | New `JerkgramProfileHistoryStore.open`: account directory, existing32byte Postbox devicekey, randomperfile salt, explicit connection header0, cipher_version + keyed schema read beforeWAL. No globalcipherdefaults changed | Actual13.2 SQLCipher Cprobe; Swift/iOS and DataProtection runtime still separate |
| P1 capture |13.2 `State/Sync/UpdateInterpreter.swift` ignores generic `.updateUser`; native external-ID subscriber refreshes only cached contexts and broad getFullUser also touches notifications | Dedicated watched-gated invalidation field propagated through state/replay/EventHub; separate stream, native external-ID stream unchanged. Narrow users.getFullUser only | Native scheduler fixture and full app gate pending |
| P1 history | Old begin assumes CachedUserData existence means BIO known; default init.about=nil is actually unknown | Begin reads current identity only; BIO known only from real full-user response. Dictionary absence=unknown, presentnil=confirmedabsent; firstknown enrichment separate from snapshots | Native store fixtures pending |
| P1 hotpath | Old updatedPeers creates Date + async closure retaining all peers on every call, loads unbounded watchedSet/cache | Fixed64KiB Bloom/account, exactSQLite check offhotpath; bounded4096FIFO and singleutilitydrain, no irrelevant serialization/task/batchcapture; streamedwatchloading; overflowdurablegap | Native realproduction admission benchmark pending; no devicejank claim |
| P1 history | Parsed userEmpty intermediate differs from effective native merge; can invent deletions/restorations | Reject empty/min placeholders; only admittedfullusers reread effective transactionpeer after merge. Partialmin data waits for stronger identity/fullresponse | Conservativepartial-data limit; fullapp compilation pending |
| P1 identity |13.2 applyUserName retains contactalias; publicname exists only in raw API event | Carry raw publicFirst/Last as metadata in same UpdatePeer operation. One replay observation combines publicname +username. Generic identity never overwrites publicfields with contactalias | Native actualoperation fixture pending |
| P1 races | Token/enqueue generation gap could wedge drain; old stop could close new store; readiness messages could reorder | Expectedgeneration checked atomically in ingress; lifecyclequeues enqueue underlock; readiness serialized withopen/close; stalequery emitsfalse/completion; explicitrestart afterfailedopen | Independent review found these; actualFoundationfixture/fullapp pending |
| P1 visibility | Initial version treats failedopen as permanent and hides errors | Public storageStatus signal + sanitized operation/SQLiteerror log; requiredmigration failure keepsnotready, oldstores remain; retryonexplicitactivation/open. Capturegapcount retained until persistence succeeds | NoUIyet; diagnostics signal readyforfutureowner |
| P1 preservation | No migration, no indexedread API | Atomicper-source archive+normalizedevents+fingerprint withexactbytecollisioncheck; idempotent changedsource revisions; original defaults retained. Unparsed/unknownlegacy kept raw, never presentedasverifiedhistory | Native rollback/retry/bytes fixtures pending |
| P2 Presence | Current13.2 legacy recordPresence compares until,lastActivity and only2secondwindow; redundantrecently records | Semanticstatus+hidden dedup in retained oldwriter; new Presence journal separate fromprofileevents; no BIO request fromPresence | Oldhistorical repetitions retained, notrewritten |
| P2 resources | Old statecache clears all; newhistory lacked paging | Indexedkeyset pages maximum256, no eventcap/cache. Avatar descriptors include resourceid/dimensions/video/personal flags, no bulkdownload | Resources notpinned/downloaded: historical media can later expire |
| P1 verification | Original workflow only Python/Swiftparse/markers called GREEN | Dedicated current13.2 exactproductmaterialization + realnativecomponents + full Bazel //Telegram:Telegram, Xcode27.1/Bazel9.2.0 customxcode-27 | Compilation notclaimed until actualrun succeeds |

## Call / cost map

- **Account creation:** weakaccount registry; keys obtained from alreadyexisting authorized accountWithId encryptionParameters. Singleutility open/schema/migration/streammembershipload. Noaccount retainedindefinitely. No database recreation on wrongkey/corruption.
- **No watchers afterload:** registrylock + fixedmembershipgate; no newqueue task, Date, JSON, SQLitework or observerBIOrequest. Duringstartup loading a boundedqueue permits possiblyrestoredwatchIDs; overload isexplicitgap, notsilentinfinitebacklog.
- **Peer update:** cheapIDfilter, rejectplaceholder, effectivepeer read onlyforcandidateinsideexistingPostboxtransaction; immutableuser reference entersboundedFIFO. Projection/JSON/SQL on utilityqueue. Bloomfalsepositive dropped by indexedexactmembership.
- **Profile firstopen:** onefinitePostbox currentidentityread, enrollbaselineifnotalreadywatched, newwatch signal schedules firstBIOsample. No CachedUserData assumption. Targetedlegacyimport uses30constantlookups, notglobalsettingscopy.
- **BIO invalidation:** dedup4096IDs, oneinflight/account, >=1secondglobalspacing and >=5seconds/peer,512timestampcache. One-shot timeronlypendingcooldown. Requesttimeout30seconds; atmost2failure retries; serverFLOOD_WAIT suppressesallrequestsforaccount. Foregroundoff cancelswork/timer and retainsboundedpending; dispose invalidatescallbacks/ closesstore. No all-userpolling.
- **Presence:** independent semanticjournal; until/lastActivity retainedasmetadata butnottransitionidentity. Online/recently/lastWeek etc reflect receivedprecision; no offlineinferencefromsilence.
- **Background / keyboard:** noobserverUIbindings, viewinvalidations, theme work, keyboardhook, permanenttimer or allwatchedscan.
- **Legacy costs:** oldwriters remain intentionally untildevice/migrationretentionconfirmed. Their existing global knownuser/Presence tasks and oldcaps are not represented as cured; newuncappedjournal is independent. Full-domain migration is oneoffutilitywork and peakmemorydepends on existing UserDefaults archives, not a claimedconstant-memory migration.

## Storage / migration truth

SQLite/WAL contents are encrypted by the actualSQLCipher connection; SHM is coordinationmetadata, not profilepayload. Directory and SQLite/WAL/SHM receive iOS completeUntilFirstUserAuthentication protection; no claimthat SHM itself is SQLCipherencrypted. Backupexcluded directory; temp_storeMEMORY; fullsynchronousWAL; no manualsidecardeletion. **P1 inherited key-protection limit:** `BuildConfig/Sources/BuildConfig.m:368–460` persists rootPath/.tempkey as plaintext48bytes (32key+16salt); SecureEnclavewrapping code is commentedout. `AppDelegate.swift:1195/1210` passes that key into ValueBox. AccountManager rootbackup exclusion is attempted, but this owner sets no explicit keyfile DataProtectionclass; actualclass needsdeviceinspection. Thus SQLCipher encryption is real, but Keychain/SecureEnclave keyprotection is NOTverifiedandNOTclaimed. A future keywrapping/migration patch must account for logout, re-signing/teamchanges and existingPostbox compatibility before changing the shared key owner. No sharedproductionkeyowner was changed here. Compromiseofunlockedprocess is outsideatrestprotection, and oldplaintextv1/defaults remain untilauthorizedcutover, so this is **not a claim that all existing history has become encrypted**.

Each legacy sourcearchive/normalizedrows/marker commitsatomically; interruption acrosssources isresumable, notglobalcutover. Original stores and writers retained, so partialmigration neverreplaces them. ProfileIntel2opaque text and malformedpayloads preservedexactly. Legacyobserver watches restored with unknownemptyfields, no inventedoldbaseline; firstrealnewobservation startsbaseline atactualobservationtime. Olduntrustedabout flags neverbecomeknowncurrentdata.

## Guarantees / limits

- Records values actually observed, with observationtime; no reconstruction of intermediates neverdelivered byTelegram or missedwhileappnotrunning.
- GenericupdateUser is aninvalidation hint, not BIOcontent. No guarantee server sends everychange; throttling can coalesceunreceivedintermediateBIO.
- Overflow/cancellation/storagefailure maycreate explicitcapturegaps; boundedRAMcannotpromise infiniteburstlosslessness.
- Min placeholders deliberately donotimply clearedfields; somepartial-only decorationswait forfullerdata.
- Foregroundcapture is not iOS suspended/backgroundexecution and doesnotuse BGAppRefresh.
- Firstopen enrolls ownaccountcontext'sothercloudusers only; accountids arestable Telegram peerids, pathsareexistingaccountdirectories, sessions rejectwrong Account object/stalegeneration.
- No userinterface added. Existing historypanes stillreadlegacy stores, pendinglaterverifiedUIwork.

## Evidence levels

1. **SOURCE VERIFIED locally:** entire currentBuild183 source chain reproduced on actual13.2, installer repeat/refusal/rollback/tampertests; request/statehook anchors checked onbothpristineandproduct. Native tests skip/fail explicitly withoutSwift, nevertreatedasPASS.
2. **C SQLCipher probe:** `python3 tests/profile_observer_storage_cipher_probe.py --source-root ../profile-observer-source-13.2`; actualpinned dependency, productionDDL, encryptedheader/WAL, globalheaderisolation, wrongkey/reopen. Reproduction documented tests/profile_observer_storage_native/README.md. This doesnotproveSwift or iOSruntime.
3. **NATIVE COMPONENTS / FULL APP:** required dedicatedActions workflow; status/URL tobeaddedfromrealrun. No localmacOS/iOScompiler. FullBazelcompile mustsucceedbeforereadinessclaim.
4. **DEVICE:** notperformed. No TimeProfiler/jank/<10ms/no-regression claim withoutrealmeasurement. Existingdeviceuserreports arenotevidenceofnewobserverruntime.

## Next narrow patches

Implemented source successors are mainobserver+admission, encryptedstore, BIOscheduler+statehelper, installerverifier and dedicatedbuild. After compiler failures (ifany) are repaired, verifycapture/migration/lifecycleonrealruntime beforeaddinghistoryUI orremovinglegacywriters. Do notchangeStable/release, batch observerwithunrelatedfeatures, or enableAnalyticsproduction aspartofthisexperiment.
