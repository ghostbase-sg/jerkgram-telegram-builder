#!/bin/sh
set -e

SWIFTGRAM_REPO="https://github.com/TelegramMessenger/Telegram-iOS.git"
SWIFTGRAM_COMMIT="master"

rm -rf work
mkdir -p work

echo "== Clone official Telegram-iOS master =="
git clone --filter=blob:none --depth 1 "$SWIFTGRAM_REPO" work/swiftgram-src

cd work/swiftgram-src

echo "== Checkout commit =="
git checkout "$SWIFTGRAM_COMMIT"

echo "== Apply GhostBase patch =="
echo "== Skip GhostBase profile patch for official Telegram baseline =="

echo "== Source prepared =="
git status --short
