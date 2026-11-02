// Unavoidable facades: transport submits/calls back; Signal is cold; parameters
// deliberately trap. Both Network methods are inserted verbatim below.
protocol Disposable: AnyObject { func dispose() }
final class ActionDisposable: Disposable {
    private let lock = NSLock(); private var action: (() -> Void)?
    init(_ action: @escaping () -> Void) { self.action = action }
    func dispose() { lock.lock(); let value = action; action = nil; lock.unlock(); value?() }
}
final class SpyDisposable: Disposable { var count = 0; func dispose() { count += 1 } }
final class Subscriber<T, E: Error> {
    let next: (T) -> Void; let error: (E) -> Void; let completion: () -> Void
    init(_ next: @escaping (T) -> Void, _ error: @escaping (E) -> Void, _ completion: @escaping () -> Void) { self.next = next; self.error = error; self.completion = completion }
    func putNext(_ value: T) { next(value) }; func putError(_ value: E) { error(value) }; func putCompletion() { completion() }
}
final class Signal<T, E: Error> {
    let generator: (Subscriber<T, E>) -> Disposable
    init(_ generator: @escaping (Subscriber<T, E>) -> Disposable) { self.generator = generator }
    func start(next: @escaping (T) -> Void = { _ in }, error: @escaping (E) -> Void = { _ in }, completed: @escaping () -> Void = {}) -> Disposable { generator(Subscriber(next,error,completed)) }
}
final class FunctionDescription {
    let name: String
    init(_ name: String) { self.name = name }
    var parameters: [String] { preconditionFailure("PRIVATE_TEXT_TOKEN_PATH_QUOTE sentinel loader touched") }
}
struct Buffer { let data: Data; init(data: Data = Data()) { self.data = data }; func makeData() -> Data { data } }
struct DeserializeFunctionResponse<T> { let parse: (Buffer) -> T? }
struct BoxedMessage { let body: Any; init(_ body: Any) { self.body = body } }
final class NetworkRequestDependencyTag {}
struct WrappedFunctionDescription { let value: FunctionDescription; init(_ value: FunctionDescription) { self.value = value } }
struct WrappedShortFunctionDescription { init(_ value: FunctionDescription) {} }
struct WrappedRequestMetadata { let metadata: WrappedFunctionDescription; let tag: NetworkRequestDependencyTag? }
struct WrappedRequestShortMetadata { let shortMetadata: WrappedShortFunctionDescription }
struct NetworkEngineRequestOptions {}
struct NetworkEngineErrorContext { let floodWaitSeconds: Int }
final class MTRpcError: Error { let errorCode: Int32; let errorDescription: String; init(errorCode: Int32, errorDescription: String) { self.errorCode = errorCode; self.errorDescription = errorDescription } }
struct Response { let result: Any }
struct Failure { let error: MTRpcError }
enum TransportResult { case success(Response), failure(Failure) }
final class NetworkEngineRequest {
    let metadata: WrappedRequestMetadata
    let parse: (Data) -> BoxedMessage?
    let shouldContinueAfterError: (NetworkEngineErrorContext) -> Bool
    let acknowledged: (() -> Void)?
    let completed: (TransportResult) -> Void
    let spy = SpyDisposable()
    init(payload: Data, metadata: WrappedRequestMetadata, shortMetadata: WrappedRequestShortMetadata, parse: @escaping (Data) -> BoxedMessage?, options: NetworkEngineRequestOptions, shouldContinueAfterError: @escaping (NetworkEngineErrorContext) -> Bool, dependsOn: ((WrappedRequestMetadata) -> Bool)?, acknowledged: (() -> Void)?, progress: ((Float, Int) -> Void)?, completed: @escaping (TransportResult) -> Void) {
        self.metadata = metadata; self.parse = parse; self.shouldContinueAfterError = shouldContinueAfterError; self.acknowledged = acknowledged; self.completed = completed
    }
}
final class RequestService {
    var requests: [NetworkEngineRequest] = []
    func add(_ value: NetworkEngineRequest) -> Disposable { requests.append(value); return value.spy }
}
func networkRequestErrorPolicy(automaticFloodWait: Bool, onFloodWaitError: ((String) -> Void)?, failOnServerErrors: Bool) -> (NetworkEngineErrorContext) -> Bool { return { context in automaticFloodWait || context.floodWaitSeconds == 0 } }
func networkRequestDependency(tag: NetworkRequestDependencyTag?) -> ((WrappedRequestMetadata) -> Bool)? { nil }
struct NetworkRequestAdditionalInfo: OptionSet { let rawValue: Int; static let acknowledgement = Self(rawValue: 1); static let progress = Self(rawValue: 2) }
enum NetworkRequestResult<T> { case acknowledged, progress(Float, Int32), result(T) }
final class Network {
    let requestService = RequestService()
    let botBridgeRegistration = BotBridgeScopeRegistration()
    /* REAL_REQUESTS */
}
class Peer {}
final class TelegramChannel: Peer { enum Info { case broadcast, group }; let info: Info; init(_ info: Info) { self.info = info } }
protocol MessageAttribute {}
struct ReplyMessageAttribute: MessageAttribute {}
struct ReplyStoryAttribute: MessageAttribute {}
/* REAL_WORKER_CONTEXT */
func check(_ value: @autoclosure () -> Bool, _ message: String) { precondition(value(), message) }
let data = (FunctionDescription("messages.sendMessage"), Buffer(), DeserializeFunctionResponse<Int>(parse: { _ in 42 }))
// Unsubscribed construction creates no attempt; ordinary requests return exact original disposable.
let user = Network(); let ordinary = user.request(data)
check(user.requestService.requests.isEmpty, "constructed is not submitted")
let u = ordinary.start(); check(u === user.requestService.requests[0].spy, "direct ordinary disposable")
check(botBridgeOperationContext(network: user, peer: Peer(), attributes: [ReplyMessageAttribute()], hasText: true) == nil, "ordinary worker context factory gates before allocating logical UUID")
let sinkRoot = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
let sink = BotBridgeDiagnosticSink(root: sinkRoot)
let scope = BotBridgeDiagnosticScope(generation: UUID().uuidString, sink: sink, cancelHistory: { _ in })
var network: Network? = Network(); network!.botBridgeRegistration.install(scope)
let context = botBridgeOperationContext(network: network!, peer: TelegramChannel(.broadcast), attributes: [ReplyMessageAttribute()], hasText: true)!
check(context.flags == [.reply, .post, .text], "resolved broadcast reply text")
let forum = botBridgeOperationContext(network: network!, peer: TelegramChannel(.group), attributes: [], hasText: false)!
check(forum.flags.isEmpty, "forum routing and megagroup alone are neither reply nor broadcast")
let tag = NetworkRequestDependencyTag()
let signal = network!.requestWithAdditionalInfo(data, info: .acknowledgement, tag: tag, automaticFloodWait: false, diagnosticContext: context)
check(scope.snapshotEvents().isEmpty, "cold request")
var values = 0
let one = signal.start(next: { _ in values += 1 })
let service = network!.requestService; let request = service.requests[0]
check(request.metadata.tag === tag, "original dependency tag identity")
check(request.parse(Data())?.body as? Int == 42, "original parser preserved")
check(!request.shouldContinueAfterError(NetworkEngineErrorContext(floodWaitSeconds: 3)), "original policy result")
request.acknowledged?(); request.completed(.success(Response(result: BoxedMessage(42))))
one.dispose(); one.dispose()
check(values == 2 && request.spy.count == 1, "ack and result, underlying once")
check(scope.snapshotEvents().filter { $0.phase == .cancelled }.isEmpty, "completion disposal not cancellation")
let two = signal.start(); two.dispose(); two.dispose(); service.requests[1].completed(.success(Response(result: BoxedMessage(42))))
check(service.requests[1].spy.count == 1, "cancel exactly once")
check(scope.snapshotEvents().filter { $0.phase == .cancelled }.count == 1, "late result loses race")
check(scope.snapshotEvents().filter { $0.phase == .submitted }.map { $0.attempt } == [1,2], "resubscription attempts")
var observedError: MTRpcError?
let three = network!.request(data).start(error: { observedError = $0 })
let failure = MTRpcError(errorCode: 401, errorDescription: "PRIVATE_TOKEN_ERROR")
service.requests[2].completed(.failure(Failure(error: failure))); three.dispose()
check(observedError === failure, "original error identity")
let four = network!.request(data).start(error: { observedError = $0 })
check(service.requests[3].acknowledged == nil, "ack availability unchanged")
service.requests[3].completed(.success(Response(result: BoxedMessage("not Int")))); four.dispose()
check(observedError?.errorDescription == "TL_VERIFICATION_ERROR", "parse failure remains original")
check(scope.snapshotEvents().contains { $0.phase == .parseFailure && $0.errorCode == 500 }, "finite parse diagnostics")
let raced = network!.request(data).start()
let racedRequest = service.requests.last!
let racedId = scope.snapshotEvents().last { $0.phase == .submitted }!.request
DispatchQueue.concurrentPerform(iterations: 2) { index in
    if index == 0 { racedRequest.completed(.success(Response(result: BoxedMessage(42)))) } else { raced.dispose() }
}
raced.dispose()
check(racedRequest.spy.count == 1, "concurrent cancel-result disposes underlying exactly once")
check(scope.snapshotEvents().filter { $0.request == racedId && ($0.phase == .result || $0.phase == .cancelled) }.count == 1, "concurrent terminal race has one diagnostic winner")
weak var weakNetwork = network; network = nil
check(weakNetwork == nil, "Signal owns no Network")
let encoded = try! JSONEncoder().encode(scope.snapshotEvents())
check(!String(data: encoded, encoding: .utf8)!.contains("PRIVATE"), "error and lazy-parameter sentinels absent")
print("PASS actual Network request methods: cold, direct path, ack, parse, error, race, resubscription, disposal, deallocation")
