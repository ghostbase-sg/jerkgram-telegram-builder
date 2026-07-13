#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILE = ROOT / (
    "work/swiftgram-src/submodules/TelegramUI/Components/"
    "PeerInfo/PeerInfoScreen/Sources/"
    "PeerInfoSettingsItems.swift"
)

text = FILE.read_text()

old = (
    'label: .text(user.phone.flatMap({ '
    'formatPhoneNumber(context: context, number: $0) '
    '}) ?? "")'
)

new = (
    'label: .text(((UserDefaults.standard.object('
    'forKey: "GhostBase.Appearance.HideOwnPhone") '
    'as? Bool) ?? false) ? "" : '
    '(user.phone.flatMap({ '
    'formatPhoneNumber(context: context, number: $0) '
    '}) ?? ""))'
)

marker = "GhostBase.Appearance.HideOwnPhone"

if marker in text:
    print("[v1.0W phone] already applied")
elif old not in text:
    raise RuntimeError(
        "[v1.0W phone] official phone label anchor missing"
    )
else:
    text = text.replace(old, new, 1)
    FILE.write_text(text)
    print("[v1.0W phone] settings phone value hidden")
