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
        let reply = String(repeating: "Я", count: 4000)
        let fitted = JerkgramDeletedReplyText.fittedQuote(String(repeating: "😀", count: 1000), reply: reply, limit: 4096, languageCode: "ru")
        precondition((fitted.text as NSString).length + 2 + (reply as NSString).length <= 4096)
        precondition(fitted.text.contains("Контекст сокращён"))
        precondition(!fitted.text.contains("�"))
        precondition((fitted.text as NSString).substring(to: fitted.retainedLength) == String(repeating: "😀", count: fitted.retainedLength / 2))
        let exact = JerkgramDeletedReplyText.fittedQuote("Автор\nТекст", reply: "Ответ", limit: 4096, languageCode: "en")
        precondition(exact.text == "Автор\nТекст" && exact.retainedLength == 11)
        let full = JerkgramDeletedReplyText.fittedQuote("quote", reply: String(repeating: "x", count: 1024), limit: 1024, languageCode: "en")
        precondition(full.text.isEmpty && full.retainedLength == 0)
        let caption = JerkgramDeletedReplyText.fittedQuote(String(repeating: "x", count: 4000), reply: "caption", limit: 2048, languageCode: "en")
        precondition((caption.text as NSString).length + 2 + 7 <= 2048 && caption.text.contains("Context shortened"))
        print("DeletedReplyText: localization, UTF-16 offsets, composition and empty chunks passed")
    }
}
