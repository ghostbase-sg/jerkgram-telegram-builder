# Draft app analytics privacy addendum — not published

This text is a review draft for the public Jerkgram app privacy policy. It does not replace the website's separate Cloudflare Web Analytics notice. Production Analytics v3 remains disabled pending server readiness, policy review/publication and explicit approval.

## English

If you enable usage analytics in Jerkgram, the app uses a randomly generated installation ID and records installation registration, app opens, session starts and an engaged-session signal after at least10seconds in the foreground. The installation ID is pseudonymous: it can connect activity from the same installation across days. It is not derived from your Telegram account, phone number, advertising identifier, vendor identifier or hardware identifier.

Analytics events include Jerkgram version/build, iOS version/major, and optionally the device's technical model identifier and locale region. They do not contain Telegram IDs, usernames, contacts, messages, chat/peer IDs, device names, coordinates or authentication tokens. Network delivery necessarily exposes connection metadata to the service infrastructure; this does not make the installation ID an IP-derived identifier.

Events are kept in a bounded local queue of up to approximately500events, expire after7days, and are delivered in small batches. Disabling analytics stops collection and delivery, cancels pending delivery and deletes queued events; old events are not sent if you enable it again. Updating the app or re-enabling analytics does not register a new installation.

Server retention, access controls, infrastructure providers, contact information and applicable deletion rights must be supplied and reviewed by the service operator before this policy is published. This draft does not assert unverified server retention or anonymity guarantees.

## Русский

Если вы включаете аналитику использования в Jerkgram, приложение использует случайно созданный ID установки и фиксирует регистрацию новой установки, открытия приложения, начало сессий и признак вовлечённой сессии после не менее10секунд на переднем плане. ID установки является псевдонимным: он позволяет связывать активность одной установки между днями. Он не создаётся из аккаунта Telegram, номера телефона, рекламного идентификатора, идентификатора производителя или аппаратного идентификатора.

События содержат версию и сборку Jerkgram, версию и основной номер iOS, а также, при наличии, технический идентификатор модели устройства и регион локали. Они не содержат Telegram ID, имён пользователей, контактов, сообщений, chat/peer ID, имени устройства, координат или токенов авторизации. При сетевой передаче инфраструктура сервиса неизбежно видит метаданные соединения; это не означает, что ID установки создаётся из IP-адреса.

События сохраняются в ограниченной локальной очереди примерно до500событий, удаляются по истечении7суток и передаются небольшими пакетами. Выключение аналитики останавливает сбор и передачу, отменяет ожидающую отправку и удаляет очередь; старые события не отправляются после повторного включения. Обновление приложения и повторное включение аналитики не регистрируются как новая установка.

До публикации оператор сервиса должен указать и проверить сроки серверного хранения, контроль доступа, поставщиков инфраструктуры, контактные данные и применимые права на удаление. Этот проект не утверждает непроверенные гарантии серверного хранения или анонимности.
