#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
REPORT = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileReportPaneNode.swift"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"

def require(value, message):
    if not value: raise RuntimeError("[Build118 profile report polish] " + message)

def main():
    require(REPORT.is_file() and STRINGS.is_file(), "owners missing")
    report = REPORT.read_text()
    require("BUILD118_PROFILE_REPORT_SEMANTICS1" not in report, "already applied")
    helper_anchor = '''            func value(_ value: String?) -> String {
                guard let value, !value.isEmpty else {
                    return "—"
                }
                return value
            }
'''
    require(helper_anchor in report, "profile value helper missing")
    helper = helper_anchor + r'''
            // MARK: Jerkgram v1.2G BUILD118_PROFILE_REPORT_SEMANTICS1
            func emojiStatusValue(_ raw: String) -> String {
                if raw == "nil" { return "—" }
                if let marker = raw.range(of: "fileId: ") {
                    let suffix = raw[marker.upperBound...]
                    let digits = suffix.prefix(where: { $0.isNumber })
                    if !digits.isEmpty { return "#" + digits }
                }
                if raw.localizedCaseInsensitiveContains("starGift") { return "🎁" }
                return "●"
            }
'''
    report = report.replace(helper_anchor, helper, 1)
    replacements = {
        '"Username: \\(value(previous.username)) → \\(value(current.username))"': '"Юзернейм: \\(value(previous.username)) → \\(value(current.username))"',
        '"BIO: \\(value(previous.about)) → \\(value(current.about))"': '"Описание: \\(value(previous.about)) → \\(value(current.about))"',
        '"Emoji-status: \\(previous.emojiStatus) → \\(current.emojiStatus)"': '"Эмодзи-статус: \\(emojiStatusValue(previous.emojiStatus)) → \\(emojiStatusValue(current.emojiStatus))"',
        '"Username: "\n                        + value(previous.username)': '"Юзернейм: "\n                        + value(previous.username)',
    }
    for old, new in replacements.items():
        require(old in report, "report label missing: " + old)
        report = report.replace(old, new)
    REPORT.write_text(report, encoding="utf-8")
    strings = STRINGS.read_text()
    anchor = '''            ("Имя:", "Name:"),
'''
    require(anchor in strings, "localization prefix anchor missing")
    strings = strings.replace(anchor, anchor + '''            ("Юзернейм:", "Username:"),
            ("Описание:", "Bio:"),
            ("Эмодзи-статус:", "Emoji status:"),
''', 1)
    STRINGS.write_text(strings, encoding="utf-8")
    print("[Build118 profile report polish] semantic emoji status and full RU/EN labels installed")

if __name__ == "__main__": main()
