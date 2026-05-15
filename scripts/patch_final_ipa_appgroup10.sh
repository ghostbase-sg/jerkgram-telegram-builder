#!/bin/sh
set -e

IPA_IN="${1:-}"
if [ -z "$IPA_IN" ]; then
  echo "Usage: $0 path/to/GhostBase.ipa"
  exit 1
fi

case "$IPA_IN" in
  /*) IPA="$IPA_IN" ;;
  *) IPA="$(pwd)/$IPA_IN" ;;
esac

echo "== Final IPA AppGroup .10 patch =="
echo "IPA=$IPA"
test -f "$IPA"

T="$(mktemp -d)"
unzip -q "$IPA" -d "$T"

APP="$(find "$T/Payload" -maxdepth 1 -type d -name "*.app" | head -n 1)"
test -d "$APP"

EXE="$(/usr/libexec/PlistBuddy -c "Print CFBundleExecutable" "$APP/Info.plist")"
BIN="$APP/$EXE"
test -f "$BIN"

echo "APP=$APP"
echo "BIN=$BIN"

python3 - "$BIN" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
data = p.read_bytes()

old = b"group.4a348a9b186b700c.10"
new = b"group.4a348a9b186b700c.1\x00"

count = data.count(old)
print("found .10 occurrences:", count)

if count:
    p.write_bytes(data.replace(old, new))
    print("patched .10 occurrences:", count)
else:
    print("No .10 found")
PY

echo "-- verify forbidden .10 absent --"
if LC_ALL=C grep -Rao 'group.4a348a9b186b700c.10' "$APP"; then
  echo "BAD: .10 still present"
  exit 1
else
  echo "OK: .10 absent"
fi

echo "-- final AppGroups --"
LC_ALL=C grep -RaoE 'group\.4a348a9b186b700c\.[0-9]+' "$APP" | sort | uniq -c || true

OUT="$T/patched.ipa"
cd "$T"
zip -0qry "$OUT" Payload
mv -f "$OUT" "$IPA"

ls -lh "$IPA"
echo "== Final IPA AppGroup .10 patch OK =="
