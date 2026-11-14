# Analytics v3 current13.2 integration audit

## Product and ownership

Experimental branch `dev/analytics-v3-13.2`, based on actual current Build183 product commit243e367a3d5fa7cf353e11bb58db677525df31cf. Official source remains Telegram13.2 commit24638bc69bd083981b178dd1e7f921eebbf7fc46, Xcode27.1/Bazel9.2.0/current xcode-27 runner. Stable and released source are read-only and unchanged.

The inspected final product source is `release-1.2.0/source`. `JerkgramTelemetry` lives in TelegramUI/Sources/AppDelegate.swift; SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift owns `jerkgram.telemetry.anonymous.enabled` and broadcasts `JerkgramTelemetryPreferenceChanged`. An absent preference currently means enabled. TelegramPresentationData/Sources/JerkgramStrings.swift supplies both RU/EN descriptions.

The successor changes exactly AppDelegate lifecycle bridges and those two description strings, and adds isolated v3/bridge/probe Swift sources through TelegramUI's existing recursive source glob. It does not change Settings ownership, app identity, notifications, Telegram requests, or the existing v1 telemetry class. The patch records exact before/after hashes; v1 class bytes are explicitly checked unchanged. An unsupported or partially modified parent fails closed before writes.

## Existing-install evidence

Legacy telemetry keys:

- jerkgram.telemetry.secret.v1
- jerkgram.telemetry.firstDate.v1
- jerkgram.telemetry.installReceipt.v1
- jerkgram.telemetry.installReported.v1
- jerkgram.telemetry.lastSuccess.v1
- jerkgram.telemetry.lastAttempt.v2
- jerkgram.telemetry.opens.day
- jerkgram.telemetry.opens.count

`installReceipt.v1` is deleted after the first HTTP2xx, while `installReported.v1` becomes true. Its absence cannot prove a new installation. OFF or never-enabled installations can lack all telemetry keys. Any object at any legacy key, including false/zero, is prior evidence. The probe checks a fixed ten keys: those eight telemetry keys, the existing OFF preference, and the legacy namespace migration marker. It never copies or enumerates the persistent preferences domain.

The new bridge runs as the first statement in didFinishLaunching, before `JerkGramLegacyDefaultsMigration.run()` writes the current launch's marker and before v1 lifecycle calls. It captures only ten fixed preference existence booleans, two root-path metadata checks, and a bounded first-entry directory proof. Each of at most four directory probes reads at most four entries (dot entries/optional empty OS Library included); it never copies arrays of file names, recursively enumerates storage, or copies the full preferences domain. Actual configuration/storage work is queued by the v3 runtime onto its utility queue. Current `rootPathForBasePath` is appgroup/telegram-data; account manager storage is telegram-data/accounts-metadata and persists for logged-out installs. Legacy appgroup/accounts-metadata and existing sandbox Documents/ApplicationSupport are also prior evidence. An unavailable app group, bundle domain identity, or filesystem error is unknown. Fresh is allowed only when all ten known prior-install preference keys are absent and shared/sandbox storage is verified empty before current-launch writes. Nonempty ambiguous state is classified unknown and never registers a new installation. No account IDs, account files, or contents are read or transmitted by this probe.

The core receives `.fresh`, `.provenExisting`, or `.unknown`; it independently retains its v3 installation classification even when analytics is OFF. Unknown never produces install_registered. Re-enabling analytics and upgrading an existing installation never become a new install. A real reinstall that removes all local installation state can be a new installation; restored storage stays existing.

## Lifecycle/consent

AppDelegate's existing consolidated `handleDidBecomeActive`, `handleWillResignActive`, and `handleDidEnterBackground` are the source of v3 callbacks. Scene/application callback routing stays unchanged. The v3 core suppresses duplicate/inactive-only callbacks independently from v1. The bridge passes actual JerkgramReleaseIdentity technicalVersion/build, iOS version/major, optional locale region and uname technical model. It never passes a Telegram/account identifier or device name.

The existing preference notification calls v3 setEnabled with the persisted current value. OFF cancellation and queue clearing are executed even while production delivery is disabled. V1's preference observer and `/v1/activity` implementation remain intact. V1 and v3 records must be interpreted separately by the backend; they must not be added into a common DAU figure.

## Privacy policy audit

Read-only public repository check: `jerkgram/jerkgram.github.io`, main tree38c1543063f3aff26241cf8983162a494edbbcad. Its tree contains index/support/releases assets and no app privacy policy document. The live https://jerkgram.app/ FAQ only describes the website's Cloudflare Web Analytics; it does not disclose the app's persistent installation ID, opens or sessions. Website analytics and app analytics are separate data flows. The current public site therefore does not yet provide the requested v3 app disclosure.

The in-app RU/EN description now explicitly calls the installation ID pseudonymous rather than fully anonymous, lists opens/sessions/device model/region/client and OS versions, exclusions, and OFF clearing. A draft public app-policy addendum is in docs/analytics-v3-privacy-addendum.md. It has not been published and no live website file was edited. Publish/review the applicable app privacy policy before a separately approved production v3 enablement.

Sources: https://github.com/jerkgram/jerkgram.github.io/tree/38c1543063f3aff26241cf8983162a494edbbcad and https://jerkgram.app/ (checked 2026-11-14).

## Verification and limits

The native integration fixture executes the actual Foundation pre-bootstrap evidence probe with the actual production v3 module. It exercises fresh, existing OFF, legacy receipt evidence, logged-out account metadata, existing sandbox data, and unknown/error paths. Structural integration tests check exact-parent guards, lifecycle ordering, byte-identical v1 implementation, and RU/EN disclosures. The full app compiler must still validate UIKit/module integration on the actual pinned current product.

Production v3 transport remains a hard false constant. Tests use an injected local mock transport. No production v3 requests, CI job, app publication or device runtime test has been performed by this integration audit.

## Local real-source integration result

An independent no-hardlinks checkout at `analytics-v3-source-13.2` (official HEAD24638bc69bd083981b178dd1e7f921eebbf7fc46) was materialized with the unchanged current product materializer. All32 baseline, Beta3, post180 and post181/current successors passed exact source checks. Compilation-only build configuration used the approved public API ID with a deliberately invalid all-zero fixture hash; no real credential was read or sent. The v3 successor then applied successfully, repeated idempotently, and passed its exact materialized source verifier. The v1 class remained byte-identical to the released product (SHA25604cb5adedd82993705aaf7591ca0b7db636c047ed806a4e44ee83ccadec639e9).

The manual workflow defaults `compile_app` to false. Required native tests compile the real core/probe and run an actual local HTTP mock, producing payload/result JSON evidence. With explicit compile_app=true, the existing current native product gate runs before this successor, then the actual full app target compiles with the same identity/build183 and pinned toolchain. The wrapper contains no package/publish action and uploads no IPA. Native/loopback compiler execution and device testing remain unperformed locally because this Linux session has no Swift compiler. No native JSON result is fabricated.

## Future activation requires a separate approval patch

There is no runtime URL switch, remote configuration or user-default override that enables production v3. The production wrapper's `JerkgramAnalyticsV3.productionTransportEnabled` is a literal false and is checked again at the actual network boundary. The installer, source verifier, manifest and native tests also require that disabled state.

After backend readiness is confirmed and the public app privacy notice is reviewed/published, enabling production delivery requires explicit approval and a separately reviewed code patch changing this constant and its corresponding disabled-only guards/tests/manifest. The four-event contract, opt-out cancellation/revocation protection, local queue limits, mock delivery cases and full app build must pass for that patch. No ADMIN_TOKEN is needed or permitted in the app. Current code cannot be activated by a server response or a persisted setting.

### Fresh-container device validation remains required

The empty temporary-directory fixture validates classifier behavior, not the layout of a fresh iOS shared container. OS-managed metadata or nonempty system Library scaffolding may make a real new container ambiguous; current code intentionally returns unknown rather than assuming a new install or ignoring undocumented files. Before claiming fresh-install registration on devices, inspect a clean simulator/device container's structural names only and verify the actual pre-bootstrap proof. If verified OS scaffolding needs an allowlist, add it as a bounded, reviewed proof change with native coverage. No account contents or identifiers are needed for that validation. Until then a conservative undercount of fresh installations remains possible; production delivery is disabled.
