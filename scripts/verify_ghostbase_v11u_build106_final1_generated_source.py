#!/usr/bin/env python3

from pathlib import Path
import os
import re

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

FILES = {
    "bg": ROOT / (
        "submodules/TelegramUI/Components/PeerInfo/"
        "PeerInfoScreen/Sources/"
        "GhostBaseProfileFullscreenBackground.swift"
    ),

    "peer_item": ROOT / (
        "submodules/ItemListPeerItem/Sources/"
        "ItemListPeerItem.swift"
    ),

    "music_controller": ROOT / (
        "submodules/TelegramUI/Sources/"
        "OverlayAudioPlayerControllerNode.swift"
    ),

    "music_controls": ROOT / (
        "submodules/TelegramUI/Sources/"
        "OverlayAudioPlayerControlsNode.swift"
    ),

    "chat_text": ROOT / (
        "submodules/ChatPresentationInterfaceState/Sources/"
        "ChatTextFormat.swift"
    ),

    "enqueue": ROOT / (
        "submodules/TelegramCore/Sources/PendingMessages/"
        "EnqueueMessage.swift"
    ),

    "gift_options": ROOT / (
        "submodules/TelegramUI/Components/Gifts/"
        "GiftOptionsScreen/Sources/"
        "GiftOptionsScreen.swift"
    ),
}

texts = {}

print()
print("============================================================")
print("V11U BUILD106 FINAL1 MATERIALIZED SOURCE VERIFIER")
print("============================================================")

for name, path in FILES.items():
    if not path.is_file():
        print(f"FAIL: missing file [{name}] {path}")
        texts[name] = ""
    else:
        texts[name] = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

T = texts

passes = []
fails = []


def check(label, condition):
    if condition:
        passes.append(label)
        print(f"OK   : {label}")
    else:
        fails.append(label)
        print(f"FAIL : {label}")


def contains(file_key, text):
    return text in T[file_key]


def regex(file_key, pattern):
    return re.search(
        pattern,
        T[file_key],
        re.S,
    ) is not None


# ============================================================
# 1. BUILD105 CORE MUST SURVIVE
# ============================================================

print()
print("--- Build105 prerequisites ---")

check(
    "static avatar pipeline retained",
    contains(
        "bg",
        "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1",
    ),
)

check(
    "static avatar cache retained",
    contains(
        "bg",
        "GhostBase v1.1T BUILD97_STATIC_AVATAR_CACHE1",
    ),
)

check(
    "Build105 deleted-reply core retained",
    contains(
        "enqueue",
        "GhostBase v1.1T BUILD105_FULL1",
    ),
)

check(
    "deleted portable reply setting retained",
    contains(
        "enqueue",
        "GhostBase.Messages.DeletedPortableReplies",
    ),
)

check(
    "deleted media preservation retained",
    contains(
        "enqueue",
        "GhostBase.Messages.PreserveDeletedMedia",
    ),
)

check(
    "deleted media cache retained",
    contains(
        "enqueue",
        "GhostBaseDeletedMediaCache",
    ),
)

check(
    "original quoteable entities retained",
    contains(
        "enqueue",
        "ghostBaseOriginalQuoteableEntities",
    ),
)


# ============================================================
# 2. STATIC AVATAR BLUR
# ============================================================

print()
print("--- Static avatar blur ---")

check(
    "Build106 static blur marker",
    contains(
        "bg",
        "BUILD106_STATIC_AVATAR_BLUR1",
    ),
)

check(
    "old 0.24/0.38 blur alpha removed",
    not regex(
        "bg",
        r"blurView\.alpha\s*=\s*"
        r"reduced\s*\?\s*0\.24\s*:\s*0\.38",
    ),
)

check(
    "persistent blur alpha is 1.0",
    regex(
        "bg",
        r"self\.blurView\.alpha\s*=\s*1\.0",
    ),
)


# ============================================================
# 3. COMMON GROUPS
# ============================================================

print()
print("--- Common Groups ---")

check(
    "Build106 Common Groups marker",
    contains(
        "peer_item",
        "BUILD106_COMMON_GROUPS_OWNER1",
    ),
)

check(
    "late background owner respects displayBackground",
    regex(
        "peer_item",
        r"backgroundNode\.isHidden\s*=\s*"
        r"!item\.displayDecorations\s*"
        r"\|\|\s*"
        r"!item\.displayBackground",
    ),
)


# ============================================================
# 4. MUSIC
# ============================================================

print()
print("--- Music sheet ---")

check(
    "Build106 music moving-sheet marker",
    contains(
        "music_controller",
        "BUILD106_MUSIC_MOVING_SHEET1",
    ),
)

check(
    "history background uses sheetColor",
    regex(
        "music_controller",
        r"self\.historyBackgroundContentNode\s*"
        r"\.\s*backgroundColor\s*=\s*sheetColor",
    ),
)

check(
    "left moving surface uses sheetColor",
    regex(
        "music_controller",
        r"self\.historyFrameLeftOverlayNode\s*"
        r"\.\s*backgroundColor\s*=\s*sheetColor",
    ),
)

check(
    "right moving surface uses sheetColor",
    regex(
        "music_controller",
        r"self\.historyFrameRightOverlayNode\s*"
        r"\.\s*backgroundColor\s*=\s*sheetColor",
    ),
)

check(
    "top moving surface uses sheetColor",
    regex(
        "music_controller",
        r"self\.historyFrameTopOverlayNode\s*"
        r"\.\s*backgroundColor\s*=\s*sheetColor",
    ),
)

check(
    "extra header glass disabled",
    regex(
        "music_controller",
        r"ghostBaseHeaderGlassView\?"
        r"\.isHidden\s*=\s*true",
    ),
)

check(
    "extra header glass effect removed",
    regex(
        "music_controller",
        r"ghostBaseHeaderGlassView\?"
        r"\.effect\s*=\s*nil",
    ),
)

check(
    "Build106 controls marker",
    contains(
        "music_controls",
        "BUILD106_MUSIC_CONTROLS1",
    ),
)

check(
    "controls glass enabled by music controller",
    regex(
        "music_controller",
        r"controlsNode\s*"
        r"\.\s*ghostBaseGlassBackgroundEnabled"
        r"\s*=\s*true",
    ),
)


# ============================================================
# 5. CUSTOM / PREMIUM EMOJI
# ============================================================

print()
print("--- Custom / Premium emoji ---")

check(
    "Build106 custom emoji quote marker",
    contains(
        "chat_text",
        "BUILD106_CUSTOM_EMOJI_QUOTE1",
    ),
)

check(
    "quote transform preserves customEmoji",
    regex(
        "chat_text",
        r"else\s+if\s+key\s*==\s*"
        r"ChatTextInputAttributes\.customEmoji",
    ),
)


# ============================================================
# 6. PORTABLE DELETED REPLY AUTHOR
# ============================================================

print()
print("--- Portable deleted reply author ---")

check(
    "Build106 deleted-reply V2 marker",
    contains(
        "enqueue",
        "GhostBase v1.1U BUILD106_FINAL1",
    ),
)

check(
    "portable author marker",
    contains(
        "enqueue",
        "BUILD106_PORTABLE_AUTHOR1",
    ),
)

check(
    "author username stored in plan",
    contains(
        "enqueue",
        "let authorUsername: String?",
    ),
)

check(
    "public username TextUrl path",
    contains(
        "enqueue",
        'https://t.me/\\(authorUsername)',
    ),
)

check(
    "TextMention fallback exists",
    contains(
        "enqueue",
        "type: .TextMention(",
    )
    and contains(
        "enqueue",
        "peerId: mentionPeerId",
    ),
)

check(
    "author Bold entity exists",
    contains(
        "enqueue",
        "type: .Bold",
    ),
)


# ============================================================
# 7. STICKER RECOVERY
# ============================================================

print()
print("--- Sticker recovery ---")

check(
    "Build106 sticker recovery marker",
    contains(
        "enqueue",
        "BUILD106_STICKER_RECOVERY1",
    ),
)

check(
    "TGS cache extension",
    contains(
        "enqueue",
        'case "application/x-tgsticker":',
    ),
)

check(
    "WebM cache extension",
    contains(
        "enqueue",
        'case "video/webm":',
    ),
)

check(
    "WebP cache extension",
    contains(
        "enqueue",
        'case "image/webp":',
    ),
)

check(
    "file mimeType preserved",
    contains(
        "enqueue",
        "mimeType: file.mimeType",
    ),
)

check(
    "file attributes preserved",
    contains(
        "enqueue",
        "attributes: file.attributes",
    ),
)

check(
    "old sticker hard rejection removed",
    not regex(
        "enqueue",
        r"if\s+let\s+file\s*=\s*media\s+as\?\s*"
        r"TelegramMediaFile\s*,\s*"
        r"file\.isSticker\s*\{\s*"
        r"return\s+nil",
    ),
)


# ============================================================
# 8. ALBUM RECOVERY
# ============================================================

print()
print("--- Album recovery ---")

check(
    "Build106 album query marker",
    contains(
        "enqueue",
        "BUILD106_ALBUM_QUERY1",
    ),
)

check(
    "native Postbox getMessageGroup used",
    regex(
        "enqueue",
        r"getMessageGroup\s*\(\s*source\.id\s*\)",
    ),
)

check(
    "Build106 album recovery marker",
    contains(
        "enqueue",
        "BUILD106_ALBUM_RECOVERY1",
    ),
)

check(
    "album tail helper exists",
    contains(
        "enqueue",
        "ghostBaseBuildRecoveredAlbumTail(",
    ),
)

check(
    "forced localGroupingKey supported",
    contains(
        "enqueue",
        "forcedLocalGroupingKey:",
    ),
)

check(
    "new random localGroupingKey generated",
    regex(
        "enqueue",
        r"let\s+localGroupingKey\s*=\s*"
        r"Int64\.random\s*\(",
    ),
)

check(
    "grouped media reconstruction gate removed",
    not regex(
        "enqueue",
        r"guard\s+source\.groupingKey\s*==\s*nil",
    ),
)


# ============================================================
# 9. USER-ATTACHED MEDIA PRIORITY
# ============================================================

print()
print("--- User media priority ---")

check(
    "user-attached media priority retained",
    regex(
        "enqueue",
        r"userMedia\s*==\s*nil\s+else",
    ),
)


# ============================================================
# 10. LONG QUOTE / FORMATTING
# ============================================================

print()
print("--- Quote / formatting preservation ---")

check(
    "long quote collapse retained",
    regex(
        "enqueue",
        r"let\s+collapse\s*=\s*"
        r"sourceLength\s*>\s*320",
    ),
)

check(
    "original quote entities retained",
    contains(
        "enqueue",
        "ghostBaseOriginalQuoteableEntities(",
    ),
)

check(
    "UTF-16 entity shifting retained",
    contains(
        "enqueue",
        "ghostBaseShiftEntities(",
    ),
)


# ============================================================
# 11. NEW BEAR
# ============================================================

print()
print("--- New bear ---")

bear_descriptor = regex(
    "gift_options",
    r"GhostBaseSeasonalGiftDescriptor\s*\(\s*"
    r"id\s*:\s*6046178578163303744\s*,\s*"
    r"title\s*:\s*\"Мишка\"\s*,\s*"
    r"price\s*:\s*50\s*,\s*"
    r"stickerIndex\s*:\s*11\s*"
    r"\)",
)

check(
    "new bear is real seasonal descriptor",
    bear_descriptor,
)

check(
    "new bear descriptor occurs exactly once",
    T["gift_options"].count(
        "id: 6046178578163303744"
    ) == 1,
)

check(
    "DeletedGiftsStickers provider retained",
    contains(
        "gift_options",
        'reference: .name("DeletedGiftsStickers")',
    ),
)

check(
    "Football Bear predecessor retained",
    contains(
        "gift_options",
        "id: 5974210632977745012",
    )
    and contains(
        "gift_options",
        "stickerIndex: 10",
    ),
)


# ============================================================
# 12. SEASONAL GIFT CORE
# ============================================================

print()
print("--- Seasonal gift core ---")

for proof in (
    "GhostBase v1.0ZB Seasonal Gifts",
    "ghostBaseMakeSeasonalGifts",
    "ghostBaseMergeSeasonalGifts",
    "ghostBaseSeasonalGiftDescriptors",
):
    check(
        f"seasonal core: {proof}",
        contains(
            "gift_options",
            proof,
        ),
    )


# ============================================================
# RESULT
# ============================================================

print()
print("============================================================")
print("V11U BUILD106 VERIFIER RESULT")
print("============================================================")
print(f"PASS: {len(passes)}")
print(f"FAIL: {len(fails)}")

if fails:
    print()
    print("FAILED CHECKS:")
    for i, label in enumerate(fails, 1):
        print(f"{i:02d}. {label}")
else:
    print()
    print("BUILD106_FINAL1 GENERATED SOURCE OK")
    print()
    print("blur          : OK")
    print("Common Groups : OK")
    print("Music         : OK")
    print("author        : Bold + TextUrl/TextMention OK")
    print("custom emoji  : OK")
    print("stickers      : OK")
    print("albums        : OK")
    print("user media    : priority preserved")
    print("quote/entity  : preserved")
    print("new bear      : 6046178578163303744 / index 11 OK")
