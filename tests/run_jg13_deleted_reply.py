"""Execute real quote-body functions against small Telegram model facades.

These test composition/entity offsets, not Postbox persistence, transport or UI.
Full app compilation remains a separate release gate.
"""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/reply158"))


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
    enum Kind: Equatable { case Bold, BlockQuote(isCollapsed: Bool) }
    let range: Range<Int>
    let type: Kind
}
func messageTextEntitiesInRange(entities: [MessageTextEntity], range: NSRange, onlyQuoteable: Bool) -> [MessageTextEntity] {
    precondition(!onlyQuoteable)
    return entities.filter { $0.range.lowerBound >= range.location && $0.range.upperBound <= range.location + range.length }
}
struct Message { var text: String; var media: [Any]; var groupingKey: Int64? = nil }
struct TelegramMediaPoll {
    struct Option { let text: String; let entities: [MessageTextEntity] }
    struct Results {
        struct Solution { let text: String; let entities: [MessageTextEntity] }
        var solution: Solution? = nil
    }
    let text: String; let textEntities: [MessageTextEntity]; let options: [Option]; var results = Results()
}
struct TelegramMediaTodo {
    struct Item { let id: Int32; let text: String; let entities: [MessageTextEntity] }
    struct Completion { let id: Int32 }
    let text: String; let textEntities: [MessageTextEntity]; let items: [Item]; let completions: [Completion]
}
struct TelegramMediaContact { let firstName: String; let lastName: String; let phoneNumber: String }
struct TelegramMediaMap {
    struct Venue { let title: String; let address: String? }
    let latitude: Double; let longitude: Double; let venue: Venue?
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
precondition(todoBody.text == "Список задач\nПокупки\n☑ Да\n☐ Хлеб")
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
'''


def main():
    enqueue = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift").read_text()
    helper = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift").read_text()
    owners = "\n".join(block(enqueue, needle) for needle in (
        "private struct GhostBaseDeletedQuoteBody",
        "private func ghostBaseDeletedMediaLabel(",
        "private func ghostBaseQuoteBody(",
        "private func ghostBaseShiftEntities(",
    ))
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "main.swift"
        target.write_text(FACADE + "\n" + helper + "\n" + owners + "\nprivate func runFixture() {\n" + FIXTURE + "\n}\nrunFixture()\n")
        subprocess.run(["xcrun", "swift", str(target)], check=True)


if __name__ == "__main__":
    main()
