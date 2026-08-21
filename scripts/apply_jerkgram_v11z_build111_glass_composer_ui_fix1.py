#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

BUILDER = Path(
    os.environ.get(
        "GHOSTBASE_BUILDER_ROOT",
        str(Path(__file__).resolve().parents[1]),
    )
).resolve()

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

ASSET_ROOT = BUILDER / "assets/JerkgramGlass"
PACKAGE_ZIP = ASSET_ROOT / "JerkgramGlassIconComposerPackages.zip"
PREVIEW_ZIP = ASSET_ROOT / "JerkgramGlassUIPreviews.zip"
LEGACY_ICON_ROOT = BUILDER / "assets/JerkGram_Icons/files"

IOS = ROOT / "Telegram/Telegram-iOS"
BUILD = ROOT / "Telegram/BUILD"
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
THEME_SETTINGS = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsController.swift"
THEME_ICON_ITEM = ROOT / "submodules/SettingsUI/Sources/Themes/ThemeSettingsAppIconItem.swift"
JG_SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
PEER_LIST = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoListPaneNode.swift"

OFFICIAL_ICON = IOS / "Telegram.icon"
OLD_STEEL_COMPOSER = IOS / "JerkGramSteelReveal.icon"
PREVIEW_DIR = IOS / "JerkgramGlassUIPreviews"

COMPOSER_IDS = ["JerkgramGlassReveal", "JerkgramGlassSolid"]
LEGACY_JG_IDS = [
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
]

EXPECTED_ICON_JSON = "cf7c84b1ceef48a16c9ea2c193428417f99b80258752d7fcc14914f6b0ca4c89"
EXPECTED_OVAL = "30b7245c9edef107ea7520cdd958246fcc771fa0872bb2f6cd13ab2dc11cfffd"
EXPECTED_REVEAL_PLANE = "9dc83c22a01878aac9f8494c509a7862fdd1679d7e7f7f0026afc367d3a7e304"
EXPECTED_SOLID_PLANE = "bf53330c359bb661f93b86f292d48206a31027b107e7b92d274c8663d2ceb61a"
EXPECTED_REVEAL_PREVIEW = "60900a0dfe618efb8d4414e07a2f211206cbc76467fb5ddec0ef7669bbf0c77e"
EXPECTED_SOLID_PREVIEW = "6562cd0d2f23b57cf19d0ad133f395d586cd33a65ec7a4098fb476bc36ff9dd5"
EXPECTED_STEEL_MASTER = "e1a72196d6ff5a4d86d1653d3c368d0c40c51bc7240218cd3082b2f2f3c61097"


def require(condition, message):
    if not condition:
        raise RuntimeError("[Build111] " + message)


def read(path):
    require(path.is_file(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(path):
    data = path.read_bytes()[:24]
    require(
        len(data) >= 24
        and data[:8] == b"\x89PNG\r\n\x1a\n"
        and data[12:16] == b"IHDR",
        f"invalid PNG: {path}",
    )
    return struct.unpack(">II", data[16:24])


def safe_extract(zip_path, destination):
    with zipfile.ZipFile(zip_path, "r") as archive:
        base = destination.resolve()
        for info in archive.infolist():
            target = (destination / info.filename).resolve()
            require(
                target == base or base in target.parents,
                f"unsafe ZIP member: {info.filename}",
            )
        archive.extractall(destination)


def svg_info(path):
    raw = path.read_text(encoding="utf-8")
    require("<image" not in raw, f"<image> forbidden: {path}")
    require("<mask" not in raw, f"<mask> forbidden: {path}")
    require("<filter" not in raw, f"<filter> forbidden: {path}")
    root = ET.fromstring(raw)
    require(root.attrib.get("width") == "1024", f"width != 1024: {path}")
    require(root.attrib.get("height") == "1024", f"height != 1024: {path}")
    require(root.attrib.get("viewBox") == "0 0 1024 1024", f"viewBox mismatch: {path}")
    paths = [node for node in root.iter() if node.tag.split("}")[-1] == "path"]
    require(len(paths) == 1, f"expected exactly one Plane path element: {path}")
    return raw, paths[0]


def validate_and_install_composer_assets():
    require(PACKAGE_ZIP.is_file(), f"missing package ZIP: {PACKAGE_ZIP}")
    require(PREVIEW_ZIP.is_file(), f"missing preview ZIP: {PREVIEW_ZIP}")
    require(OFFICIAL_ICON.is_dir(), "Official Telegram.icon missing")

    official_json = OFFICIAL_ICON / "icon.json"
    official_oval = OFFICIAL_ICON / "Assets/Oval.svg"
    require(sha256(official_json) == EXPECTED_ICON_JSON, "Telegram.icon/icon.json is not Official 12.9.2")
    require(sha256(official_oval) == EXPECTED_OVAL, "Telegram.icon/Assets/Oval.svg is not Official 12.9.2")

    with tempfile.TemporaryDirectory(prefix="jerkgram-build111-") as tmp_raw:
        tmp = Path(tmp_raw)
        pkg_out = tmp / "package"
        prev_out = tmp / "previews"
        pkg_out.mkdir()
        prev_out.mkdir()
        safe_extract(PACKAGE_ZIP, pkg_out)
        safe_extract(PREVIEW_ZIP, prev_out)

        pkg = pkg_out / "JerkgramGlassIconComposerPackages"
        checksums_path = pkg / "CHECKSUMS.json"
        require(checksums_path.is_file(), "CHECKSUMS.json missing")
        checksums = json.loads(checksums_path.read_text(encoding="utf-8"))
        require(checksums.get("official_icon_json_sha256") == EXPECTED_ICON_JSON, "CHECKSUMS official icon.json mismatch")
        require(checksums.get("official_oval_svg_sha256") == EXPECTED_OVAL, "CHECKSUMS official Oval mismatch")

        installed = {}
        for icon_id, plane_hash in (
            ("JerkgramGlassReveal", EXPECTED_REVEAL_PLANE),
            ("JerkgramGlassSolid", EXPECTED_SOLID_PLANE),
        ):
            source = pkg / f"{icon_id}.icon"
            icon_json = source / "icon.json"
            oval = source / "Assets/Oval.svg"
            plane = source / "Assets/Plane.svg"
            for path in (icon_json, oval, plane):
                require(path.is_file(), f"package file missing: {path}")

            require(sha256(icon_json) == EXPECTED_ICON_JSON, f"{icon_id} icon.json hash mismatch")
            require(sha256(oval) == EXPECTED_OVAL, f"{icon_id} Oval hash mismatch")
            require(sha256(plane) == plane_hash, f"{icon_id} Plane hash mismatch")
            require(icon_json.read_bytes() == official_json.read_bytes(), f"{icon_id} icon.json != Official")
            require(oval.read_bytes() == official_oval.read_bytes(), f"{icon_id} Oval != Official")
            _, plane_node = svg_info(plane)
            installed[icon_id] = (source, plane_node.attrib.get("d", ""), plane_node.attrib.get("fill-rule"))

        solid_d = installed["JerkgramGlassSolid"][1]
        reveal_d = installed["JerkgramGlassReveal"][1]
        require(bool(solid_d), "Solid Plane d is empty")
        require(reveal_d.startswith(solid_d), "Reveal outer path is not byte-identical to Solid outer path")
        require(len(reveal_d) > len(solid_d), "Reveal contains no negative-space subpath")
        require(installed["JerkgramGlassReveal"][2] == "evenodd", "Reveal must use evenodd negative-space")

        for icon_id in COMPOSER_IDS:
            source = installed[icon_id][0]
            target = IOS / f"{icon_id}.icon"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)

        previews = prev_out / "JerkgramGlassUIPreviews"
        reveal_preview = previews / "JerkgramGlassRevealPreview.png"
        solid_preview = previews / "JerkgramGlassSolidPreview.png"
        require(sha256(reveal_preview) == EXPECTED_REVEAL_PREVIEW, "Reveal UI preview hash mismatch")
        require(sha256(solid_preview) == EXPECTED_SOLID_PREVIEW, "Solid UI preview hash mismatch")
        require(png_size(reveal_preview) == (1024, 1024), "Reveal UI preview size mismatch")
        require(png_size(solid_preview) == (1024, 1024), "Solid UI preview size mismatch")

        if PREVIEW_DIR.exists():
            shutil.rmtree(PREVIEW_DIR)
        PREVIEW_DIR.mkdir(parents=True)
        shutil.copy2(reveal_preview, PREVIEW_DIR / reveal_preview.name)
        shutil.copy2(solid_preview, PREVIEW_DIR / solid_preview.name)

    print("[Build111] canonical Composer assets + UI-only previews installed")


def materialize_steel_reveal_legacy_alticon():
    template = IOS / "BlueIcon.alticon"
    master = LEGACY_ICON_ROOT / "JerkGramSteelReveal.png"
    target = IOS / "JerkGramSteelReveal.alticon"
    require(template.is_dir(), "BlueIcon.alticon template missing")
    require(master.is_file(), "Steel Reveal legacy master missing")
    require(sha256(master) == EXPECTED_STEEL_MASTER, "Steel Reveal legacy master hash mismatch")
    require(png_size(master) == (1254, 1254), "Steel Reveal legacy master size mismatch")
    template_pngs = sorted(template.glob("*.png"))
    require(template_pngs, "BlueIcon.alticon has no PNGs")
    sips = Path("/usr/bin/sips")
    require(sips.is_file(), "/usr/bin/sips missing")

    dimensions = {p.name: png_size(p) for p in template_pngs}
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(template, target)
    for p in target.glob("*.png"):
        p.unlink()

    names = []
    for src in template_pngs:
        if src.name.startswith("BlueIcon"):
            suffix = src.name[len("BlueIcon"):]
        elif src.name.startswith("Blue"):
            suffix = src.name[len("Blue"):]
        else:
            raise RuntimeError(f"[Build111] unsupported BlueIcon template PNG: {src.name}")
        output = target / ("JerkGramSteelReveal" + suffix)
        width, height = dimensions[src.name]
        subprocess.run(
            [str(sips), "-z", str(height), str(width), str(master), "--out", str(output)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        require(png_size(output) == (width, height), f"Steel Reveal alticon size mismatch: {output}")
        names.append(output.name)

    require(len(names) == len(set(names)), "duplicate Steel Reveal alticon resource names")
    print("[Build111] Steel Reveal restored as legacy alternate")


def patch_build():
    text = read(BUILD)

    # Restore all eight old JerkGram PNG alternates, but never put Glass Composer icons here.
    start = text.find("alternate_icon_folders = [")
    end = text.find("\n]", start)
    require(start >= 0 and end >= 0, "alternate_icon_folders block missing")
    block = text[start:end]
    require("JerkgramGlassReveal" not in block and "JerkgramGlassSolid" not in block, "Glass icon leaked into legacy alternate list")
    missing = [name for name in LEGACY_JG_IDS if f'"{name}"' not in block]
    if missing:
        line_end = text.find("\n", start)
        addition = "".join(f'    "{name}",\n' for name in missing)
        text = text[:line_end + 1] + addition + text[line_end + 1:]

    # Build108/110 made Steel Reveal the only Composer primary. Build111 returns the official
    # Telegram.icon primary and adds exactly two additional Composer variants.
    composer_pattern = re.compile(r'composer_icon_folders\s*=\s*\[[^\]]*\]', re.S)
    m = composer_pattern.search(text)
    require(m is not None, "composer_icon_folders missing")
    composer = '''composer_icon_folders = [
    "Telegram",
    "JerkgramGlassReveal",
    "JerkgramGlassSolid",
]'''
    text = text[:m.start()] + composer + text[m.end():]

    preview_group = '''filegroup(
    name = "JerkgramGlassUIPreviews",
    srcs = glob([
        "Telegram-iOS/JerkgramGlassUIPreviews/*.png",
    ]),
)

'''
    if 'name = "JerkgramGlassUIPreviews"' not in text:
        anchor = 'filegroup(\n    name = "LaunchScreen",'
        pos = text.find(anchor)
        require(pos >= 0, "LaunchScreen filegroup anchor missing")
        text = text[:pos] + preview_group + text[pos:]

    app_icons_line = '    app_icons = [ ":{}_icon".format(name) for name in composer_icon_folders ],\n'
    require(app_icons_line in text, "ios_application app_icons line missing")
    if '    primary_app_icon = "Telegram",\n' not in text:
        text = text.replace(
            app_icons_line,
            app_icons_line + '    primary_app_icon = "Telegram",\n',
            1,
        )

    resource_anchor = '    resources = [\n        ":LaunchScreen",\n'
    require(resource_anchor in text, "ios_application resources anchor missing")
    if '        ":JerkgramGlassUIPreviews",\n' not in text:
        text = text.replace(
            resource_anchor,
            '    resources = [\n        ":LaunchScreen",\n        ":JerkgramGlassUIPreviews",\n',
            1,
        )

    write(BUILD, text)

    if OLD_STEEL_COMPOSER.exists():
        shutil.rmtree(OLD_STEEL_COMPOSER)

    print("[Build111] BUILD -> Telegram primary + 2 Composer alternates + 8 legacy JerkGram alternates")


def patch_app_delegate():
    text = read(APP_DELEGATE)

    text = text.replace(
        'PresentationAppIcon(name: "JerkGramSteelReveal", imageName: "JerkGramSteelReveal", isDefault: true)',
        'PresentationAppIcon(name: "JerkGramSteelReveal", imageName: "JerkGramSteelReveal")',
        1,
    )

    blue_variants = [
        'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon"),',
        'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: buildConfig.isAppStoreBuild),',
    ]
    if 'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: true),' not in text:
        replaced = False
        for old in blue_variants:
            if old in text:
                text = text.replace(old, 'PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: true),', 1)
                replaced = True
                break
        require(replaced, "BlueIcon default row missing")

    marker = "// MARK: Jerkgram v1.1Z BUILD111_GLASS_COMPOSER_ICONS1"
    if marker not in text:
        anchor = 'PresentationAppIcon(name: "JerkGramOliveSolid", imageName: "JerkGramOliveSolid"),'
        pos = text.find(anchor)
        require(pos >= 0, "JerkGramOliveSolid AppDelegate anchor missing")
        line_end = text.find("\n", pos)
        indent = re.match(r"\s*", text[text.rfind("\n", 0, pos) + 1:pos]).group(0)
        addition = (
            "\n" + indent + marker + "\n"
            + indent + 'PresentationAppIcon(name: "JerkgramGlassReveal", imageName: "JerkgramGlassRevealPreview"),\n'
            + indent + 'PresentationAppIcon(name: "JerkgramGlassSolid", imageName: "JerkgramGlassSolidPreview"),'
        )
        text = text[:line_end] + addition + text[line_end:]

    write(APP_DELEGATE, text)
    print("[Build111] runtime icon list -> 8 legacy + 2 Composer Glass; Telegram primary maps to nil")


def find_case_branch(region, case_name):
    lines = region.splitlines(keepends=True)
    pattern = re.compile(r'^(?P<i>\s*)case (?:let )?\.' + re.escape(case_name) + r'\b')
    for index, line in enumerate(lines):
        m = pattern.match(line)
        if not m:
            continue
        indent = m.group("i")
        end = index + 1
        next_pattern = re.compile(r'^' + re.escape(indent) + r'case (?:let )?\.')
        while end < len(lines) and not next_pattern.match(lines[end]):
            end += 1
        prefix = "".join(lines[:index])
        branch = "".join(lines[index:end])
        suffix = "".join(lines[end:])
        return prefix, branch, suffix
    raise RuntimeError(f"[Build111] case branch not found: {case_name}")


def clone_case_in_region(text, region_start, region_end, source_name, target_name):
    region = text[region_start:region_end]
    if f".{target_name}" in region:
        return text
    prefix, branch, suffix = find_case_branch(region, source_name)
    clone = branch.replace(f".{source_name}", f".{target_name}")
    region = prefix + clone + branch + suffix
    return text[:region_start] + region + text[region_end:]


def patch_theme_settings():
    text = read(THEME_SETTINGS)

    # Remove Build110's content-dependent 9100/9101 stable-id workaround first.
    stable110 = re.compile(
        r'\s*// MARK: JerkGram v1\.1Y BUILD110_ICON_STABLE_IDS1\n'
        r'\s*case let \.iconHeader\(_, text\):\n'
        r'\s*return text == "JERKGRAM APP ICON" \? 9100 : 12\n'
        r'\s*case let \.iconItem\(_, _, icons, _, _\):\n'
        r'\s*return icons\.first\?\.name\.hasPrefix\("JerkGram"\) == true \? 9101 : 13\n'
    )
    text, count = stable110.subn(
        '\n        case .iconHeader:\n            return 12\n        case .iconItem:\n            return 13\n',
        text,
        count=1,
    )
    require(count == 1 or "BUILD111_SAFE_ICON_ENTRIES1" in text, "Build110 stable-id block missing")

    if "BUILD111_SAFE_ICON_ENTRIES1" not in text:
        definition_anchor = '    case iconHeader(PresentationTheme, String)\n    case iconItem(PresentationTheme, PresentationStrings, [PresentationAppIcon], Bool, String?)\n'
        require(definition_anchor in text, "ThemeSettings icon enum definitions missing")
        definitions = (
            '    // MARK: Jerkgram v1.1Z BUILD111_SAFE_ICON_ENTRIES1\n'
            '    case jerkgramIconHeader(PresentationTheme, String)\n'
            '    case jerkgramIconItem(PresentationTheme, PresentationStrings, [PresentationAppIcon], Bool, String?)\n'
            + definition_anchor
        )
        text = text.replace(definition_anchor, definitions, 1)

        section_old = '            case .iconHeader, .iconItem:\n                return ThemeSettingsControllerSection.icon.rawValue\n'
        section_new = '            case .jerkgramIconHeader, .jerkgramIconItem, .iconHeader, .iconItem:\n                return ThemeSettingsControllerSection.icon.rawValue\n'
        require(section_old in text, "ThemeSettings icon section branch missing")
        text = text.replace(section_old, section_new, 1)

        stable_old = '''        case .iconHeader:
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
        require(stable_old in text, "ThemeSettings stock stable-id tail missing")
        text = text.replace(stable_old, stable_new, 1)

        eq_start = text.find("    static func ==")
        item_start = text.find("    func item(", eq_start)
        require(eq_start >= 0 and item_start > eq_start, "ThemeSettings equality/item regions missing")
        text = clone_case_in_region(text, eq_start, item_start, "iconHeader", "jerkgramIconHeader")
        item_start = text.find("    func item(", eq_start)
        text = clone_case_in_region(text, eq_start, item_start, "iconItem", "jerkgramIconItem")

        item_start = text.find("    func item(", eq_start)
        entries_start = text.find("private func themeSettingsControllerEntries", item_start)
        require(entries_start > item_start, "ThemeSettings entries function anchor missing")
        text = clone_case_in_region(text, item_start, entries_start, "iconHeader", "jerkgramIconHeader")
        entries_start = text.find("private func themeSettingsControllerEntries", item_start)
        text = clone_case_in_region(text, item_start, entries_start, "iconItem", "jerkgramIconItem")

    text = text.replace(
        'currentAppIconName.set(currentAppIcon?.name ?? "JerkGramSteelReveal")',
        'currentAppIconName.set(currentAppIcon?.name ?? "Blue")',
        1,
    )

    old_sections = '''    // MARK: JerkGram v1.1Y BUILD110_ICON_SECTIONS1
    let jerkGramAppIcons = availableAppIcons.filter {
        $0.name.hasPrefix("JerkGram")
    }
    let telegramAppIcons = availableAppIcons.filter {
        !$0.name.hasPrefix("JerkGram")
    }

    if !jerkGramAppIcons.isEmpty {
        entries.append(.iconHeader(
            presentationData.theme,
            "JERKGRAM APP ICON"
        ))
        entries.append(.iconItem(
            presentationData.theme,
            presentationData.strings,
            jerkGramAppIcons,
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
    new_sections = '''    // MARK: Jerkgram v1.1Z BUILD111_ICON_SECTIONS1
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
    if "BUILD111_ICON_SECTIONS1" not in text:
        require(old_sections in text, "Build110 icon sections block missing")
        text = text.replace(old_sections, new_sections, 1)

    write(THEME_SETTINGS, text)
    print("[Build111] Appearance picker uses dedicated stable entries; Build110 9100/9101 hack removed")


def patch_icon_labels():
    text = read(THEME_ICON_ITEM)
    marker = "// MARK: Jerkgram v1.1Z BUILD111_GLASS_LABELS1"
    if marker not in text:
        anchor = '        case "JerkGramSteelReveal":\n'
        pos = text.find(anchor)
        require(pos >= 0, "Build110 JerkGram icon label switch missing")
        addition = (
            '        ' + marker + '\n'
            '        case "JerkgramGlassReveal":\n'
            '            name = "Glass Reveal"\n'
            '        case "JerkgramGlassSolid":\n'
            '            name = "Glass Solid"\n'
        )
        text = text[:pos] + addition + text[pos:]
    write(THEME_ICON_ITEM, text)
    print("[Build111] Glass picker labels installed")


def patch_portable_reply_title():
    text = read(JG_SETTINGS)
    old = '"Переносимый ответ на удалённое"'
    new = '"Переносимый ответ"'
    require(old in text or new in text, "portable deleted reply title missing")
    text = text.replace(old, new)
    marker = "// MARK: Jerkgram v1.1Z BUILD111_PORTABLE_REPLY_TITLE1"
    if marker not in text:
        pos = text.find(new)
        line_start = text.rfind("\n", 0, pos) + 1
        text = text[:line_start] + "            " + marker + "\n" + text[line_start:]
    write(JG_SETTINGS, text)
    print("[Build111] portable deleted reply title shortened")


def patch_profile_list_readability():
    text = read(PEER_LIST)
    marker = "// MARK: Jerkgram v1.1Z BUILD111_LIST_PANE_READABILITY1"
    if marker in text:
        return

    class_tokens = ["final class PeerInfoListPaneNode", "class PeerInfoListPaneNode"]
    start = -1
    for token in class_tokens:
        start = text.find(token)
        if start >= 0:
            break
    require(start >= 0, "PeerInfoListPaneNode class missing")
    tail = text[start:]
    brace = tail.find("{")
    require(brace >= 0, "PeerInfoListPaneNode class brace missing")
    next_class = re.search(
        r"\n(?:private\s+|public\s+|internal\s+)?(?:final\s+)?class\s+[A-Za-z_]",
        tail[brace + 1:],
    )
    if next_class is not None:
        end = brace + 1 + next_class.start()
        region = tail[:end]
        suffix = tail[end:]
    else:
        region = tail
        suffix = ""
    require("self.presentationData" in region, "PeerInfoListPaneNode presentationData owner missing")
    count = region.count("self.backgroundColor = .clear")
    require(count > 0, "PeerInfoListPaneNode clear background anchor missing")

    helper = '''{
    // MARK: Jerkgram v1.1Z BUILD111_LIST_PANE_READABILITY1
    // Shared owner for Files / Links / Voice / Music profile list panes.
    // One pane-wide translucent surface, never per-cell blur.
    private func jerkgramUpdateListPaneReadabilityBackground() {
        let isDark = self.presentationData.theme.overallDarkAppearance
        self.backgroundColor = UIColor(
            white: isDark ? 0.0 : 1.0,
            alpha: isDark ? 0.26 : 0.18
        )
    }
'''
    region = region[:brace] + helper + region[brace + 1:]
    region = region.replace("self.backgroundColor = .clear", "self.jerkgramUpdateListPaneReadabilityBackground()")
    text = text[:start] + region + suffix
    write(PEER_LIST, text)
    print(f"[Build111] profile list pane readability surface installed at {count} clear-background owner(s)")


def main():
    for owner in (BUILD, APP_DELEGATE, THEME_SETTINGS, THEME_ICON_ITEM, JG_SETTINGS, PEER_LIST):
        require(owner.is_file(), f"source owner missing: {owner}")
    validate_and_install_composer_assets()
    materialize_steel_reveal_legacy_alticon()
    patch_build()
    patch_app_delegate()
    patch_theme_settings()
    patch_icon_labels()
    patch_portable_reply_title()
    patch_profile_list_readability()
    print("[Build111] GREEN: Composer Glass + Appearance crash hardening + settings/profile polish applied")


if __name__ == "__main__":
    main()
