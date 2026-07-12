#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = (
    ROOT
    / "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)

def require(value, message):
    if not value:
        raise RuntimeError(f"[v1.0T-menu] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

require(FILE.is_file(), f"missing source: {FILE}")
text = FILE.read_text(encoding="utf-8")

if "import ContextUI\n" not in text:
    text = text.replace(
        "import Foundation\n",
        "import Foundation\nimport ContextUI\n",
        1
    )

if "import AsyncDisplayKit\n" not in text:
    text = text.replace(
        "import Foundation\n",
        "import Foundation\nimport AsyncDisplayKit\n",
        1
    )

helper_marker = "GhostBase v1.0T send style menu helpers"

if helper_marker not in text:
    text = replace_once(
        text,
        "struct GhostBaseSettingsState: Equatable {\n",
        '''// MARK: GhostBase v1.0T send style menu helpers
private func ghostBaseSendTextStyleTitle(
    _ value: String
) -> String {
    switch value {
    case "bold":
        return "Жирный"
    case "italic":
        return "Курсив"
    case "monospace":
        return "Моноширинный"
    case "strikethrough":
        return "Зачёркнутый"
    case "underline":
        return "Подчёркнутый"
    case "spoiler":
        return "Спойлер"
    default:
        return "Обычный"
    }
}

struct GhostBaseSettingsState: Equatable {
''',
        "style title helper"
    )

if "ghostBaseSendTextStyleTitle(state.sendTextStyle)" not in text:
    text = replace_once(
        text,
        "                state.sendTextStyle\n",
        "                ghostBaseSendTextStyleTitle(state.sendTextStyle)\n",
        "selector displayed value"
    )

source_marker = "GhostBase v1.0T send style context source"

if source_marker not in text:
    text = replace_once(
        text,
        "struct GhostBaseSettingsState: Equatable {\n",
        '''// MARK: GhostBase v1.0T send style context source
private final class GhostBaseSendStyleContextSource:
    ContextControllerContentSource
{
    let controller: ViewController
    let navigationController: NavigationController? = nil
    let passthroughTouches: Bool = false

    weak var sourceNode: ASDisplayNode?

    init(
        controller: ViewController,
        sourceNode: ASDisplayNode
    ) {
        self.controller = controller
        self.sourceNode = sourceNode
    }

    func transitionInfo() -> ContextControllerTakeControllerInfo? {
        guard let sourceNode = self.sourceNode else {
            return nil
        }

        let contentArea = self.controller.view.convert(
            self.controller.view.bounds,
            to: nil
        )

        return ContextControllerTakeControllerInfo(
            contentAreaInScreenSpace: contentArea,
            sourceNode: { [weak sourceNode] in
                guard let sourceNode = sourceNode else {
                    return nil
                }

                return (
                    sourceNode.view,
                    sourceNode.bounds
                )
            }
        )
    }

    func animatedIn() {
    }
}

struct GhostBaseSettingsState: Equatable {
''',
        "context source"
    )

items_marker = "GhostBase v1.0T send style menu items"

if items_marker not in text:
    text = replace_once(
        text,
        "struct GhostBaseSettingsState: Equatable {\n",
        '''// MARK: GhostBase v1.0T send style menu items
private func ghostBaseSendStyleMenuItems(
    selected: String,
    select: @escaping (String) -> Void
) -> [ContextMenuItem] {
    let styles = [
        ("normal", "Обычный"),
        ("bold", "Жирный"),
        ("italic", "Курсив"),
        ("monospace", "Моноширинный"),
        ("strikethrough", "Зачёркнутый"),
        ("underline", "Подчёркнутый"),
        ("spoiler", "Спойлер")
    ]

    return styles.map { value, title in
        let prefix = value == selected ? "✓ " : ""
        var displayText = prefix + title
        var entities: [MessageTextEntity] = []

        let start = (prefix as NSString).length
        let end = start + (title as NSString).length
        let titleRange = start ..< end

        switch value {
        case "bold":
            entities.append(
                MessageTextEntity(range: titleRange, type: .Bold)
            )
        case "italic":
            entities.append(
                MessageTextEntity(range: titleRange, type: .Italic)
            )
        case "monospace":
            entities.append(
                MessageTextEntity(range: titleRange, type: .Code)
            )
        case "strikethrough":
            entities.append(
                MessageTextEntity(
                    range: titleRange,
                    type: .Strikethrough
                )
            )
        case "underline":
            entities.append(
                MessageTextEntity(range: titleRange, type: .Underline)
            )
        case "spoiler":
            displayText += "  пример"

            let range = (displayText as NSString).range(
                of: "пример",
                options: .backwards
            )

            entities.append(
                MessageTextEntity(
                    range: range.location ..< NSMaxRange(range),
                    type: .Spoiler
                )
            )
        default:
            break
        }

        return .action(
            ContextMenuActionItem(
                text: displayText,
                entities: entities,
                textLayout: .singleLine,
                icon: { _ in nil },
                action: { _, dismiss in
                    select(value)
                    dismiss(.default)
                }
            )
        )
    }
}

struct GhostBaseSettingsState: Equatable {
''',
        "menu items"
    )

menu_marker = "GhostBase v1.0T compact send style menu"

if menu_marker not in text:
    require(
        "var openSendTextStyleImpl: (() -> Void)?" in text,
        "openSendTextStyleImpl missing"
    )

    text = replace_once(
        text,
        '''    pushController = { [weak controller] target in
''',
        '''    // MARK: GhostBase v1.0T compact send style menu
    openSendTextStyleImpl = { [weak controller] in
        guard let controller = controller else {
            return
        }

        var sourceNode: ASDisplayNode?

        controller.forEachItemNode { itemNode in
            guard
                let disclosureNode =
                    itemNode as? ItemListDisclosureItemNode,
                let tag = disclosureNode.tag
            else {
                return
            }

            if GhostBaseSettingsEntryTag.sendTextStyle.isEqual(
                to: tag
            ) {
                sourceNode = disclosureNode
            }
        }

        guard let sourceNode = sourceNode else {
            return
        }

        let presentationData =
            context.sharedContext.currentPresentationData.with {
                $0
            }

        let selected = stateValue.with {
            $0.sendTextStyle
        }

        let items = ghostBaseSendStyleMenuItems(
            selected: selected,
            select: { style in
                updateState { current in
                    var updated = current
                    updated.sendTextStyle = style
                    return updated
                }
            }
        )

        let menu = makeContextController(
            context: context,
            presentationData: presentationData,
            source: .controller(
                GhostBaseSendStyleContextSource(
                    controller: controller,
                    sourceNode: sourceNode
                )
            ),
            items: .single(
                ContextController.Items(
                    content: .list(items)
                )
            )
        )

        controller.present(
            menu,
            in: .window(.root)
        )
    }

    pushController = { [weak controller] target in
''',
        "menu wiring"
    )

FILE.write_text(text, encoding="utf-8")

require(helper_marker in text, "helper marker missing")
require(source_marker in text, "source marker missing")
require(items_marker in text, "items marker missing")
require(menu_marker in text, "menu marker missing")

print("[v1.0T-menu] compact style menu applied")
