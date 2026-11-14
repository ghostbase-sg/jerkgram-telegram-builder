public extension JerkgramStrings {
    var version: String { self.languageCode == "ru" ? "ВЕРСИЯ" : "VERSION" }
    var privacy: String { self.languageCode == "ru" ? "КОНФИДЕНЦИАЛЬНОСТЬ" : "PRIVACY" }
    var jerkgramVersion: String { self.languageCode == "ru" ? "Версия Jerkgram" : "Jerkgram Version" }
    var build: String { self.languageCode == "ru" ? "Сборка" : "Build" }
    var telegramBase: String { self.languageCode == "ru" ? "База Telegram" : "Telegram Base" }
    var anonymousAnalytics: String { self.languageCode == "ru" ? "Анонимная аналитика" : "Anonymous Analytics" }
    var anonymousAnalyticsDescription: String {
        if self.languageCode == "ru" {
            return "Помогайте улучшать Jerkgram, отправляя анонимную статистику использования: версию Jerkgram, версию iOS и регион устройства. Аккаунты Telegram, сообщения, имена пользователей и номера телефонов никогда не собираются."
        } else {
            return "Help improve Jerkgram by sharing anonymous usage statistics such as Jerkgram version, iOS version and device region. Telegram accounts, messages, usernames and phone numbers are never collected."
        }
    }
}
