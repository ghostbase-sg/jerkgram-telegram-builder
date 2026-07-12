#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = (
    ROOT
    / "work/swiftgram-src/submodules/TelegramUI/Sources"
    / "ChatController.swift"
)

def require(value, message):
    if not value:
        raise RuntimeError(f"[v1.0T-runtime] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

require(FILE.is_file(), f"missing source: {FILE}")
text = FILE.read_text(encoding="utf-8")

marker = "GhostBase v1.0T send text style runtime"

if marker not in text:
    text = replace_once(
        text,
        '''        let ghostBaseScheduleBaseTime = Int32(Date().timeIntervalSince1970) + 12
        let ghostBaseIsScheduledMessages: Bool
''',
        '''        let ghostBaseScheduleBaseTime = Int32(Date().timeIntervalSince1970) + 12

        // MARK: GhostBase v1.0T send text style runtime
        let ghostBaseSendTextStyle = UserDefaults.standard.string(
            forKey: "GhostBase.Messages.SendTextStyle"
        ) ?? "normal"

        let ghostBaseIsScheduledMessages: Bool
''',
        "selected style"
    )

    text = replace_once(
        text,
        '''            return message.withUpdatedAttributes { attributes in
                var attributes = attributes

                let ghostBaseHasExistingSchedule = attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute })
''',
        '''            let ghostBaseText: String
            switch message {
            case let .message(text, _, _, _, _, _, _, _, _, _):
                ghostBaseText = text
            case .forward:
                ghostBaseText = ""
            }

            return message.withUpdatedAttributes { attributes in
                var attributes = attributes

                if !ghostBaseText.isEmpty && ghostBaseSendTextStyle != "normal" {
                    let textLength = (ghostBaseText as NSString).length
                    var styleEntities: [MessageTextEntity] = []

                    switch ghostBaseSendTextStyle {
                    case "bold":
                        styleEntities.append(
                            MessageTextEntity(
                                range: 0 ..< textLength,
                                type: .Bold
                            )
                        )

                    case "italic":
                        styleEntities.append(
                            MessageTextEntity(
                                range: 0 ..< textLength,
                                type: .Italic
                            )
                        )

                    case "monospace":
                        styleEntities.append(
                            MessageTextEntity(
                                range: 0 ..< textLength,
                                type: .Code
                            )
                        )

                    case "strikethrough":
                        styleEntities.append(
                            MessageTextEntity(
                                range: 0 ..< textLength,
                                type: .Strikethrough
                            )
                        )

                    case "underline":
                        styleEntities.append(
                            MessageTextEntity(
                                range: 0 ..< textLength,
                                type: .Underline
                            )
                        )

                    case "spoiler":
                        if let expression = try? NSRegularExpression(
                            pattern: "[\\\\p{L}\\\\p{N}]+"
                        ) {
                            let matches = expression.matches(
                                in: ghostBaseText,
                                range: NSRange(
                                    location: 0,
                                    length: textLength
                                )
                            )

                            for match in matches {
                                styleEntities.append(
                                    MessageTextEntity(
                                        range: match.range.location ..< NSMaxRange(match.range),
                                        type: .Spoiler
                                    )
                                )
                            }
                        }

                    default:
                        break
                    }

                    if !styleEntities.isEmpty {
                        var entities: [MessageTextEntity] = []

                        for attribute in attributes {
                            if let attribute = attribute as? TextEntitiesMessageAttribute {
                                entities.append(contentsOf: attribute.entities)
                            }
                        }

                        attributes.removeAll {
                            $0 is TextEntitiesMessageAttribute
                        }

                        entities.append(contentsOf: styleEntities)

                        attributes.append(
                            TextEntitiesMessageAttribute(
                                entities: entities
                            )
                        )

                        UserDefaults.standard.set(
                            UserDefaults.standard.integer(
                                forKey: "GhostBase.V10T.SendTextStyleApplied.Count"
                            ) + 1,
                            forKey: "GhostBase.V10T.SendTextStyleApplied.Count"
                        )
                    }
                }

                let ghostBaseHasExistingSchedule = attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute })
''',
        "style entities"
    )

FILE.write_text(text, encoding="utf-8")

require(marker in text, "runtime marker missing")
require(
    "GhostBase.V10T.SendTextStyleApplied.Count" in text,
    "runtime counter missing"
)

print("[v1.0T-runtime] send text style applied")
