#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# One exact source projection and one current native/component gate.
# Exhaustive historical suites remain in no-ads-native.yml (manual regression).
python3 scripts/materialize_jg132_product.py
python3 tests/run_jg132_post181.py --require-native --require-full-source
python3 scripts/pin_jg13_dependencies.py
cd work/swiftgram-src
git submodule sync --recursive
git submodule update --init --recursive --depth 1
python3 ../../scripts/pin_jg13_dependencies.py --verify
python3 ../../scripts/prepare_jg13_build_rules.py
# A build action may emit an IPA before a later action fails. Preserve it too.
# The freshly cloned source guarantees this cannot pick up an earlier run's IPA.
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
  -c opt \
  --ios_multi_cpus=arm64 \
  --check_direct_dependencies=off \
  --//Telegram:disableExtensions=false \
  --//Telegram:disableProvisioningProfiles=true \
  --features=disable_legacy_signing \
  --define=buildNumber=182 \
  //Telegram:Telegram
test -f bazel-bin/Telegram/Telegram.ipa
# Inspect retained build actions without a second build or target analysis.
# Only optimization tokens are printed; complete command lines stay temporary.
optimization_query=$(mktemp)
if "${BAZEL_BIN:-bazelisk}" aquery --skyframe_state --output=textproto \
  --include_commandline --include_param_files --include_artifacts=false \
  'inputs(".*ChatTextInputPanelNode[.]swift", mnemonic("SwiftCompile"))' \
  > "$optimization_query" 2>/dev/null; then
  python3 ../../scripts/report_jg13_swift_optimization.py "$optimization_query" || true
else
  printf '%s\n' 'Swift optimization action query unavailable; no conclusion.'
fi
rm -f "$optimization_query"
cd ../..
python3 scripts/package_jg13.py work/swiftgram-src/bazel-bin/Telegram/Telegram.ipa
