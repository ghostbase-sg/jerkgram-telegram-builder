#!/usr/bin/env python3
from pathlib import Path
import os
import re

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd()))).resolve()

THEME = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
BUILD = ROOT / "Telegram/BUILD"
APP = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

PRIMARY = "JerkgramGlassReveal"

def require(v, msg):
    if not v:
        raise RuntimeError("[Build113 recovery] " + msg)

def remove_case_branch(text, region_start, region_end, case_name):
    region = text[region_start:region_end]
    lines = region.splitlines(keepends=True)
    pattern = re.compile(r'^(?P<i>\s*)case (?:let )?\.' + re.escape(case_name) + r'\b')
    for index, line in enumerate(lines):
        m = pattern.match(line)
        if not m:
            continue
        indent = m.group("i")
        end = index + 1
        while end < len(lines):
            if re.match(r'^' + re.escape(indent) + r'case (?:let )?\.', lines[end]):
                break
            end += 1
        del lines[index:end]
        return text[:region_start] + "".join(lines) + text[region_end:]
    raise RuntimeError("[Build113 recovery] missing case branch: " + case_name)

def recover_theme_settings():
    text = THEME.read_text(encoding="utf-8")

    definitions = (
        '    // MARK: Jerkgram v1.1Z BUILD111_SAFE_ICON_ENTRIES1\n'
        '    case jerkgramIconHeader(PresentationTheme, String)\n'
        '    case jerkgramIconItem(PresentationTheme, PresentationStrings, [PresentationAppIcon], Bool, String?)\n'
        '    case iconHeader(PresentationTheme, String)\n'
        '    case iconItem(PresentationTheme, PresentationStrings, [PresentationAppIcon], Bool, String?)\n'
    )
    stock_definitions = (
        '    case iconHeader(PresentationTheme, String)\n'
        '    case iconItem(PresentationTheme, PresentationStrings, [PresentationAppIcon], Bool, String?)\n'
    )
    require(definitions in text, "Build111 icon enum definitions missing")
    text = text.replace(definitions, stock_definitions, 1)

    section_new = (
        '            case .jerkgramIconHeader, .jerkgramIconItem, .iconHeader, .iconItem:\n'
        '                return ThemeSettingsControllerSection.icon.rawValue\n'
    )
    section_stock = (
        '            case .iconHeader, .iconItem:\n'
        '                return ThemeSettingsControllerSection.icon.rawValue\n'
    )
    require(section_new in text, "Build111 icon section branch missing")
    text = text.replace(section_new, section_stock, 1)

    stable_new = '''        case .jerkgramIconHeader:
            return 12
        case .jerkgramIconItem:
            return 13
        case .iconHeader:
            return 14
        case .iconItem:
            return 15
        case .otherHeader:
            return 16
        case .sendWithCmdEnter:
            return 17
        case .showNextMediaOnTap:
            return 18
        case .showNextMediaOnTapInfo:
            return 19
'''
    stable_stock = '''        case .iconHeader:
            return 12
        case .iconItem:
            return 13
        case .otherHeader:
            return 14
        case .sendWithCmdEnter:
            return 15
        case .showNextMediaOnTap:
            return 16
        case .showNextMediaOnTapInfo:
            return 17
'''
    require(stable_new in text, "Build111 stable-id tail missing")
    text = text.replace(stable_new, stable_stock, 1)

    for case_name in ("jerkgramIconHeader", "jerkgramIconItem"):
        eq_start = text.find("    static func ==")
        item_start = text.find("    func item(", eq_start)
        require(eq_start >= 0 and item_start > eq_start, "ThemeSettings equality region missing")
        text = remove_case_branch(text, eq_start, item_start, case_name)

    for case_name in ("jerkgramIconHeader", "jerkgramIconItem"):
        item_start = text.find("    func item(", text.find("    static func =="))
        entries_start = text.find("private func themeSettingsControllerEntries", item_start)
        require(item_start >= 0 and entries_start > item_start, "ThemeSettings item region missing")
        text = remove_case_branch(text, item_start, entries_start, case_name)

    build111_sections = '''    // MARK: Jerkgram v1.1Z BUILD111_ICON_SECTIONS1
    let jerkgramAppIcons = availableAppIcons.filter {
        $0.name.hasPrefix("JerkGram") || $0.name.hasPrefix("Jerkgram")
    }
    let telegramAppIcons = availableAppIcons.filter {
        !$0.name.hasPrefix("JerkGram") && !$0.name.hasPrefix("Jerkgram")
    }

    if !jerkgramAppIcons.isEmpty {
        entries.append(.jerkgramIconHeader(
            presentationData.theme,
            "JERKGRAM APP ICON"
        ))
        entries.append(.jerkgramIconItem(
            presentationData.theme,
            presentationData.strings,
            jerkgramAppIcons,
            isPremium,
            currentAppIconName
        ))
    }

    if !telegramAppIcons.isEmpty {
        entries.append(.iconHeader(
            presentationData.theme,
            strings.Appearance_AppIcon.uppercased()
        ))
        entries.append(.iconItem(
            presentationData.theme,
            presentationData.strings,
            telegramAppIcons,
            isPremium,
            currentAppIconName
        ))
    }
'''
    stock_sections = '''    if !availableAppIcons.isEmpty {
        entries.append(.iconHeader(presentationData.theme, strings.Appearance_AppIcon.uppercased()))
        entries.append(.iconItem(presentationData.theme, presentationData.strings, availableAppIcons, isPremium, currentAppIconName))
    }
'''
    require(build111_sections in text, "Build111 icon sections block missing")
    text = text.replace(build111_sections, stock_sections, 1)

    fallback_old = 'currentAppIconName.set(currentAppIcon?.name ?? "Blue")'
    fallback_new = f'currentAppIconName.set(currentAppIcon?.name ?? "{PRIMARY}")'
    require(fallback_old in text, "stock icon fallback anchor missing")
    text = text.replace(fallback_old, fallback_new, 1)

    require("jerkgramIconHeader" not in text and "jerkgramIconItem" not in text, "custom icon enum cases survived")
    THEME.write_text(text, encoding="utf-8")

def recover_primary_icon():
    text = BUILD.read_text(encoding="utf-8")
    old = '    primary_app_icon = "Telegram",\n'
    new = f'    primary_app_icon = "{PRIMARY}",\n'
    require(old in text, "Build111 Telegram primary_app_icon missing")
    text = text.replace(old, new, 1)
    for name in ("Telegram", "JerkgramGlassReveal", "JerkgramGlassSolid"):
        require(f'"{name}"' in text, f"Composer icon missing: {name}")
    BUILD.write_text(text, encoding="utf-8")

def recover_app_delegate_default():
    text = APP.read_text(encoding="utf-8")
    reveal_old = 'PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview"),'
    reveal_new = 'PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview", isDefault: true),'
    require(reveal_old in text, "Glass Reveal runtime row missing")
    text = text.replace(reveal_old, reveal_new, 1)

    blue_old = 'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: true),'
    blue_new = 'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon"),'
    require(blue_old in text, "Build111 BlueIcon default row missing")
    text = text.replace(blue_old, blue_new, 1)

    require(reveal_new in text, "Glass Reveal is not logical default")
    APP.write_text(text, encoding="utf-8")

recover_theme_settings()
recover_primary_icon()
recover_app_delegate_default()
print("[Build113 recovery] Appearance enum restored to stock topology")
print("[Build113 recovery] primary icon = JerkgramGlassReveal")
print("[Build113 recovery] AppDelegate logical default = JerkgramGlassReveal")
