#!/usr/bin/env python3
from pathlib import Path
import os
import re

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
FETCH = ROOT / "submodules/TelegramCore/Sources/Network/FetchV2.swift"
NETWORK = ROOT / "submodules/TelegramCore/Sources/Network/Network.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
KEY = "jerkgram.global.DownloadBoost"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build140 Download Boost verify] " + message)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "block missing: " + signature)
    brace = text.find("{", start)
    require(brace >= 0, "opening brace missing: " + signature)
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise RuntimeError("[Build140 Download Boost verify] unbalanced block: " + signature)


for path in (FETCH, NETWORK, SETTINGS, STRINGS):
    require(path.is_file(), "missing source file: " + str(path))

fetch = FETCH.read_text(encoding="utf-8")
network = NETWORK.read_text(encoding="utf-8")
settings = SETTINGS.read_text(encoding="utf-8")
strings = STRINGS.read_text(encoding="utf-8")

require(fetch.count("// MARK: Jerkgram Build140 Download Boost1") == 1, "Fetch marker missing or duplicated")
require(fetch.count(KEY) == 1, "Fetch global key missing or duplicated")
require('guard let fileSize, fileSize > 1 * 1024 * 1024 else' in fetch, "small-file stock guard missing")
require('case "medium":\n        return 512 * 1024' in fetch, "Medium 512 KiB part size missing")
require('case "maximum":\n        return 1024 * 1024' in fetch, "Maximum 1 MiB part size missing")
require('case "medium":\n        return 8' in fetch, "Medium pending-parts count missing")
require('case "maximum":\n        return 12' in fetch, "Maximum pending-parts count missing")
require('self.defaultPartSize = jerkgramDownloadPartSize(512 * 1024, fileSize: self.size)' in fetch, "story part-size hook missing")
require('self.defaultPartSize = jerkgramDownloadPartSize(128 * 1024, fileSize: self.size)' in fetch, "normal part-size hook missing")
require('maxPendingParts: jerkgramDownloadMaxPendingParts(6)' in fetch, "pending-parts hook missing")
require('self.cdnPartSize = 128 * 1024' in fetch, "CDN stock 128 KiB owner changed")

require('networkSettings?.useExperimentalDownload ?? true' in network, "Telegram stock Download V2 default changed")
require('ios_killswitch_disable_downloadv2' in network, "Telegram Download V2 server kill-switch missing")

require(settings.count("// MARK: Jerkgram Build140 Download Boost Settings1") == 1, "Settings marker missing or duplicated")
legacy_menu_marker = "// MARK: Jerkgram Build140 Download Boost Menu1"
native_page_marker = "// MARK: Jerkgram Build140 Download Boost Native Page1"
native_opener_marker = "// MARK: Jerkgram Build140 Download Boost Native Page Opener1"
legacy_menu_count = settings.count(legacy_menu_marker)
native_page_count = settings.count(native_page_marker)
require(native_page_count in (0, 1), "native Settings page marker duplicated")
if native_page_count == 1:
    require(legacy_menu_count == 0, "legacy Settings menu survived native page")
    require(settings.count(native_opener_marker) == 1, "native Settings page opener missing or duplicated")
    require(settings.count("controller?.push(downloadBoostController)") == 1, "native Settings page push missing or duplicated")
else:
    require(legacy_menu_count == 1, "Settings menu marker missing or duplicated")
require(settings.count(KEY) == 1, "Settings global key missing or duplicated")
require('UserDefaults.standard.string(forKey: jerkgramDownloadBoostKey) ?? "off"' in settings, "global settings read missing")
global_write_pattern = re.compile(
    r"UserDefaults\.standard\.set\(\s*mode\s*,\s*forKey:\s*jerkgramDownloadBoostKey\s*\)"
)
require(len(global_write_pattern.findall(settings)) == 1, "global settings write missing or duplicated")
require('case downloadBoost' in settings and '.downloadBoost(' in settings, "Download Boost selector row missing")
require('downloadBoostRefreshNonce' in settings, "Download Boost list refresh owner missing")

if "private func jerkgramStateValues(" in settings:
    start, end = block_bounds(settings, "private func jerkgramStateValues(")
    state_map = settings[start:end]
    require("DownloadBoost" not in state_map and "downloadBoost" not in state_map, "global Download Boost leaked into account-scoped state map")

require(strings.count("// MARK: Jerkgram Build140 Download Boost Strings1") == 1, "Download Boost strings marker missing or duplicated")
require("Ускоренная загрузка" in strings and "Download Boost" in strings, "RU/EN Download Boost title missing")
require("Среднее" in strings and "Максимальное" in strings, "RU Download Boost values missing")

print("[Build140 Download Boost verify] GREEN")
print("[Build140 Download Boost verify] Off=Telegram stock; Medium=512KiB/8; Maximum=1MiB/12; CDN=128KiB; global setting; V2 kill-switch preserved")
