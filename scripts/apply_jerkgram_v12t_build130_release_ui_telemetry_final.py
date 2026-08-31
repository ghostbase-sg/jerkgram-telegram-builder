#!/usr/bin/env python3
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
BASE = HERE / "apply_jerkgram_v12t_build130_release_ui_telemetry1.py"
spec = importlib.util.spec_from_file_location("build130_release_base", BASE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.PROFILE = module.ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenMultilineInputtem.swift"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    module.req(text.count(old) == 1, f"{label}: expected exactly one materialized owner, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_settings_final(text: str) -> str:
    if module.MARK in text:
        return text

    start, end = module.bounds(text, "if page == .appearance {")
    block = text[start:end]
    target_rows = (
        "            .info(0, strings.animatedBackgroundHint),\n",
        "            .info(0, strings.profileEffectDisabledHint),\n",
    )
    for row in target_rows:
        module.req(block.count(row) == 1, f"Appearance target hint missing or ambiguous: {row.strip()}")
        block = block.replace(row, "", 1)
    module.req("strings.hidePhoneHint" in block, "Appearance hide-phone hint must survive")
    text = text[:start] + block + text[end:]

    bridge = '''private let jerkgramTelemetryEnabledKey = "jerkgram.telemetry.anonymous.enabled"
private func jerkgramTelemetryEnabled() -> Bool {
    let defaults = UserDefaults.standard
    return defaults.object(forKey: jerkgramTelemetryEnabledKey) == nil ? true : defaults.bool(forKey: jerkgramTelemetryEnabledKey)
}
private func jerkgramSetTelemetryEnabled(_ enabled: Bool) {
    UserDefaults.standard.set(enabled, forKey: jerkgramTelemetryEnabledKey)
    NotificationCenter.default.post(name: Notification.Name("JerkgramTelemetryPreferenceChanged"), object: nil)
}

'''
    enum_owner = "private enum GhostBaseSettingsEntry: ItemListNodeEntry {"
    enum_index = text.find(enum_owner)
    module.req(enum_index >= 0, "settings entry enum missing")
    text = text[:enum_index] + bridge + text[enum_index:]

    enum_index = text.find(enum_owner)
    insert = text.find("\n", enum_index) + 1
    text = text[:insert] + "    case aboutValue(Int32, Int32, String, String)\n    case telemetryToggle(Int32, Int32, String, Bool)\n" + text[insert:]

    section_owner = '''        case let .toggle(section, _, _, _, _):
            return section'''
    section_replacement = '''        case let .aboutValue(section, _, _, _):
            return section
        case let .telemetryToggle(section, _, _, _):
            return section
''' + section_owner
    text = replace_once(text, section_owner, section_replacement, "section switch")

    stable_owner = '''        case let .toggle(section, index, _, _, _):
            return section * 1000 + index'''
    stable_replacement = '''        case let .aboutValue(section, index, _, _):
            return section * 1000 + index
        case let .telemetryToggle(section, index, _, _):
            return section * 1000 + index
''' + stable_owner
    text = replace_once(text, stable_owner, stable_replacement, "stableId switch")

    equality_owner = '''        case let .toggle(ls, li, lk, lt, lv):
            if case let .toggle(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            }
            return false'''
    equality_replacement = '''        case let .aboutValue(ls, li, lt, lv):
            if case let .aboutValue(rs, ri, rt, rv) = rhs {
                return ls == rs && li == ri && lt == rt && lv == rv
            }
            return false
        case let .telemetryToggle(ls, li, lt, lv):
            if case let .telemetryToggle(rs, ri, rt, rv) = rhs {
                return ls == rs && li == ri && lt == rt && lv == rv
            }
            return false
''' + equality_owner
    text = replace_once(text, equality_owner, equality_replacement, "Equatable switch")

    item_owner = "        case let .toggle(_, _, key, title, value):"
    item_replacement = '''        case let .aboutValue(_, _, title, value):
            return ItemListDisclosureItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                label: value,
                labelStyle: .text,
                sectionId: self.section,
                style: .blocks,
                disclosureStyle: .none,
                action: nil
            )

        case let .telemetryToggle(_, _, title, value):
            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                value: value,
                sectionId: self.section,
                style: .blocks,
                updated: { enabled in
                    jerkgramSetTelemetryEnabled(enabled)
                }
            )

''' + item_owner
    text = replace_once(text, item_owner, item_replacement, "item renderer switch")

    start, end = module.bounds(text, "if page == .about {")
    block = text[start:end]
    return_index = block.find("return [")
    module.req(return_index >= 0, "About return array missing")
    array_start, array_end = module.bracket(block, return_index)
    array = '''[
            .header(0, strings.about),
            channelEntry(index: 1, username: "JerkgramApp", state: aboutChannelState),
            channelEntry(index: 2, username: "JerkgramCommunity", state: aboutCommunityState),
            .header(1, strings.version),
            .aboutValue(1, 1, strings.jerkgramVersion, Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "—"),
            .aboutValue(1, 2, strings.build, Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "—"),
            .aboutValue(1, 3, strings.telegramBase, "12.9.2"),
            .header(2, strings.privacy),
            .telemetryToggle(2, 1, strings.anonymousAnalytics, jerkgramTelemetryEnabled()),
            .info(3, strings.anonymousAnalyticsDescription)
        ]'''
    block = block[:array_start] + array + block[array_end:]
    text = text[:start] + block + text[end:]

    entries_owner = "private func ghostBaseSettingsEntries("
    owner_index = text.find(entries_owner)
    module.req(owner_index >= 0, "settings entries owner missing")
    text = text[:owner_index] + module.MARK + "\n" + text[owner_index:]
    return text


module.patch_settings = patch_settings_final

if __name__ == "__main__":
    module.main()
