#!/bin/sh
set -e

TELEGRAM_REPO="https://github.com/TelegramMessenger/Telegram-iOS.git"
TELEGRAM_REF="release-12.8"

rm -rf work
mkdir -p work

echo "== Clone official Telegram-iOS $TELEGRAM_REF =="
git clone --filter=blob:none --depth 1 --branch "$TELEGRAM_REF" "$TELEGRAM_REPO" work/swiftgram-src

cd work/swiftgram-src

echo "== Source ref =="
git log --oneline --decorate -n 3
cat versions.json 2>/dev/null || true

echo "== Source prepared =="
git status --short
