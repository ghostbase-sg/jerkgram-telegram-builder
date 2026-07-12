from pathlib import Path
import re

SETTINGS = Path(
    "work/swiftgram-src/submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)
PANEL = Path(
    "work/swiftgram-src/submodules/TelegramUI/Components/Chat/"
    "ChatMessageSelectionInputPanelNode/Sources/"
    "ChatMessageSelectionInputPanelNode.swift"
)

settings = SETTINGS.read_text()
panel = PANEL.read_text()

def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"[v1.0V forward] missing anchor: {label}")
    return text.replace(old, new, 1)

settings = once(
    settings,
    '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n',
    '    static let showEditHistory = "GhostBase.Messages.ShowEditHistory"\n'
    '    static let forwardWithoutAuthorButton = '
    '"GhostBase.Messages.ForwardWithoutAuthorButton"\n',
    "key"
)

settings = once(
    settings,
    "    var showEditHistory: Bool\n"
    "    var sendTextStyle: String\n",
    "    var showEditHistory: Bool\n"
    "    var forwardWithoutAuthorButton: Bool\n"
    "    var sendTextStyle: String\n",
    "state field"
)

load_old = (
    "            showEditHistory: ghostBaseBool("
    "GhostBaseKey.showEditHistory, defaultValue: true),\n"
    "            sendTextStyle: ghostBaseString(\n"
)

load_new = (
    "            showEditHistory: ghostBaseBool("
    "GhostBaseKey.showEditHistory, defaultValue: true),\n"
    "            forwardWithoutAuthorButton: ghostBaseBool(\n"
    "                GhostBaseKey.forwardWithoutAuthorButton,\n"
    "                defaultValue: true\n"
    "            ),\n"
    "            sendTextStyle: ghostBaseString(\n"
)

settings = once(settings, load_old, load_new, "state load")

save_old = (
    "        UserDefaults.standard.set("
    "self.showEditHistory, forKey: GhostBaseKey.showEditHistory)\n"
)

save_new = (
    save_old
    + "        UserDefaults.standard.set(\n"
    + "            self.forwardWithoutAuthorButton,\n"
    + "            forKey: GhostBaseKey.forwardWithoutAuthorButton\n"
    + "        )\n"
)

settings = once(settings, save_old, save_new, "state save")

handler_old = (
    "            case GhostBaseKey.showEditHistory:\n"
    "                updated.showEditHistory = value\n"
)

handler_new = (
    handler_old
    + "            case GhostBaseKey.forwardWithoutAuthorButton:\n"
    + "                updated.forwardWithoutAuthorButton = value\n"
)

settings = once(settings, handler_old, handler_new, "toggle handler")

row_marker = "GhostBaseKey.forwardWithoutAuthorButton"

if settings.count(row_marker) < 4:
    pattern = re.compile(
        r'(?P<indent>[ \t]*)\.header\('
        r'(?P<section>\d+),[ \t]*"Отправка текста"\),'
    )
    match = pattern.search(settings)

    if match is None:
        raise RuntimeError(
            "[v1.0V forward] missing Messages send-style header"
        )

    indent = match.group("indent")
    section = match.group("section")

    row = (
        f'{indent}.header({section}, "Пересылка"),\n'
        f'{indent}.toggle(\n'
        f'{indent}    {section},\n'
        f'{indent}    40,\n'
        f'{indent}    GhostBaseKey.forwardWithoutAuthorButton,\n'
        f'{indent}    "Кнопка «Переслать без автора»",\n'
        f'{indent}    state.forwardWithoutAuthorButton\n'
        f'{indent}),\n\n'
    )

    settings = settings[:match.start()] + row + settings[match.start():]

panel_marker = "GhostBase v1.0V forward without author visibility"

if panel_marker not in panel:
    anchor = "        reportButton.isHidden = true\n"

    block = (
        anchor
        + "\n"
        + "        // MARK: GhostBase v1.0V forward without author visibility\n"
        + "        let ghostBaseShowForwardWithoutAuthor = (\n"
        + "            UserDefaults.standard.object(\n"
        + '                forKey: "GhostBase.Messages.ForwardWithoutAuthorButton"\n'
        + "            ) as? Bool\n"
        + "        ) ?? true\n"
        + "        self.forwardHideNamesButton.isHidden = "
        + "!ghostBaseShowForwardWithoutAuthor\n"
    )

    panel = once(panel, anchor, block, "selection panel")

SETTINGS.write_text(settings)
PANEL.write_text(panel)

print("[v1.0V forward] settings toggle applied")
print("[v1.0V forward] existing hide-author button connected")
