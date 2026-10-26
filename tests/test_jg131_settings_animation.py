"""Animation wiring/lifecycle contracts; runtime continuity requires iOS."""
from pathlib import Path
import os, unittest, shutil, subprocess, tempfile
ROOT=Path(os.environ.get('JG_SETTINGS_SOURCE',Path(__file__).resolve().parents[1]/'work/swiftgram-src'))
OWNER='submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift'
class SettingsAnimationTests(unittest.TestCase):
 def test_descendants_use_native_clock_and_release_offscreen(self):
  s=(ROOT/OWNER).read_text()
  self.assertIn('private final class JerkgramSettingsPlaybackSession',s)
  session=s.split('private final class JerkgramSettingsPlaybackSession',1)[1].split('private final class JerkgramSettingsBackdropView',1)[0]
  self.assertNotIn('UniversalVideoNode(',session)
  self.assertIn('setCanPlaybackWithoutHierarchy(true)',session)
  self.assertIn('setCanPlaybackWithoutHierarchy(false)',session)
  self.assertIn('registerSecondaryVideoLayer',session)
  self.assertIn('willResignActiveNotification',session)
  self.assertIn('didBecomeActiveNotification',session)
  view=s.split('private final class JerkgramSettingsBackdropView',1)[1].split('final class GhostBaseProfileBackgroundView',1)[0]
  self.assertIn('self.addSubview(self.mirrorVideoView)',view)
  self.assertIn('override func didMoveToWindow()',view)
  self.assertIn('self.playbackDisposable?.dispose()',view)
 def test_secondary_output_disposes_on_main_before_a_rebind(self):
  owner='submodules/AccountContext/Sources/UniversalVideoNode.swift'
  p=ROOT/owner
  self.assertTrue(p.exists(), 'secondary output race fix owner missing')
  body=p.read_text().split('public func registerSecondaryVideoLayer(',1)[1].split('public func play()',1)[0]
  self.assertIn('if Queue.mainQueue().isCurrent()',body)
  self.assertIn('removeOutput()',body)
 def test_no_new_opacity_or_decode_pipeline(self):
  s=(ROOT/OWNER).read_text()
  update=s.split('private func updateSettingsBackdrop(',1)[1].split('private func updateSettingsBackdrops()',1)[0]
  self.assertIn('backdrop.blurView.alpha = self.blurView.alpha',update)
  self.assertIn('backdrop.tintView.alpha = self.tintView.alpha',update)
  self.assertIn('backdrop.setPlaybackSession(session)',update)
 @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; actual secondary-output fixture runs on macOS CI')
 def test_actual_secondary_output_dispose_rebind_order(self):
  source=(ROOT/'submodules/AccountContext/Sources/UniversalVideoNode.swift').read_text()
  method='    public func registerSecondaryVideoLayer('+source.split('    public func registerSecondaryVideoLayer(',1)[1].split('    public func play()',1)[0]
  owner='final class OutputOwner {let manager=Manager();let content=Content();'+method+'}'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift';p.write_text('import Foundation\n'+OUTPUT_MOCKS+owner+OUTPUT_CHECKS)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
 @unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable; actual session fixture runs on macOS CI')
 def test_actual_session_visibility_suspension_overlap_and_release(self):
  s=(ROOT/OWNER).read_text().split('// JG174 playback session begin\n',1)[1].split('// JG174 playback session end',1)[0]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'main.swift'
   p.write_text('import Foundation\n'+MOCKS+s.replace('private final class JerkgramSettingsPlaybackSession','final class JerkgramSettingsPlaybackSession',1)+FIXTURE)
   subprocess.run(['swiftc',str(p),'-o',d+'/check'],check=True)
   subprocess.run([d+'/check'],check=True)
MOCKS = r'''
protocol Disposable { func dispose() }
final class ActionDisposable: Disposable {
 var body: (() -> Void)?
 init(_ body: @escaping () -> Void) { self.body = body }
 func dispose() { let body = self.body; self.body = nil; body?() }
 deinit { self.dispose() }
}
final class AVSampleBufferDisplayLayer: NSObject {}
final class UIApplication {
 enum State { case active, inactive }
 static let shared = UIApplication()
 var applicationState = State.active
 static let willResignActiveNotification = Notification.Name("inactive")
 static let didBecomeActiveNotification = Notification.Name("active")
}
final class UniversalVideoNode {
 var withoutHierarchy = false
 var plays = 0
 var outputs = 0
 func setCanPlaybackWithoutHierarchy(_ value: Bool) { self.withoutHierarchy = value }
 func play() { self.plays += 1 }
 func registerSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) -> Disposable? {
  self.outputs += 1
  return ActionDisposable { [weak self] in self?.outputs -= 1 }
 }
}
'''
FIXTURE = r'''
let session = JerkgramSettingsPlaybackSession()
var source: UniversalVideoNode? = UniversalVideoNode()
weak var weakSource = source
session.updateSource(source)
let firstLayer = AVSampleBufferDisplayLayer(), secondLayer = AVSampleBufferDisplayLayer()
let first = session.attach(firstLayer)
assert(source!.withoutHierarchy && source!.plays == 1 && source!.outputs == 1)
let second = session.attach(secondLayer)
assert(source!.outputs == 2 && source!.plays == 1)
first.dispose()
assert(source!.outputs == 1 && source!.withoutHierarchy)
source = nil
assert(weakSource != nil) // original avatar removed: child keeps the same clock
session.updateSource(nil)
assert(weakSource?.outputs == 1)
NotificationCenter.default.post(name: UIApplication.willResignActiveNotification, object: nil)
assert(weakSource != nil && weakSource!.outputs == 0 && !weakSource!.withoutHierarchy)
NotificationCenter.default.post(name: UIApplication.didBecomeActiveNotification, object: nil)
assert(weakSource!.outputs == 1 && weakSource!.withoutHierarchy && weakSource!.plays == 2)
second.dispose()
assert(weakSource == nil) // last visible output leaves: no player retained
var next: UniversalVideoNode? = UniversalVideoNode()
session.updateSource(next)
let again = session.attach(firstLayer)
session.invalidate()
assert(next!.outputs == 0 && !next!.withoutHierarchy)
weak var weakNext = next
next = nil
assert(weakNext == nil)
again.dispose()
print("settings native shared playback session PASS")
'''
OUTPUT_MOCKS = 'protocol Disposable { func dispose() }\nfinal class ActionDisposable: Disposable {\n var body:(()->Void)?;init(_ body:@escaping ()->Void){self.body=body}\n func dispose(){let body=self.body;self.body=nil;body?()}\n deinit {self.dispose()}\n}\nfinal class Queue {\n static let main=Queue();var current=true;var pending:[()->Void]=[]\n static func mainQueue()->Queue {main}\n func isCurrent()->Bool {current}\n func async(_ body:@escaping ()->Void) {pending.append(body)}\n func flush(){while !pending.isEmpty {pending.removeFirst()()}}\n}\nfinal class AVSampleBufferDisplayLayer:NSObject { var flushes=0;func flushAndRemoveImage(){flushes += 1} }\nprotocol UniversalVideoSecondaryOutputContentNode {func removeSecondaryVideoLayer(_ layer:AVSampleBufferDisplayLayer)}\nfinal class ContentNode:UniversalVideoSecondaryOutputContentNode {\n var layers=Set<ObjectIdentifier>()\n func removeSecondaryVideoLayer(_ layer:AVSampleBufferDisplayLayer){layers.remove(ObjectIdentifier(layer))}\n}\nfinal class Manager {\n let node=ContentNode()\n func withUniversalVideoContent(id:AnyHashable,_ body:(AnyObject?)->Void){body(node)}\n}\nenum GhostBaseUniversalVideoSecondaryOutputRegistry {\n static var layers=Set<ObjectIdentifier>()\n static func register(manager:AnyObject,contentId:AnyHashable,layer:AVSampleBufferDisplayLayer){layers.insert(ObjectIdentifier(layer))}\n static func unregister(manager:AnyObject,contentId:AnyHashable,layer:AVSampleBufferDisplayLayer){layers.remove(ObjectIdentifier(layer))}\n static func attachRegisteredLayers(manager:AnyObject,contentId:AnyHashable,contentNode:AnyObject){(contentNode as! ContentNode).layers=layers}\n}\nstruct Content {let id:AnyHashable=1}\n'
OUTPUT_CHECKS = 'let owner=OutputOwner(), layer=AVSampleBufferDisplayLayer()\nlet first=owner.registerSecondaryVideoLayer(layer)!\nfirst.dispose()\nassert(Queue.main.pending.isEmpty && owner.manager.node.layers.isEmpty)\nlet second=owner.registerSecondaryVideoLayer(layer)!\nQueue.main.flush()\nassert(owner.manager.node.layers.contains(ObjectIdentifier(layer))) // no stale detach after new attach\nQueue.main.current=false\nsecond.dispose()\nassert(Queue.main.pending.count==1)\nQueue.main.current=true\nQueue.main.flush()\nassert(owner.manager.node.layers.isEmpty && GhostBaseUniversalVideoSecondaryOutputRegistry.layers.isEmpty)\nprint("native secondary output dispose/rebind ordering PASS")\n'
if __name__=='__main__':unittest.main()
