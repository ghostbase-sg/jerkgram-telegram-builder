#!/usr/bin/env python3
import plistlib
import sys
import tempfile
import zipfile
from pathlib import Path

IPA = Path(sys.argv[1] if len(sys.argv) > 1 else "ghostbase-final/GhostBase.ipa").resolve()

REQUIRED_EXTENSIONS = (
    "BroadcastUploadExtension.appex",
    "ShareExtension.appex",
    "WidgetExtension.appex",
)

OPTIONAL_EXTENSIONS = (
    "NotificationContentExtension.appex",
    "NotificationServiceExtension.appex",
    "IntentsExtension.appex",
)

LEGACY_JERKGRAM = {
    "JerkGramSteelReveal",
    "JerkGramSteelSolid",
    "JerkGramRustReveal",
    "JerkGramRustSolid",
    "JerkGramInkReveal",
    "JerkGramInkSolid",
    "JerkGramOliveReveal",
    "JerkGramOliveSolid",
}

STOCK_TELEGRAM = {
    "BlackIcon",
    "BlackClassicIcon",
    "BlackFilledIcon",
    "BlueIcon",
    "BlueClassicIcon",
    "BlueFilledIcon",
    "WhiteFilledIcon",
    "New1",
    "New2",
    "Premium",
    "PremiumBlack",
    "PremiumTurbo",
}

GLASS = {"JerkgramGlassReveal", "JerkgramGlassSolid"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[verify Build112 final] " + message)


def load_plist(path: Path):
    require(path.is_file(), f"Info.plist missing: {path}")
    with path.open("rb") as f:
        return plistlib.load(f)


def main() -> None:
    require(IPA.is_file(), f"IPA missing: {IPA}")

    with tempfile.TemporaryDirectory(prefix="jerkgram-build112-final-") as td:
        root = Path(td)
        with zipfile.ZipFile(IPA, "r") as zf:
            zf.extractall(root)

        apps = [p for p in (root / "Payload").glob("*.app") if p.is_dir()]
        require(len(apps) == 1, f"expected one main app, found {[p.name for p in apps]}")
        app = apps[0]
        info = load_plist(app / "Info.plist")

        require(
            info.get("CFBundleIdentifier") == "ph.telegra.Telegraph",
            f"main Bundle ID changed: {info.get('CFBundleIdentifier')!r}",
        )
        require(
            info.get("CFBundleDisplayName") == "Jerkgram",
            f"CFBundleDisplayName != Jerkgram: {info.get('CFBundleDisplayName')!r}",
        )
        require(
            info.get("CFBundleName") == "Jerkgram",
            f"CFBundleName != Jerkgram: {info.get('CFBundleName')!r}",
        )
        require((app / "Assets.car").is_file(), "Assets.car missing")

        expected_alternates = LEGACY_JERKGRAM | STOCK_TELEGRAM | GLASS
        for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
            icons = info.get(key)
            require(isinstance(icons, dict), f"{key} missing/not a dict")
            primary = icons.get("CFBundlePrimaryIcon")
            require(isinstance(primary, dict), f"{key}.CFBundlePrimaryIcon missing")
            require(
                primary.get("CFBundleIconName") == "Telegram",
                f"{key} primary icon != Telegram: {primary}",
            )
            alternates = icons.get("CFBundleAlternateIcons")
            require(isinstance(alternates, dict), f"{key}.CFBundleAlternateIcons missing")
            missing = expected_alternates - set(alternates.keys())
            require(not missing, f"{key} missing alternates: {sorted(missing)}")
            for name in GLASS:
                entry = alternates.get(name)
                require(isinstance(entry, dict), f"{key}.{name} entry malformed")
                require(
                    entry.get("CFBundleIconName") == name,
                    f"{key}.{name} CFBundleIconName mismatch: {entry}",
                )

        plugins = app / "PlugIns"
        require(plugins.is_dir(), "Payload/*.app/PlugIns/ missing")
        appex = {p.name: p for p in plugins.glob("*.appex") if p.is_dir()}
        missing_ext = [name for name in REQUIRED_EXTENSIONS if name not in appex]
        require(
            not missing_ext,
            f"missing required Official extensions: {missing_ext}",
        )

        present_optional = [
            name for name in OPTIONAL_EXTENSIONS
            if name in appex
        ]
        missing_optional = [
            name for name in OPTIONAL_EXTENSIONS
            if name not in appex
        ]

        seen_bundle_ids = set()
        for name in REQUIRED_EXTENSIONS + tuple(present_optional):
            ext = appex[name]
            ext_info = load_plist(ext / "Info.plist")
            bundle_id = ext_info.get("CFBundleIdentifier")
            require(
                isinstance(bundle_id, str) and bundle_id,
                f"{name} CFBundleIdentifier missing",
            )
            require(bundle_id not in seen_bundle_ids, f"duplicate extension Bundle ID: {bundle_id}")
            seen_bundle_ids.add(bundle_id)

            ns = ext_info.get("NSExtension")
            require(isinstance(ns, dict) and ns, f"{name} NSExtension missing")
            point = ns.get("NSExtensionPointIdentifier")
            require(
                isinstance(point, str) and point,
                f"{name} NSExtensionPointIdentifier missing",
            )

            executable = ext_info.get("CFBundleExecutable")
            if isinstance(executable, str) and executable:
                require((ext / executable).is_file(), f"{name} executable missing: {executable}")

            has_profile = (ext / "embedded.mobileprovision").is_file()
            print(
                f"[verify Build112 final] {name}: "
                f"id={bundle_id} point={point} embedded.mobileprovision={has_profile}"
            )

        broadcast_info = load_plist(appex["BroadcastUploadExtension.appex"] / "Info.plist")
        broadcast_ns = broadcast_info["NSExtension"]
        require(
            broadcast_ns.get("NSExtensionPointIdentifier")
            == "com.apple.broadcast-services-upload",
            "BroadcastUploadExtension is not ReplayKit Broadcast Upload",
        )

        principal = broadcast_ns.get("NSExtensionPrincipalClass")
        if principal is not None:
            require(
                isinstance(principal, str)
                and "BroadcastUploadSampleHandler" in principal,
                "BroadcastUploadExtension principal class is unexpected: "
                + repr(principal),
            )

        print("[verify Build112 final] GREEN: Glass Reveal/Solid registered as native Composer alternates")
        print("[verify Build112 final] GREEN: all eight legacy Jerkgram + stock Telegram icons preserved")
        print("[verify Build112 final] GREEN: required Broadcast/Share/Widget extensions are present")
        if present_optional:
            print(
                "[verify Build112 final] GREEN: optional Official extensions present: "
                + ", ".join(present_optional)
            )
        if missing_optional:
            print(
                "[verify Build112 final] NOTE: optional Official extensions absent: "
                + ", ".join(missing_optional)
            )
        print("[verify Build112 final] GREEN: BroadcastUploadExtension has com.apple.broadcast-services-upload")
        print("[verify Build112 final] NOTE: extension embedded.mobileprovision presence is informational only")


if __name__ == "__main__":
    main()
