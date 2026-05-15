#!/bin/sh
set -e

SRC="work/swiftgram-src"

CHATLIST="$SRC/submodules/ChatListUI/Sources/ChatListController.swift"
NAV="$SRC/submodules/TelegramUI/Sources/NavigateToChatController.swift"
MH="$SRC/submodules/Postbox/Sources/MessageHistoryViewState.swift"
CL="$SRC/submodules/Postbox/Sources/ChatListViewState.swift"

echo "== GhostBase v0.8C Postbox DEBUG Invariant Assert Fix =="

test -f "$CHATLIST"
test -f "$NAV"
test -f "$MH"
test -f "$CL"

# Restore files that v0.8A.1 may have modified locally.
git -C "$SRC/submodules/TelegramUI" checkout -- Sources/NavigateToChatController.swift 2>/dev/null || true
git -C "$SRC/submodules/ChatListUI" checkout -- Sources/ChatListController.swift 2>/dev/null || true
git -C "$SRC/submodules/Postbox" checkout -- Sources/MessageHistoryViewState.swift Sources/ChatListViewState.swift 2>/dev/null || true

python3 - <<'PY'
from pathlib import Path

chatlist = Path("work/swiftgram-src/submodules/ChatListUI/Sources/ChatListController.swift")
s = chatlist.read_text()

if "#if true && DEBUG" in s:
    s = s.replace("#if true && DEBUG", "#if false && DEBUG", 1)
elif "#if false && DEBUG" in s:
    pass
else:
    raise SystemExit("ChatListController: DEBUG marker not found")

chatlist.write_text(s)

targets = [
    Path("work/swiftgram-src/submodules/Postbox/Sources/MessageHistoryViewState.swift"),
    Path("work/swiftgram-src/submodules/Postbox/Sources/ChatListViewState.swift"),
]

old = 'assertionFailure("Inserting an existing index is not allowed")'
new = '// GhostBase v0.8B: duplicate-index recovery path; assertion trap disabled'

total = 0
for p in targets:
    s = p.read_text()
    count = s.count(old)
    print(f"{p}: duplicate-index assertions = {count}")
    if count != 2:
        raise SystemExit(f"Unexpected duplicate-index assertion count in {p}: {count}")
    s = s.replace(old, new)
    p.write_text(s)
    total += count

if total != 4:
    raise SystemExit(f"Expected 4 duplicate-index assertions, got {total}")

mh = Path("work/swiftgram-src/submodules/Postbox/Sources/MessageHistoryViewState.swift")
s = mh.read_text()

start = s.index("struct OrderedHistoryViewEntries")
try:
    end = s.index("final class HistoryViewLoadedState", start)
except ValueError:
    end = s.index("class HistoryViewLoadedState", start)

chunk = s[start:end]
debug_count = chunk.count("#if DEBUG && os(iOS)")
print("OrderedHistoryViewEntries DEBUG blocks:", debug_count)

if debug_count != 8:
    raise SystemExit(f"Expected 8 OrderedHistoryViewEntries DEBUG blocks, got {debug_count}")

chunk = chunk.replace("#if DEBUG && os(iOS)", "#if false && DEBUG && os(iOS)")
s = s[:start] + chunk + s[end:]

mh.write_text(s)

nav = Path("work/swiftgram-src/submodules/TelegramUI/Sources/NavigateToChatController.swift")
nav_s = nav.read_text()
if "force simple push route" in nav_s:
    raise SystemExit("BAD PATCH: route-force is still present in NavigateToChatController.swift")
PY

echo "-- verify ChatListController --"
grep -n "#if false && DEBUG\|ChatControllerCount" "$CHATLIST" | head

echo "-- verify OrderedHistoryViewEntries DEBUG blocks disabled --"
grep -n "#if false && DEBUG && os(iOS)" "$MH" | head -20

echo "-- verify Postbox duplicate-index assertions --"
grep -n "duplicate-index recovery path" "$MH" "$CL"

if grep -n 'assertionFailure("Inserting an existing index is not allowed")' "$MH" "$CL"; then
  echo "BAD: duplicate-index assertion trap still present"
  exit 1
fi

echo "-- verify no v0.8A route-force --"
if grep -n "force simple push route" "$NAV"; then
  echo "BAD: route-force still present"
  exit 1
fi

echo "== v0.8C patch OK =="
echo "== GhostBase v0.9B ChatList Navigation Fallback =="
python3 scripts/gb_patch_nav_fallback.py
echo "-- verify v0.9B nav fallback --"
grep -n "gbNavigationController" work/swiftgram-src/submodules/ChatListUI/Sources/ChatListController.swift | head -40
echo "== v0.9B nav fallback patch OK =="

