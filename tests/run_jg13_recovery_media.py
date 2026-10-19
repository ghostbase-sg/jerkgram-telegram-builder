"""Execute extracted production static-media and action quote functions on macOS Swift."""
import os
from pathlib import Path
import subprocess
import tempfile
from run_jg13_deleted_reply import FACADE, block
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
FIXTURE = r'''
let contact = TelegramMediaContact(firstName: "Иван", lastName: "Петров", phoneNumber: "+123", peerId: 44, vCardData: "BEGIN:VCARD\nEND:VCARD")
let reconstructedContact = ghostBaseStaticDeletedMedia(media: contact)!.media as! TelegramMediaContact
precondition(reconstructedContact.firstName == contact.firstName && reconstructedContact.lastName == contact.lastName)
precondition(reconstructedContact.phoneNumber == contact.phoneNumber && reconstructedContact.vCardData == contact.vCardData)
let contactBody = ghostBaseQuoteBody(source: .init(text: "", media: [contact]), recoveredMedia: true, languageCode: "ru")
precondition(contactBody.text.isEmpty && contactBody.entities.isEmpty)
let contactCaption = ghostBaseQuoteBody(source: .init(text: "Комментарий", media: [contact]), recoveredMedia: true, languageCode: "ru")
precondition(contactCaption.text == "Комментарий" && contactCaption.originalTextOffset == 0)
let map = TelegramMediaMap(latitude: 55.75, longitude: 37.61, heading: 5, accuracyRadius: 20, venue: .init(title: "Парк", address: "Москва"), address: "RU", liveBroadcastingTimeout: 900, liveProximityNotificationRadius: 50)
let reconstructedMap = ghostBaseStaticDeletedMedia(media: map)!.media as! TelegramMediaMap
precondition(reconstructedMap.latitude == map.latitude && reconstructedMap.longitude == map.longitude)
precondition(reconstructedMap.venue?.title == "Парк" && reconstructedMap.address == "RU" && reconstructedMap.accuracyRadius == 20)
precondition(reconstructedMap.liveBroadcastingTimeout == nil && reconstructedMap.liveProximityNotificationRadius == nil)
var sticker = TelegramMediaFile(isSticker: true, fileName: "sticker.tgs", attributes: [.FileName(fileName: "sticker.tgs"), .Sticker(displayText: " 😎 ", packReference: nil, maskData: nil)])
let stickerBody = ghostBaseQuoteBody(source: .init(text: "", media: [sticker]), recoveredMedia: false, languageCode: "ru")
precondition(stickerBody.text == "Стикер 😎" && stickerBody.originalTextOffset == nil)
let stickerCaption = ghostBaseQuoteBody(source: .init(text: "caption 😀", media: [sticker]), recoveredMedia: false, languageCode: "en")
precondition(stickerCaption.text == "Sticker 😎\ncaption 😀")
precondition(stickerCaption.originalTextOffset == ("Sticker 😎\n" as NSString).length)
sticker.attributes = []
precondition(ghostBaseQuoteBody(source: .init(text: "", media: [sticker]), recoveredMedia: false, languageCode: "en").text == "Sticker")
for media in [TelegramMediaImage(), TelegramMediaFile(fileName: "document.pdf"), map, contact] as [Any] {
    let native = ghostBaseQuoteBody(source: .init(text: "", media: [media]), recoveredMedia: true, languageCode: "ru")
    precondition(native.text.isEmpty && native.entities.isEmpty)
    let captioned = ghostBaseQuoteBody(source: .init(text: "Текст", media: [media]), recoveredMedia: true, languageCode: "ru")
    precondition(captioned.text == "Текст" && captioned.originalTextOffset == 0)
}
let bold = MessageTextEntity(range: 0..<2, type: .Bold)
let appended = TelegramMediaAction(action: .todoAppendTasks([.init(id: 8, text: "😀 хлеб", entities: [bold])]))
let addedBody = ghostBaseQuoteBody(source: .init(text: "", media: [appended]), recoveredMedia: false, languageCode: "ru")
precondition(addedBody.text == "Добавлены задачи\n+ 😀 хлеб")
precondition((addedBody.text as NSString).substring(with: NSRange(location: addedBody.entities[0].range.lowerBound, length: 2)) == "😀")
let option = TelegramMediaPollOption(text: "😀 Да", entities: [bold])
for (action, expected) in [(TelegramMediaAction.Action.pollOptionAppended(option), "Добавлен вариант опроса"), (.pollOptionDeleted(option), "Удалён вариант опроса")] {
    let body = ghostBaseQuoteBody(source: .init(text: "", media: [TelegramMediaAction(action: action)]), recoveredMedia: false, languageCode: "ru-RU")
    precondition(body.text == expected + "\n• 😀 Да")
    precondition((body.text as NSString).substring(with: NSRange(location: body.entities[0].range.lowerBound, length: 2)) == "😀")
}
let completion = TelegramMediaAction(action: .todoCompletions(completed: [8, 9], incompleted: [10]))
let counts = ghostBaseQuoteBody(source: .init(text: "", media: [completion]), recoveredMedia: false, languageCode: "en")
precondition(counts.text == "Tasks completed: 2\nTasks marked incomplete: 1")
let todo = TelegramMediaTodo(text: "Покупки", textEntities: [], items: [.init(id: 8, text: "😀 хлеб", entities: [bold])], completions: [])
let appendedContext = ghostBaseQuoteBody(source: .init(text: "", media: [appended], attributes: [ReplyMessageAttribute(messageId: 1)], associatedMessages: [1: .init(text: "", media: [todo])]), recoveredMedia: false, languageCode: "ru")
precondition(appendedContext.text == "Список задач\nПокупки\nДобавлены задачи\n+ 😀 хлеб")
let named = ghostBaseQuoteBody(source: .init(text: "", media: [TelegramMediaAction(action: .todoCompletions(completed: [8], incompleted: []))], attributes: [ReplyMessageAttribute(messageId: 1)], associatedMessages: [1: .init(text: "", media: [todo])]), recoveredMedia: false, languageCode: "ru")
precondition(named.text == "Список задач\nПокупки\nЗавершены задачи\n☑ 😀 хлеб")
precondition((named.text as NSString).substring(with: NSRange(location: named.entities[0].range.lowerBound, length: 2)) == "😀")
var oldPoll = TelegramMediaPoll(text: "Выбор", textEntities: [], options: [.init(text: "Да", entities: [], opaqueIdentifier: Data([50])), .init(text: "Нет", entities: [], opaqueIdentifier: Data([60]))])
oldPoll.pollId = .init(namespace: 99, id: 777); oldPoll.isClosed = true
oldPoll.results.totalVoters = 20
oldPoll.results.voters = [.init(opaqueIdentifier: Data([50]), count: 15, selected: true)]
let optionContext = ghostBaseQuoteBody(source: .init(text: "", media: [TelegramMediaAction(action: .pollOptionAppended(option))], attributes: [ReplyMessageAttribute(messageId: 1)], associatedMessages: [1: .init(text: "", media: [oldPoll])]), recoveredMedia: false, languageCode: "en")
precondition(optionContext.text == "Poll\nВыбор\nPoll option added\n• 😀 Да")
let pollSnapshot = ghostBaseQuoteBody(source: .init(text: "подпись", media: [oldPoll]), recoveredMedia: true, languageCode: "ru")
precondition(pollSnapshot.text.contains("Снимок исходного опроса") && pollSnapshot.text.contains("Закрыт"))
precondition(pollSnapshot.text.contains("Голоса: 20") && pollSnapshot.text.contains("Голоса: 15") && pollSnapshot.text.contains("Выбран"))
precondition(pollSnapshot.text.hasSuffix("подпись"))
let fresh = ghostBaseFreshDeletedInteractiveMedia(media: oldPoll, randomId: 123, canSendPolls: true, canSendTodos: false)!.media as! TelegramMediaPoll
precondition(fresh.pollId.namespace == Namespaces.Media.LocalPoll && fresh.pollId.id == 123 && !fresh.isClosed)
precondition(fresh.results.totalVoters == nil && fresh.results.voters == nil && fresh.results.recentVoters.isEmpty)
precondition(fresh.options[0].opaqueIdentifier != oldPoll.options[0].opaqueIdentifier)
precondition(fresh.deadlineDate == nil && fresh.deadlineTimeout == nil && fresh.pollHash == 0)
precondition(ghostBaseFreshDeletedInteractiveMedia(media: oldPoll, randomId: 123, canSendPolls: false, canSendTodos: false) == nil)
oldPoll.kind = .quiz(multipleAnswers: false)
precondition(ghostBaseFreshDeletedInteractiveMedia(media: oldPoll, randomId: 123, canSendPolls: true, canSendTodos: true) == nil)
precondition(ghostBaseFreshDeletedInteractiveMedia(media: todo, randomId: 123, canSendPolls: true, canSendTodos: false) == nil)
let freshTodo = ghostBaseFreshDeletedInteractiveMedia(media: todo, randomId: 123, canSendPolls: false, canSendTodos: true)!.media as! TelegramMediaTodo
precondition(freshTodo.items[0].id == 124 && freshTodo.completions.isEmpty)
precondition(freshTodo.items[0].text == todo.items[0].text && freshTodo.items[0].entities == todo.items[0].entities)
let snapshot = ghostBaseQuoteBody(source: .init(text: "подпись", media: [todo]), recoveredMedia: true, languageCode: "ru")
precondition(snapshot.text.contains("Покупки") && snapshot.text.contains("😀 хлеб") && snapshot.text.hasSuffix("подпись"))
print("Actual recovery media PASS: static geo/contact, fresh clean poll/todo with gates, preserved snapshots, four localized actions, named completion/count fallback, UTF-16 entities")
'''
def main():
    enqueue = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift').read_text()
    helper = (SOURCE / 'submodules/TelegramCore/Sources/PendingMessages/JerkgramDeletedReplyText.swift').read_text()
    owners = '\n'.join(block(enqueue, name) for name in (
        'private struct GhostBaseDeletedQuoteBody', 'private func ghostBaseDeletedMediaLabel(',
        'private func ghostBaseQuoteBody(', 'private func ghostBaseShiftEntities(', 'private func ghostBaseStaticDeletedMedia(', 'private func ghostBaseFreshDeletedInteractiveMedia('))
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'main.swift'
        target.write_text(FACADE + '\n' + helper + '\n' + owners + '\nprivate func runFixture() {\n' + FIXTURE + '\n}\nrunFixture()\n')
        subprocess.run(['xcrun', 'swift', str(target)], check=True)
if __name__ == '__main__': main()
