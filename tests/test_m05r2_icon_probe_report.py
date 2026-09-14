#!/usr/bin/env python3
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/m05r2-icon-probe")
manifest_path = root / "probe_manifest.json"
assert manifest_path.is_file(), f"missing {manifest_path}"

data = json.loads(manifest_path.read_text())
assert data["source_icon_name"] == "JerkgramGlassReveal"
assert data["source_plane_sha256"] == "9dc83c22a01878aac9f8494c509a7862fdd1679d7e7f7f0026afc367d3a7e304"

plist = data["info_plist"]
assert plist.get("CFBundleIdentifier") == "com.jerkgram.iconprobe"
assert plist.get("CFBundleIcons") or plist.get("CFBundleIconName"), "no primary icon declaration emitted"

files = data["bundle_files"]
assert any(name.endswith(".icon") or ".icon/" in name for name in files), "compiled bundle does not carry Icon Composer source/package"
assert data.get("icon_related_files"), "missing emitted icon file inventory"
assert data.get("xcode_version", "").startswith("Xcode 26"), data.get("xcode_version")

assert (root / "Info.plist.xml").is_file()
assert (root / "bundle-files.txt").is_file()
assert (root / "icon-related-sha256.txt").is_file()

print("M05R2_ICON_PROBE_REPORT_PASS")
