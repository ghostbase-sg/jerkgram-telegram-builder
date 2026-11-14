func expect(_ condition: @autoclosure () -> Bool, _ message: String) {
    precondition(condition(), message)
}

var policy = JerkgramProfileRequestPolicy()
policy.enqueue(1)
expect(policy.take(now: 0) == nil, "startup must wait for storage and foreground")
policy.ready = true
policy.setForeground(true)
let first = policy.take(now: 0)!
expect(first.peerId == 1, "queued invalidation survives startup")
policy.enqueue(1)
policy.enqueue(1)
policy.finish(token: first.token, outcome: .success, now: 0)
expect(policy.count == 1, "in-flight invalidations coalesce into one follow-up")
expect(policy.wait(now: 0) == 5, "same peer spacing")
expect(policy.take(now: 4) == nil, "rate gate")
let followup = policy.take(now: 5)!
policy.finish(token: followup.token, outcome: .success, now: 5)
expect(policy.count == 0 && policy.wait(now: 50) == nil, "idle has no wakeup or polling")
policy.enqueue(2)
expect(policy.take(now: 5) == nil, "global spacing")
let second = policy.take(now: 6)!
policy.finish(token: second.token, outcome: .floodWait(30), now: 6)
expect(policy.wait(now: 6) == 30, "server flood wait dominates local spacing")
policy.enqueue(3)
expect(policy.take(now: 35) == nil, "flood wait applies across peers")
let retry = policy.take(now: 36)!
expect(retry.peerId == 2, "flooded peer retries once cooldown expires")
policy.setForeground(false)
expect(policy.take(now: 100) == nil, "background suspends queued work")
policy.finish(token: retry.token, outcome: .success, now: 100)
expect(policy.count == 2, "late cancelled result cannot consume pending work")
policy.setForeground(true)
let resumed = policy.take(now: 100)!
expect(resumed.token != retry.token, "cancellation invalidates old callbacks")
policy.finish(token: resumed.token, outcome: .permanent, now: 100)
let third = policy.take(now: 101)!
policy.finish(token: third.token, outcome: .success, now: 101)
policy.enqueue(4)
let transient = policy.take(now: 102)!
policy.finish(token: transient.token, outcome: .transient, now: 102)
let thirdRetry = policy.take(now: 107)!
policy.finish(token: thirdRetry.token, outcome: .transient, now: 107)
let finalRetry = policy.take(now: 112)!
policy.finish(token: finalRetry.token, outcome: .transient, now: 112)
expect(policy.count == 0, "transient retries are bounded")
for id in 0..<5000 { policy.enqueue(Int64(id)) }
expect(policy.count == 4096 && policy.dropped == 904, "pending memory is bounded and overflow counted")
var lru = JerkgramProfileRequestPolicy()
lru.ready = true
lru.setForeground(true)
for id in 0..<1000 {
    lru.enqueue(Int64(id))
    let request = lru.take(now: Double(id) * 10)!
    lru.finish(token: request.token, outcome: .success, now: Double(id) * 10)
}
expect(lru.cachedTimesCount <= 512, "rate timestamp memory is bounded")
expect(JerkgramProfileRequestPolicy.floodWait("FLOOD_WAIT_99") == 99, "parse flood wait")
expect(JerkgramProfileRequestPolicy.floodWait("FLOOD_PREMIUM_WAIT_12") == 12, "parse premium flood wait")
expect(JerkgramProfileRequestPolicy.floodWait("USER_ID_INVALID") == nil, "permanent error isn't a cooldown")
expect(JerkgramProfileRequestPolicy.floodWait("FLOOD_WAIT_nan") == nil, "invalid wait cannot reach timer")
expect(JerkgramProfileRequestPolicy.floodWait("FLOOD_WAIT_1e300") == nil, "overflow cannot reach timer")
// The Atomic owner mutates this same reference under its lock. A drain swaps
// in a new reference before reading the old batch, so producers cannot mutate
// a handed-off batch and incoming updates do not clone a growing Set.
var ingressOwner = JerkgramProfileRequestIngress<Int64>()
let originalIngress = ingressOwner
expect(ingressOwner.insert(7), "first insert schedules one drain")
expect(!ingressOwner.insert(7), "duplicate must not schedule another drain")
for id in 0..<5000 { _ = ingressOwner.insert(Int64(id)) }
expect(originalIngress === ingressOwner, "burst mutates one reference owner")
expect(ingressOwner.peers.count == 4096 && ingressOwner.overflow, "ingress is bounded before queue admission")
let drainedIngress = ingressOwner
let drainedPeers = drainedIngress.peers
// Dropping the Atomic's old reference transfers it to the consumer.
ingressOwner = JerkgramProfileRequestIngress<Int64>()
expect(ingressOwner.insert(6000), "new batch schedules its own drain")
expect(drainedIngress.peers == drainedPeers && !drainedIngress.peers.contains(6000), "new producers cannot mutate drained batch")
print("Profile observer request policy: all checks passed")
