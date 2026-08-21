#!/usr/bin/env python3
import os
import re
from pathlib import Path

ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

BUILD = ROOT / "Telegram/BUILD"
POST = ROOT / "Telegram/Telegram-iOS/JerkgramIconComposerPostProcessor.sh"

MARKER = "# MARK: Jerkgram v1.2A BUILD112_COMPOSER_ALTERNATES1"
POST_MARKER = "Jerkgram Build112 Icon Composer alternate registration bridge"
POST_LABEL = ":JerkgramIconComposerPostProcessor"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Build112] " + message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


POSTPROCESSOR = r'''#!/bin/bash
# Jerkgram Build112 Icon Composer alternate registration bridge
# rules_apple already compiled the canonical Xcode 26 .icon bundles through
# app_icons. Build111 proved they were not registered in CFBundleAlternateIcons.
# Merge only the missing registration metadata; do not replace Assets.car,
# do not rasterize the Composer packages, and do not touch legacy .alticon data.

archive_root="$1"

exec /usr/bin/python3 - "$archive_root" <<'PYPOST'
import plistlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
apps = [p for p in root.iterdir() if p.is_dir() and p.suffix == ".app"]
if len(apps) != 1:
    raise SystemExit(
        "[Build112 post] expected exactly one top-level .app, found "
        + str([p.name for p in apps])
    )

app = apps[0]
plist_path = app / "Info.plist"
assets = app / "Assets.car"
if not plist_path.is_file():
    raise SystemExit("[Build112 post] main Info.plist missing")
if not assets.is_file():
    raise SystemExit("[Build112 post] Assets.car missing")

raw = plist_path.read_bytes()
fmt = plistlib.FMT_BINARY if raw.startswith(b"bplist") else plistlib.FMT_XML
info = plistlib.loads(raw)

primary = info.get("CFBundleIcons", {}).get("CFBundlePrimaryIcon", {})
primary_name = primary.get("CFBundleIconName")
if primary_name != "Telegram":
    raise SystemExit(
        "[Build112 post] unexpected primary app icon: " + repr(primary_name)
    )

composer_names = ("JerkgramGlassReveal", "JerkgramGlassSolid")
for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
    icons = info.get(key)
    if icons is None:
        icons = {}
        info[key] = icons
    if not isinstance(icons, dict):
        raise SystemExit(f"[Build112 post] {key} is not a dictionary")

    alternates = icons.get("CFBundleAlternateIcons")
    if alternates is None:
        alternates = {}
        icons["CFBundleAlternateIcons"] = alternates
    if not isinstance(alternates, dict):
        raise SystemExit(
            f"[Build112 post] {key}.CFBundleAlternateIcons is not a dictionary"
        )

    # Xcode 26's generated registration for Icon Composer alternates is a
    # CFBundleIconName reference. Preserve every stock / legacy alternate.
    for name in composer_names:
        current = alternates.get(name)
        if current is None:
            alternates[name] = {"CFBundleIconName": name}
        elif not isinstance(current, dict):
            raise SystemExit(
                f"[Build112 post] malformed existing alternate {name}: {current!r}"
            )
        else:
            current["CFBundleIconName"] = name

with plist_path.open("wb") as f:
    plistlib.dump(info, f, fmt=fmt, sort_keys=False)

print(
    "[Build112 post] registered native Composer alternates: "
    + ", ".join(composer_names)
)
PYPOST
'''


def main() -> None:
    build = read(BUILD)

    # Build111 preconditions: canonical Composer packages are already compiled
    # as app icons, Telegram is the explicit primary, Glass never went through
    # the legacy PNG .alticon registration path.
    for name in ("JerkgramGlassReveal", "JerkgramGlassSolid"):
        require(
            f'"{name}"' in build,
            f"Build111 Composer owner missing for {name}",
        )
    require(
        'primary_app_icon = "Telegram"' in build,
        "Build111 primary_app_icon = Telegram missing",
    )
    require(
        "Telegram-iOS/JerkgramGlassReveal.alticon" not in build
        and "Telegram-iOS/JerkgramGlassSolid.alticon" not in build,
        "Glass must not be routed through legacy .alticon",
    )

    POST.parent.mkdir(parents=True, exist_ok=True)
    write(POST, POSTPROCESSOR)
    POST.chmod(0o755)

    if MARKER not in build:
        require(
            re.search(r'(?m)^\s*ipa_post_processor\s*=', build) is None,
            "pre-existing ipa_post_processor found; refusing to overwrite its owner",
        )

        primary_matches = list(re.finditer(
            r'(?m)^(?P<indent>[ \t]*)primary_app_icon = "Telegram",[ \t]*$',
            build,
        ))
        require(
            len(primary_matches) == 1,
            "expected exactly one Telegram primary_app_icon anchor",
        )
        match = primary_matches[0]
        indent = match.group("indent")
        replacement = (
            match.group(0)
            + "\n"
            + indent + MARKER
            + "\n"
            + indent + 'ipa_post_processor = ":JerkgramIconComposerPostProcessor",'
        )
        build = build[:match.start()] + replacement + build[match.end():]

        target = r'''

# MARK: Jerkgram v1.2A BUILD112_COMPOSER_ALTERNATES1
sh_binary(
    name = "JerkgramIconComposerPostProcessor",
    srcs = ["Telegram-iOS/JerkgramIconComposerPostProcessor.sh"],
    visibility = ["//visibility:private"],
)
'''
        build = build.rstrip() + target + "\n"
        write(BUILD, build)
    else:
        require(
            'ipa_post_processor = ":JerkgramIconComposerPostProcessor"' in build,
            "Build112 marker present but ipa_post_processor missing",
        )
        require(
            'name = "JerkgramIconComposerPostProcessor"' in build,
            "Build112 marker present but sh_binary missing",
        )

    print("[Build112] native Composer alternate registration bridge installed")
    print("[Build112] legacy alternate icons untouched")
    print("[Build112] no Glass PNG/.alticon fallback introduced")


if __name__ == "__main__":
    main()
