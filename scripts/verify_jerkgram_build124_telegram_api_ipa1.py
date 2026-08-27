#!/usr/bin/env python3

from dataclasses import dataclass
import os
from pathlib import Path
import plistlib
import re
import sys
import tempfile
import zipfile


EXPECTED_API_ID = "22732185"
OFFICIAL_API_HASH = b"7245de8e747a0d6fbe11f7cc14fcc0bb"
API_HASH_FORMAT_RE = re.compile(r"^[0-9a-fA-F]{32}$")
API_ID_OWNER_RE = re.compile(rb"JERKGRAM_BUILD124_API_ID=([0-9]+)")


@dataclass(frozen=True)
class CredentialVerificationResult:
    api_id: str
    hash_owner: str


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build124 API IPA verify] " + message)


def load_plist(path: Path) -> dict:
    with path.open("rb") as file:
        return plistlib.load(file)


def normalized_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def verify_ipa_credentials(ipa: Path, expected_hash: str) -> CredentialVerificationResult:
    ipa = Path(ipa).resolve()
    expected_hash = (expected_hash or "").strip().lower()
    require(ipa.is_file(), "IPA is missing")
    require(API_HASH_FORMAT_RE.fullmatch(expected_hash) is not None, "configured API hash has an invalid shape")
    require(expected_hash.encode("ascii") != OFFICIAL_API_HASH, "configured API hash is the Official Telegram sample")

    with tempfile.TemporaryDirectory(prefix="jerkgram-build124-api-ipa-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            archive.extractall(root)

        payload = root / "Payload"
        apps = [path for path in payload.glob("*.app") if path.is_dir()]
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        main_info = load_plist(app / "Info.plist")
        executable_name = main_info.get("CFBundleExecutable")
        require(isinstance(executable_name, str) and executable_name, "main CFBundleExecutable is missing")
        main_executable = app / executable_name
        require(main_executable.is_file(), "main executable is missing")

        expected_hash_bytes = expected_hash.encode("ascii")
        main_relative = normalized_relative(main_executable, root)
        private_hash_owners: list[str] = []
        api_id_owners: list[tuple[str, str]] = []

        for path in sorted(app.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            relative = normalized_relative(path, root)
            lowered = data.lower()

            require(OFFICIAL_API_HASH not in lowered, f"Official Telegram sample API hash remains in {relative}")

            if expected_hash_bytes in lowered:
                private_hash_owners.append(relative)

            for match in API_ID_OWNER_RE.finditer(data):
                api_id_owners.append((relative, match.group(1).decode("ascii")))

        require(len(api_id_owners) == 1, "compiled API ID owner marker is missing or duplicated")
        marker_owner, api_id = api_id_owners[0]
        require(marker_owner == main_relative, f"compiled API ID owner marker is outside the main executable: {marker_owner}")
        require(api_id == EXPECTED_API_ID, f"compiled API ID owner has the wrong Build124 canary identity in {marker_owner}")

        require(main_relative in private_hash_owners, "configured API hash is missing from the main compiled credential owner")
        unexpected_hash_owners = [owner for owner in private_hash_owners if owner != main_relative]
        require(
            not unexpected_hash_owners,
            "configured API hash escaped the compiled credential owner into " + ", ".join(unexpected_hash_owners),
        )

        return CredentialVerificationResult(api_id=api_id, hash_owner=main_relative)


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/Jerkgram-Build124-canary.ipa")
    expected_hash = os.environ.get("JERKGRAM_TELEGRAM_API_HASH", "")
    result = verify_ipa_credentials(ipa, expected_hash)
    print("[Build124 API IPA verify] GREEN")
    print(f"[Build124 API IPA verify] approved API ID is compiled at {result.hash_owner}; private hash value was not logged")


if __name__ == "__main__":
    main()
