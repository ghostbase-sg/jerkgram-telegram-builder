#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
TIME_MACHINE = ROOT / "submodules/TelegramUI/Components/Chat/ChatSearchNavigationContentNode/Sources/JerkgramTimeMachineController.swift"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build123 settings UI] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, f"{label}: expected one anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


SHARED = r'''// MARK: Jerkgram v1.2L BUILD123_SETTINGS_SYSTEM1
// Shared visual contract used by every internal Jerkgram destination.
private func JerkgramSettingsSectionHeaderItem(
    presentationData: ItemListPresentationData,
    text: String,
    sectionId: ItemListSectionId
) -> ListViewItem {
    return ItemListSectionHeaderItem(
        presentationData: presentationData,
        text: text.uppercased(),
        sectionId: sectionId
    )
}

private func JerkgramSettingsStatusItem(
    presentationData: ItemListPresentationData,
    text: String,
    sectionId: ItemListSectionId
) -> ListViewItem {
    return ItemListDisclosureItem(
        presentationData: presentationData,
        systemStyle: .glass,
        title: text,
        label: "",
        labelStyle: .text,
        sectionId: sectionId,
        style: .blocks,
        disclosureStyle: .none,
        action: nil
    )
}

// MARK: Jerkgram v1.2L BUILD123_SETTINGS_TOGGLE_ICONS1
private func jerkgramSettingsToggleIcon(_ key: String) -> UIImage? {
    if key.hasPrefix("jerkgram.GhostMode.") {
        return jerkgramSettingsMenuIcon("Chat/Context Menu/Eye")
    } else if key.hasPrefix("jerkgram.Messages.") {
        return jerkgramSettingsMenuIcon("Chat/Context Menu/MessageBubble")
    } else if key.hasPrefix("jerkgram.ProtectedContent.") {
        return jerkgramSettingsMenuIcon("Premium/CopyProtection/NoForward")
    } else if key.hasPrefix("jerkgram.Appearance.") || key.hasPrefix("jerkgram.Glass.") {
        return jerkgramSettingsMenuIcon("Chat/Context Menu/ApplyTheme")
    } else if key.hasPrefix("jerkgram.Stars.") || key.hasPrefix("jerkgram.Profile.") {
        return jerkgramSettingsMenuIcon("Jerkgram/Settings/Airplane")
    } else {
        return jerkgramSettingsMenuIcon("Chat/Context Menu/Info")
    }
}

'''


def patch_toggle_icons(text: str) -> str:
    if "BUILD123_SETTINGS_TOGGLE_ICONS1" not in text:
        anchor = "private enum GhostBaseSettingsEntry: ItemListNodeEntry {"
        require(text.count(anchor) == 1, "settings toggle icon anchor")
        helper = SHARED[SHARED.index("// MARK: Jerkgram v1.2L BUILD123_SETTINGS_TOGGLE_ICONS1"):]
        text = text.replace(anchor, helper + anchor, 1)
    old = '''            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,'''
    if "icon: jerkgramSettingsToggleIcon(key)" not in text:
        new = '''            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                icon: jerkgramSettingsToggleIcon(key),
                title: title,'''
        text = replace_once(text, old, new, "settings toggle category icon")
    return text


def patch_settings() -> None:
    text = SETTINGS.read_text(encoding="utf-8")
    if "BUILD123_SETTINGS_SYSTEM1" in text:
        updated = patch_toggle_icons(text)
        if updated != text:
            SETTINGS.write_text(updated, encoding="utf-8")
        return
    anchor = "private enum GhostBaseSettingsEntry: ItemListNodeEntry {"
    require(text.count(anchor) == 1, "settings entry anchor")
    text = text.replace(anchor, SHARED + anchor, 1)
    text = replace_once(
        text,
        "            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)",
        "            return JerkgramSettingsSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)",
        "shared section header",
    )
    text = replace_once(
        text,
        '''            return ItemListTextItem(
                presentationData: presentationData,
                text: .plain(text),
                sectionId: self.section
            )''',
        "            return JerkgramSettingsStatusItem(presentationData: presentationData, text: text, sectionId: self.section)",
        "research status",
    )
    text = replace_once(
        text,
        "            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)",
        "            return JerkgramSettingsStatusItem(presentationData: presentationData, text: text, sectionId: self.section)",
        "page status",
    )
    text = patch_toggle_icons(text)
    SETTINGS.write_text(text, encoding="utf-8")


DATE_HELPER = r'''// MARK: Jerkgram v1.2L BUILD123_TIME_MACHINE_UI1
private func jerkgramTimeMachineDateText(_ timestampMs: Int64, dateTimeFormat: PresentationDateTimeFormat) -> String {
    let _ = dateTimeFormat
    let timestamp = TimeInterval(timestampMs) / 1000.0
    guard timestamp > 0.0 else { return "" }
    let formatter = DateFormatter()
    formatter.locale = Locale.current
    formatter.dateStyle = .medium
    formatter.timeStyle = .short
    return formatter.string(from: Date(timeIntervalSince1970: timestamp))
}

'''


def patch_time_machine() -> None:
    text = TIME_MACHINE.read_text(encoding="utf-8")
    if "BUILD123_TIME_MACHINE_UI1" in text:
        return
    anchor = "private func jerkgramTimeMachineRootURL() -> URL {"
    require(text.count(anchor) == 1, "Time Machine date helper anchor")
    text = text.replace(anchor, DATE_HELPER + anchor, 1)
    old_filter = '''            return ItemListDisclosureItem(
                presentationData: presentationData,
                title: title, label: value, labelStyle: .text,'''
    new_filter = '''            return ItemListDisclosureItem(
                presentationData: presentationData, systemStyle: .glass,
                title: title, label: value, labelStyle: .text,'''
    text = replace_once(text, old_filter, new_filter, "Time Machine filter glass")
    old_result = '''            let text = event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
            entries.append(.result(2, Int32(index + 1), String(text.prefix(80)), jerkgramEventKindTitle(event.kind, strings: strings), event))'''
    new_result = r'''            let text = event.payload.text ?? event.payload.previousText ?? event.eventId.rawValue
            let date = jerkgramTimeMachineDateText(event.observedAtMs, dateTimeFormat: presentationData.dateTimeFormat)
            let kind = jerkgramEventKindTitle(event.kind, strings: strings)
            let detail = date.isEmpty ? kind : "\(kind) · \(date)"
            entries.append(.result(2, Int32(index + 1), String(text.prefix(120)), detail, event))'''
    text = replace_once(text, old_result, new_result, "Time Machine dated results")
    TIME_MACHINE.write_text(text, encoding="utf-8")


def main() -> None:
    patch_settings()
    patch_time_machine()
    print("[Build123 settings UI] GREEN")


if __name__ == "__main__":
    main()
