import Foundation
struct PeerId: Equatable { let raw: Int64 }
final class Peer {}
struct JerkgramProfileObserverPublicName: Equatable {
    let firstName: String
    let lastName: String
}
enum AccountStateOperation {
/* ENUM_CASE */
}
struct MutableStateHarness {
    var operations: [AccountStateOperation] = []
    mutating func addOperation(_ operation: AccountStateOperation) { self.operations.append(operation) }
/* UPDATE_METHOD */
}
var state = MutableStateHarness()
let peer = Peer()
let id = PeerId(raw: 17)
let rawName = JerkgramProfileObserverPublicName(firstName: "Public", lastName: "Name")
state.updatePeer(id, { _ in peer }, jerkgramObserverPublicName: rawName)
state.updatePeer(id, { _ in peer })
// Branch/merge copies the operation itself; metadata remains attached to the
// same closure, without registry state or a separate asynchronous observation.
var branch: [AccountStateOperation] = []
branch.append(contentsOf: state.operations)
for (index, operation) in branch.enumerated() {
    switch operation {
    case let .UpdatePeer(observedId, transform, name):
        precondition(observedId == id && transform(nil) === peer)
        precondition(name == (index == 0 ? rawName : nil))
    }
}
print("Public name metadata: raw names survive operation copies; existing callers default to unknown")
