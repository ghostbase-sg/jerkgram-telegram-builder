#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

ENQUEUE = ROOT / (
    "submodules/TelegramCore/Sources/PendingMessages/"
    "EnqueueMessage.swift"
)

BUILD107_MARKER = "GhostBase v1.1V BUILD107_STICKER_TEXT_FALLBACK1"
BUILD121_MARKER = "Jerkgram v1.2J BUILD121_NATIVE_STICKER_RECOVERY1"

if not ENQUEUE.is_file():
    raise RuntimeError(f"[BUILD121] missing source: {ENQUEUE}")

enqueue = ENQUEUE.read_text(encoding="utf-8")

if BUILD121_MARKER in enqueue:
    print("[BUILD121] native sticker recovery already materialized")
    raise SystemExit(0)

for proof in (
    "GhostBase v1.1U BUILD106_FINAL1",
    "BUILD106_ALBUM_RECOVERY1",
    "BUILD106_PORTABLE_AUTHOR1",
    BUILD107_MARKER,
    "mimeType: file.mimeType",
    "attributes: file.attributes",
):
    if proof not in enqueue:
        raise RuntimeError(f"[BUILD121] prerequisite missing: {proof}")

hard_rejection = re.compile(
    r"^[ \t]*// MARK: GhostBase v1\.1V BUILD107_STICKER_TEXT_FALLBACK1\n"
    r"^[ \t]*// Deleted stickers intentionally remain textual portable replies\.\n"
    r"^[ \t]*// Do not reconstruct or reupload sticker media\.\n"
    r"^[ \t]*if let file = media as\? TelegramMediaFile, file\.isSticker \{\n"
    r"^[ \t]*return nil\n"
    r"^[ \t]*\}\n\n",
    re.M,
)

replacement = (
    "    // MARK: Jerkgram v1.2J BUILD121_NATIVE_STICKER_RECOVERY1\n"
    "    // Preserve the original TelegramMediaFile mimeType + attributes and\n"
    "    // let the existing deleted-media reconstruction path rebuild it.\n"
    "    // The textual Sticker label remains only as the missing-media fallback.\n\n"
)

enqueue, count = hard_rejection.subn(replacement, enqueue, count=1)
if count != 1:
    raise RuntimeError(
        f"[BUILD121] Build107 sticker rejection: expected 1, found {count}"
    )

mime_anchor = '''                case "video/mp4":
                    ext = "mp4"
'''
if enqueue.count(mime_anchor) != 1:
    raise RuntimeError(
        "[BUILD121] video/mp4 cache anchor: "
        f"expected 1, found {enqueue.count(mime_anchor)}"
    )

for mime in ("video/webm", "application/x-tgsticker", "image/webp"):
    if f'case "{mime}":' in enqueue:
        raise RuntimeError(f"[BUILD121] unexpected pre-existing MIME case: {mime}")

mime_replacement = mime_anchor + '''                case "video/webm":
                    ext = "webm"
                case "application/x-tgsticker":
                    ext = "tgs"
                case "image/webp":
                    ext = "webp"
'''
enqueue = enqueue.replace(mime_anchor, mime_replacement, 1)

proofs = (
    ("Build121 marker", BUILD121_MARKER in enqueue),
    ("Build107 hard rejection removed", BUILD107_MARKER not in enqueue),
    (
        "sticker return-nil removed",
        re.search(
            r"if let file = media as\? TelegramMediaFile,\s*"
            r"file\.isSticker\s*\{\s*return nil",
            enqueue,
            re.S,
        ) is None,
    ),
    ("WebM extension", enqueue.count('case "video/webm":') == 1),
    ("TGS extension", enqueue.count('case "application/x-tgsticker":') == 1),
    ("WebP extension", enqueue.count('case "image/webp":') == 1),
    ("mimeType preserved", "mimeType: file.mimeType" in enqueue),
    ("attributes preserved", "attributes: file.attributes" in enqueue),
    ("album retained", "BUILD106_ALBUM_RECOVERY1" in enqueue),
    ("portable author retained", "BUILD106_PORTABLE_AUTHOR1" in enqueue),
    (
        "textual fallback retained",
        ('return "Sticker"' in enqueue) or ('return "Стикер"' in enqueue),
    ),
)
failed = [label for label, ok in proofs if not ok]
if failed:
    raise RuntimeError("[BUILD121] final proof failure: " + ", ".join(failed))

ENQUEUE.write_text(enqueue, encoding="utf-8")
print("[BUILD121] native deleted-sticker reconstruction restored")
print("[BUILD121] WebP/TGS/WebM cache extensions restored")
print("[BUILD121] Build107 quote/custom-emoji scope untouched")
