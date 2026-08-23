#!/usr/bin/env python3

from pathlib import Path
import os
import re


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"
REPORT = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
TABS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoPaneContainerNode.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[verify Build117 profile localization] " + message)


def verify(strings, report, tabs):
    require(strings.count("BUILD117_PROFILE_REPORT_LOCALIZATION1") == 1, "catalog marker count != 1")
    for key in (
        "profileHistoryTab",
        "presenceHistoryTab",
        "giftHistoryTab",
        "personalChannelTab",
        "profileReportLoading",
    ):
        require("case " + key in strings, "key missing: " + key)
        require("self.text(." + key + ")" in strings, "accessor missing: " + key)

    require("strings.localizedProfileReport(rawText)" in report, "report render localization missing")
    require('self.reportText ?? "Загрузка…"' not in report, "hardcoded loading state remains")

    literals = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', report)
    cyrillic = sorted({value for value in literals if re.search(r"[А-Яа-яЁё]", value)})
    for value in cyrillic:
        static_prefix = value.split(r"\(", 1)[0].rstrip()
        require(static_prefix in strings, "unmapped profile report literal: " + value)

    for literal in ("История", "Присутствие", "Подарки · история", "Канал"):
        require('text: "' + literal + '"' not in tabs, "hardcoded tab remains: " + literal)
    for accessor in (
        "profileHistoryTab",
        "presenceHistoryTab",
        "giftHistoryTab",
        "personalChannelTab",
    ):
        require("presentationData.strings.jerkgram." + accessor in tabs, "localized tab missing: " + accessor)


def main():
    for path in (STRINGS, REPORT, TABS):
        require(path.is_file(), "source owner missing: " + str(path))
    verify(
        STRINGS.read_text(encoding="utf-8"),
        REPORT.read_text(encoding="utf-8"),
        TABS.read_text(encoding="utf-8"),
    )
    print("[verify Build117 profile localization] GREEN: all profile report literals mapped")


if __name__ == "__main__":
    main()
