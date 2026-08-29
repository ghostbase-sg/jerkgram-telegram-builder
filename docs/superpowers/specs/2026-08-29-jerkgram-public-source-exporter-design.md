# Jerkgram Public Source Exporter Design

## Goal

Build a standalone, fail-closed release-source exporter that takes the final materialized Jerkgram source tree and produces a deterministic public source snapshot which can be tied to one Stable IPA without exposing internal builder history, signing material, API credentials, or other secrets.

## Context

The current Build124 workflow prepares Official Telegram iOS 12.9.2 at `work/swiftgram-src` and then continues to mutate that tree through late compatibility and Jerkgram overlays before Bazel compilation. Therefore the public-source exporter must not be inserted into the existing workflow until the exact final materialization boundary is frozen and verified.

The exporter is initially standalone. It accepts an explicit materialized-tree path and release metadata and can be exercised entirely with fixtures.

## Upstream identity

- Repository: `TelegramMessenger/Telegram-iOS`
- Tag: `release-12.9.2`
- Commit: `6ad963e5b62d354da79040f388ae2b9132fb17b8`

## Architecture

### Inputs

- fully materialized source tree
- Jerkgram version
- build number
- optional public source tag (defaults to `v<version>`)
- optional Stable IPA path
- explicit output directory
- public-source policy file
- known runtime secret values from environment when available

### Outputs

A release directory containing:

- `source/` — public source snapshot
- `internal-materialized-manifest.json` — private audit manifest of the input tree
- `public-source-manifest.json` — public snapshot manifest
- `excluded-paths.json` — private audit record of explicit exclusions and reasons
- `JERKGRAM_RELEASE.json` — release provenance without private builder history
- deterministic `Jerkgram-<version>-source.tar.xz`
- archive `.sha256`

The internal manifest and exclusion report are audit artifacts and are not automatically copied into the public source tree.

### Copy policy

Copy-all-by-default. A materialized file remains public unless a policy rule explicitly classifies it as generated metadata/state rather than corresponding source.

Permitted initial exclusions are limited to:

- VCS metadata (`.git` directories/files, including nested submodule metadata)
- top-level Bazel output symlinks/directories (`bazel-*`)
- top-level `ghostbase-final/` generated package staging
- `build-input/configuration-repository/` generated local build configuration

The exporter must scan the entire materialized tree for secrets before applying exclusions. Exclusion is not a secrecy mechanism.

### Secret policy

Fail the export if any of the following are present anywhere in the materialized tree:

- private-key PEM markers
- `.p12`, `.pfx`, `.mobileprovision`, `.key` files
- credential-like environment values supplied by `JERKGRAM_TELEGRAM_API_ID`, `JERKGRAM_TELEGRAM_API_HASH`, `P12_PASSWORD`, `KEYCHAIN_PASSWORD`, `CERT_B64`, `PROF_B64`
- obvious GitHub/private token prefixes

Do not redact or rewrite source automatically. Failure requires correcting the release materialization path or credential injection architecture.

### Symlinks

- preserve retained relative symlinks only when their resolved target remains inside the materialized tree
- reject retained absolute symlinks
- reject retained relative symlinks that escape the materialized tree
- explicitly excluded generated symlinks such as root `bazel-*` may point outside the tree; they are recorded for private audit and are never copied into the public source snapshot

### Manifests

Manifest entries are sorted by UTF-8 path and include:

- path
- type (`file` or `symlink`)
- mode
- size
- SHA-256 for files
- symlink target for symlinks

The verifier checks that:

`internal materialized paths - approved exclusions == public source paths`

and that every retained file hash/mode/symlink target is identical.

### Deterministic archive

The tar stream must:

- sort paths
- normalize uid/gid to 0
- normalize uname/gname to empty strings
- normalize mtime to 0
- preserve file mode
- preserve safe symlinks

The resulting `.tar.xz` must hash identically across two exports of identical input on the same toolchain.

## Release metadata

Public release metadata contains only:

- Jerkgram version
- build number
- public source tag
- upstream repository/tag/commit
- source archive filename + SHA-256
- optional Stable IPA filename + SHA-256
- source manifest filename + SHA-256

It does not expose the private builder commit, internal patch-chain names, server paths, or signing identity.

## CLI

Exporter:

```text
python3 scripts/jerkgram_export_public_source.py \
  --materialized-tree work/swiftgram-src \
  --version 1.0.0 \
  --build-number 124 \
  --source-tag v1.0.0 \
  --output artifacts/public-source \
  [--ipa artifacts/Jerkgram-1.0.0.ipa]
```

`--source-tag` is optional and defaults to `v<version>`.

Verifier:

```text
python3 scripts/verify_jerkgram_public_source.py \
  --materialized-tree work/swiftgram-src \
  --export-dir artifacts/public-source
```

## CI integration boundary

No automatic CI integration in v1. The exporter becomes a release workflow step only after the exact final-source boundary immediately preceding compilation is frozen and a source/IPA provenance check is demonstrated on a real Stable candidate.
