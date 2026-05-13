#!/usr/bin/env bash
set -euo pipefail

export USE_BAZEL_VERSION="${USE_BAZEL_VERSION:-7.6.1}"
BAZEL_BIN="${BAZEL_BIN:-bazelisk}"

cd work/swiftgram-src

echo "== bazelisk / bazel =="
which "$BAZEL_BIN"
"$BAZEL_BIN" --version || true

echo
echo "== init bazel rule submodules =="
git submodule sync --recursive

git submodule update --init --recursive --depth 1 \
  build-system/bazel-rules/apple_support \
  build-system/bazel-rules/rules_apple \
  build-system/bazel-rules/rules_swift \
  build-system/bazel-rules/rules_xcodeproj \
  build-system/bazel-rules/sourcekit-bazel-bsp

echo
echo "== submodules status =="
git submodule status build-system/bazel-rules/*

echo
echo "== create build configuration repo =="
rm -rf build-input/configuration-repository
mkdir -p build-input
cp -R build-system/example-configuration build-input/configuration-repository

printf '%s\n' 'module(name = "build_configuration", version = "0.0.0")' \
  > build-input/configuration-repository/MODULE.bazel

cat >> build-input/configuration-repository/variables.bzl <<'EOF'

# Added by GhostBase builder for Bazel compatibility
telegram_bazel_path = "."
telegram_use_xcode_managed_codesigning = False
EOF

echo
echo "== config variables =="
grep -nE "telegram_bundle_id|telegram_team_id|telegram_aps_environment|telegram_enable_siri|telegram_enable_icloud|telegram_enable_watch|telegram_bazel_path|telegram_use_xcode_managed_codesigning" \
  build-input/configuration-repository/variables.bzl

echo
echo "== Telegram BUILD target hints =="
grep -nE 'name = "Swiftgram"|ios_application|disableExtensions|TelegramEntitlements|provisioning_profile' Telegram/BUILD | head -140

echo
echo "== query target =="
"$BAZEL_BIN" query //Telegram:Swiftgram

echo
echo "== target kind =="
"$BAZEL_BIN" query --output=label_kind //Telegram:Swiftgram

echo
echo "== package targets =="
"$BAZEL_BIN" query 'kind(rule, //Telegram:*)' | head -120
