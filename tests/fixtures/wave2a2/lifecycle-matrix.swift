let a = AccountContext(), b = AccountContext()
var owner: JerkgramDiagnosticSettingsController? = makeOwner(a, page: .about)
weak var weakOwner = owner
check(a.tracker.activeHistory == (fixed ? 0 : 2), "initial readiness does not require view appearance")
owner!.viewWillAppear(false); owner!.viewDidAppear(false)
check(a.tracker.activeHistory == 2 && a.tracker.activePoll == 2, "two necessary visible channel feeds")
let firstStarts = a.tracker.starts
owner!.viewDidAppear(false)
check(a.tracker.starts == firstStarts, "repeated didAppear never duplicates feeds")
owner!.viewWillDisappear(false)
check(a.tracker.activeHistory == (fixed ? 0 : 2) && a.tracker.activePoll == (fixed ? 0 : 2), "hidden history and poll ownership")
let hiddenDeliveries = a.tracker.deliveries
a.tracker.deliver()
check(a.tracker.deliveries - hiddenDeliveries == (fixed ? 0 : 2), "hidden and disposed late callbacks")
for _ in 0..<20 {
    owner!.viewWillAppear(false);owner!.viewDidAppear(false)
    check(a.tracker.activeHistory == 2 && a.tracker.maxActive == 2, "A-B-A pages never accumulate subscriptions")
    let delivered = a.tracker.deliveries; a.tracker.deliver()
    check(a.tracker.deliveries == delivered + 2, "current visible feeds receive required updates")
    owner!.viewWillDisappear(false)
}
owner = nil
check(weakOwner == nil && a.tracker.activeHistory == 0 && a.tracker.activePoll == 0 && a.tracker.disposals == a.tracker.starts, "destroy in-flight owner releases subscriptions")
let goneDeliveries = a.tracker.deliveries;a.tracker.deliver();check(a.tracker.deliveries == goneDeliveries, "destroyed owner rejects late callbacks")
owner = makeOwner(b, page: .about);owner!.viewWillAppear(false);owner!.viewDidAppear(false)
check(a.tracker.activeHistory == 0 && b.tracker.activeHistory == 2, "account B has separate request owner")
let bDelivered = b.tracker.deliveries;a.tracker.deliver();check(b.tracker.deliveries == bDelivered, "old account callback cannot update B")
owner = nil
let media = makeOwner(b, page: .media);media.viewWillAppear(false);media.viewDidAppear(false)
check(b.tracker.activeHistory == 0 && b.tracker.activePoll == 0, "non-About pages perform no channel work")
print("\(fixed ? "AFTER" : "BEFORE") visible history/poll=2/2 hidden=\(fixed ? "0/0" : "2/2") hidden deliveries=\(fixed ? "0" : "2") maxActive=\(a.tracker.maxActive) destroyed=0 account-isolation=PASS")
