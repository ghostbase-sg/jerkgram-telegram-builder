# Current product baseline

Jerkgram 1.2.1 Stable / Build184 is the product baseline for all subsequent development and builds. Start new work from `dev/analytics-v3-13.2`, including its Analytics v3 integration. The single identity configuration is `jerkgram-migration.json`; settings and both telemetry paths consume the generated JerkgramReleaseIdentity. Product and Analytics appVersion are1.2.1; the official Telegram source base remains13.2.

The current build184 reads its number from the shared configuration. Package metadata, artifact names and the general product build workflow follow1.2.1. Historical Build183/released1.2.0 sources remain provenance and are not a starting point for new work. Earlier stage identities remain unchanged; post183-product121-identity is the exact verified successor.

Production Analytics v3 remains disabled pending server readiness and separate approval. This baseline change is not a public release or a claim of device validation.

Both the ordinary product build (`scripts/build_jg13.sh`) and the dedicated Analytics workflow apply and verify the same Analytics v3 source integration after the existing product gate. Future builds from this baseline therefore retain Analytics v3, not just its version number.

The same1.2.1 baseline now includes the Profile Observer foundation from its successful full compile43752098737. Both normal and dedicated build routes install and verify it after Analytics v3. The dedicated workflow saves the combined test IPA and also uploads explicitly unverified raw/recovery files if later packaging fails. Combined device runtime remains unverified.
