#!/usr/bin/env python3

from pathlib import Path
import hashlib
import plistlib
import shutil
import tempfile
import zipfile


SOURCE_CANDIDATES = (
    Path("work/swiftgram-src/ghostbase-final/GhostBase.ipa"),
    Path("work/telegram-src/jerkgram-final/Jerkgram.ipa"),
)
OUTPUT_DIR = Path("artifacts")
OUTPUT_IPA = OUTPUT_DIR / "Jerkgram-build117.ipa"
OUTPUT_INFO = OUTPUT_DIR / "Jerkgram-build117-info.txt"


def require(value, message):
    if not value:
        raise RuntimeError("[Build117 artifact] " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    source = next((path for path in SOURCE_CANDIDATES if path.is_file()), None)
    require(source is not None, "final IPA source missing")
    with tempfile.TemporaryDirectory(prefix="jerkgram-build117-artifact-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(source, "r") as archive:
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one .app")
        with (apps[0] / "Info.plist").open("rb") as file:
            info = plistlib.load(file)
        require(info.get("CFBundleDisplayName") == "Jerkgram", "final display name is not Jerkgram")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, OUTPUT_IPA)
    output_hash = sha256(OUTPUT_IPA)
    require(sha256(source) == output_hash, "published IPA is not byte-identical")
    OUTPUT_INFO.write_text(
        "Name=Jerkgram\n"
        "Build=117\n"
        f"Source={source}\n"
        f"SHA256={output_hash}\n",
        encoding="utf-8",
    )
    print("[Build117 artifact] GREEN")
    print("[Build117 artifact] final file:", OUTPUT_IPA)
    print("[Build117 artifact] sha256:", output_hash)


if __name__ == "__main__":
    main()
