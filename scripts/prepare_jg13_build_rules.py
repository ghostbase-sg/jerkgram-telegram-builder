#!/usr/bin/env python3
"""Port Stable unsigned IPA intent to the pinned current Apple rule owners."""
from pathlib import Path
from types import SimpleNamespace
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src/build-system/bazel-rules/rules_apple"
RELATIVE = "apple/internal/ios_rules.bzl"
COMMIT = "485016eb5b0948cc17307064e7977a6d68e94046"
BLOB = "7d2f703c21b099a9399abb387a234e0cf213c2ee"
OWNERS = ("_ios_application_impl", "_ios_extension_impl")
CONDITION = 'platform_prerequisites.platform.is_device and ("disable_legacy_signing" not in features or provisioning_profile)'


def owner(text, name):
    start = text.index("def " + name + "(ctx):")
    end = text.index("\ndef ", start + 1)
    return start, end, text[start:end]


def transform(text):
    old = "    if platform_prerequisites.platform.is_device:\n        processor_partials.append(\n            partials.provisioning_profile_partial("
    new = "    if " + CONDITION + ":\n        processor_partials.append(\n            partials.provisioning_profile_partial("
    for name in OWNERS:
        start, end, block = owner(text, name)
        assert block.count(old) == 1, "Unexpected provisioning owner: " + name
        assert block.count("profile_artifact = provisioning_profile") == 1
        text = text[:start] + block.replace(old, new, 1) + text[end:]
    return text


def verify(text):
    for name in OWNERS:
        _, _, block = owner(text, name)
        assert block.count("    if " + CONDITION + ":") == 1
        for device, disabled, profile, expected in [
            (True, True, None, False),   # explicitly unsigned device IPA
            (True, False, None, True),  # signed build still reaches stock missing-profile error
            (True, True, "profile", True),
            (True, False, "profile", True),
            (False, True, None, False),
            (False, False, None, False),
        ]:
            actual = eval(CONDITION, {"__builtins__": {}}, {
                "platform_prerequisites": SimpleNamespace(platform=SimpleNamespace(is_device=device)),
                "features": {"disable_legacy_signing"} if disabled else set(),
                "provisioning_profile": profile,
            })
            assert bool(actual) == expected, (name, device, disabled, profile)


def main():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=SOURCE, text=True).strip()
    assert git("rev-parse", "HEAD") == COMMIT, "Apple rules pin changed"
    assert git("rev-parse", "HEAD:" + RELATIVE) == BLOB, "Apple rule owner changed"
    path = SOURCE / RELATIVE
    original = subprocess.check_output(["git", "show", "HEAD:" + RELATIVE], cwd=SOURCE).decode()
    expected = transform(original)
    assert path.read_text() in (original, expected), "Unexpected local Apple rules edits"
    path.write_text(expected)
    assert path.read_text() == expected
    verify(path.read_text())
    print("Current app + extension unsigned provisioning owners VERIFIED; signed-build checks retained")


if __name__ == "__main__":
    main()
