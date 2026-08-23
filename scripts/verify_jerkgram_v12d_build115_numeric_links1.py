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

DEVICE_CONTACT = (
    ROOT
    / "submodules/AccountContext/Sources/DeviceContactData.swift"
)

URL_HANDLING = (
    ROOT
    / "submodules/UrlHandling/Sources/UrlHandling.swift"
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
            "[verify Build115 numeric links] "
            + message
        )


def numeric_peer_id(value):
    value = value.strip()

    if value.startswith("@"):
        value = value[1:]

    if value.lower().startswith("id"):
        value = value[2:]

    if not value:
        return None

    if not all("0" <= c <= "9" for c in value):
        return None

    try:
        result = int(value)
    except ValueError:
        return None

    if result <= 0 or result > 9223372036854775807:
        return None

    return result


def canonical_peer_url(value):
    peer_id = numeric_peer_id(value)
    if peer_id is None:
        return None
    return f"https://t.me/@id{peer_id}"


# Behaviour model: every supported numeric form collapses to the exact
# Official Telegram contact-reference URL already understood by iOS.
for source in (
    "73638283",
    "@73638283",
    "id73638283",
    "@id73638283",
):
    require(
        numeric_peer_id(source) == 73638283,
        "normalization failed: " + source
    )
    require(
        canonical_peer_url(source)
        == "https://t.me/@id73638283",
        "canonical URL failed: " + source
    )

for source in (
    "",
    "@",
    "id",
    "@id",
    "0",
    "-1",
    "12a",
    "@id12a",
):
    require(
        numeric_peer_id(source) is None,
        "invalid numeric form accepted: " + repr(source)
    )

for path in (
    OPEN_URL,
    TEXT_LINK,
    DEVICE_CONTACT,
    URL_HANDLING,
):
    require(
        path.is_file(),
        "source owner missing: " + str(path)
    )

open_url = OPEN_URL.read_text(encoding="utf-8")
text_link = TEXT_LINK.read_text(encoding="utf-8")
device_contact = DEVICE_CONTACT.read_text(encoding="utf-8")
url_handling = URL_HANDLING.read_text(encoding="utf-8")

# Official source contract we intentionally reuse instead of inventing a
# separate user-by-id network API.
require(
    'public let phonebookUsernamePathPrefix = "@id"'
    in device_contact,
    "Official @id contact-reference prefix missing"
)
require(
    'private let phonebookUsernamePrefix = "https://t.me/" + phonebookUsernamePathPrefix'
    in device_contact,
    "Official @id contact-reference URL owner missing"
)
require(
    "case let .peerId(peerId):" in url_handling,
    "Official peerId resolver missing"
)
require(
    "TelegramEngine.EngineData.Item.Peer.Peer(id: peerId)"
    in url_handling,
    "Official peerId local EngineData lookup missing"
)
require(
    "return .single(.result(.inaccessiblePeer))"
    in url_handling,
    "Official unknown-peer limitation missing"
)

require(
    open_url.count(OPEN_MARKER) == 1,
    "openmessage marker count != 1"
)
require(
    'case "openmessage":' in open_url,
    "tg://openmessage case missing"
)
require(
    'params["user_id"].flatMap(Int64.init)'
    in open_url,
    "openmessage user_id parser missing"
)
require(
    'convertedUrl = makeTelegramUrl("/@id\\(idValue)")'
    in open_url,
    "openmessage does not normalize to Official @id URL"
)

require(
    text_link.count(MENTION_MARKER) == 1,
    "numeric mention marker count != 1"
)
require(
    "jerkgramNumericMentionPeerId"
    in text_link,
    "numeric mention parser missing"
)
require(
    'openLinkImpl("https://t.me/@id\\(idValue)")'
    in text_link,
    "numeric mention does not reuse Official @id URL path"
)
require(
    "context.engine.peers.resolvePeerByName("
    in text_link,
    "stock username resolver was removed"
)

# Keep the new overlay deliberately local-only. The Official @id pipeline
# resolves known peers from EngineData and returns inaccessiblePeer otherwise.
open_slice_start = open_url.index(OPEN_MARKER)
open_slice = open_url[
    open_slice_start:
    open_slice_start + 700
]
mention_slice_start = text_link.index(MENTION_MARKER)
mention_slice = text_link[
    mention_slice_start:
    mention_slice_start + 1800
]

for forbidden in (
    "accessHash",
    "findUserById",
    "resolvePeerById",
    "Api.functions.users",
):
    require(
        forbidden not in open_slice,
        "openmessage invented unsupported resolver: " + forbidden
    )
    require(
        forbidden not in mention_slice,
        "mention invented unsupported resolver: " + forbidden
    )

print("[verify Build115 numeric links] GREEN")
print("[verify Build115 numeric links] tg openmessage -> Official t.me/@id path")
print("[verify Build115 numeric links] @idN / @N -> same Official path")
print("[verify Build115 numeric links] stock username resolution retained")
print("[verify Build115 numeric links] unknown raw IDs keep Official local-only limitation")
