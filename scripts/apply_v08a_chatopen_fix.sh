#!/bin/sh
set -e

SRC="work/swiftgram-src"

CHATLIST="$SRC/submodules/ChatListUI/Sources/ChatListController.swift"
NAV="$SRC/submodules/TelegramUI/Sources/NavigateToChatController.swift"

echo "== GhostBase v0.8A ChatOpen Route Fix =="

test -f "$CHATLIST"
test -f "$NAV"

python3 - <<'PY'
from pathlib import Path

chatlist = Path("work/swiftgram-src/submodules/ChatListUI/Sources/ChatListController.swift")
s = chatlist.read_text()

old = "#if true && DEBUG"
new = "#if false && DEBUG"

if old in s:
    s = s.replace(old, new, 1)
elif new in s:
    pass
else:
    raise SystemExit("ChatListController: DEBUG guard marker not found")

chatlist.write_text(s)

nav = Path("work/swiftgram-src/submodules/TelegramUI/Sources/NavigateToChatController.swift")
s = nav.read_text()

marker = "// GhostBase v0.8A: force simple push route for chat open test"
if marker not in s:
    needle = "            let resolvedKeepStack: Bool\n            switch params.keepStack {"
    if needle not in s:
        raise SystemExit("NavigateToChatController: keepStack block start not found")
    start = s.index(needle)
    end = s.index("            if resolvedKeepStack {", start)
    replacement = f"            {marker}\n            let resolvedKeepStack: Bool = true\n"
    s = s[:start] + replacement + s[end:]

nav.write_text(s)
PY

echo "-- verify ChatListController --"
grep -n "#if false && DEBUG\|ChatControllerCount" "$CHATLIST" | head

echo "-- verify NavigateToChatController --"
grep -n "GhostBase v0.8A\|resolvedKeepStack" "$NAV" | head -20

echo "== v0.8A patch OK =="
