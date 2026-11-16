import Foundation

func require(_ value: @autoclosure () -> Bool, _ label: String) {
    if !value() { fatalError(label) }
}
let ingress = JerkgramProfileObserverAdmission<Int>(capacity: 3)
let generation = ingress.start()
ingress.loaded(generation: generation)
var projections = 0
require(!ingress.enqueue(peerId: 7, enroll: false, make: { projections += 1; return 1 }), "no-watch dispatch")
require(projections == 0, "no-watch work")
require(ingress.enqueue(peerId: 7, enroll: true, make: { projections += 1; return 11 }), "first drain")
require(!ingress.enqueue(peerId: 7, enroll: false, make: { return 12 }), "one drain only")
require(!ingress.enqueue(peerId: 7, enroll: false, make: { return 13 }), "one drain only2")
require(!ingress.enqueue(peerId: 7, enroll: false, make: { projections += 1; return 14 }), "bounded overflow")
require(projections == 1, "overflow must not evaluate event")
require(ingress.take(generation: generation) == 11, "FIFO1")
require(ingress.take(generation: generation) == 12, "FIFO2")
require(ingress.take(generation: generation) == 13, "FIFO3")
require(ingress.take(generation: generation) == nil, "empty")
require(ingress.takeDropped(generation: generation) == 1, "visible gap")
require(ingress.takeDropped(generation: generation) == 0, "gap once")
require(ingress.enqueue(peerId: 7, enroll: false, make: { return 15 }), "new drain after empty")
ingress.stop()
require(ingress.take(generation: generation) == nil, "stale work cancelled")
require(!ingress.enqueue(peerId: 7, enroll: true, make: { fatalError("inactive work") }), "inactive")
let next = ingress.start()
ingress.loaded(generation: next)
require(next != generation, "new generation")
require(ingress.take(generation: generation) == nil, "old drain cannot consume new events")
require(!ingress.enqueue(peerId: 4, enroll: true, generation: generation, make: { fatalError("stale admission") }), "stale submit cannot lock fresh drain")
for i in 1...10000 { ingress.addWatched(Int64(i)) }
for i in 1...10000 { require(ingress.mightWatch(Int64(i)), "Bloom false negative") }
require(ingress.enqueue(peerId: 4, enroll: false, make: { return 99 }), "restored membership")
require(ingress.take(generation: generation) == nil, "stale drain with fresh pending")
require(ingress.take(generation: next) == 99, "fresh pending remains")
require(ingress.take(generation: next) == nil, "fresh drain ends")
let start = ProcessInfo.processInfo.systemUptime
for i in 0..<100000 { _ = ingress.mightWatch(Int64(1000000+i)) }
print("admission PASS: fixed 64KiB Bloom, bounded FIFO/gaps, no irrelevant work, generation isolation; 100k membership seconds=\(ProcessInfo.processInfo.systemUptime-start)")
