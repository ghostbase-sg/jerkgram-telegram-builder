// Boundary fixtures only. Python inserts the complete production wrapper class
// unchanged; its cache, comparison and update methods are the code under test.
import Foundation

enum PeerInfoPaneKey { case test }
struct DeviceMetrics {}
final class PresentationData {}
enum ContainedViewLayoutTransition { case immediate }
final class ViewController {}

protocol PeerInfoPaneNode: AnyObject {
    var parentController: ViewController? { get set }
    func removeFromSupernode()
    func updateJerkgramVisualState(glassEnabled: Bool, revision: UInt64)
    func update(size: CGSize, topInset: CGFloat, sideInset: CGFloat, bottomInset: CGFloat, deviceMetrics: DeviceMetrics, visibleHeight: CGFloat, isScrollingLockedAtTop: Bool, expandProgress: CGFloat, navigationHeight: CGFloat, presentationData: PresentationData, synchronous: Bool, transition: ContainedViewLayoutTransition)
}

final class ObservedPane: PeerInfoPaneNode {
    var parentController: ViewController?
    var layouts = 0
    var visualUpdates = 0
    var glassEnabled = false
    var revision: UInt64 = 0
    func removeFromSupernode() {}
    func updateJerkgramVisualState(glassEnabled: Bool, revision: UInt64) {
        self.visualUpdates += 1
        self.glassEnabled = glassEnabled
        self.revision = revision
    }
    func update(size: CGSize, topInset: CGFloat, sideInset: CGFloat, bottomInset: CGFloat, deviceMetrics: DeviceMetrics, visibleHeight: CGFloat, isScrollingLockedAtTop: Bool, expandProgress: CGFloat, navigationHeight: CGFloat, presentationData: PresentationData, synchronous: Bool, transition: ContainedViewLayoutTransition) {
        self.layouts += 1
    }
}

// INSERT_PRODUCTION_WRAPPER

let node = ObservedPane()
let wrapper = PeerInfoPaneWrapper(key: .test, node: node)
let data = PresentationData()
func layout() {
    wrapper.update(size: CGSize(width: 390, height: 800), topInset: 20, sideInset: 16, bottomInset: 34, deviceMetrics: DeviceMetrics(), visibleHeight: 700, isScrollingLockedAtTop: false, expandProgress: 1, navigationHeight: 44, presentationData: data, synchronous: true, transition: .immediate)
}
wrapper.updateJerkgramVisualState(glassEnabled: true, revision: 1)
layout()
precondition(node.layouts == 1 && node.visualUpdates == 1 && node.glassEnabled && node.revision == 1)
wrapper.updateJerkgramVisualState(glassEnabled: true, revision: 1)
layout()
precondition(node.layouts == 1 && node.visualUpdates == 1, "same revision/layout must stay cached")
wrapper.updateJerkgramVisualState(glassEnabled: true, revision: 2)
layout()
precondition(node.layouts == 2 && node.visualUpdates == 2 && node.revision == 2, "new visual revision must bypass same-layout cache")
wrapper.updateJerkgramVisualState(glassEnabled: false, revision: 2)
layout()
precondition(node.layouts == 3 && node.visualUpdates == 3 && !node.glassEnabled, "changed policy must reconcile even with same revision")
precondition(wrapper.node === node, "revision must preserve pane identity")
print("production wrapper revision runtime PASS")
