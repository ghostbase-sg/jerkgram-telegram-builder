#!/bin/sh
set -e

TELEGRAM_REPO="https://github.com/TelegramMessenger/Telegram-iOS.git"
TELEGRAM_REF="release-12.9.2"
EXPECTED_COMMIT="6ad963e5b62d354da79040f388ae2b9132fb17b8"

rm -rf work
mkdir -p work

echo "== Clone official Telegram-iOS $TELEGRAM_REF =="
git clone --filter=blob:none --depth 1 --branch "$TELEGRAM_REF" "$TELEGRAM_REPO" work/swiftgram-src

cd work/swiftgram-src

ACTUAL_COMMIT="$(git rev-parse HEAD)"
echo "Expected commit: $EXPECTED_COMMIT"
echo "Actual commit:   $ACTUAL_COMMIT"

if [ "$ACTUAL_COMMIT" != "$EXPECTED_COMMIT" ]; then
    echo "ERROR: unexpected Official Telegram source commit"
    false
fi

echo "== Source ref =="
git log --oneline --decorate -n 3
cat versions.json 2>/dev/null || true

echo "== Source prepared =="
git status --short
