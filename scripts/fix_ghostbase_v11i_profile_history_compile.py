#!/usr/bin/env python3

import os
from pathlib import Path


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        "/root/gb_builder/work/swiftgram-src",
    )
)

PATH = (
    ROOT
    / "submodules/TelegramUI/Components/PeerInfo/"
      "PeerInfoScreen/Sources/"
      "GhostBaseProfileReportPaneNode.swift"
)

if not PATH.is_file():
    raise RuntimeError(
        f"[V11I HISTORY FIX] missing: {PATH}"
    )


text = PATH.read_text(
    encoding="utf-8"
)


MARKER = (
    "// MARK: GhostBase v1.1I "
    "HISTORYCOMPILEFIX1"
)

if MARKER in text:
    print(
        "[V11I HISTORY FIX] already materialized"
    )
else:
    start_token = (
        "    static func personalChannelReport("
    )

    end_token = (
        "\n}\n\nfunc ghostBaseRecordObservedProfileV11G"
    )

    start = text.find(start_token)
    end = text.find(end_token, start)

    if start < 0 or end < 0:
        raise RuntimeError(
            "[V11I HISTORY FIX] "
            "personalChannelReport boundaries missing"
        )

    replacement = r'''    // MARK: GhostBase v1.1I HISTORYCOMPILEFIX1
    static func personalChannelReport(
        accountPeerId: Int64,
        peerId: Int64
    ) -> String? {
        let key = self.personalChannelKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )

        guard
            let data = UserDefaults.standard.data(
                forKey: key
            ),
            let history = try? JSONDecoder().decode(
                GhostBasePersonalChannelHistoryV11G.self,
                from: data
            )
        else {
            return nil
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(
            identifier: "ru_RU"
        )
        formatter.dateFormat = "dd.MM.yyyy HH:mm"

        func stringValue(
            _ value: String?
        ) -> String {
            guard let value, !value.isEmpty else {
                return "—"
            }

            return value
        }

        func optionalValue<T>(
            _ value: T?
        ) -> String {
            guard let value else {
                return "—"
            }

            return String(
                describing: value
            )
        }

        var blocks: [String] = []
        var changeCount = 0

        if history.events.count >= 2 {
            for index in stride(
                from: history.events.count - 1,
                through: 1,
                by: -1
            ) {
                let previous =
                    history.events[index - 1]

                let current =
                    history.events[index]

                var changes: [String] = []

                if previous.channelPeerId
                    != current.channelPeerId {

                    if current.channelPeerId == nil {
                        changes.append(
                            "Личный канал: откреплён"
                        )
                    } else if previous.channelPeerId == nil {
                        changes.append(
                            "Личный канал: прикреплён"
                        )
                    } else {
                        let oldValue =
                            optionalValue(
                                previous.channelPeerId
                            )

                        let newValue =
                            optionalValue(
                                current.channelPeerId
                            )

                        changes.append(
                            "Канал ID: \(oldValue) → \(newValue)"
                        )
                    }
                }

                if previous.title
                    != current.title {

                    let oldValue =
                        stringValue(
                            previous.title
                        )

                    let newValue =
                        stringValue(
                            current.title
                        )

                    changes.append(
                        "Название: \(oldValue) → \(newValue)"
                    )
                }

                if previous.username
                    != current.username {

                    let oldValue =
                        stringValue(
                            previous.username
                        )

                    let newValue =
                        stringValue(
                            current.username
                        )

                    changes.append(
                        "Username: \(oldValue) → \(newValue)"
                    )
                }

                if previous.link
                    != current.link {

                    let oldValue =
                        stringValue(
                            previous.link
                        )

                    let newValue =
                        stringValue(
                            current.link
                        )

                    changes.append(
                        "Ссылка: \(oldValue) → \(newValue)"
                    )
                }

                if previous.subscriberCount
                    != current.subscriberCount {

                    let oldValue =
                        optionalValue(
                            previous.subscriberCount
                        )

                    let newValue =
                        optionalValue(
                            current.subscriberCount
                        )

                    changes.append(
                        "Подписчики: \(oldValue) → \(newValue)"
                    )
                }

                if previous.topMessageId
                    != current.topMessageId {

                    let oldValue =
                        optionalValue(
                            previous.topMessageId
                        )

                    let newValue =
                        optionalValue(
                            current.topMessageId
                        )

                    changes.append(
                        "Последний message ID: \(oldValue) → \(newValue)"
                    )
                }

                guard !changes.isEmpty else {
                    continue
                }

                changeCount += changes.count

                let timestamp =
                    TimeInterval(
                        current.observedAt
                    )

                let date =
                    formatter.string(
                        from: Date(
                            timeIntervalSince1970:
                                timestamp
                        )
                    )

                var lines: [String] = [
                    date
                ]

                for change in changes {
                    lines.append(
                        "• \(change)"
                    )
                }

                blocks.append(
                    lines.joined(
                        separator: "\n"
                    )
                )
            }
        }

        var lines: [String] = [
            "История личного канала",
            "Зафиксировано изменений: \(changeCount)"
        ]

        if let first = history.events.first {
            let timestamp =
                TimeInterval(
                    first.observedAt
                )

            let date =
                formatter.string(
                    from: Date(
                        timeIntervalSince1970:
                            timestamp
                    )
                )

            lines.append(
                "Первое наблюдение: \(date)"
            )
        }

        if blocks.isEmpty {
            lines.append(
                "Изменений после первого наблюдения пока нет."
            )
        } else {
            lines.append("")
            lines.append(
                blocks.joined(
                    separator: "\n\n"
                )
            )
        }

        return lines.joined(
            separator: "\n"
        )
    }
'''

    text = (
        text[:start]
        + replacement
        + text[end:]
    )

    PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[V11I HISTORY FIX] patched:"
    )
    print(
        f"  {PATH}"
    )
    print(
        "[V11I HISTORY FIX] complex Optional.map "
        "expressions removed"
    )
    print(
        "[V11I HISTORY FIX] done"
    )
