import Foundation
typealias MessageIndex = Int
struct MessageId: Hashable { let value: Int }
struct MessageHistoryViewInput {}
struct HistoryViewInputTag {}
struct MessageIdNamespaces {}
struct MessageHistoryViewOrderStatistics {}
enum HistoryViewInputAnchor { case lowerBound, upperBound, unread, index(MessageIndex), message(MessageId) }
enum HistoryViewAnchor: Equatable { case lowerBound, upperBound, index(MessageIndex) }
struct HistoryViewHoles { let holesBySpace: [Int: IndexSet] }
struct IndexTable {
    func getIndex(_ id: MessageId) -> MessageIndex? { id.value == 77 ? 770 : nil }
}
final class PostboxImpl { let messageHistoryIndexTable = IndexTable(); let storedHoles = [1: IndexSet(integersIn: 1..<1000)] }
struct HistoryViewLoadedState {
    let anchor: HistoryViewAnchor
    let holes: HistoryViewHoles
    init(anchor: HistoryViewAnchor, tag: HistoryViewInputTag?, appendMessagesFromTheSameGroup: Bool, namespaces: MessageIdNamespaces, statistics: MessageHistoryViewOrderStatistics, ignoreMessagesInTimestampRange: ClosedRange<Int32>?, ignoreMessageIds: Set<MessageId>, halfLimit: Int, locations: MessageHistoryViewInput, postbox: PostboxImpl, holes: HistoryViewHoles) { self.anchor = anchor; self.holes = holes }
}
enum HistoryViewState {
    case loaded(HistoryViewLoadedState)
    case native
    init(postbox: PostboxImpl, inputAnchor: HistoryViewInputAnchor, tag: HistoryViewInputTag?, appendMessagesFromTheSameGroup: Bool, namespaces: MessageIdNamespaces, statistics: MessageHistoryViewOrderStatistics, ignoreMessagesInTimestampRange: ClosedRange<Int32>?, ignoreMessageIds: Set<MessageId>, halfLimit: Int, locations: MessageHistoryViewInput, includeAnchorWhileLoading: Bool) { self = .native }
}
/* REAL_VIEW_FACTORY */
struct PeerIdAndNamespace: Hashable { let value: Int }
struct Entry { let index: Int }
struct OrderedHistoryViewEntries { let lowerOrAtAnchor: [Entry]; let higherThanAnchor: [Entry] }
/* REAL_NATIVE_SAMPLE_ENTRIES */
let database = PostboxImpl()
func view(_ anchor: HistoryViewInputAnchor, local: Bool) -> HistoryViewState {
    return locallyAvailableHistoryState(postbox: database, inputAnchor: anchor, tag: nil, appendMessagesFromTheSameGroup: false, namespaces: MessageIdNamespaces(), statistics: MessageHistoryViewOrderStatistics(), ignoreMessagesInTimestampRange: nil, ignoreMessageIds: [], halfLimit: 3, locations: MessageHistoryViewInput(), locallyAvailableOnly: local)
}
for (input, expected) in [(HistoryViewInputAnchor.upperBound, HistoryViewAnchor.upperBound), (.lowerBound, .lowerBound), (.unread, .upperBound), (.index(900), .index(900)), (.message(MessageId(value: 77)), .index(770))] {
    guard case let .loaded(state) = view(input, local: true) else { fatalError("sparse view stayed loading") }
    precondition(state.anchor == expected && state.holes.holesBySpace.isEmpty)
}
guard case .native = view(.upperBound, local: false) else { fatalError("ordinary history changed") }
precondition(database.storedHoles[1]!.contains(77))
let first = PeerIdAndNamespace(value: 1), second = PeerIdAndNamespace(value: 2)
let spaces = [first: OrderedHistoryViewEntries(lowerOrAtAnchor: [Entry(index: 10), Entry(index: 30), Entry(index: 50)], higherThanAnchor: [Entry(index: 70), Entry(index: 90)]), second: OrderedHistoryViewEntries(lowerOrAtAnchor: [Entry(index: 20), Entry(index: 40)], higherThanAnchor: [Entry(index: 60), Entry(index: 80)])]
let sample = sampleEntries(orderedEntriesBySpace: spaces, anchor: .index(50), halfLimit: 3)
precondition(sample.lowerOrAtAnchor.map { spaces[$0.0]!.lowerOrAtAnchor[$0.1].index } == [30, 40, 50])
precondition(sample.higherThanAnchor.map { spaces[$0.0]!.higherThanAnchor[$0.1].index } == [60, 70, 80])
print("PASS Stable182 real view factory and native pagination sampler")
