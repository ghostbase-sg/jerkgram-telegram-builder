#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILE = ROOT / (
    "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

text = FILE.read_text()
marker = "GhostBase v1.0W native send style page"

if marker in text:
    print("[v1.0W style] already applied")
    raise SystemExit

anchor = '''private func ghostBaseSettingsPageController(
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> ViewController {
'''

helper = r'''// MARK: GhostBase v1.0W native send style page
private final class GhostBaseSendStylePageArguments {
    let select: (String) -> Void

    init(select: @escaping (String) -> Void) {
        self.select = select
    }
}

private enum GhostBaseSendStylePageEntry: ItemListNodeEntry {
    case option(Int32, String, String, Bool)

    var section: ItemListSectionId {
        return 0
    }

    var stableId: Int32 {
        switch self {
        case let .option(index, _, _, _):
            return index
        }
    }

    static func ==(
        lhs: GhostBaseSendStylePageEntry,
        rhs: GhostBaseSendStylePageEntry
    ) -> Bool {
        switch (lhs, rhs) {
        case let (
            .option(li, lv, lt, ls),
            .option(ri, rv, rt, rs)
        ):
            return li == ri
                && lv == rv
                && lt == rt
                && ls == rs
        }
    }

    static func <(
        lhs: GhostBaseSendStylePageEntry,
        rhs: GhostBaseSendStylePageEntry
    ) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(
        presentationData: ItemListPresentationData,
        arguments: Any
    ) -> ListViewItem {
        let arguments =
            arguments as! GhostBaseSendStylePageArguments

        switch self {
        case let .option(_, value, title, selected):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: "",
                attributedTitle: ghostBaseSendStyleAttributedText(
                    style: value,
                    text: title,
                    color:
                        presentationData.theme.list.itemPrimaryTextColor,
                    size: 17.0
                ),
                label: selected ? "✓" : "",
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .none,
                action: {
                    arguments.select(value)
                }
            )
        }
    }
}

private func ghostBaseSendStylePageEntries(
    selected: String
) -> [GhostBaseSendStylePageEntry] {
    let styles: [(String, String)] = [
        ("normal", "Обычный"),
        ("bold", "Жирный"),
        ("italic", "Курсив"),
        ("monospace", "Моноширинный"),
        ("strikethrough", "Зачёркнутый"),
        ("underline", "Подчёркнутый"),
        ("spoiler", "Спойлер")
    ]

    return styles.enumerated().map { index, item in
        return .option(
            Int32(index),
            item.0,
            item.1,
            selected == item.0
        )
    }
}

private func ghostBaseSendStylePageController(
    context: AccountContext,
    selected: String,
    select: @escaping (String) -> Void
) -> ViewController {
    let selectedValue = Atomic(value: selected)
    let selectedPromise = ValuePromise(
        selected,
        ignoreRepeated: true
    )

    let arguments = GhostBaseSendStylePageArguments(
        select: { value in
            let updated = selectedValue.modify { _ in value }
            selectedPromise.set(updated)
            select(value)
        }
    )

    let signal = combineLatest(
        context.sharedContext.presentationData,
        selectedPromise.get()
    )
    |> deliverOnMainQueue
    |> map { presentationData, value
        -> (ItemListControllerState, (ItemListNodeState, Any)) in

        let itemPresentationData =
            ItemListPresentationData(presentationData)

        let controllerState = ItemListControllerState(
            presentationData: itemPresentationData,
            title: .text("Стиль отправки"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(
                title: presentationData.strings.Common_Back
            ),
            animateChanges: false
        )

        let listState = ItemListNodeState(
            presentationData: itemPresentationData,
            entries: ghostBaseSendStylePageEntries(
                selected: value
            ),
            style: .blocks,
            ensureVisibleItemTag: nil,
            emptyStateItem: nil,
            animateChanges: false
        )

        return (
            controllerState,
            (listState, arguments as Any)
        )
    }

    return ItemListController(
        context: context,
        state: signal
    )
}

private func ghostBaseSettingsPageController(
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> ViewController {
'''

if anchor not in text:
    raise RuntimeError(
        "[v1.0W style] page controller anchor missing"
    )

text = text.replace(anchor, helper, 1)

start_marker = (
    "    // MARK: GhostBase v1.0T compact send style menu\n"
)

end_marker = '''    pushController = { [weak controller] target in
'''

start = text.find(start_marker)
end = text.find(end_marker, start)

if start == -1:
    raise RuntimeError(
        "[v1.0W style] old menu start missing"
    )

if end == -1:
    raise RuntimeError(
        "[v1.0W style] old menu end missing"
    )

replacement = '''    // MARK: GhostBase v1.0W native style page opener
    openSendTextStyleImpl = { [weak controller] in
        let selected = stateValue.with {
            $0.sendTextStyle
        }

        let styleController =
            ghostBaseSendStylePageController(
                context: context,
                selected: selected,
                select: { style in
                    updateState { current in
                        var updated = current
                        updated.sendTextStyle = style
                        return updated
                    }
                }
            )

        controller?.push(styleController)
    }

'''

text = text[:start] + replacement + text[end:]


FILE.write_text(text)

print("[v1.0W style] native style page applied")
print("[v1.0W style] broken context menu opener removed")
