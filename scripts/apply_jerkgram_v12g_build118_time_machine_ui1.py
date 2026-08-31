#!/usr/bin/env python3

from pathlib import Path
import os
import shutil


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_time_machine_ui1_payload/JerkgramTimeMachineController.swift"
ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SOURCE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/ChatSearchNavigationContentNode.swift"
BUILD = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/BUILD"
STRINGS = ROOT / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift"


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 Time Machine UI] " + message)


def patch_source(text):
    properties = '''    private let jerkgramTimeMachineBackground: GlassBackgroundView
    private let jerkgramTimeMachineLabel: UILabel
'''
    marker = "    private let interaction: ChatPanelInterfaceInteraction\n"
    require(marker in text, "interaction property missing")
    text = text.replace(marker, marker + properties, 1)
    init_marker = "        self.interaction = interaction\n"
    require(init_marker in text, "interaction init missing")
    text = text.replace(init_marker, init_marker + '''        self.jerkgramTimeMachineBackground = GlassBackgroundView()
        self.jerkgramTimeMachineLabel = UILabel()
        self.jerkgramTimeMachineLabel.textAlignment = .center
        self.jerkgramTimeMachineLabel.font = UIFont.systemFont(ofSize: 13.0, weight: .semibold)
''', 1)
    super_marker = "        super.init()\n"
    require(super_marker in text, "super init missing")
    background_marker = "        self.view.addSubview(self.backgroundContainer)\n"
    require(background_marker in text, "background hierarchy missing")
    text = text.replace(background_marker, background_marker + '''
        // Keep the Time Machine control above the full-size background container.
        self.view.addSubview(self.jerkgramTimeMachineBackground)
        self.jerkgramTimeMachineBackground.contentView.addSubview(self.jerkgramTimeMachineLabel)
        self.jerkgramTimeMachineBackground.contentView.addGestureRecognizer(
            UITapGestureRecognizer(target: self, action: #selector(self.jerkgramOpenTimeMachine))
        )
''', 1)
    text = text.replace("        return 60.0\n", "        return 104.0\n", 1)
    layout_marker = "        return size\n    }"
    require(layout_marker in text, "layout return missing")
    layout = '''        let timeMachineFrame = CGRect(
            x: leftInset + 16.0,
            y: 56.0,
            width: size.width - leftInset - rightInset - 32.0,
            height: 36.0
        )
        self.jerkgramTimeMachineLabel.text = self.strings.jerkgram.timeMachine
        self.jerkgramTimeMachineLabel.textColor = self.theme.chat.inputPanel.panelControlColor
        transition.setFrame(view: self.jerkgramTimeMachineBackground, frame: timeMachineFrame)
        self.jerkgramTimeMachineBackground.update(
            size: timeMachineFrame.size, cornerRadius: 18.0,
            isDark: self.theme.overallDarkAppearance,
            tintColor: .init(kind: self.preferClearGlass ? .clear : .panel),
            isInteractive: true, transition: transition
        )
        self.jerkgramTimeMachineLabel.frame = CGRect(origin: .zero, size: timeMachineFrame.size)

        return size
    }'''
    text = text.replace(layout_marker, layout, 1)
    class_end = text.rfind("}\n")
    require(class_end >= 0, "class end missing")
    method = '''    @objc private func jerkgramOpenTimeMachine() {
        guard let chatPeerId = self.chatLocation.peerId else { return }
        let controller = jerkgramTimeMachineController(
            context: self.context,
            chatPeerId: chatPeerId.toInt64(),
            initialQuery: self.searchBar.text,
            navigateToMessage: { [weak self] messageId in
                self?.interaction.navigateToMessage(messageId, false, false, .generic)
            }
        )
        self.interaction.presentController(
            controller,
            ViewControllerPresentationArguments(presentationAnimation: .modalSheet)
        )
    }

'''
    return text[:class_end] + method + text[class_end:]


def patch_build(text):
    for dep in ('        "//submodules/JerkgramCore:JerkgramCore",\n', '        "//submodules/ItemListUI:ItemListUI",\n', '        "//submodules/AlertUI:AlertUI",\n', '        "//submodules/PresentationDataUtils:PresentationDataUtils",\n'):
        if dep not in text:
            require("deps = [\n" in text, "BUILD deps missing")
            text = text.replace("deps = [\n", "deps = [\n" + dep, 1)
    return text


def main():
    for path in (SOURCE, BUILD, STRINGS):
        require(path.is_file(), "missing target: " + str(path))
    target = SOURCE.parent / "JerkgramTimeMachineController.swift"
    require(not target.exists(), "controller already exists")
    shutil.copy2(PAYLOAD, target)
    SOURCE.write_text(patch_source(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    BUILD.write_text(patch_build(BUILD.read_text(encoding="utf-8")), encoding="utf-8")
    strings = STRINGS.read_text(encoding="utf-8")
    strings += '''

// MARK: Jerkgram v1.2G BUILD118_TIME_MACHINE_STRINGS1
public extension JerkgramStrings {
    var timeMachine: String { self.languageCode == "ru" ? "Машина времени" : "Time Machine" }
    var timeMachineFilters: String { self.languageCode == "ru" ? "Фильтры" : "Filters" }
    var timeMachineDeleted: String { self.languageCode == "ru" ? "Удалённые" : "Deleted" }
    var timeMachineEdited: String { self.languageCode == "ru" ? "Отредактированные" : "Edited" }
    var timeMachineMedia: String { self.languageCode == "ru" ? "Восстановленные медиа" : "Recovered Media" }
    var timeMachineAuthor: String { self.languageCode == "ru" ? "Автор" : "Author" }
    var timeMachineAllAuthors: String { self.languageCode == "ru" ? "Все" : "All" }
    var timeMachineResults: String { self.languageCode == "ru" ? "Результаты" : "Results" }
    var timeMachineEmpty: String { self.languageCode == "ru" ? "Локальных изменений не найдено." : "No local changes found." }
    var timeMachineLoadMore: String { self.languageCode == "ru" ? "Загрузить ещё" : "Load More" }
}
'''
    STRINGS.write_text(strings, encoding="utf-8")
    print("[Build118 Time Machine UI] ordinary chat search route and local filters installed")


if __name__ == "__main__":
    main()
