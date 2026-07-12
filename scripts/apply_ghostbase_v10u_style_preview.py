#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

def need(value, message):
    if not value:
        raise RuntimeError(message)

def once(text, old, new, label):
    need(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

need(FILE.is_file(), f"missing: {FILE}")
text = FILE.read_text()

marker = "GhostBase v1.0U styled send text preview"

if marker not in text:
    anchor = '''private func ghostBaseSendTextStyleTitle(
'''

    helper = '''// MARK: GhostBase v1.0U styled send text preview
private func ghostBaseSendStyleAttributedText(
    style: String,
    text: String,
    color: UIColor,
    size: CGFloat
) -> NSAttributedString {
    var visibleText = text

    if style == "spoiler" {
        visibleText = text.unicodeScalars.map { scalar in
            CharacterSet.alphanumerics.contains(scalar)
                ? "#"
                : String(scalar)
        }.joined()
    }

    var attributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: size),
        .foregroundColor: color
    ]

    switch style {
    case "bold":
        attributes[.font] = UIFont.boldSystemFont(ofSize: size)
    case "italic":
        attributes[.font] = UIFont.italicSystemFont(ofSize: size)
    case "monospace":
        attributes[.font] = UIFont.monospacedSystemFont(
            ofSize: size,
            weight: .regular
        )
    case "strikethrough":
        attributes[.strikethroughStyle] =
            NSUnderlineStyle.single.rawValue
    case "underline":
        attributes[.underlineStyle] =
            NSUnderlineStyle.single.rawValue
    default:
        break
    }

    return NSAttributedString(
        string: visibleText,
        attributes: attributes
    )
}

private func ghostBaseSendTextStyleTitle(
'''

    text = once(text, anchor, helper, "style helper")

    text = once(
        text,
        '''    case selector(Int32, Int32, String, String)
    case info(Int32, String)
''',
        '''    case selector(Int32, Int32, String, String)
    case stylePreview(Int32, Int32, String)
    case info(Int32, String)
''',
        "preview entry case"
    )

    text = once(
        text,
        '''        case let .selector(section, _, _, _):
            return section
        case let .info(section, _):
''',
        '''        case let .selector(section, _, _, _):
            return section
        case let .stylePreview(section, _, _):
            return section
        case let .info(section, _):
''',
        "preview section"
    )

    text = once(
        text,
        '''        case let .selector(section, index, _, _):
            return section * 1000 + index
        case let .info(section, _):
''',
        '''        case let .selector(section, index, _, _):
            return section * 1000 + index
        case let .stylePreview(section, index, _):
            return section * 1000 + index
        case let .info(section, _):
''',
        "preview stable id"
    )

    text = once(
        text,
        '''            return false
        case let .info(ls, lt):
''',
        '''            return false
        case let .stylePreview(ls, li, lv):
            if case let .stylePreview(rs, ri, rv) = rhs {
                return ls == rs && li == ri && lv == rv
            }
            return false
        case let .info(ls, lt):
''',
        "preview equality"
    )

    old = '''        case let .selector(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: value,
                labelStyle: .text,
'''

    new = '''        case let .selector(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: "",
                attributedLabel: ghostBaseSendStyleAttributedText(
                    style: value,
                    text: ghostBaseSendTextStyleTitle(value),
                    color: presentationData.theme.list.itemSecondaryTextColor,
                    size: 15.0
                ),
                labelStyle: .text,
'''

    text = once(text, old, new, "styled selector label")

    old = '''        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
'''

    new = '''        case let .stylePreview(_, _, value):
            let line = NSMutableAttributedString(
                string: "Пример: ",
                attributes: [
                    .font: UIFont.systemFont(ofSize: 15.0),
                    .foregroundColor:
                        presentationData.theme.list.itemPrimaryTextColor
                ]
            )

            line.append(
                ghostBaseSendStyleAttributedText(
                    style: value,
                    text: "так будет выглядеть ваш текст",
                    color: presentationData.theme.list.itemPrimaryTextColor,
                    size: 15.0
                )
            )

            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: "",
                attributedTitle: line,
                label: "",
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .none,
                action: nil
            )

        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
'''

    text = once(text, old, new, "preview item")

    text = once(
        text,
        '''                ghostBaseSendTextStyleTitle(state.sendTextStyle)
            ),
            .info(
''',
        '''                state.sendTextStyle
            ),
            .stylePreview(
                2,
                6,
                state.sendTextStyle
            ),
            .info(
''',
        "messages preview row"
    )

    old = '''        var displayText = prefix + title
        var entities: [MessageTextEntity] = []

        let start = (prefix as NSString).length
'''

    new = '''        var displayText = prefix + title
        var entities: [MessageTextEntity] = []

        let menuFont: ContextMenuActionItemFont
        switch value {
        case "bold":
            menuFont = .custom(
                font: UIFont.boldSystemFont(ofSize: 17.0),
                height: nil,
                verticalOffset: nil
            )
        case "italic":
            menuFont = .custom(
                font: UIFont.italicSystemFont(ofSize: 17.0),
                height: nil,
                verticalOffset: nil
            )
        case "monospace":
            menuFont = .custom(
                font: UIFont.monospacedSystemFont(
                    ofSize: 17.0,
                    weight: .regular
                ),
                height: nil,
                verticalOffset: nil
            )
        default:
            menuFont = .regular
        }

        let start = (prefix as NSString).length
'''

    text = once(text, old, new, "menu fonts")

    text = once(
        text,
        '''                textLayout: .singleLine,
                icon: { _ in nil },
''',
        '''                textLayout: .singleLine,
                textFont: menuFont,
                icon: { _ in nil },
''',
        "menu text font"
    )

FILE.write_text(text)
need(marker in text, "style preview marker missing")

print("[v1.0U] styled selector and preview applied")
