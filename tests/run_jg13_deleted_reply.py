"""Execute real quote-body functions against small Telegram model facades.

These test composition/entity offsets, not Postbox persistence, transport or UI.
Full app compilation remains a separate release gate.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))


def block(text, needle):
    start = text.index(needle)
    end = text.index("{", start)
    depth = 1
    end += 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


FACADE = r'''
import Foundation
struct MessageTextEntity: Equatable {
    enum Kind: Equatable { case Bold, Italic, Underline, Strikethrough, Spoiler, CustomEmoji(stickerPack: Int64?, fileId: Int64), BlockQuote(isCollapsed: Bool), TextUrl(url: String), TextMention(peerId: Int64) }
    let range: Range<Int>
    let type: Kind
}
func messageTextEntitiesInRange(entities: [MessageTextEntity], range: NSRange, onlyQuoteable: Bool) -> [MessageTextEntity] {
    precondition(!onlyQuoteable)
    let allowed = range.location..<(range.location + range.length)
    return entities.compactMap { entity in
        guard entity.range.overlaps(allowed) else { return nil }
        let clipped = entity.range.clamped(to: allowed)
        return MessageTextEntity(range: (clipped.lowerBound - allowed.lowerBound)..<(clipped.upperBound - allowed.lowerBound), type: entity.type)
    }
}
typealias PeerId = Int64
protocol MessageAttribute {}
struct TextEntitiesMessageAttribute: MessageAttribute { let entities: [MessageTextEntity] }
struct GhostBaseMessageAttribute: MessageAttribute { let originalEntities: [MessageTextEntity] }
struct ReplyMessageAttribute: MessageAttribute { var messageId: Int = 0 }
struct RetainedTestAttribute: MessageAttribute {}
typealias Media = Any
struct AnyMediaReference: Equatable {
    let identity: Int
    var media: Any? = nil
    static func standalone(media: Any) -> AnyMediaReference { .init(identity: 0, media: media) }
    static func ==(lhs: Self, rhs: Self) -> Bool { lhs.identity == rhs.identity }
}
struct UserLimitsConfiguration { let maxMessageLength: Int32; let maxCaptionLength: Int32 }
enum EnqueueMessage {
    case message(text: String, attributes: [MessageAttribute], inlineStickers: [Int64: Int],
        mediaReference: AnyMediaReference?, threadId: Int64?, replyToMessageId: Int?,
        replyToStoryId: Int?, localGroupingKey: Int64?, correlationId: Int64?, bubbleUpEmojiOrStickersets: [Int64])
    case other
}
struct Message { var text: String; var media: [Any]; var groupingKey: Int64? = nil; var attributes: [MessageAttribute] = []; var associatedMessages: [Int: Message] = [:] }
struct MediaId: Equatable { let namespace: Int32; let id: Int64 }
enum Namespaces { enum Media { static let LocalPoll: Int32 = 9 } }
enum TelegramMediaPollKind { case poll(multipleAnswers: Bool), quiz(multipleAnswers: Bool) }
enum TelegramMediaPollPublicity { case anonymous, `public` }
struct TelegramMediaPollOption { let text: String; let entities: [MessageTextEntity]; var opaqueIdentifier = Data(); var media: Any? = nil; var date: Int32? = nil; var addedBy: PeerId? = nil }
struct TelegramMediaPollResults {
    struct Solution { let text: String; let entities: [MessageTextEntity]; var media: Any? = nil }
    struct Voter { let opaqueIdentifier: Data; let count: Int32?; let selected: Bool }
    var voters: [Voter]? = nil; var totalVoters: Int32? = nil; var recentVoters: [PeerId] = []
    var solution: Solution? = nil; var hasUnseenVotes: Bool? = nil; var canViewStats = false
}
struct TelegramMediaPoll {
    typealias Option = TelegramMediaPollOption
    typealias Results = TelegramMediaPollResults
    var pollId = MediaId(namespace: 0, id: 0); var publicity = TelegramMediaPollPublicity.anonymous
    var kind = TelegramMediaPollKind.poll(multipleAnswers: false)
    let text: String; let textEntities: [MessageTextEntity]; let options: [Option]; var correctAnswers: [Data]? = nil
    var results = Results(); var isClosed = false; var deadlineTimeout: Int32? = nil; var deadlineDate: Int32? = nil; var pollHash: Int64 = 0
    var attachedMedia: Any? = nil; var openAnswers = false; var restrictToSubscribers = false; var countries: [String] = []
    init(text: String, textEntities: [MessageTextEntity], options: [Option], results: Results = Results()) {
        self.text = text; self.textEntities = textEntities; self.options = options; self.results = results
    }
    init(pollId: MediaId, publicity: TelegramMediaPollPublicity, kind: TelegramMediaPollKind, text: String, textEntities: [MessageTextEntity], options: [Option], correctAnswers: [Data]?, results: Results, isClosed: Bool, deadlineTimeout: Int32?, deadlineDate: Int32?, pollHash: Int64) {
        self.pollId = pollId; self.publicity = publicity; self.kind = kind; self.text = text; self.textEntities = textEntities; self.options = options
        self.correctAnswers = correctAnswers; self.results = results; self.isClosed = isClosed; self.deadlineTimeout = deadlineTimeout; self.deadlineDate = deadlineDate; self.pollHash = pollHash
    }
}
struct TelegramMediaTodo {
    struct Flags: OptionSet { let rawValue: Int32; static let othersCanAppend = Flags(rawValue: 1); static let othersCanComplete = Flags(rawValue: 2) }
    struct Item {
        let id: Int32; let text: String; let entities: [MessageTextEntity]
        init(id: Int32, text: String, entities: [MessageTextEntity]) { self.id = id; self.text = text; self.entities = entities }
        init(text: String, entities: [MessageTextEntity], id: Int32) { self.init(id: id, text: text, entities: entities) }
    }
    struct Completion { let id: Int32 }
    var flags: Flags = []
    let text: String; let textEntities: [MessageTextEntity]; let items: [Item]; let completions: [Completion]
    init(text: String, textEntities: [MessageTextEntity], items: [Item], completions: [Completion]) {
        self.text = text; self.textEntities = textEntities; self.items = items; self.completions = completions
    }
    init(flags: Flags, text: String, textEntities: [MessageTextEntity], items: [Item], completions: [Completion]) {
        self.init(text: text, textEntities: textEntities, items: items, completions: completions); self.flags = flags
    }
}
struct TelegramMediaContact {
    let firstName: String; let lastName: String; let phoneNumber: String
    var peerId: PeerId? = nil; var vCardData: String? = nil
}
struct TelegramMediaMap {
    struct Venue { let title: String; let address: String? }
    let latitude: Double; let longitude: Double; let venue: Venue?
    var heading: Int32? = nil; var accuracyRadius: Double? = nil; var address: String? = nil
    var liveBroadcastingTimeout: Int32? = nil; var liveProximityNotificationRadius: Int32? = nil
    init(latitude: Double, longitude: Double, heading: Int32? = nil, accuracyRadius: Double? = nil,
        venue: Venue?, address: String? = nil, liveBroadcastingTimeout: Int32? = nil, liveProximityNotificationRadius: Int32? = nil) {
        self.latitude = latitude; self.longitude = longitude; self.heading = heading; self.accuracyRadius = accuracyRadius
        self.venue = venue; self.address = address; self.liveBroadcastingTimeout = liveBroadcastingTimeout
        self.liveProximityNotificationRadius = liveProximityNotificationRadius
    }
}
struct TelegramMediaAction {
    enum Action { case todoCompletions(completed: [Int32], incompleted: [Int32]), todoAppendTasks([TelegramMediaTodo.Item]), pollOptionAppended(TelegramMediaPollOption), pollOptionDeleted(TelegramMediaPollOption), other }
    let action: Action
}
struct TelegramMediaDice { let emoji: String; let value: Int32? }
struct TelegramMediaInvoice { let title: String; let description: String }
struct TelegramMediaImage {}
struct TelegramMediaFile {
    var isSticker = false, isVoice = false, isInstantVideo = false, isAnimated = false, isVideo = false, isMusic = false
    var fileName: String? = nil
}
'''
FIXTURE = r'''
let bold = MessageTextEntity(range: 0..<2, type: .Bold)
let nestedQuote = MessageTextEntity(range: 0..<2, type: .BlockQuote(isCollapsed: false))
let poll = TelegramMediaPoll(text: "😀 вопрос", textEntities: [bold, nestedQuote],
    options: [.init(text: "Да", entities: [bold]), .init(text: "Нет", entities: [])])
let pollBody = ghostBaseQuoteBody(source: Message(text: "подпись", media: [poll]), recoveredMedia: false, languageCode: "ru")
precondition(pollBody.text == "Опрос\n😀 вопрос\n• Да\n• Нет\nподпись")
precondition(pollBody.entities.count == 2)
for entity in pollBody.entities {
    precondition((pollBody.text as NSString).substring(with: NSRange(location: entity.range.lowerBound, length: entity.range.count)) == (entity == pollBody.entities[0] ? "😀" : "Да"))
}
precondition((pollBody.text as NSString).substring(from: pollBody.originalTextOffset!) == "подпись")
let todo = TelegramMediaTodo(text: "Покупки", textEntities: [], items: [
    .init(id: 7, text: "Да", entities: [bold]), .init(id: 9, text: "Хлеб", entities: [])], completions: [.init(id: 7)])
let todoBody = ghostBaseQuoteBody(source: Message(text: "", media: [todo]), recoveredMedia: false, languageCode: "ru-RU")
precondition(todoBody.text == "Список задач\nПокупки\n☑ Да\n- Хлеб")
precondition(todoBody.originalTextOffset == nil)
precondition((todoBody.text as NSString).substring(with: NSRange(location: todoBody.entities[0].range.lowerBound, length: 2)) == "Да")
let photoBody = ghostBaseQuoteBody(source: Message(text: "", media: [TelegramMediaImage()]), recoveredMedia: true, languageCode: "ru")
precondition(photoBody.text == "📷 Фото", "Recovered captionless media must not produce an author-only reply")
let caption = ghostBaseQuoteBody(source: Message(text: "caption", media: [TelegramMediaImage()]), recoveredMedia: true, languageCode: "en")
precondition(caption.text == "caption" && caption.originalTextOffset == 0)
let contact = ghostBaseQuoteBody(source: Message(text: "", media: [TelegramMediaContact(firstName: "Иван", lastName: "Иванов", phoneNumber: "+7000")]), recoveredMedia: false, languageCode: "ru")
precondition(contact.text == "👤 Контакт\nИван Иванов\n+7000")
let point = ghostBaseQuoteBody(source: Message(text: "", media: [TelegramMediaMap(latitude: 55.5, longitude: 37.5, venue: .init(title: "Место", address: "Улица"))]), recoveredMedia: false, languageCode: "ru")
precondition(point.text == "📍 Местоположение\nМесто\nУлица\n55.5, 37.5")
let dice = ghostBaseQuoteBody(source: Message(text: "", media: [TelegramMediaDice(emoji: "🎯", value: 6)]), recoveredMedia: false, languageCode: "ru")
precondition(dice.text == "🎯\nРезультат: 6")
let plain = ghostBaseQuoteBody(source: Message(text: "Текст 😀", media: []), recoveredMedia: false, languageCode: "ru")
precondition(plain.text == "Текст 😀" && plain.originalTextOffset == 0)
print("Actual quote body PASS: poll/todo contents, UTF-16 entities, captions, contact, location, dice and app language")
func makeOutgoing(_ text: String, media: AnyMediaReference? = nil) -> EnqueueMessage {
    return .message(text: text, attributes: [TextEntitiesMessageAttribute(entities: [.init(range: 0..<2, type: .Bold)]), ReplyMessageAttribute(), RetainedTestAttribute()],
        inlineStickers: [:], mediaReference: media, threadId: 10, replyToMessageId: 1,
        replyToStoryId: nil, localGroupingKey: nil, correlationId: 12, bubbleUpEmojiOrStickersets: [])
}
let largeSource = Message(text: String(repeating: "😀", count: 4000), media: [], attributes: [
    TextEntitiesMessageAttribute(entities: [.init(range: 0..<8000, type: .Bold)])])
func assertPortable(_ result: EnqueueMessage, originalUserText: String, limit: Int, expectedMedia: AnyMediaReference?) {
    guard case let .message(text, attributes, _, media, thread, reply, _, _, correlation, _) = result else { preconditionFailure() }
    precondition(text.hasSuffix(originalUserText) && (text as NSString).length <= limit)
    precondition(media == expectedMedia && thread == 10 && reply == nil && correlation == 12)
    precondition(attributes.contains { $0 is RetainedTestAttribute } && !attributes.contains { $0 is ReplyMessageAttribute })
    let entities = (attributes.first { $0 is TextEntitiesMessageAttribute } as! TextEntitiesMessageAttribute).entities
    for entity in entities {
        precondition(entity.range.lowerBound >= 0 && entity.range.upperBound <= (text as NSString).length && !entity.range.isEmpty)
    }
    let userStart = (text as NSString).length - (originalUserText as NSString).length
    precondition(entities.contains { $0.range == userStart..<(userStart + 2) && $0.type == .Bold })
}
let longReply = "😀" + String(repeating: "x", count: 3998)
let regular = ghostBaseBuildPortableDeletedReply(outgoing: makeOutgoing(longReply), source: largeSource,
    authorName: "Автор", authorUsername: "author", mentionPeerId: nil, recoveredMedia: nil,
    languageCode: "ru", limits: .init(maxMessageLength: 4096, maxCaptionLength: 1024))
assertPortable(regular, originalUserText: longReply, limit: 4096, expectedMedia: nil)
if case let .message(text, _, _, _, _, _, _, _, _, _) = regular {
    precondition(text.contains("Контекст сокращён") && !text.contains("�"))
}
let userMedia = AnyMediaReference(identity: 5)
let mediaReply = ghostBaseBuildPortableDeletedReply(outgoing: makeOutgoing("😀 ответ", media: userMedia), source: largeSource,
    authorName: "Автор", authorUsername: nil, mentionPeerId: 7, recoveredMedia: nil,
    languageCode: "en", limits: .init(maxMessageLength: 4096, maxCaptionLength: 1024))
assertPortable(mediaReply, originalUserText: "😀 ответ", limit: 1024, expectedMedia: userMedia)
let premiumReply = ghostBaseBuildPortableDeletedReply(outgoing: makeOutgoing("😀 ответ", media: userMedia), source: largeSource,
    authorName: "Автор", authorUsername: nil, mentionPeerId: nil, recoveredMedia: nil,
    languageCode: "en", limits: .init(maxMessageLength: 4096, maxCaptionLength: 2048))
assertPortable(premiumReply, originalUserText: "😀 ответ", limit: 2048, expectedMedia: userMedia)
let fullReply = "😀" + String(repeating: "x", count: 1022)
let fullCaption = ghostBaseBuildPortableDeletedReply(outgoing: makeOutgoing(fullReply, media: userMedia), source: largeSource,
    authorName: "Автор", authorUsername: nil, mentionPeerId: nil, recoveredMedia: nil,
    languageCode: "ru", limits: .init(maxMessageLength: 4096, maxCaptionLength: 1024))
assertPortable(fullCaption, originalUserText: fullReply, limit: 1024, expectedMedia: userMedia)
if case let .message(text, _, _, _, _, _, _, _, _, _) = fullCaption { precondition(text == fullReply) }
print("Actual portable builder PASS: text/caption budgets, full user text, retained attributes, exact limits, no split and UTF-16 entity clipping")
'''


def main():
    enqueue = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift").read_text()
    helper = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift").read_text()
    owners = "\n".join(block(enqueue, needle) for needle in (
        "private struct GhostBaseDeletedQuoteBody",
        "private func ghostBaseDeletedMediaLabel(",
        "private func ghostBaseQuoteBody(",
        "private func ghostBaseShiftEntities(",
        "private func ghostBaseOriginalPortableEntities(",
        "private func ghostBaseBuildPortableDeletedReply(",
    ))
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "main.swift"
        target.write_text(FACADE + "\n" + helper + "\n" + owners + "\nprivate func runFixture() {\n" + FIXTURE + "\n}\nrunFixture()\n")
        subprocess.run(["xcrun", "swift", str(target)], check=True)


if __name__ == "__main__":
    main()
