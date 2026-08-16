#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

P = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"

PATHS = {
    "bg": P / "GhostBaseProfileFullscreenBackground.swift",
    "groups": P / "Panes/PeerInfoGroupsInCommonPaneNode.swift",
    "music_controls": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControlsNode.swift",
    "music_controller": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift",
    "enqueue": ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift",
    "state": ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift",
    "delete": ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift",
    "settings": ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
    "media": ROOT / "submodules/MediaPlayer/Sources/MediaPlayerNode.swift",
    "chunk": ROOT / "submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift",
    "cover": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift",
    "gift": ROOT / "submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift",
    "quote": ROOT / "submodules/TextFormat/Sources/ChatInputContentConversion.swift",
    "report": P / "GhostBaseProfileReportPaneNode.swift",
    "root": ROOT / "submodules/TelegramUI/Sources/TelegramRootController.swift",
    "members": P / "Panes/PeerInfoMembersPane.swift",
    "section": P / "PeerInfoScreenItemSectionContainerNode.swift",
    "list_section": ROOT / "submodules/TelegramUI/Components/ListSectionComponent/Sources/ListSectionComponent.swift",
}

for name, path in PATHS.items():
    if not path.is_file():
        raise RuntimeError(
            f"[V11T VERIFY] missing {name}: {path}"
        )

S = {
    name: path.read_text(encoding="utf-8")
    for name, path in PATHS.items()
}

errors: list[str] = []


def need(condition: bool, label: str) -> None:
    if not condition:
        errors.append(label)


def exactly(
    text: str,
    token: str,
    count: int,
    label: str
) -> None:
    actual = text.count(token)
    if actual != count:
        errors.append(
            f"{label}: expected {count}, found {actual}"
        )


# ------------------------------------------------------------
# Build104 -> Build105 profile visual recovery.
# ------------------------------------------------------------
bg = S["bg"]

need(
    "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1" in bg,
    "static avatar V11T pipeline marker"
)

need(
    "displayDimensions: CGSize(width: 360.0, height: 360.0)" in bg,
    "Build97 360 avatar feed"
)

need(
    "synchronousLoad: false" in bg,
    "Build97 async avatar feed"
)

need(
    "GhostBaseProfileAvatarBackgrounds" in bg,
    "decoded avatar disk reopen cache"
)

need(
    "ghostBaseLoadAvatarDiskCache" in bg
    and "ghostBaseStoreAvatarDiskCache" in bg,
    "avatar disk cache load/store"
)

need(
    "self.blurView.alpha = reduced ? 0.24 : 0.38" in bg,
    "static-only lighter blur"
)

need(
    "if animatedSource == nil" in bg
    and "self.blurView.alpha = 1.0" in bg,
    "animated avatar blur preserved"
)

need(
    "Self.sampledTint(\n                from: image" in bg,
    "avatar tint comes from decoded pixels"
)

avatar_marker = bg.find(
    "BUILD97_STATIC_AVATAR_PIPELINE1"
)

avatar_end = bg.find(
    "private func resourceEntrySignal",
    avatar_marker
)

need(
    "storePersistentTint(tint, identity: identity)"
    not in bg[avatar_marker:avatar_end],
    "static avatar must not persist grey tint"
)

# ------------------------------------------------------------
# Common Groups.
# ------------------------------------------------------------
groups = S["groups"]

need(
    "GhostBase v1.1T COMMON_GROUPS_NO_BLACK1" in groups,
    "Common Groups V11T marker"
)

need(
    "systemStyle: .legacy" in groups,
    "Common Groups legacy row renderer"
)

need(
    "displayBackground: !ghostBaseGlassEnabled" in groups,
    "Common Groups backgroundless rows"
)

need(
    "UIColor.white.withAlphaComponent(0.055)" in groups,
    "Common Groups dark neutral frost"
)

need(
    "UIColor.black.withAlphaComponent(0.045)" in groups,
    "Common Groups light neutral frost"
)

need(
    (
        "itemBlocksBackgroundColor\n"
        "                    .withAlphaComponent(isDark ? 0.22 : 0.32)"
    ) not in groups,
    "old black Common Groups tint removed"
)

# ------------------------------------------------------------
# Music: middle-ground glass, real PeerInfo remains underneath.
# ------------------------------------------------------------
mc = S["music_controls"]
mn = S["music_controller"]

need(
    "GhostBase v1.1T MUSIC_READABLE_GLASS1" in mc,
    "music controls V11T marker"
)

need(
    "systemUltraThinMaterialDark" in mc
    and "self.ghostBaseGlassEffectView.alpha = 0.48" in mc,
    "music weak material"
)

need(
    "GhostBase v1.1T MUSIC_HEADER_READABLE_GLASS1" in mn,
    "music header V11T marker"
)

need(
    "headerGlassView.alpha = 0.46" in mn
    and "systemUltraThinMaterialLight" in mn,
    "music header weak material"
)

need(
    "GhostBaseMusicProfileBackdropView" not in mn,
    "music cloned profile backdrop forbidden"
)

# ------------------------------------------------------------
# Deferred deleted reply.
# ------------------------------------------------------------
enq = S["enqueue"]

exactly(
    enq,
    "// MARK: GhostBase v1.1T BUILD105_FULL1",
    1,
    "resolver marker"
)

exactly(
    enq,
    "public func enqueueMessages(\n    account: Account,",
    1,
    "public enqueue wrapper"
)

exactly(
    enq,
    "private func ghostBaseEnqueueResolvedMessages",
    1,
    "renamed original enqueue"
)

need(
    "return ghostBaseResolveDeletedReplies(" in enq,
    "public enqueue invokes resolver"
)

wrapper_pos = enq.find(
    "public func enqueueMessages(\n    account: Account,"
)

resolver_call = enq.find(
    "ghostBaseResolveDeletedReplies(",
    wrapper_pos
)

normal_call = enq.find(
    "ghostBaseEnqueueResolvedMessages(",
    wrapper_pos
)

need(
    wrapper_pos >= 0
    and resolver_call > wrapper_pos
    and normal_call > resolver_call,
    "resolver runs before normal enqueue"
)

need(
    "ghostBaseSaveDeletedKey" in enq,
    "SaveDeleted gate"
)

need(
    "GhostBase.Messages.DeletedPortableReplies" in enq,
    "portable reply key"
)

need(
    "GhostBase.Messages.PreserveDeletedMedia" in enq,
    "preserve media key"
)

need(
    "GhostBase.Messages.DeletedMediaCacheLimit" in enq,
    "cache limit key"
)

need(
    "GhostBase.Messages.DeletedMediaRetentionDays" in enq,
    "retention key"
)

need(
    "ghostbase-deleted-media" in enq,
    "dedicated internal cache root"
)

need(
    "completedResourcePath(spec.resource)" in enq,
    "complete MediaBox resource only"
)

need(
    "FileManager.default" in enq
    and "copyItem(" in enq,
    "filesystem copy path"
)

need(
    "Data(contentsOf:" not in enq,
    "no huge Data file reads"
)

need(
    "PHPhoto" not in enq
    and "UIImageWriteToSavedPhotosAlbum" not in enq
    and "UIDocumentPicker" not in enq,
    "no Photos/Files export APIs"
)

need(
    "1024 * 1024 * 1024" in enq
    and "?? 30" in enq,
    "1GiB/30d bounded defaults"
)

need(
    "lastCleanupTimestamp" in enq
    and "300.0" in enq,
    "bounded cleanup throttle"
)

need(
    "files.sorted(by:" in enq,
    "oldest-first LRU cleanup"
)

need(
    "type: .TextMention(peerId: mentionPeerId)" in enq,
    "native TextMention author"
)

need(
    "type: .BlockQuote(isCollapsed: collapse)" in enq,
    "native BlockQuote"
)

need(
    "sourceLength > 320" in enq
    and 'components(separatedBy: "\\n").count > 4' in enq,
    "long quote collapse heuristic"
)

need(
    "messageTextEntitiesInRange(" in enq
    and "onlyQuoteable: true" in enq,
    "safe original formatting"
)

need(
    "ghostBaseShiftEntities" in enq,
    "UTF16 user/source entity shifting"
)

need(
    "attribute is ReplyMessageAttribute" in enq,
    "old reply attribute removed"
)

need(
    "replyToMessageId: nil" in enq,
    "dead server reply cleared"
)

need(
    "userMediaReference == nil ? recoveredMedia : nil" in enq,
    "user media priority"
)

need(
    "TextEntitiesMessageAttribute(entities: entities)" in enq,
    "merged text entities"
)

need(
    "apiInputUser(authorPeer) != nil" in enq,
    "mention InputUser safety gate"
)

need(
    "ghostBaseCloudDestination" in enq,
    "secret/noncloud mention safety"
)

# ------------------------------------------------------------
# Text fallback matrix.
# ------------------------------------------------------------
for token, label in (
    ("TelegramMediaPoll", "poll fallback"),
    ("TelegramMediaMap", "location fallback"),
    ("TelegramMediaContact", "contact fallback"),
    ("TelegramMediaDice", "dice fallback"),
    ("TelegramMediaTodo", "todo fallback"),
    ('return "Альбом"', "album fallback"),
    ('return "Стикер"', "sticker fallback"),
    (
        'return "🎙 Голосовое сообщение"',
        "voice fallback"
    ),
    (
        'return "📷 Фотография"',
        "photo fallback"
    ),
    (
        'return "🎬 Видео"',
        "video fallback"
    ),
    (
        'return "GIF"',
        "GIF fallback"
    ),
    (
        'return "🎵 Аудиофайл"',
        "audio fallback"
    ),
):
    need(token in enq, label)

# ------------------------------------------------------------
# Native recovered media.
# ------------------------------------------------------------
need(
    "LocalFileReferenceMediaResource(" in enq,
    "local recovered file resource"
)

need(
    "attributes: file.attributes" in enq,
    "voice/video/GIF/audio semantic attributes preserved"
)

need(
    "partialReference: nil" in enq,
    "stale file reference removed"
)

need(
    "TelegramMediaImageRepresentation(" in enq
    and "TelegramMediaImage(" in enq,
    "local recovered photo"
)

need(
    "return .standalone(media: localFile)" in enq,
    "native recovered file media reference"
)

need(
    "return .standalone(media: localImage)" in enq,
    "native recovered image media reference"
)

need(
    "source.groupingKey == nil" in enq,
    "album native reconstruction disabled"
)

need(
    "file.isSticker" in enq,
    "sticker native reconstruction disabled"
)

need(
    "OutgoingScheduleInfoMessageAttribute" in enq,
    "scheduled recovered-media safe fallback"
)

need(
    "(text as NSString).length > 1024" in enq,
    "caption overflow safe fallback"
)

# ------------------------------------------------------------
# Public self-set name snapshot.
# ------------------------------------------------------------
need(
    "GhostBasePublicPeerNameStore" in enq,
    "public-name store"
)

# EnginePeer debugDisplayTitle compile lock
need(
    "EnginePeer(authorPeer).debugDisplayTitle" in enq,
    "Official EnginePeer debugDisplayTitle API"
)

need(
    "compactDisplayTitle" not in enq,
    "invalid EnginePeer compactDisplayTitle removed"
)

need(
    "maximumCount = 256" in enq,
    "public-name store bounded"
)

need(
    "ghostBaseStorePublicPeerName" in enq,
    "public-name snapshot bridge"
)

state = S["state"]

need(
    "GhostBase v1.1T PUBLIC_NAME_SNAPSHOT1" in state,
    "raw updateUserName snapshot hook"
)

need(
    "updateUserNameData.firstName" in state
    and "updateUserNameData.lastName" in state,
    "self-set name fields"
)

# ------------------------------------------------------------
# Delete preservation hooks.
# ------------------------------------------------------------
need(
    "GhostBase v1.1T DELETED_MEDIA_PRESERVE_GLOBAL1" in state,
    "global delete cache hook"
)

need(
    "GhostBase v1.1T DELETED_MEDIA_PRESERVE_LOCAL1" in state,
    "local delete cache hook"
)

need(
    state.count(
        "ghostBaseScheduleDeletedMediaPreservation("
    ) >= 2,
    "both server delete preservation calls"
)

delete = S["delete"]

need(
    "GhostBase v1.1T DELETED_MEDIA_PRESERVE_SELF1" in delete,
    "self first-delete cache hook"
)

need(
    "GhostBase v1.1T DELETED_MEDIA_FINAL_DELETE1" in delete,
    "second physical delete cache cleanup"
)

need(
    "ghostBaseRemoveDeletedMediaCacheEntries(" in delete,
    "physical delete removes cache"
)

# ------------------------------------------------------------
# Settings gates/default policy.
# ------------------------------------------------------------
settings = S["settings"]

need(
    "GhostBase v1.1T DELETED_PORTABLE_SETTINGS1" in settings,
    "settings V11T marker"
)

need(
    "var deletedPortableReplies: Bool" in settings
    and "var preserveDeletedMedia: Bool" in settings,
    "settings state gates"
)

need(
    '"Переносимый ответ на удалённое"' in settings,
    "portable reply toggle"
)

need(
    '"Сохранять удалённые медиа"' in settings,
    "preserve deleted media toggle"
)

need(
    "Int64(1024 * 1024 * 1024)" in settings
    and "deletedMediaRetentionDays" in settings,
    "settings bounded cache defaults"
)

# ------------------------------------------------------------
# Regression locks: working Build104 areas must survive.
# ------------------------------------------------------------
need(
    "GhostBase v1.1S SECONDARY_VIDEO_STABLE1" in S["media"],
    "stable V11S secondary video preserved"
)

need(
    "GhostBase v1.1S SECONDARY_VIDEO_STABLE1" in S["chunk"],
    "stable V11S chunk path preserved"
)

need(
    "requiresFlushToResumeDecoding" not in S["chunk"],
    "aggressive V11R flush loop remains removed"
)

need(
    "layer.preventsCapture = self.captureProtected"
    not in S["media"],
    "resume watchdog fix preserved"
)

need(
    "GhostBase v1.1R PREMIUM_PATTERN_RESTORE1" in S["cover"],
    "Premium pattern regression lock"
)

need(
    "GhostBase v1.1R GIFT_READABLE_GLASS1" in S["gift"],
    "Gift glass regression lock"
)

need(
    "GhostBase v1.1R MULTILINE_QUOTE1" in S["quote"],
    "multiline Quote regression lock"
)

need(
    "GhostBase v1.1R HISTORY_CARDS1" in S["report"],
    "History cards regression lock"
)

need(
    "GhostBase v1.1R RAM_SETTING1" in settings
    and "GhostBase v1.1R RAM_OVERLAY1" in S["root"],
    "RAM regression lock"
)

need(
    "GhostBase v1.1Q MEMBERS_PANE_GLASS1" in S["members"],
    "Members glass regression lock"
)

need(
    "GhostBase v1.1P SECTION_OWNER1" in S["section"]
    and "withGhostBaseGlassCornerFillerSuppressed"
    in S["section"],
    "legacy wedge fix regression lock"
)

need(
    "ghostBaseDirectGlassBackgroundView"
    in S["list_section"],
    "modern wedge fix regression lock"
)

if errors:
    print("[V11T VERIFY] FAILED")
    for item in errors:
        print("-", item)
    raise SystemExit(1)

print("[V11T VERIFY] GREEN")
print(
    "[V11T VERIFY] Build97 static-avatar feed/reopen cache "
    "+ Common Groups + music: GREEN"
)
print(
    "[V11T VERIFY] deferred Send-time portable deleted reply "
    "+ native entities: GREEN"
)
print(
    "[V11T VERIFY] recovered media cache/re-upload/fallback/"
    "delete hooks: GREEN"
)
print(
    "[V11T VERIFY] public-name snapshot + feature gates/"
    "bounded policy: GREEN"
)
print(
    "[V11T VERIFY] animation/Premium/Gifts/Quote/History/"
    "RAM/wedges regressions: GREEN"
)
