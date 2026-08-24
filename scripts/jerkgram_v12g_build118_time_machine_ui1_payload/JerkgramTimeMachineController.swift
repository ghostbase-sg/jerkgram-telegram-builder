import Foundation
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import ItemListUI
import AccountContext
import AlertUI
import JerkgramCore

// MARK: Jerkgram v1.2G BUILD118_TIME_MACHINE_UI1
private struct JerkgramTimeMachineUIState: Equatable {
    var kinds: Set<JerkgramEventKind>
    var senderPeerId: Int64?
}

private final class JerkgramTimeMachineUIArguments {
    let toggleKind: (JerkgramEventKind) -> Void
    let selectSender: () -> Void
    let selectEvent: (JerkgramCanonicalEvent) -> Void
    init(
        toggleKind: @escaping (JerkgramEventKind) -> Void,
        selectSender: @escaping () -> Void,
        selectEvent: @escaping (JerkgramCanonicalEvent) -> Void
    ) {
        self.toggleKind = toggleKind
        self.selectSender = selectSender
        self.selectEvent = selectEvent
    }
}

private enum JerkgramTimeMachineUIEntry: ItemListNodeEntry {
    case header(Int32, String)
    case filter(Int32, Int32, String, String, JerkgramEventKind?)
    case result(Int32, Int32, String, String, JerkgramCanonicalEvent)
    case info(Int32, String)

    var section: ItemListSectionId {
        switch self {
        case let .header(section, _), let .filter(section, _, _, _, _), let .result(section, _, _, _, _), let .info(section, _): return section
        }
    }
    var stableId: Int32 {
        switch self {
        case let .header(section, _): return section * 1000
        case let .filter(section, index, _, _, _), let .result(section, index, _, _, _): return section * 1000 + index
        case let .info(section, _): return section * 1000 + 999
        }
    }
    static func == (lhs: Self, rhs: Self) -> Bool { return lhs.stableId == rhs.stableId && String(describing: lhs) == String(describing: rhs) }
    static func < (lhs: Self, rhs: Self) -> Bool { return lhs.stableId < rhs.stableId }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! JerkgramTimeMachineUIArguments
        switch self {
        case let .header(_, text):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)
        case let .filter(_, _, title, value, kind):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .arrow,
                action: { if let kind { arguments.toggleKind(kind) } else { arguments.selectSender() } }
            )
        case let .result(_, _, title, value, event):
            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,
                sectionId: self.section, style: .blocks,
                disclosureStyle: .arrow, action: { arguments.selectEvent(event) }
            )
        case let .info(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func jerkgramTimeMachineRootURL() -> URL {
    return FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("Jerkgram", isDirectory: true)
}

private func jerkgramEventKindTitle(_ kind: JerkgramEventKind, strings: JerkgramStrings) -> String {
    switch kind {
    case .deletedMessage, .deletedReply: return strings.timeMachineDeleted
    case .editedMessage: return strings.timeMachineEdited
    case .recoveredMedia: return strings.timeMachineMedia
    default: return kind.rawValue
    }
}

private func jerkgramDiffText(_ event: JerkgramCanonicalEvent) -> String {
    guard event.kind == .editedMessage,
          let old = event.payload.previousText,
          let new = event.payload.text else {
        return event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
    }
    return JerkgramTextDiff.diff(old: old, new: new).map { operation in
        switch operation {
        case let .equal(value): return value
        case let .insert(value): return "[+\(value)]"
        case let .delete(value): return "[-\(value)]"
        case let .replace(old, new): return "[-\(old)] [+\(new)]"
        }
    }.joined()
}

public func jerkgramTimeMachineController(
    context: AccountContext,
    chatPeerId: Int64,
    initialQuery: String,
    eventIds: Set<JerkgramEventId>? = nil,
    navigateToMessage: @escaping (EngineMessage.Id) -> Void
) -> ViewController {
    let accountPeerId = context.account.peerId.toInt64()
    let store = JerkgramJSONLEventStore(rootURL: jerkgramTimeMachineRootURL())
    let allEvents = (try? store.events(accountPeerId: accountPeerId, chatPeerId: chatPeerId)) ?? []
    let initial = JerkgramTimeMachineUIState(
        kinds: [.deletedMessage, .deletedReply, .editedMessage, .recoveredMedia],
        senderPeerId: nil
    )
    let stateValue = Atomic(value: initial)
    let statePromise = ValuePromise(initial, ignoreRepeated: true)
    var controller: ItemListController?
    let senders = Array(Set(allEvents.compactMap(\.senderPeerId))).sorted()

    let arguments = JerkgramTimeMachineUIArguments(toggleKind: { kind in
        let value = stateValue.modify { current in
            var current = current
            if current.kinds.contains(kind) { current.kinds.remove(kind) } else { current.kinds.insert(kind) }
            return current
        }
        statePromise.set(value)
    }, selectSender: {
        let value = stateValue.modify { current in
            var current = current
            if let sender = current.senderPeerId, let index = senders.firstIndex(of: sender), index + 1 < senders.count {
                current.senderPeerId = senders[index + 1]
            } else if current.senderPeerId == nil {
                current.senderPeerId = senders.first
            } else {
                current.senderPeerId = nil
            }
            return current
        }
        statePromise.set(value)
    }, selectEvent: { event in
        if let namespace = event.messageNamespace, let id = event.messageId {
            navigateToMessage(EngineMessage.Id(
                peerId: EnginePeer.Id(event.chatPeerId),
                namespace: namespace,
                id: id
            ))
            controller?.dismiss()
        } else {
            let presentationData = context.sharedContext.currentPresentationData.with { $0 }
            let localDetail = jerkgramDiffText(event)
            controller?.present(textAlertController(
                context: context,
                title: presentationData.strings.jerkgram.timeMachine,
                text: localDetail,
                actions: [TextAlertAction(type: .defaultAction, title: presentationData.strings.Common_OK, action: {})]
            ), in: .window(.root), with: nil)
        }
    })

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let strings = presentationData.strings.jerkgram
        let needle = initialQuery.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let results = allEvents.filter { event in
            if let eventIds, !eventIds.contains(event.eventId) { return false }
            guard state.kinds.contains(event.kind) else { return false }
            if let senderPeerId = state.senderPeerId, event.senderPeerId != senderPeerId { return false }
            if !needle.isEmpty {
                let search = [event.payload.text, event.payload.previousText]
                    .compactMap { $0 }.joined(separator: " ").lowercased()
                if !search.contains(needle) { return false }
            }
            return true
        }.sorted { lhs, rhs in
            if lhs.sequence != rhs.sequence { return lhs.sequence > rhs.sequence }
            return lhs.eventId > rhs.eventId
        }
        var entries: [JerkgramTimeMachineUIEntry] = [
            .header(0, strings.timeMachineFilters),
            .filter(0, 1, strings.timeMachineDeleted, state.kinds.contains(.deletedMessage) ? "✓" : "", .deletedMessage),
            .filter(0, 2, strings.timeMachineEdited, state.kinds.contains(.editedMessage) ? "✓" : "", .editedMessage),
            .filter(0, 3, strings.timeMachineMedia, state.kinds.contains(.recoveredMedia) ? "✓" : "", .recoveredMedia),
            .filter(0, 4, strings.timeMachineAuthor, state.senderPeerId.map(String.init) ?? strings.timeMachineAllAuthors, nil),
            .header(1, strings.timeMachineResults),
        ]
        for (index, event) in results.enumerated() {
            let text = event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
            entries.append(.result(1, Int32(index + 1), String(text.prefix(80)), jerkgramEventKindTitle(event.kind, strings: strings), event))
        }
        if results.isEmpty { entries.append(.info(1, strings.timeMachineEmpty)) }
        return (
            ItemListControllerState(
                presentationData: ItemListPresentationData(presentationData),
                title: .text(strings.timeMachine), leftNavigationButton: nil,
                rightNavigationButton: nil,
                backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
            ),
            (ItemListNodeState(
                presentationData: ItemListPresentationData(presentationData),
                entries: entries, style: .blocks, animateChanges: false
            ), arguments as Any)
        )
    }
    controller = ItemListController(context: context, state: signal)
    return controller!
}
