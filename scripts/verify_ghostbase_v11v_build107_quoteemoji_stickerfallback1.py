#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

CONVERSION = (
    ROOT
    / "submodules/TextFormat/Sources/"
    "ChatInputContentConversion.swift"
)

CHAT_TEXT = (
    ROOT
    / "submodules/ChatPresentationInterfaceState/Sources/"
    "ChatTextFormat.swift"
)

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/PendingMessages/"
    "EnqueueMessage.swift"
)

for path in (CONVERSION, CHAT_TEXT, ENQUEUE):
    if not path.is_file():
        raise SystemExit(
            f"[V11V verifier] missing: {path}"
        )

conversion = CONVERSION.read_text(
    encoding="utf-8",
    errors="replace",
)

chat_text = CHAT_TEXT.read_text(
    encoding="utf-8",
    errors="replace",
)

enqueue = ENQUEUE.read_text(
    encoding="utf-8",
    errors="replace",
)

checks = []


def check(label, ok):
    checks.append((label, bool(ok)))
    print(
        ("OK   : " if ok else "FAIL : ")
        + label
    )


print()
print("============================================================")
print("V11V BUILD107 MATERIALIZED SOURCE VERIFIER")
print("============================================================")

print()
print("--- Premium/custom emoji ---")

check(
    "V11U selection->Quote customEmoji preservation retained",
    (
        "GhostBase v1.1U "
        "BUILD106_CUSTOM_EMOJI_QUOTE1"
    )
    in chat_text,
)

check(
    "customEmoji survives quote transformation",
    (
        "else if key == "
        "ChatTextInputAttributes.customEmoji"
    )
    in chat_text,
)

check(
    "Build107 structured quote projection marker",
    (
        "GhostBase v1.1V "
        "BUILD107_BLOCKQUOTE_CUSTOM_EMOJI1"
    )
    in conversion,
)

check(
    "expanded quote no longer flattens through plainText",
    (
        "result.append("
        "NSAttributedString(string: bq.content.plainText))"
    )
    not in conversion,
)

check(
    "expanded quote preserves semantic attributed content",
    (
        "result.append("
        "attributedString(from: bq.content))"
    )
    in conversion,
)

check(
    "customEmoji semantic projection exists",
    (
        "ChatTextInputAttributes.customEmoji"
        in conversion
    ),
)


print()
print("--- Deleted sticker ---")

check(
    "Build107 sticker fallback marker",
    (
        "GhostBase v1.1V "
        "BUILD107_STICKER_TEXT_FALLBACK1"
    )
    in enqueue,
)

check(
    "sticker reconstructed-media rejection restored",
    '''if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }'''
    in enqueue,
)

check(
    "Build106 native sticker recovery removed",
    "BUILD106_STICKER_RECOVERY1"
    not in enqueue,
)

check(
    "TGS cache extension removed",
    'case "application/x-tgsticker":'
    not in enqueue,
)

check(
    "WebP cache extension removed",
    'case "image/webp":'
    not in enqueue,
)

check(
    "WebM cache extension removed",
    'case "video/webm":'
    not in enqueue,
)

check(
    'sticker textual label remains "Стикер"',
    'return "Стикер"'
    in enqueue,
)


print()
print("--- Build106 core retained ---")

for label, proof in (
    (
        "Build106 deleted reply V2",
        "GhostBase v1.1U BUILD106_FINAL1",
    ),
    (
        "portable author",
        "BUILD106_PORTABLE_AUTHOR1",
    ),
    (
        "album query",
        "BUILD106_ALBUM_QUERY1",
    ),
    (
        "album recovery",
        "BUILD106_ALBUM_RECOVERY1",
    ),
    (
        "album tail",
        "ghostBaseBuildRecoveredAlbumTail(",
    ),
    (
        "user-attached media priority",
        "userMedia == nil else",
    ),
    (
        "long quote collapse",
        "let collapse = sourceLength > 320",
    ),
    (
        "entity preservation",
        "ghostBaseOriginalQuoteableEntities(",
    ),
):
    check(
        label,
        proof in enqueue,
    )


passed = sum(
    1 for _, ok in checks if ok
)

failed = [
    label
    for label, ok in checks
    if not ok
]

print()
print("============================================================")
print("V11V BUILD107 RESULT")
print("============================================================")
print("PASS:", passed)
print("FAIL:", len(failed))

if failed:
    print()
    for index, label in enumerate(failed, 1):
        print(f"{index:02d}. {label}")

    raise SystemExit(1)

print()
print("BUILD107 MATERIALIZED SOURCE OK")
print(
    "premium emoji : "
    "Quote + inside Quote preserved"
)
print(
    'deleted sticker: "Стикер" textual fallback'
)
print(
    "Build106 core : retained"
)
