#!/usr/bin/env python3

import os
import plistlib
import re
import sys
import tempfile
import zipfile
from pathlib import Path


GLASS = (
    "JerkgramGlassReveal",
    "JerkgramGlassSolid",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Build112 finalizer] " + message)


def main() -> None:
    require(len(sys.argv) == 2, "usage: finalizer <ipa>")

    ipa = Path(sys.argv[1]).resolve()
    require(ipa.is_file(), f"IPA missing: {ipa}")

    with zipfile.ZipFile(ipa, "r") as zin:
        infos = zin.infolist()

        main_plists = [
            item
            for item in infos
            if re.fullmatch(
                r"Payload/[^/]+\.app/Info\.plist",
                item.filename,
            )
        ]

        require(
            len(main_plists) == 1,
            "expected exactly one Payload/*.app/Info.plist, found "
            + repr([x.filename for x in main_plists]),
        )

        plist_info = main_plists[0]
        raw = zin.read(plist_info)

        fmt = (
            plistlib.FMT_BINARY
            if raw.startswith(b"bplist")
            else plistlib.FMT_XML
        )
        plist = plistlib.loads(raw)

        require(
            plist.get("CFBundleIdentifier") == "ph.telegra.Telegraph",
            "refusing to patch unexpected main Bundle ID: "
            + repr(plist.get("CFBundleIdentifier")),
        )

        for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
            icons = plist.get(key)
            require(
                isinstance(icons, dict),
                f"{key} missing/not dictionary",
            )

            primary = icons.get("CFBundlePrimaryIcon")
            require(
                isinstance(primary, dict)
                and primary.get("CFBundleIconName") == "Telegram",
                f"{key} primary icon is not Telegram: {primary!r}",
            )

            alternates = icons.get("CFBundleAlternateIcons")
            require(
                isinstance(alternates, dict),
                f"{key}.CFBundleAlternateIcons missing/not dictionary",
            )

            for name in GLASS:
                existing = alternates.get(name)

                if existing is None:
                    alternates[name] = {
                        "CFBundleIconName": name,
                    }
                else:
                    require(
                        isinstance(existing, dict),
                        f"{key}.{name} malformed: {existing!r}",
                    )
                    existing["CFBundleIconName"] = name

        patched = plistlib.dumps(
            plist,
            fmt=fmt,
            sort_keys=False,
        )

        fd, tmp_name = tempfile.mkstemp(
            prefix=ipa.name + ".build112.",
            suffix=".tmp",
            dir=str(ipa.parent),
        )
        os.close(fd)
        tmp = Path(tmp_name)

        try:
            with zipfile.ZipFile(tmp, "w") as zout:
                for item in infos:
                    data = (
                        patched
                        if item.filename == plist_info.filename
                        else zin.read(item)
                    )
                    zout.writestr(item, data)

            os.replace(tmp, ipa)

        finally:
            if tmp.exists():
                tmp.unlink()

    print(
        "[Build112 finalizer] registered native Composer alternates: "
        + ", ".join(GLASS)
    )
    print(
        "[Build112 finalizer] Assets.car and all other IPA entries "
        "preserved byte-for-byte"
    )


if __name__ == "__main__":
    main()
