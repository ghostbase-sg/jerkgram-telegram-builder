// Standalone Foundation boundaries, not UIKit, Postbox or an editor simulation.
// The model declarations/getter and projection algorithm are extracted verbatim
// from the exact ported Telegram 13.2 source by beta3_performance_native.py. Only the unused media/
// table/button payloads and attribute-value objects below are boundary stand-ins.
public enum EnginePeer {
    public struct Id: Equatable, Codable {
        public let value: Int64
        public init(_ value: Int64) { self.value = value }
        public func toInt64() -> Int64 { value }
    }
}
public struct TelegramMediaFile: Equatable, Codable {}
public struct ChatInputButton: Equatable, Codable {}
public struct ChatInputMedia: Equatable, Codable {}
public struct ChatInputTable: Equatable, Codable {}
public struct ChatInputDetails: Equatable, Codable {}
public struct ChatInputButtonRow: Equatable, Codable {}

public struct ChatInputContent: Equatable, Codable {
    public var schemaVersion: Int32 = 1
    public var blocks: [ChatInputBlock] = []
    public init(blocks: [ChatInputBlock] = []) { self.blocks = blocks }
    /* EXACT_PLAIN_TEXT_GETTER */
}

enum ChatTextInputAttributes {
    static let bold = NSAttributedString.Key("fixture.bold")
    static let italic = NSAttributedString.Key("fixture.italic")
    static let monospace = NSAttributedString.Key("fixture.monospace")
    static let strikethrough = NSAttributedString.Key("fixture.strikethrough")
    static let underline = NSAttributedString.Key("fixture.underline")
    static let spoiler = NSAttributedString.Key("fixture.spoiler")
    static let textMention = NSAttributedString.Key("fixture.mention")
    static let textUrl = NSAttributedString.Key("fixture.url")
    static let date = NSAttributedString.Key("fixture.date")
    static let customEmoji = NSAttributedString.Key("fixture.emoji")
    static let block = NSAttributedString.Key("fixture.block")
    static let collapsedBlock = NSAttributedString.Key("fixture.collapsed")
}
final class ChatTextInputTextMentionAttribute: NSObject {
    let peerId: EnginePeer.Id
    init(peerId: EnginePeer.Id) { self.peerId = peerId }
}
final class ChatTextInputTextUrlAttribute: NSObject {
    let url: String
    init(url: String) { self.url = url }
}
final class ChatTextInputTextDateAttribute: NSObject {
    let date: Int32
    init(date: Int32) { self.date = date }
}
final class ChatTextInputTextCustomEmojiAttribute: NSObject {
    let fileId: Int64
    init(interactivelySelectedFromPackId: Int64?, fileId: Int64, file: TelegramMediaFile?, enableAnimation: Bool) {
        self.fileId = fileId
    }
}
final class ChatTextInputTextQuoteAttribute: NSObject {
    enum Kind { case quote }
    init(kind: Kind, isCollapsed: Bool) {}
}
func chatInputCodeBlockAttribute(language: String?) -> (key: NSAttributedString.Key, value: Any) {
    return (ChatTextInputAttributes.block, (language ?? "code") as NSString)
}

var projectionBuilds = 0
func attributedString(from content: ChatInputContent, renderListMarkers: Bool = false) -> NSAttributedString {
    projectionBuilds += 1
    return officialAttributedString(from: content, renderListMarkers: renderListMarkers)
}
struct InputState { let content: ChatInputContent }

final class GhostBaseMessageAttribute {
    let isDeleted: Bool
    init(_ value: Bool) { isDeleted = value }
}
final class OtherAttribute {}
final class CountingAttributes {
    let values: [AnyObject]
    var visits = 0
    init(_ values: [AnyObject]) { self.values = values }
    func first(where predicate: (AnyObject) -> Bool) -> AnyObject? {
        for value in values {
            visits += 1
            if predicate(value) { return value }
        }
        return nil
    }
}
struct FixtureMessage { let attributes: CountingAttributes }
