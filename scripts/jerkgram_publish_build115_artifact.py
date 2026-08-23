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
OUTPUT_IPA = OUTPUT_DIR / "Jerkgram-build115.ipa"
OUTPUT_INFO = OUTPUT_DIR / "Jerkgram-build115-info.txt"


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 artifact] "
            + message
        )


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main():
    source = next(
        (
            path
            for path in SOURCE_CANDIDATES
            if path.is_file()
        ),
        None
    )

    require(source is not None, "final IPA source missing")

    with tempfile.TemporaryDirectory(
        prefix="jerkgram-build115-artifact-"
    ) as td:
        root = Path(td)

        with zipfile.ZipFile(source, "r") as archive:
            archive.extractall(root)

        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one .app")

        with (apps[0] / "Info.plist").open("rb") as f:
            info = plistlib.load(f)

        require(
            info.get("CFBundleDisplayName") == "Jerkgram",
            "final display name is not Jerkgram"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, OUTPUT_IPA)

    source_hash = sha256(source)
    output_hash = sha256(OUTPUT_IPA)

    require(
        source_hash == output_hash,
        "published IPA is not byte-identical"
    )

    OUTPUT_INFO.write_text(
        "Name=Jerkgram\n"
        "Build=115\n"
        f"Source={source}\n"
        f"SHA256={output_hash}\n",
        encoding="utf-8"
    )

    print("[Build115 artifact] GREEN")
    print("[Build115 artifact] final file:", OUTPUT_IPA)
    print("[Build115 artifact] sha256:", output_hash)


if __name__ == "__main__":
    main()
