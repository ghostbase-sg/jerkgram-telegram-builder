#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
text = (root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift").read_text(encoding="utf-8")
if text.count("Version: v1.1C-stage1") != 2:
    raise SystemExit("V11C VERSION VERIFY FAILED: label count")
if "Base: Official Telegram 12.8" in text or "Base: Official Telegram 12.7" in text:
    raise SystemExit("V11C VERSION VERIFY FAILED: stale base")
if text.count("Base: Official Telegram 12.9.2") < 2:
    raise SystemExit("V11C VERSION VERIFY FAILED: base label")
environment_root = os.environ.get("GHOSTBASE_BUILDER_ROOT")
if environment_root:
    builder_root = Path(environment_root)
else:
    builder_root = Path(__file__).resolve().parents[1]

canonical = (builder_root / "scripts/bazel_build_probe_official.sh").read_text(encoding="utf-8")

expected_gate = 'echo "-- verify Version: v1.1C-stage1 --"\nif ! LC_ALL=C grep -Rao "Version: v1.1C-stage1" "$TMP_GB_CHECK/Payload" >/dev/null 2>&1; then\n  echo "::error::Final IPA does not contain Version: v1.1C-stage1"\n  exit 1\nfi\n'

if canonical.count(expected_gate) != 1:
    raise SystemExit(
        "V11C VERSION VERIFY FAILED: final IPA gate is not v1.1C-stage1"
    )

if 'echo "-- verify Version: v1.1a --"' in canonical:
    raise SystemExit(
        "V11C VERSION VERIFY FAILED: stale v1.1a final IPA gate remains"
    )

print("V11C VERSION VERIFY OK")
