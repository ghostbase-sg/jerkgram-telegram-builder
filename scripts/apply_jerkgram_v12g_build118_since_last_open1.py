#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
CHAT = ROOT / "submodules/TelegramUI/Sources/ChatController.swift"
BUILD = ROOT / "submodules/TelegramUI/BUILD"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 since last opening] " + message)


def replace_once(text, old, new, name):
    require(text.count(old) == 1, name + " anchor count != 1")
    return text.replace(old, new, 1)


def patch_chat(text):
    text = replace_once(text, "import TextProcessingScreen\n", "import TextProcessingScreen\nimport JerkgramCore\n", "core import")
    marker = '''        self.didAppear = true

'''
    addition = '''        // MARK: Jerkgram v1.2G BUILD118_SINCE_LAST_OPEN1
        if case .standard(.default) = self.mode, let chatPeerId = self.chatLocation.peerId {
            let accountPeerId = self.context.account.peerId.toInt64()
            let chatPeerIdValue = chatPeerId.toInt64()
            Queue.concurrentDefaultQueue().async { [weak self] in
                guard let self else { return }
                let rootURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                    .appendingPathComponent("Jerkgram", isDirectory: true)
                let eventStore = JerkgramJSONLEventStore(rootURL: rootURL)
                let events = (try? eventStore.events(accountPeerId: accountPeerId, chatPeerId: chatPeerIdValue)) ?? []
                let watermarkStore = JerkgramVisitWatermarkStore(rootURL: rootURL)
                guard let changes = try? watermarkStore.snapshotChangesSinceLastOpening(
                    accountPeerId: accountPeerId,
                    chatPeerId: chatPeerIdValue,
                    events: events
                ), changes.deletedCount + changes.editedCount + changes.recoveredMediaCount > 0 else { return }
                Queue.mainQueue().async { [weak self] in
                    guard let self, self.viewIfLoaded?.window != nil else { return }
                    let text = self.presentationData.strings.jerkgram.changesSinceLastOpening(
                        changes.deletedCount,
                        changes.editedCount,
                        changes.recoveredMediaCount
                    )
                    self.present(UndoOverlayController(
                        presentationData: self.presentationData,
                        content: .info(
                            title: nil,
                            text: text,
                            timeout: 6.0,
                            customUndoText: self.presentationData.strings.jerkgram.timeMachine
                        ),
                        elevatedLayout: false,
                        position: .top,
                        action: { [weak self] action in
                            guard case .undo = action, let self else { return false }
                            let controller = jerkgramTimeMachineController(
                                context: self.context,
                                chatPeerId: chatPeerIdValue,
                                initialQuery: "",
                                eventIds: Set(changes.eventIds),
                                navigateToMessage: { [weak self] messageId in
                                    self?.navigateToMessage(from: nil, to: .id(messageId, NavigateToMessageParams(timestamp: nil, quote: nil)), forceInCurrentChat: true)
                                }
                            )
                            self.push(controller)
                            return true
                        }
                    ), in: .current)
                }
            }
        }

'''
    return replace_once(text, marker, marker + addition, "viewDidAppear")


def main():
    for path in (CHAT, BUILD, STRINGS):
        require(path.is_file(), "missing target: " + str(path))
    CHAT.write_text(patch_chat(CHAT.read_text()), encoding="utf-8")
    build = BUILD.read_text()
    dep = '        "//submodules/JerkgramCore:JerkgramCore",\n'
    if dep not in build:
        build = replace_once(build, "    deps = [\n", "    deps = [\n" + dep, "TelegramUI deps")
    BUILD.write_text(build, encoding="utf-8")
    strings = STRINGS.read_text()
    strings += '''

// MARK: Jerkgram v1.2G BUILD118_SINCE_LAST_OPEN_STRINGS1
public extension JerkgramStrings {
    func changesSinceLastOpening(_ deleted: Int, _ edited: Int, _ media: Int) -> String {
        if self.languageCode == "ru" {
            return "С прошлого посещения: удалено \\(deleted), изменено \\(edited), медиа \\(media)"
        } else {
            return "Since your last visit: \\(deleted) deleted, \\(edited) edited, \\(media) media"
        }
    }
}
'''
    STRINGS.write_text(strings, encoding="utf-8")
    print("[Build118 since last opening] local per-chat summary installed")


if __name__ == "__main__":
    main()
