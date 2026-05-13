#!/bin/sh
set -e

SWIFTGRAM_REPO="https://github.com/Swiftgram/Telegram-iOS.git"
SWIFTGRAM_COMMIT="02fac48ed1181266780ada956a2f547f2f3edf57"

rm -rf work
mkdir -p work

echo "== Clone Swiftgram =="
git clone --filter=blob:none "$SWIFTGRAM_REPO" work/swiftgram-src

cd work/swiftgram-src

echo "== Checkout commit =="
git checkout "$SWIFTGRAM_COMMIT"

echo "== Apply GhostBase patch =="
git apply ../../patches/ghostbase_v1_main_profile.patch

echo "== Source prepared =="
git status --short
