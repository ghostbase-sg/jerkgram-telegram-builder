import Foundation

@main
struct DeletedReplyTextTests {
    static func main() {
        precondition(JerkgramDeletedReplyLabel.poll.text(languageCode: "ru") == "Опрос")
        precondition(JerkgramDeletedReplyLabel.todo.text(languageCode: "ru-RU") == "Список задач")
        precondition(JerkgramDeletedReplyLabel.poll.text(languageCode: "en") == "Poll")
        precondition(JerkgramDeletedReplyLabel.poll.text(languageCode: "de") == "Poll")
        var body = JerkgramDeletedReplyText()
        precondition(body.append("") == nil)
        precondition(body.append("Опрос") == 0)
        precondition(body.append("😀 Вопрос") == 6)
        let optionStart = body.append("ответ", prefix: "• ")!
        precondition((body.text as NSString).substring(from: optionStart) == "ответ")
        precondition(body.text == "Опрос\n😀 Вопрос\n• ответ")
        let unchanged = body.text
        precondition(body.append("", prefix: "• ") == nil)
        precondition(body.text == unchanged)
        print("DeletedReplyText: localization, UTF-16 offsets, composition and empty chunks passed")
    }
}
