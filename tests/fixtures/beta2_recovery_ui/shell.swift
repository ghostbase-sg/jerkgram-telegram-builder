// Synchronous fixture boundaries for real production policy/snapshot/transaction code.
// Not a database, Postbox codec, SwiftSignalKit scheduler, or app runtime substitute.
enum NoError: Error {}
struct Signal<Value, Failure: Error> { let value: Value }
infix operator |> : AdditionPrecedence
func |> <A, B>(value: A, transform: (A) -> B) -> B { return transform(value) }
func map<A, B, E: Error>(_ transform: @escaping (A) -> B) -> (Signal<A, E>) -> Signal<B, E> { return { Signal(value: transform($0.value)) } }
func mapToSignal<A, B, E: Error>(_ transform: @escaping (A) -> Signal<B, E>) -> (Signal<A, E>) -> Signal<B, E> { return { transform($0.value) } }
func take<A, E: Error>(_ count: Int) -> (Signal<A, E>) -> Signal<A, E> { return { $0 } }
func combineLatest<A, B, C, E: Error>(_ a: Signal<A, E>, _ b: Signal<B, E>, _ c: Signal<C, E>) -> Signal<(A, B, C), E> { return Signal(value: (a.value, b.value, c.value)) }
struct PeerId: Hashable { let value: Int64; func toInt64() -> Int64 { return value } }
struct Peer { var isPremium: Bool }
public enum ChatListFilter: Equatable { case allChats; case folder(Int32); public var id: Int32 { switch self { case .allChats: return 0; case let .folder(id): return id } } }
struct AppConfiguration: Codable { let limit: Int32; static let defaultValue = AppConfiguration(limit: 2) }
struct UserLimitsConfiguration { let maxFoldersCount: Int32; init(appConfiguration: AppConfiguration, isPremium: Bool) { self.maxFoldersCount = appConfiguration.limit } }
public enum EngineConfiguration { public struct UserLimits { let maxFoldersCount: Int32; init(_ configuration: UserLimitsConfiguration) { self.maxFoldersCount = configuration.maxFoldersCount } } }
enum PreferencesKeys { static let chatListFilters = 1; static let jerkgramDefaultFolderOrder = 2; static let appConfiguration = 3 }
struct PreferencesEntry {
    let value: Any
    init<T>(_ value: T) { self.value = value }
    func get<T>(_ type: T.Type) -> T? { return self.value as? T }
}
struct ChatListFiltersState { let filters: [ChatListFilter]; static let `default` = ChatListFiltersState(filters: [.allChats]) }
enum PostboxViewKey: Hashable { case preferences(keys: Set<Int>); case basicPeer(PeerId) }
struct PreferencesView { let values: [Int: PreferencesEntry] }
struct BasicPeerView { let peer: Peer? }
struct CombinedView { let views: [PostboxViewKey: Any] }
final class Transaction {
    var entries: [Int: PreferencesEntry] = [:]
    var peer: Peer? = Peer(isPremium: false)
    var filters: [ChatListFilter] = [.allChats, .folder(2), .folder(3), .folder(4)]
    var reads = 0
    var writes = 0
    var nativeWrites = 0
    func getPeer(_ id: PeerId) -> Peer? { return self.peer }
    func getPreferencesEntry(key: Int) -> PreferencesEntry? { self.reads += 1; return self.entries[key] }
    func updatePreferencesEntry(key: Int, _ transform: (PreferencesEntry?) -> PreferencesEntry?) { self.writes += 1; self.entries[key] = transform(self.entries[key]) }
}
final class Postbox {
    let storage = Transaction()
    func transaction<T>(_ transform: (Transaction) -> T) -> Signal<T, NoError> { return Signal(value: transform(storage)) }
    func combinedView(keys: [PostboxViewKey]) -> Signal<CombinedView, NoError> {
        var views: [PostboxViewKey: Any] = [:]
        var entries = storage.entries
        entries[PreferencesKeys.chatListFilters] = PreferencesEntry(ChatListFiltersState(filters: storage.filters))
        for key in keys {
            switch key {
            case .preferences: views[key] = PreferencesView(values: entries)
            case .basicPeer: views[key] = BasicPeerView(peer: storage.peer)
            }
        }
        return Signal(value: CombinedView(views: views))
    }
}
final class ViewTracker { var hiddenChatListFilterIds = Signal<Set<Int32>, NoError>(value: []) }
final class Account { let peerId: PeerId; let postbox = Postbox(); let viewTracker = ViewTracker(); init(_ id: Int64) { self.peerId = PeerId(value: id) } }
func jerkgramFolderPolicy(accountPeerId: Int64) -> Signal<(enabled: Bool, generation: UInt64), NoError> { return Signal(value: JerkgramDefaultFolderSettings.snapshot(accountPeerId: accountPeerId)) }
func _internal_currentChatListFiltersState(transaction: Transaction) -> ChatListFiltersState { return ChatListFiltersState(filters: transaction.filters) }
func _internal_updateChatListFiltersInteractively(transaction: Transaction, _ transform: ([ChatListFilter]) -> [ChatListFilter]) { transaction.nativeWrites += 1; transaction.filters = transform(transaction.filters) }
