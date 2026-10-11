import Foundation
import CoreGraphics
import UIKit
import XCTest
@testable import CoreListDemo

// These exercise the production geometry carrier. Producer/getter parity requires
// TelegramUI integration; synthetic line and option frames do not prove it.
final class ListViewPreparedScrollTargetTests: XCTestCase {
    func testWrappedQuoteUnionDoesNotIncludeOriginAndTranslatesOnce() {
        let lines = [CGRect(x: 30, y: 20, width: 80, height: 18), CGRect(x: 10, y: 40, width: 45, height: 18)]
        XCTAssertEqual(ListViewPreparedScrollTargetGeometry.union(lines, offset: CGPoint(x: 7, y: 11)), CGRect(x: 17, y: 31, width: 100, height: 38))
        XCTAssertNil(ListViewPreparedScrollTargetGeometry.union([], offset: CGPoint(x: 7, y: 11)))
    }

    func testDescriptorsKeepOffsetsAndOptionIdentitiesDistinct() {
        let targets: Set<ListViewPreparedScrollTarget> = [.quote("repeat", offset: nil), .quote("repeat", offset: 0), .quote("repeat", offset: 4), .todo(nil), .todo(3), .poll(nil), .poll(Data([3]))]
        XCTAssertEqual(targets.count, 7)
    }

    func testMissingTargetSurvivesNestedTranslation() {
        let geometry = ListViewPreparedScrollTargetGeometry { _ in nil }
            .translatedBy(CGPoint(x: 13, y: 21))
            .translatedBy(CGPoint(x: -3, y: 8))
        XCTAssertNil(geometry.rect(for: .quote("missing", offset: nil)))
        XCTAssertNil(geometry.rect(for: .todo(7)))
        XCTAssertNil(geometry.rect(for: .poll(Data([9]))))
    }

    func testWidthGenerationKeepsWrappedQuoteAndChildOrigin() {
        let target = ListViewPreparedScrollTarget.quote("two lines", offset: 6)
        var lines = [CGRect(x: 5, y: 2, width: 90, height: 16)]
        var origin = CGPoint(x: 8, y: 9)
        let first = ListViewPreparedScrollTargetGeometry { [lines] query in
            query == target ? ListViewPreparedScrollTargetGeometry.union(lines) : nil
        }.translatedBy(origin)
        lines = [CGRect(x: 5, y: 2, width: 45, height: 16), CGRect(x: 5, y: 20, width: 35, height: 16)]
        origin = CGPoint(x: 21, y: 30)
        let second = ListViewPreparedScrollTargetGeometry { [lines] query in
            query == target ? ListViewPreparedScrollTargetGeometry.union(lines) : nil
        }.translatedBy(origin)
        XCTAssertEqual(second.rect(for: target), CGRect(x: 26, y: 32, width: 45, height: 34))
        XCTAssertEqual(first.rect(for: target), CGRect(x: 13, y: 11, width: 90, height: 16))
        XCTAssertNil(first.rect(for: .quote("two lines", offset: 7)))
    }

    func testReorderedTodoAndPollIdentifiersUseFrozenFrames() {
        let todo = ListViewPreparedScrollTarget.todo(17)
        let poll = ListViewPreparedScrollTarget.poll(Data([0, 255]))
        var frames: [ListViewPreparedScrollTarget: CGRect] = [todo: CGRect(x: 0, y: 10, width: 80, height: 20), poll: CGRect(x: 0, y: 40, width: 80, height: 30)]
        let first = ListViewPreparedScrollTargetGeometry { [frames] in frames[$0] }
        frames[todo] = CGRect(x: 0, y: 90, width: 100, height: 20)
        frames[poll] = CGRect(x: 0, y: 15, width: 100, height: 30)
        let second = ListViewPreparedScrollTargetGeometry { [frames] in frames[$0] }
        XCTAssertEqual(first.rect(for: todo)?.minY, 10)
        XCTAssertEqual(first.rect(for: poll)?.minY, 40)
        XCTAssertEqual(second.rect(for: todo)?.minY, 90)
        XCTAssertEqual(second.rect(for: poll)?.minY, 15)
        XCTAssertNil(second.rect(for: .todo(18)))
        XCTAssertNil(second.rect(for: .poll(Data([255, 0]))))
    }

    func testFirstMatchingChildUsesItsOwnBubbleTransform() {
        let target = ListViewPreparedScrollTarget.quote("same", offset: nil)
        let first = ListViewPreparedScrollTargetGeometry { query in
            query == target ? CGRect(x: 2, y: 3, width: 20, height: 12) : nil
        }.translatedBy(CGPoint(x: 30, y: 40))
        let later = ListViewPreparedScrollTargetGeometry { _ in CGRect(x: 100, y: 100, width: 20, height: 12) }
        let combined = ListViewPreparedScrollTargetGeometry(children: [first, later])
        XCTAssertEqual(combined.rect(for: target), CGRect(x: 32, y: 43, width: 20, height: 12))
        XCTAssertEqual(combined.rect(for: .todo(2)), CGRect(x: 100, y: 100, width: 20, height: 12))
    }

    private func hierarchy() -> (item: UIView, main: UIView, clipping: UIView) {
        let item = UIView(frame: CGRect(x: 0, y: 0, width: 320, height: 400))
        let main = UIView(frame: item.bounds)
        let clipping = UIView(frame: CGRect(x: 15, y: 25, width: 280, height: 300))
        clipping.bounds = clipping.frame
        item.addSubview(main)
        main.addSubview(clipping)
        return (item, main, clipping)
    }

    func testSingleToGroupKeepsCapturedPhysicalClippingParent() throws {
        let views = hierarchy()
        let child = UIView(frame: CGRect(x: 8, y: 12, width: 90, height: 40))
        views.clipping.addSubview(child)
        let parent = try XCTUnwrap(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: []))
        XCTAssertEqual(parent.bindingIdentity, ObjectIdentifier(child))
        let local = CGRect(x: 3, y: 4, width: 50, height: 16)
        let geometry = parent.geometry(ListViewPreparedScrollTargetGeometry { _ in local }, childOrigin: CGPoint(x: 10, y: 20), updatedGroupOrigins: [17: CGPoint(x: 0, y: 100)], preservesTrailingOffset: false)
        // The real apply adds the group but does not reparent a retained child.
        let group = UIView(frame: CGRect(x: 0, y: 100, width: 320, height: 100))
        views.clipping.addSubview(group)
        child.frame.origin = CGPoint(x: 10, y: 20)
        XCTAssertEqual(geometry.rect(for: .quote("caption", offset: nil), trailingOffset: 0), child.convert(local, to: views.item))
    }

    func testGroupToSingleKeepsActualOldGroupOrigin() throws {
        let views = hierarchy()
        let group = UIView(frame: CGRect(x: 0, y: 80, width: 320, height: 100))
        let source = UIView(frame: group.bounds)
        let child = UIView(frame: CGRect(x: 8, y: 12, width: 90, height: 40))
        views.clipping.addSubview(group)
        group.addSubview(source)
        source.addSubview(child)
        let parent = try XCTUnwrap(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: [(17, group)]))
        let local = CGRect(x: 3, y: 4, width: 50, height: 16)
        let geometry = parent.geometry(ListViewPreparedScrollTargetGeometry { _ in local }, childOrigin: CGPoint(x: 10, y: 20), updatedGroupOrigins: [:], preservesTrailingOffset: false)
        // The pinned apply retains unmatched old groups, and their child parent.
        child.frame.origin = CGPoint(x: 10, y: 20)
        XCTAssertEqual(geometry.rect(for: .quote("caption", offset: nil), trailingOffset: 0), child.convert(local, to: views.item))
        XCTAssertEqual(geometry.rect(for: .quote("caption", offset: nil), trailingOffset: 0)?.minY, 104)
    }

    func testActualGroupUsesFutureFrameOnlyWhenThatGroupIsUpdated() throws {
        let views = hierarchy()
        let group = UIView(frame: CGRect(x: 0, y: 80, width: 320, height: 100))
        let child = UIView(frame: CGRect(x: 10, y: 20, width: 90, height: 40))
        views.clipping.addSubview(group)
        group.addSubview(child)
        let parent = try XCTUnwrap(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: [(17, group)]))
        let local = CGRect(x: 3, y: 4, width: 50, height: 16)
        let geometry = parent.geometry(ListViewPreparedScrollTargetGeometry { _ in local }, childOrigin: child.frame.origin, updatedGroupOrigins: [17: CGPoint(x: 0, y: 120), 99: CGPoint(x: 0, y: 300)], preservesTrailingOffset: true)
        group.frame.origin.y = 120
        views.main.frame.origin.y = -50
        XCTAssertEqual(geometry.rect(for: .todo(7), trailingOffset: -50), child.convert(local, to: views.item))
        // A blocked preparation does not freeze the old trailing-space scalar.
        views.main.frame.origin.y = -75
        XCTAssertEqual(geometry.rect(for: .todo(7), trailingOffset: -75), child.convert(local, to: views.item))
    }

    func testCandidateModeClearsOffsetAndDetachedTargetNeverReceivesIt() throws {
        let views = hierarchy()
        views.main.frame.origin.y = -50
        let child = UIView(frame: CGRect(x: 10, y: 20, width: 90, height: 40))
        views.clipping.addSubview(child)
        let parent = try XCTUnwrap(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: []))
        let local = CGRect(x: 3, y: 4, width: 50, height: 16)
        let cleared = parent.geometry(ListViewPreparedScrollTargetGeometry { _ in local }, childOrigin: child.frame.origin, updatedGroupOrigins: [:], preservesTrailingOffset: false)
        views.main.frame.origin.y = 0
        XCTAssertEqual(cleared.rect(for: .poll(Data([7])), trailingOffset: -75), child.convert(local, to: views.item))
        views.item.addSubview(child)
        let detachedParent = try XCTUnwrap(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: []))
        let detached = detachedParent.geometry(ListViewPreparedScrollTargetGeometry { _ in local }, childOrigin: child.frame.origin, updatedGroupOrigins: [:], preservesTrailingOffset: true)
        views.main.frame.origin.y = -75
        XCTAssertEqual(detached.rect(for: .quote("detached", offset: nil), trailingOffset: -75), child.convert(local, to: views.item))
        let selection = ListViewPreparedScrollTargetDynamicGeometry(children: [ListViewPreparedScrollTargetDynamicGeometry { _, _ in nil }, detached])
        XCTAssertEqual(selection.rect(for: .quote("detached", offset: nil), trailingOffset: -75), child.convert(local, to: views.item))
    }

    func testCaptureRejectsGroupAlreadyDetachedFromItem() {
        let views = hierarchy()
        let group = UIView(frame: CGRect(x: 0, y: 80, width: 320, height: 100))
        let child = UIView(frame: CGRect(x: 10, y: 20, width: 90, height: 40))
        views.clipping.addSubview(group)
        group.addSubview(child)
        group.removeFromSuperview()
        XCTAssertNil(ListViewPreparedScrollTargetParent.capture(child: child, item: views.item, mainContainer: views.main, groups: [(17, group)]))
    }

}
