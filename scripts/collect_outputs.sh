#!/usr/bin/env bash
set -euo pipefail

OUT="$GITHUB_WORKSPACE/artifacts"
rm -rf "$OUT"
mkdir -p "$OUT"

if [ -d work/swiftgram-src ]; then cd work/swiftgram-src; fi

echo "== bazel output dirs =="
bazelisk info bazel-bin | tee "$OUT/bazel-bin-path.txt"
BIN="$(bazelisk info bazel-bin)"

echo "== cquery files =="
bazelisk cquery //Telegram:Swiftgram --output=files \
  > "$OUT/cquery_files.txt" || true

echo "== find possible outputs =="
find "$BIN" -maxdepth 12 \( \
  -name "*.ipa" -o \
  -name "*.zip" -o \
  -name "*.app" -o \
  -name "*Swiftgram*" -o \
  -name "*Telegram*" \
\) -print | tee "$OUT/find_outputs.txt" || true

while IFS= read -r f; do
  [ -e "$f" ] || continue
  if [ -f "$f" ]; then
    cp -v "$f" "$OUT/$(basename "$f")" || true
  elif [ -d "$f" ] && echo "$f" | grep -q '\.app$'; then
    ditto -c -k --keepParent "$f" "$OUT/$(basename "$f").zip" || true
  fi
done < "$OUT/find_outputs.txt"

echo "== collected =="
find "$OUT" -maxdepth 2 -type f -print
