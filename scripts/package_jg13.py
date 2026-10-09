#!/usr/bin/env python3
"""Package the compiled source app using the two audited Stable sideload assets."""
from pathlib import Path
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
import jerkgram_finalize_build126_keychain_package1 as keychain
import jerkgram_finalize_build128_file_picker_package1 as picker

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {
    "BroadcastUploadExtension.appex": "BroadcastUpload",
    "IntentsExtension.appex": "SiriIntents",
    "NotificationContentExtension.appex": "NotificationContent",
    "NotificationServiceExtensionv1.appex": "NotificationService",
    "ShareExtension.appex": "Share",
    "WidgetExtension.appex": "Widget",
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def verify(ipa, config):
    with zipfile.ZipFile(ipa) as z:
        mains = [n for n in z.namelist() if n.startswith("Payload/") and n.endswith(".app/Info.plist") and n.count("/") == 2]
        require(len(mains) == 1, "Expected one main app")
        app = mains[0].removesuffix("Info.plist")
        main = plistlib.loads(z.read(mains[0]))
        require(main["CFBundleIdentifier"] == config["bundle_id"], "Wrong main Bundle ID")
        require(main["CFBundleDisplayName"] == "Jerkgram", "Wrong branding")
        infos = {n.split("/")[-2]: n for n in z.namelist() if n.startswith(app + "PlugIns/") and n.endswith(".appex/Info.plist") and n.count("/") == 4}
        require(set(infos) == set(EXTENSIONS), "Stable extension topology lost")
        for name, suffix in EXTENSIONS.items():
            require(plistlib.loads(z.read(infos[name]))["CFBundleIdentifier"] == config["bundle_id"] + "." + suffix, "Wrong extension identity: " + name)
        for name in mains + list(infos.values()):
            p = plistlib.loads(z.read(name))
            require(p["CFBundleVersion"] == str(config["build_number"]), "Wrong build: " + name)
            require(p["CFBundleShortVersionString"] == config["bundle_short_version"], "Wrong version: " + name)
        for name, expected in [("sideloadKeychainFix.dylib", keychain.EXPECTED_SHA256), ("FilePickerFix.dylib", picker.FILE_PICKER_SHA256)]:
            require(hashlib.sha256(z.read(app + "Frameworks/" + name)).hexdigest() == expected, "Stable asset hash mismatch: " + name)
        require(main.get("CFBundleIcons", {}).get("CFBundlePrimaryIcon", {}).get("CFBundleIconName") == "JerkgramGlassReveal", "Primary Jerkgram icon lost")


def main():
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    artifact_name = f'Jerkgram-1.1.0-Beta-1-Build{config["build_number"]}'
    ipa = out / (artifact_name + ".ipa")
    shutil.copy2(Path(sys.argv[1]), ipa)
    # Same asset hashes and main-app-only packaging as the proven Build138.
    keychain.package_ipa(ipa)
    picker.package_file_picker(ipa)
    with tempfile.TemporaryDirectory(prefix="jg13-package-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(ipa) as z:
            infos = z.infolist()
            z.extractall(root)
        app = next((root / "Payload").glob("*.app"))
        bundles = [app] + list((app / "PlugIns").glob("*.appex"))
        require(len(bundles) == 7, "Unexpected main/extension topology")
        for bundle in bundles:
            p = bundle / "Info.plist"
            data = plistlib.loads(p.read_bytes())
            require(data["CFBundleVersion"] == str(config["build_number"]), "Build was not set by source pipeline")
            require(data["CFBundleShortVersionString"] == config["bundle_short_version"], "Bundle version was not set by source pipeline")
            if bundle == app:
                data["CFBundleName"] = data["CFBundleDisplayName"] = "Jerkgram"
            p.write_bytes(plistlib.dumps(data, fmt=plistlib.FMT_BINARY, sort_keys=False))
            (bundle / "embedded.mobileprovision").unlink(missing_ok=True)
            shutil.rmtree(bundle / "_CodeSignature", ignore_errors=True)
            entitlements = {
                "application-identifier": "C67CF9S4VU." + data["CFBundleIdentifier"],
                "com.apple.security.application-groups": ["group." + config["bundle_id"]],
                "get-task-allow": False,
            }
            if bundle == app or bundle.name in {"BroadcastUploadExtension.appex", "IntentsExtension.appex", "WidgetExtension.appex"}:
                entitlements["com.apple.developer.team-identifier"] = "C67CF9S4VU"
                entitlements["keychain-access-groups"] = ["C67CF9S4VU.*", "com.apple.token"]
            if bundle == app:
                entitlements["aps-environment"] = "production"
            ep = root / (bundle.name + ".entitlements.plist")
            ep.write_bytes(plistlib.dumps(entitlements))
            subprocess.run(["codesign", "--force", "--sign", "-", "--timestamp=none", "--generate-entitlement-der", "--entitlements", str(ep), str(bundle / data["CFBundleExecutable"])], check=True)
        replacement = ipa.with_suffix(".tmp")
        with zipfile.ZipFile(replacement, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in (root / "Payload").rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(root).as_posix())
        replacement.replace(ipa)
    verify(ipa, config)
    report = dict(config, ci_run_id=os.environ.get("GITHUB_RUN_ID"), ci_commit=os.environ.get("GITHUB_SHA"), ipa=ipa.name, ipa_sha256=hashlib.sha256(ipa.read_bytes()).hexdigest(), status="COMPILED, NOT RUNTIME TESTED")
    (out / (artifact_name + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    print("IPA metadata VERIFIED; COMPILED, NOT RUNTIME TESTED")


if __name__ == "__main__":
    main()
