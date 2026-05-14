#!/bin/sh
set -e

SRC="work/swiftgram-src"

CHATLIST="$SRC/submodules/ChatListUI/Sources/ChatListController.swift"
NAV="$SRC/submodules/TelegramUI/Sources/NavigateToChatController.swift"

echo "== GhostBase v0.8A.1 ChatOpen Route Fix =="

test -f "$CHATLIST"
test -f "$NAV"

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

nav = Path("work/swiftgram-src/submodules/TelegramUI/Sources/NavigateToChatController.swift")
s = nav.read_text()

start_markers = [
    "            // GhostBase v0.8A: force simple push route for chat open test",
    "            // GhostBase v0.8A.1: force simple push route for chat open test",
    "            let resolvedKeepStack: Bool\n            switch params.keepStack {"
]

start = None
for marker in start_markers:
    if marker in s:
        start = s.index(marker)
        break

if start is None:
    raise SystemExit("NavigateToChatController: keepStack block start not found")

end_marker = "            if let activateInput = params.activateInput {"
end = s.index(end_marker, start)

replacement = """            // GhostBase v0.8A.1: force simple push route for chat open test
            if let pushController = params.pushController {
                pushController(controller, params.animated, {
                    params.completion(controller)
                })
            } else {
                params.navigationController.pushViewController(controller, animated: params.animated, completion: {
                    params.completion(controller)
                })
            }
"""

s = s[:start] + replacement + s[end:]

bad_patterns = [
    "let resolvedKeepStack: Bool = true",
    "if resolvedKeepStack",
    "switch params.keepStack"
]

for bad in bad_patterns:
    if bad in s:
        raise SystemExit(f"BAD PATCH: still contains {bad}")

nav.write_text(s)
PY

echo "-- verify ChatListController --"
grep -n "#if false && DEBUG\|ChatControllerCount" "$CHATLIST" | head

echo "-- verify NavigateToChatController --"
grep -n "GhostBase v0.8A.1" "$NAV" | head

if grep -n "let resolvedKeepStack: Bool = true\|if resolvedKeepStack\|switch params.keepStack" "$NAV"; then
  echo "BAD PATCH: unsafe keepStack code still present"
  exit 1
fi

echo "== v0.8A.1 patch OK =="
