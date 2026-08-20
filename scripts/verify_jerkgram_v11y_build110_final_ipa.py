#!/usr/bin/env python3

from pathlib import Path
import plistlib
import sys
import zipfile


IPA = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
)

EXPECTED_ICONS = {
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(
            "[verify Build110 final] " + message
        )


require(
    IPA.is_file(),
    f"IPA missing: {IPA}",
)


with zipfile.ZipFile(IPA, "r") as z:
    plist_paths = [
        name
        for name in z.namelist()
        if name.startswith("Payload/")
        and name.endswith(".app/Info.plist")
        and name.count("/") == 2
    ]

    require(
        len(plist_paths) == 1,
        f"expected one main Info.plist: {plist_paths}",
    )

    plist = plistlib.loads(
        z.read(plist_paths[0])
    )


require(
    plist.get("CFBundleIdentifier")
    == "ph.telegra.Telegraph",
    (
        "official Bundle ID changed: "
        f"{plist.get('CFBundleIdentifier')!r}"
    ),
)

require(
    plist.get("CFBundleDisplayName")
    == "JerkGram",
    (
        "display name mismatch: "
        f"{plist.get('CFBundleDisplayName')!r}"
    ),
)

require(
    plist.get("CFBundleName")
    == "JerkGram",
    (
        "bundle name mismatch: "
        f"{plist.get('CFBundleName')!r}"
    ),
)


alternate_ids = set()


def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if (
                key == "CFBundleAlternateIcons"
                and isinstance(child, dict)
            ):
                alternate_ids.update(
                    child.keys()
                )

            walk(child)

    elif isinstance(value, list):
        for child in value:
            walk(child)


walk(plist)


missing = (
    EXPECTED_ICONS
    - alternate_ids
)

require(
    not missing,
    (
        "final IPA did not register alternate "
        f"JerkGram icons: {sorted(missing)}"
    ),
)


print(
    "[verify Build110 final] GREEN"
)
print(
    "CFBundleIdentifier:",
    plist.get("CFBundleIdentifier"),
)
print(
    "CFBundleDisplayName:",
    plist.get("CFBundleDisplayName"),
)
print(
    "CFBundleName:",
    plist.get("CFBundleName"),
)
print(
    "JerkGram alternate icons:",
    ", ".join(
        sorted(
            EXPECTED_ICONS
            & alternate_ids
        )
    ),
)
