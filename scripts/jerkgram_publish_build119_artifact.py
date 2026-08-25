#!/usr/bin/env python3

from pathlib import Path
import hashlib
import plistlib
import shutil
import tempfile
import zipfile


EXPECTED_BUILD = "119"
EXPECTED_DISPLAY = "Jerkgram"
SOURCE_CANDIDATES = (
    Path("work/swiftgram-src/ghostbase-final/GhostBase.ipa"),
    Path("work/telegram-src/jerkgram-final/Jerkgram.ipa"),
)
OUTPUT_DIR = Path("artifacts")
OUTPUT_IPA = OUTPUT_DIR / "Jerkgram-build119.ipa"
OUTPUT_INFO = OUTPUT_DIR / "Jerkgram-build119-info.txt"


def require(value, message):
    if not value:
        raise RuntimeError("[Build119 artifact] " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_embedded_identity(source):
    with tempfile.TemporaryDirectory(prefix="jerkgram-build119-artifact-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(source, "r") as archive:
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one .app")
        app = apps[0]
        with (app / "Info.plist").open("rb") as file:
            info = plistlib.load(file)
        require(info.get("CFBundleDisplayName") == EXPECTED_DISPLAY, "CFBundleDisplayName is not Jerkgram")
        require(str(info.get("CFBundleVersion")) == EXPECTED_BUILD, "embedded main CFBundleVersion is not 119")
        extensions = list((app / "PlugIns").glob("*.appex"))
        require(len(extensions) == 6, "expected 6 extensions")
        for extension in extensions:
            with (extension / "Info.plist").open("rb") as file:
                extension_info = plistlib.load(file)
            require(
                str(extension_info.get("CFBundleVersion")) == EXPECTED_BUILD,
                extension.name + " embedded CFBundleVersion is not 119",
            )


def main():
    source = next((path for path in SOURCE_CANDIDATES if path.is_file()), None)
    require(source is not None, "final IPA source missing")
    verify_embedded_identity(source)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUTPUT_DIR.glob("Jerkgram-build11[0-8]*"):
        if stale.is_file():
            stale.unlink()

    shutil.copy2(source, OUTPUT_IPA)
    output_hash = sha256(OUTPUT_IPA)
    require(sha256(source) == output_hash, "published IPA is not byte-identical")
    verify_embedded_identity(OUTPUT_IPA)

    OUTPUT_INFO.write_text(
        "Name=Jerkgram\n"
        "Build=119\n"
        f"Source={source}\n"
        f"SHA256={output_hash}\n",
        encoding="utf-8",
    )
    require("Build=119" in OUTPUT_INFO.read_text(encoding="utf-8"), "metadata build mismatch")

    print("[Build119 artifact] GREEN")
    print("[Build119 artifact] final file:", OUTPUT_IPA)
    print("[Build119 artifact] sha256:", output_hash)


if __name__ == "__main__":
    main()
