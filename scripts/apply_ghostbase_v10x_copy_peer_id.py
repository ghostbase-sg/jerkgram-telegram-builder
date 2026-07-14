#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / (
    "work/swiftgram-src/submodules/TelegramUI/Components/"
    "PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
)

text = path.read_text()

old = '''                items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(id: ghostBaseItemId, label: "id: \\(ghostBasePeerIdText)", text: "", textColor: .primary, action: nil, longTapAction: nil, requestLayout: { _ in
                    interaction.requestLayout(false)
                }))'''

new = '''                items[.ghostbase]!.append(PeerInfoScreenLabeledValueItem(
                    id: ghostBaseItemId,
                    label: "id: \\(ghostBasePeerIdText)",
                    text: "",
                    textColor: .primary,
                    action: nil,
                    longTapAction: { sourceNode in
                        // MARK: GhostBase v1.0X peer ID generic copy context menu
                        interaction.openPeerInfoContextMenu(
                            .businessHours(ghostBasePeerIdText),
                            sourceNode,
                            nil
                        )
                    },
                    requestLayout: { _ in
                        interaction.requestLayout(false)
                    }
                ))'''

if new in text:
    print("[v1.0X] peer ID copy already applied")
elif old in text:
    text = text.replace(old, new, 1)
    path.write_text(text)
    print("[v1.0X] peer ID copy applied")
else:
    raise RuntimeError("[v1.0X] peer ID item anchor missing")
