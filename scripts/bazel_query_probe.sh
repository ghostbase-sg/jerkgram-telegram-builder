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

echo "== patch sh_binary load =="
SH_LOAD='load("@bazel_tools//tools/build_defs/shell:shell.bzl", "sh_binary")'
if ! grep -q 'tools/build_defs/shell:shell.bzl' Telegram/BUILD; then
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
bazel query //Telegram:Swiftgram

echo "== target kind =="
bazel query --output=label_kind //Telegram:Swiftgram
