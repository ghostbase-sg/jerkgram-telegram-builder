#!/bin/sh
set -e

TELEGRAM_REPO="https://github.com/TelegramMessenger/Telegram-iOS.git"
EXPECTED_COMMIT="fb0e62ba8a147f0821da6aa63c09da7d79a10111"
TELEGRAM_REF="$EXPECTED_COMMIT"

rm -rf work/swiftgram-src
mkdir -p work

echo "== Clone official Telegram-iOS $TELEGRAM_REF =="
git init work/swiftgram-src
git -C work/swiftgram-src remote add origin "$TELEGRAM_REPO"
git -C work/swiftgram-src fetch --depth 1 origin "$EXPECTED_COMMIT"
git -C work/swiftgram-src checkout --detach FETCH_HEAD

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
python3 - <<'PY'
import json
versions = json.load(open('versions.json'))
assert versions['app'] == '13.1.1', versions
assert versions['bazel'].split(':')[0] == '9.2.0', versions
assert versions['xcode'] == '27.1', versions
PY

echo "== Source prepared =="
git status --short
