#!/usr/bin/env bash
# Combined current product + Analytics v3 + Profile Observer; workflow packages the IPA.
set -euo pipefail
cd "$(dirname "$0")/.."
product_build=$(python3 -c 'import json; print(json.load(open("jerkgram-migration.json"))["build_number"])')
export DEVELOPER_DIR=/Applications/Xcode_27.1.app/Contents/Developer
export USE_BAZEL_VERSION=9.2.0
test "$(xcodebuild -version | head -1)" = "Xcode 27.1"
xcodebuild -version
"${BAZEL_BIN:-bazelisk}" version
python3 scripts/materialize_jg132_product.py
# Current product ownership/native gate describes the exact parent, before v3.
python3 tests/run_jg132_post181.py --require-native --require-full-source
python3 scripts/apply_jerkgram_analytics_v3.py
python3 scripts/verify_jerkgram_analytics_v3.py
JERKGRAM_SOURCE_ROOT="$PWD/work/swiftgram-src" python3 scripts/apply_jerkgram_profile_observer_v1.py
JERKGRAM_SOURCE_ROOT="$PWD/work/swiftgram-src" python3 scripts/verify_jerkgram_profile_observer_v1.py
python3 scripts/pin_jg13_dependencies.py
cd work/swiftgram-src
git submodule sync --recursive
git submodule update --init --recursive --depth 1
python3 ../../scripts/pin_jg13_dependencies.py --verify
python3 ../../scripts/prepare_jg13_build_rules.py
compiled_ipa="$PWD/bazel-bin/Telegram/Telegram.ipa"
recovery_script="$PWD/../../scripts/preserve_jg13_ipa.py"
preserve_compiled_ipa() {
  local result=$?
  trap - EXIT
  if [ -f "$compiled_ipa" ]; then
    python3 "$recovery_script" "$compiled_ipa" || true
  fi
  exit "$result"
}
trap preserve_compiled_ipa EXIT
"${BAZEL_BIN:-bazelisk}" build \
  -c opt --ios_multi_cpus=arm64 --check_direct_dependencies=off \
  --experimental_ui_max_stdouterr_bytes=10485760 \
  --//Telegram:disableExtensions=false --//Telegram:disableProvisioningProfiles=true \
  --features=disable_legacy_signing --define=buildNumber="$product_build" //Telegram:Telegram
python3 ../../scripts/verify_jerkgram_analytics_v3.py
JERKGRAM_SOURCE_ROOT="$PWD" python3 ../../scripts/verify_jerkgram_profile_observer_v1.py
