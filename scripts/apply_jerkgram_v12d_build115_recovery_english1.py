#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd())
        )
    )
).resolve()

ENQUEUE = (
    ROOT
    / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift"
)

MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_RECOVERY_ENGLISH1"
)


REPLACEMENTS = (
    ('return "Альбом"', 'return "Album"'),
    ('return "Опрос"', 'return "Poll"'),
    ('return "📍 Геолокация"', 'return "📍 Location"'),
    ('return "👤 Контакт"', 'return "👤 Contact"'),
    ('return "🎲 Бросок кубика"', 'return "🎲 Dice"'),
    ('return "Список задач"', 'return "Task List"'),
    ('return "📷 Фотография"', 'return "📷 Photo"'),
    ('return "Стикер"', 'return "Sticker"'),
    ('return "🎙 Голосовое сообщение"', 'return "🎙 Voice Message"'),
    ('return "🎥 Видеосообщение"', 'return "🎥 Video Message"'),
    ('return "🎬 Видео"', 'return "🎬 Video"'),
    ('return "🎵 Аудиофайл"', 'return "🎵 Audio"'),
    ('return "📎 Файл: \\(name)"', 'return "📎 File: \\(name)"'),
    ('return "📎 Файл"', 'return "📎 File"'),
    ('return "Вложение"', 'return "Attachment"'),
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 recovery English] "
            + message
        )


def function_bounds(text, signature):
    start = text.find(signature)
    require(start >= 0, "function missing: " + signature)

    brace = text.find("{", start)
    require(brace >= 0, "function brace missing")

    depth = 0
    in_string = False
    escaped = False

    for index in range(brace, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, brace, index + 1

    raise RuntimeError(
        "[Build115 recovery English] "
        "function closing brace missing"
    )


def main():
    require(ENQUEUE.is_file(), "EnqueueMessage.swift missing")
    text = ENQUEUE.read_text(encoding="utf-8")

    require(
        MARKER not in text,
        "recovery English overlay already applied"
    )

    require(
        "BUILD107_STICKER_TEXT_FALLBACK1" in text,
        "Build107 sticker fallback prerequisite missing"
    )

    start, brace, end = function_bounds(
        text,
        "private func ghostBaseDeletedMediaLabel("
    )

    region = text[start:end]

    for old, new in REPLACEMENTS:
        require(
            region.count(old) == 1,
            (
                "recovery label anchor count != 1: "
                + old
                + " -> "
                + str(region.count(old))
            )
        )
        region = region.replace(old, new, 1)

    # GIF is already language-neutral and intentionally remains unchanged.
    require(
        'return "GIF"' in region,
        "GIF label missing"
    )

    local_brace = region.find("{")
    require(local_brace >= 0, "local function brace missing")

    region = (
        region[:local_brace + 1]
        + "\n    "
        + MARKER
        + "\n"
        + "    // TelegramCore cannot depend on presentation/UI localization.\n"
        + "    // Portable recovery text therefore uses English canonical labels;\n"
        + "    // richer UI localization uses semantic JerkgramStringKey values."
        + region[local_brace + 1:]
    )

    updated = text[:start] + region + text[end:]

    ENQUEUE.write_text(
        updated,
        encoding="utf-8"
    )

    print(
        "[Build115 recovery English] "
        "portable deleted-media labels -> English canonical"
    )
    print(
        "[Build115 recovery English] "
        "sticker reconstruction policy unchanged"
    )


if __name__ == "__main__":
    main()
