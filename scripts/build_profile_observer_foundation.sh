#!/usr/bin/env bash
# Current product + observer full app compilation; no release packaging/publication.
set -euo pipefail
cd "$(dirname "$0")/.."
export DEVELOPER_DIR=/Applications/Xcode_27.1.app/Contents/Developer
export USE_BAZEL_VERSION=9.2.0
test "$(xcodebuild -version | head -1)" = "Xcode 27.1"
xcodebuild -version
xcrun --sdk iphoneos --show-sdk-version
"${BAZEL_BIN:-bazelisk}" version
python3 scripts/materialize_profile_observer_foundation.py --require-native
python3 scripts/pin_jg13_dependencies.py
cd work/swiftgram-src
git submodule sync --recursive
git submodule update --init --recursive --depth 1
python3 ../../scripts/pin_jg13_dependencies.py --verify
python3 ../../scripts/prepare_jg13_build_rules.py
"${BAZEL_BIN:-bazelisk}" build \
  -c opt --ios_multi_cpus=arm64 --check_direct_dependencies=off \
  --//Telegram:disableExtensions=false --//Telegram:disableProvisioningProfiles=true \
  --features=disable_legacy_signing --define=buildNumber=183 //Telegram:Telegram
cd ../..
python3 - <<'PY'
import json
from pathlib import Path
path = Path('artifacts/profile-observer-materialization.json')
evidence = json.loads(path.read_text())
assert evidence['observer_materialized']
evidence['native_app_compile'] = 'passed-full-app-Xcode27.1-Bazel9.2.0'
path.write_text(json.dumps(evidence, indent=2) + '\n')
PY
