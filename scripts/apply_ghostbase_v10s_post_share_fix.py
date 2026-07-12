#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATH = (
    ROOT
    / "work/swiftgram-src/submodules/ShareController/Sources"
    / "ShareController.swift"
)

if not PATH.is_file():
    raise RuntimeError(f"missing source: {PATH}")

text = PATH.read_text(encoding="utf-8")

marker = "GhostBase v1.0S Post Share Scheduled Send"

old = '''                    messagesToEnqueue = transformMessages(messagesToEnqueue, showNames: showNames, silently: silently, sendPaidMessageStars: requiresStars[peerId])
                    shareSignals.append(enqueueMessages(account: currentContext.context.account, peerId: peerId, messages: messagesToEnqueue))
'''

new = '''                    messagesToEnqueue = transformMessages(messagesToEnqueue, showNames: showNames, silently: silently, sendPaidMessageStars: requiresStars[peerId])

                    // MARK: GhostBase v1.0S Post Share Scheduled Send
                    let ghostBasePostShareScheduledEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false)

                    if ghostBasePostShareScheduledEnabled {
                        let ghostBasePostShareScheduleTime = Int32(Date().timeIntervalSince1970) + 12

                        messagesToEnqueue = messagesToEnqueue.map { message -> EnqueueMessage in
                            return message.withUpdatedAttributes { attributes in
                                var attributes = attributes

                                if !attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute }) {
                                    attributes.append(
                                        OutgoingScheduleInfoMessageAttribute(
                                            scheduleTime: ghostBasePostShareScheduleTime,
                                            repeatPeriod: nil
                                        )
                                    )
                                }

                                return attributes
                            }
                        }

                        UserDefaults.standard.set(
                            UserDefaults.standard.integer(
                                forKey: "GhostBase.SH1.ShareScheduledIntercept.Count"
                            ) + 1,
                            forKey: "GhostBase.SH1.ShareScheduledIntercept.Count"
                        )

                        UserDefaults.standard.set(
                            "\\(peerId)",
                            forKey: "GhostBase.SH1.LastSharePeerId"
                        )

                        UserDefaults.standard.set(
                            messagesToEnqueue.count,
                            forKey: "GhostBase.SH1.LastShareMessageCount"
                        )

                        UserDefaults.standard.set(
                            Int(ghostBasePostShareScheduleTime),
                            forKey: "GhostBase.SH1.LastShareScheduleTime"
                        )
                    }

                    shareSignals.append(enqueueMessages(account: currentContext.context.account, peerId: peerId, messages: messagesToEnqueue))
'''

if marker not in text:
    if old not in text:
        raise RuntimeError(
            "post-share messagesToEnqueue anchor missing"
        )

    text = text.replace(old, new, 1)
    PATH.write_text(text, encoding="utf-8")

result = PATH.read_text(encoding="utf-8")

if marker not in result:
    raise RuntimeError("post-share marker missing")

print("[v1.0S POST SHARE] real .messages path patched")
