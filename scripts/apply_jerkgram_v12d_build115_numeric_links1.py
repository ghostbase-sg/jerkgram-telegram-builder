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

OPEN_URL = (
    ROOT
    / "submodules/TelegramUI/Sources/OpenUrl.swift"
)

TEXT_LINK = (
    ROOT
    / "submodules/TelegramUI/Sources/TextLinkHandling.swift"
)

OPEN_MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_NUMERIC_OPENMESSAGE1"
)

MENTION_MARKER = (
    "// MARK: Jerkgram v1.2D "
    "BUILD115_NUMERIC_MENTION1"
)


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 numeric links] "
            + message
        )


def replace_once(text, old, new, label):
    count = text.count(old)
    require(
        count == 1,
        f"{label}: expected 1 anchor, found {count}"
    )
    return text.replace(old, new, 1)


def patch_open_url(text):
    require(
        OPEN_MARKER not in text,
        "openmessage normalization already applied"
    )

    anchor = '''                case "msg_url":
'''

    replacement = '''                // MARK: Jerkgram v1.2D BUILD115_NUMERIC_OPENMESSAGE1
                // Android-oriented tg://openmessage?user_id=N is
                // normalized into the exact Official Telegram iOS
                // contact-reference path. The downstream @id resolver
                // intentionally keeps its stock local-peer semantics.
                case "openmessage":
                    if let idValue = params["user_id"].flatMap(Int64.init), idValue > 0 {
                        convertedUrl = makeTelegramUrl("/@id\\(idValue)")
                    }
                case "msg_url":
'''

    return replace_once(
        text,
        anchor,
        replacement,
        "OpenUrl msg_url switch"
    )


def patch_text_link(text):
    require(
        MENTION_MARKER not in text,
        "numeric mention normalization already applied"
    )

    anchor = '''    let openPeerMentionImpl: (String) -> Void = { mention in
        navigateDisposable.set((context.engine.peers.resolvePeerByName(name: mention, referrer: nil, ageLimit: 10)
'''

    replacement = '''    // MARK: Jerkgram v1.2D BUILD115_NUMERIC_MENTION1
    // Reuse Official Telegram's t.me/@idN parser for textual numeric
    // mentions instead of introducing a second peer lookup implementation.
    let jerkgramNumericMentionPeerId: (String) -> Int64? = { mention in
        var value = mention.trimmingCharacters(in: .whitespacesAndNewlines)

        if value.hasPrefix("@") {
            value.removeFirst()
        }

        if value.lowercased().hasPrefix("id") {
            value.removeFirst(2)
        }

        guard !value.isEmpty,
              value.unicodeScalars.allSatisfy({ scalar in
                  scalar.value >= 48 && scalar.value <= 57
              }),
              let idValue = Int64(value),
              idValue > 0 else {
            return nil
        }

        return idValue
    }

    let openPeerMentionImpl: (String) -> Void = { mention in
        if let idValue = jerkgramNumericMentionPeerId(mention) {
            openLinkImpl("https://t.me/@id\\(idValue)")
            return
        }

        navigateDisposable.set((context.engine.peers.resolvePeerByName(name: mention, referrer: nil, ageLimit: 10)
'''

    return replace_once(
        text,
        anchor,
        replacement,
        "TextLinkHandling mention resolver"
    )


def main():
    for path in (OPEN_URL, TEXT_LINK):
        require(
            path.is_file(),
            "source owner missing: " + str(path)
        )

    open_url = patch_open_url(
        OPEN_URL.read_text(encoding="utf-8")
    )

    text_link = patch_text_link(
        TEXT_LINK.read_text(encoding="utf-8")
    )

    OPEN_URL.write_text(
        open_url,
        encoding="utf-8"
    )

    TEXT_LINK.write_text(
        text_link,
        encoding="utf-8"
    )

    print(
        "[Build115 numeric links] "
        "tg://openmessage?user_id=N -> https://t.me/@idN"
    )
    print(
        "[Build115 numeric links] "
        "@idN and @N mentions -> same Official @id path"
    )
    print(
        "[Build115 numeric links] "
        "stock non-numeric username resolver retained"
    )


if __name__ == "__main__":
    main()
