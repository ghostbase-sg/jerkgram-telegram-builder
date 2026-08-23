#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(Path.cwd())
        )
    )
).resolve()

SETTINGS = (
    ROOT
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)
MAIN_ITEMS = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo"
    / "PeerInfoScreen/Sources/PeerInfoSettingsItems.swift"
)

MARKER = "// MARK: Jerkgram v1.2D BUILD115_SETTINGS_LOCALIZATION1"
MAIN_MARKER = "// MARK: Jerkgram v1.2D BUILD115_MAIN_SETTINGS_LOCALIZATION1"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build115 settings localization] " + message)


def function_region(text, signature):
    start = text.find(signature)
    require(start >= 0, "function missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "function brace missing: " + signature)
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
                return text[start:index + 1]
    raise RuntimeError("[verify Build115 settings localization] unterminated function")


def cyrillic_string_literals(text):
    pattern = re.compile(r'"""(.*?)"""|"(?:\\.|[^"\\])*"', re.S)
    return [
        match.group(0)
        for match in pattern.finditer(text)
        if re.search(r"[А-Яа-яЁё]", match.group(0))
    ]


require(SETTINGS.is_file(), "GhostBaseSettingsController.swift missing")
require(MAIN_ITEMS.is_file(), "PeerInfoSettingsItems.swift missing")
settings = SETTINGS.read_text(encoding="utf-8")
main_items = MAIN_ITEMS.read_text(encoding="utf-8")

require(settings.count(MARKER) == 1, "settings marker count != 1")
require(main_items.count(MAIN_MARKER) == 1, "main settings marker count != 1")

entries = function_region(settings, "private func ghostBaseSettingsEntries(")
require("strings: JerkgramStrings" in entries, "JerkgramStrings parameter missing")
require(
    "page.localizedTitle(presentationData.strings.jerkgram)" in settings,
    "localized navigation title missing"
)
require(
    "strings: presentationData.strings.jerkgram" in settings,
    "Telegram presentation language not passed to entries"
)

required_entry_tokens = (
    "strings.basicFunctions",
    "strings.profileCard",
    "strings.showIds",
    "strings.showDcs",
    "strings.registrationDate",
    "strings.localStarsBalance",
    "strings.starsBalance",
    "strings.currentVisualBalance(balance)",
    "strings.readGhost",
    "strings.typing",
    "strings.recording",
    "strings.uploading",
    "strings.choosingSticker",
    "strings.gameActivity",
    "strings.choosingEmoji",
    "strings.hideOnline",
    "strings.scheduledSend",
    "strings.deletedMessages",
    "strings.saveDeletedMessages",
    "strings.showDeletedMessages",
    "strings.editHistory",
    "strings.saveEditHistory",
    "strings.showEditHistory",
    "strings.savedDataHint",
    "strings.textSending",
    "strings.sendStyle",
    "strings.sendStyleHint",
    "strings.deletedReplies",
    "strings.portableReply",
    "strings.saveDeletedMedia",
    "strings.portableReplyHint",
    "strings.protectedContent",
    "strings.protectionEnabled",
    "strings.shareFromGallery",
    "strings.saveFromGallery",
    "strings.copyFromGallery",
    "strings.saveFromChat",
    "strings.copyFromChat",
    "strings.forwardFromChat",
    "strings.allowScreenshots",
    "strings.allowScreenRecording",
    "strings.mediaAndStories",
    "strings.oneTimeScreenshots",
    "strings.oneTimeScreenRecording",
    "strings.oneTimeSave",
    "strings.oneTimeMedia",
    "strings.storySave",
    "strings.profileBackground",
    "strings.profileBackgroundEffect",
    "strings.blurProfileAvatar",
    "strings.preferAvatarAsBackground",
    "strings.animatedBackground",
    "strings.colorTint",
    "strings.reducedBlur",
    "strings.animatedBackgroundHint",
    "strings.profileEffectDisabledHint",
    "strings.interface",
    "strings.messageSeconds",
    "strings.hideMyPhone",
    "strings.showRamUnderClock",
    "strings.hidePhoneHint",
    "strings.presenceHistoryEmpty",
    "strings.knownUsersNoData",
    "strings.recentEvents",
    "strings.eventsEmpty",
    "strings.diagnosticsBufferHint",
)
for token in required_entry_tokens:
    require(token in entries, "localized settings token missing: " + token)

leftovers = cyrillic_string_literals(entries)
require(
    not leftovers,
    "hard-coded Cyrillic survived in visible settings string literals: "
    + " | ".join(value.replace("\n", "\\n")[:160] for value in leftovers[:8])
)

page_start = settings.find("private enum GhostBaseSettingsPage")
page_end = settings.find("private final class GhostBaseSettingsArguments", page_start)
require(page_start >= 0 and page_end > page_start, "settings page enum bounds missing")
page_region = settings[page_start:page_end]
require("func localizedTitle(_ strings: JerkgramStrings)" in page_region, "page title localizer missing")
require(
    not cyrillic_string_literals(page_region),
    "hard-coded Cyrillic survived in page title string literals"
)
require('return "Jerkgram"' in page_region, "canonical page root is not Jerkgram")

main_required = (
    "presentationData.strings.jerkgram.settingsTitle",
    "presentationData.strings.jerkgram.ghostMode",
    "presentationData.strings.jerkgram.messages",
    "presentationData.strings.jerkgram.protectedContent",
    "presentationData.strings.jerkgram.mediaAndStories",
    "presentationData.strings.jerkgram.appearance",
    "presentationData.strings.jerkgram.debugResearch",
    "presentationData.strings.jerkgram.about",
)
for token in main_required:
    require(token in main_items, "localized main settings row missing: " + token)

require('text: "GhostBase"' not in main_items, "visible GhostBase main-row branding survived")

print("[verify Build115 settings localization] GREEN")
print("[verify Build115 settings localization] settings language owner: Telegram PresentationStrings")
print("[verify Build115 settings localization] visible settings literals are semantic Jerkgram strings")
print("[verify Build115 settings localization] main Settings rows localized")
