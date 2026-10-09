#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/materialize_jg13.py
python3 scripts/configure_jg13.py
python3 scripts/verify_jg13_source.py
python3 tests/run_jg13_ping_policy.py
python3 scripts/pin_jg13_dependencies.py
cd work/swiftgram-src
git submodule sync --recursive
git submodule update --init --recursive --depth 1
python3 ../../scripts/pin_jg13_dependencies.py --verify
"${BAZEL_BIN:-bazelisk}" build \
  -c opt \
  --ios_multi_cpus=arm64 \
  --check_direct_dependencies=off \
  --//Telegram:disableExtensions=false \
  --//Telegram:disableProvisioningProfiles=true \
  --features=disable_legacy_signing \
  --define=buildNumber=142 \
  //Telegram:Telegram
test -f bazel-bin/Telegram/Telegram.ipa
cd ../..
python3 scripts/package_jg13.py work/swiftgram-src/bazel-bin/Telegram/Telegram.ipa
