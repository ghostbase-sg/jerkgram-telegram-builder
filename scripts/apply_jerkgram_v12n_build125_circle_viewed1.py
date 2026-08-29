#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
DURATION = ROOT / "submodules/TelegramUI/Components/Chat/ChatInstantVideoMessageDurationNode/Sources/ChatInstantVideoMessageDurationNode.swift"
INSTANT = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveInstantVideoNode/Sources/ChatMessageInteractiveInstantVideoNode.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_CIRCLE_VIEWED_CHECK1"

def require(value, message):
    if not value:
        raise RuntimeError("[Build125 circle viewed] " + message)

def duration_fixture():
    return '''private final class ChatInstantVideoMessageDurationNodeParameters: NSObject {
    let state: ChatInstantVideoMessageDurationNodeState
    let isSeen: Bool
    let textColor: UIColor
    init(state: ChatInstantVideoMessageDurationNodeState, isSeen: Bool, textColor: UIColor) {
        self.state = state
        self.isSeen = isSeen
        self.textColor = textColor
    }
}
public final class Node {
    public var isSeen: Bool = false {
        didSet { self.updateContents() }
    }
    private var updateTimer: SwiftSignalKit.Timer?
    private func getParameters() -> NSObjectProtocol {
        return ChatInstantVideoMessageDurationNodeParameters(state: self.state, isSeen: self.isSeen, textColor: self.textColor)
    }
    private func draw(_ context: CGContext, size: CGSize, parameters: Parameters) {
            if !parameters.isSeen {
                context.setFillColor(parameters.textColor.cgColor)
                let diameter: CGFloat = 4.0
                context.fillEllipse(in: CGRect(origin: CGPoint(x: size.width - size.height + floor((size.height - diameter) / 2.0), y: floor((size.height - diameter) / 2.0)), size: CGSize(width: diameter, height: diameter)))
            }
    }
}
'''

def instant_fixture():
    return '''var jerkgramOutgoingOneTimeCircleViewed = false
durationNode.isSeen = !notConsumed || jerkgramOutgoingOneTimeCircleViewed || item.presentationData.isPreview
'''

def patch_duration_text(text):
    if MARKER in text:
        return text
    old = "let isSeen: Bool\n    let textColor: UIColor\n"
    require(text.count(old) == 1, "duration parameter fields missing")
    text = text.replace(old, "let isSeen: Bool\n    let showsViewedCheck: Bool\n    let textColor: UIColor\n", 1)
    old = "init(state: ChatInstantVideoMessageDurationNodeState, isSeen: Bool, textColor: UIColor) {\n        self.state = state\n        self.isSeen = isSeen\n        self.textColor = textColor"
    new = "init(state: ChatInstantVideoMessageDurationNodeState, isSeen: Bool, showsViewedCheck: Bool, textColor: UIColor) {\n        self.state = state\n        self.isSeen = isSeen\n        self.showsViewedCheck = showsViewedCheck\n        self.textColor = textColor"
    require(text.count(old) == 1, "duration parameter initializer missing")
    text = text.replace(old, new, 1)
    anchor = "    private var updateTimer: SwiftSignalKit.Timer?"
    addition = '''    // MARK: Jerkgram v1.2N BUILD125_CIRCLE_VIEWED_CHECK1
    public var showsViewedCheck: Bool = false {
        didSet {
            if self.showsViewedCheck != oldValue {
                self.updateContents()
            }
        }
    }

'''
    require(text.count(anchor) == 1, "duration property insertion anchor missing")
    text = text.replace(anchor, addition + anchor, 1)
    old = "return ChatInstantVideoMessageDurationNodeParameters(state: self.state, isSeen: self.isSeen, textColor: self.textColor)"
    new = "return ChatInstantVideoMessageDurationNodeParameters(state: self.state, isSeen: self.isSeen, showsViewedCheck: self.showsViewedCheck, textColor: self.textColor)"
    require(text.count(old) == 1, "duration parameter call missing")
    text = text.replace(old, new, 1)
    old = '''            if !parameters.isSeen {
                context.setFillColor(parameters.textColor.cgColor)
                let diameter: CGFloat = 4.0
                context.fillEllipse(in: CGRect(origin: CGPoint(x: size.width - size.height + floor((size.height - diameter) / 2.0), y: floor((size.height - diameter) / 2.0)), size: CGSize(width: diameter, height: diameter)))
            }
'''
    new = '''            if !parameters.isSeen {
                context.setFillColor(parameters.textColor.cgColor)
                let diameter: CGFloat = 4.0
                context.fillEllipse(in: CGRect(origin: CGPoint(x: size.width - size.height + floor((size.height - diameter) / 2.0), y: floor((size.height - diameter) / 2.0)), size: CGSize(width: diameter, height: diameter)))
            } else if parameters.showsViewedCheck {
                context.setStrokeColor(parameters.textColor.cgColor)
                context.setLineWidth(1.4)
                context.setLineCap(.round)
                context.setLineJoin(.round)
                context.move(to: CGPoint(x: size.width - 11.0, y: 10.0))
                context.addLine(to: CGPoint(x: size.width - 8.0, y: 13.0))
                context.addLine(to: CGPoint(x: size.width - 3.0, y: 6.0))
                context.strokePath()
            }
'''
    require(text.count(old) == 1, "duration unread-dot renderer missing")
    return text.replace(old, new, 1)

def patch_instant_text(text):
    if MARKER in text:
        return text
    old = "durationNode.isSeen = !notConsumed || jerkgramOutgoingOneTimeCircleViewed || item.presentationData.isPreview"
    new = MARKER + "\n                        " + old + "\n                        durationNode.showsViewedCheck = jerkgramOutgoingOneTimeCircleViewed"
    require(text.count(old) == 1, "Build124 circle owner missing")
    return text.replace(old, new, 1)

def main():
    DURATION.write_text(patch_duration_text(DURATION.read_text(encoding="utf-8")), encoding="utf-8")
    INSTANT.write_text(patch_instant_text(INSTANT.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 circle viewed] GREEN")

if __name__ == "__main__":
    main()
