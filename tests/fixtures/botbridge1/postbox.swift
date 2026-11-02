import Foundation
struct PeerId: Hashable { let value: Int }
struct MessageId: Comparable, Hashable {
    typealias Namespace = Int
    let peerId: PeerId; let namespace: Int; let id: Int32
    static func <(a: Self, b: Self) -> Bool { return a.id < b.id }
}
enum StoreMessageId { case Id(MessageId) }
struct StoreMessage { let id: StoreMessageId; let tag: Int }
enum AddMessagesLocation { case Random, UpperHistoryBlock }
final class Bag<T> { var values: [T] = []; func copyItems() -> [T] { return values } }
final class StoreHook { var callback: ([StoreMessage], Transaction) -> Void; init(_ callback: @escaping ([StoreMessage], Transaction) -> Void) { self.callback = callback }; func addOrUpdate(messages: [StoreMessage], transaction: Transaction) { callback(messages, transaction) } }
final class History {
    var stored: [MessageId: StoreMessage] = [:]; var tags: [Int] = []; var indexes = 0
    func addMessages(messages: [StoreMessage], operationsByPeerId: inout Int, updatedMedia: inout Int, unsentMessageOperations: inout Int, updatedPeerReadStateOperations: inout Int, globalTagsOperations: inout Int, pendingActionsOperations: inout Int, updatedMessageActionsSummaries: inout Int, updatedMessageTagSummaries: inout Int, invalidateMessageTagSummaries: inout Int, localTagsOperations: inout Int, timestampBasedMessageAttributesOperations: inout Int, processMessages: ([PeerId: [StoreMessage]]) -> Void) -> [Int64: MessageId] {
        var grouped: [PeerId: [StoreMessage]] = [:]; var result: [Int64: MessageId] = [:]
        for message in messages { if case let .Id(id) = message.id { stored[id] = message; indexes += 1; tags.append(message.tag); grouped[id.peerId, default: []].append(message); result[Int64(id.id)] = id } }
        processMessages(grouped); return result
    }
}
final class Holes {
    enum Space { case everywhere }; var count = 0
    func remove(peerId: PeerId, namespace: Int, space: Space, range: ClosedRange<Int32>, operations: inout Int) { count += 1 }
}
final class PostboxImpl {
    let messageHistoryTable = History(); let messageHistoryHoleIndexTable = Holes()
    var currentOperationsByPeerId = 0, currentUpdatedMedia = 0, currentUnsentOperations = 0, currentUpdatedSynchronizeReadStateOperations = 0, currentGlobalTagsOperations = 0, currentPendingMessageActionsOperations = 0, currentUpdatedMessageActionsSummaries = 0, currentUpdatedMessageTagSummaries = 0, currentInvalidateMessageTagSummaries = 0, currentLocalTagsOperations = 0, currentTimestampBasedMessageAttributesOperations = 0, currentPeerHoleOperations = 0
    var installedMessageActionsByPeerId: [PeerId: Bag<([StoreMessage], Transaction)->Void>] = [:]
    var installedStoreOrUpdateMessageActionsByPeerId: [PeerId: Bag<StoreHook>] = [:]
    /* REAL_IMPL */
}
final class Transaction {
    let disposed = false; let postbox: PostboxImpl?
    init(_ p: PostboxImpl) { postbox = p }
    /* REAL_ENTRIES */
}
let peer = PeerId(value: 1); let p = PostboxImpl(); let t = Transaction(p)
var events: [String] = []; var consume = 0, reactions = 0, maxRead = 0, wallet = 0
let insertion = Bag<([StoreMessage], Transaction)->Void>()
insertion.values = [{ messages, transaction in
    precondition(transaction === t && messages.count == 1)
    events.append("interactive"); consume += 1; reactions += 1; maxRead += 1
}]
p.installedMessageActionsByPeerId[peer] = insertion
let updates = Bag<StoreHook>()
updates.values = [StoreHook({ messages, transaction in precondition(transaction === t && messages.count == 1); events.append("visibleReaction"); reactions += 1 }), StoreHook({ _, _ in events.append("wallet"); wallet += 1 })]
p.installedStoreOrUpdateMessageActionsByPeerId[peer] = updates
func message(_ n: Int32) -> StoreMessage { return StoreMessage(id: .Id(MessageId(peerId: peer, namespace: 0, id: n)), tag: 7) }
let historical = t.addHistoricalMessagesWithoutInteractiveActions([message(1)])
precondition(events.isEmpty && consume == 0 && reactions == 0 && maxRead == 0 && wallet == 0)
precondition(historical[1]?.id == 1 && p.messageHistoryTable.indexes == 1 && p.messageHistoryTable.tags == [7] && p.messageHistoryHoleIndexTable.count == 0)
let ordinary = t.addMessages([message(2)], location: .Random)
precondition(events == ["interactive", "visibleReaction", "wallet"] && ordinary[2]?.id == 2)
precondition(consume == 1 && reactions == 2 && maxRead == 1 && wallet == 1)
_ = t.addHistoricalMessagesWithoutInteractiveActions([message(3)])
precondition(events.count == 3 && p.messageHistoryTable.indexes == 3 && p.messageHistoryHoleIndexTable.count == 0)
_ = t.addMessages([message(4)], location: .UpperHistoryBlock)
precondition(events.count == 6 && p.messageHistoryHoleIndexTable.count == 1)
print("PASS real Postbox entries/implementation: callback suppression, mixed transaction, IDs, storage boundary, Random and UpperHistoryBlock")
