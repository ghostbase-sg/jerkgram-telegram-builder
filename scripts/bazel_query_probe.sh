#!/usr/bin/env bash
set -euo pipefail

cd work/swiftgram-src

echo "== init bazel rule submodules =="
git submodule sync --recursive
git submodule update --init --recursive --depth 1 build-system/bazel-rules/apple_support
git submodule update --init --recursive --depth 1 build-system/bazel-rules/rules_apple
git submodule update --init --recursive --depth 1 build-system/bazel-rules/rules_swift
git submodule update --init --recursive --depth 1 build-system/bazel-rules/rules_xcodeproj
git submodule update --init --recursive --depth 1 build-system/bazel-rules/sourcekit-bazel-bsp

echo "== create build configuration repo =="
rm -rf build-input/configuration-repository
mkdir -p build-input
cp -R build-system/example-configuration build-input/configuration-repository

printf '%s\n' 'module(name = "build_configuration", version = "0.0.0")' > build-input/configuration-repository/MODULE.bazel

cat >> build-input/configuration-repository/variables.bzl <<'EOF'

# Added by GhostBase builder for Bazel compatibility
telegram_bazel_path = "."
telegram_use_xcode_managed_codesigning = False
EOF

echo "== variables after patch =="
grep -nE "telegram_bazel_path|telegram_use_xcode_managed_codesigning|telegram_bundle_id|telegram_team_id" build-input/configuration-repository/variables.bzl

echo "== patch MODULE.bazel with rules_shell =="
python3 - <<'PY'
from pathlib import Path

p = Path("MODULE.bazel")
s = p.read_text()

line = 'bazel_dep(name = "rules_shell", version = "0.5.0")\n'

if 'bazel_dep(name = "rules_shell"' not in s:
    marker = 'bazel_dep(name = "platforms", version = "0.0.11")\n'
    if marker in s:
        s = s.replace(marker, marker + line)
    else:
        s = line + s

p.write_text(s)
PY

grep -n 'rules_shell' MODULE.bazel

echo "== patch sh_binary load =="
SH_LOAD='load("@rules_shell//shell:sh_binary.bzl", "sh_binary")'
if ! grep -q '@rules_shell//shell:sh_binary.bzl' Telegram/BUILD; then
  tmp="$(mktemp)"
  printf '%s\n' "$SH_LOAD" > "$tmp"
  cat Telegram/BUILD >> "$tmp"
  mv "$tmp" Telegram/BUILD
fi

echo "== Telegram BUILD around 990 =="
sed -n '985,1005p' Telegram/BUILD

echo "== bazel version =="
bazel --version

echo "== query target =="
bazel query --check_direct_dependencies=off //Telegram:Swiftgram

echo "== target kind =="
bazel query --check_direct_dependencies=off --output=label_kind //Telegram:Swiftgram
