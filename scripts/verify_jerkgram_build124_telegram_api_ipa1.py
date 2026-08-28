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


def bundle_executable(bundle: Path, root: Path, label: str) -> tuple[Path, str]:
    info_path = bundle / "Info.plist"
    require(info_path.is_file(), f"{label} Info.plist is missing")
    info = load_plist(info_path)
    executable_name = info.get("CFBundleExecutable")
    require(
        isinstance(executable_name, str) and executable_name,
        f"{label} CFBundleExecutable is missing",
    )
    executable = bundle / executable_name
    require(executable.is_file(), f"{label} executable is missing")
    return executable, normalized_relative(executable, root)


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
        main_executable, main_relative = bundle_executable(app, root, "main app")

        executable_owners = {main_relative}
        plugins_root = app / "PlugIns"
        if plugins_root.is_dir():
            for extension in sorted(plugins_root.glob("*.appex")):
                if not extension.is_dir():
                    continue
                _, extension_relative = bundle_executable(extension, root, extension.name)
                executable_owners.add(extension_relative)

        expected_hash_bytes = expected_hash.encode("ascii")
        private_hash_owners: set[str] = set()
        api_id_owners: dict[str, str] = {}

        for path in sorted(app.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            relative = normalized_relative(path, root)
            lowered = data.lower()

            require(OFFICIAL_API_HASH not in lowered, f"Official Telegram sample API hash remains in {relative}")

            if expected_hash_bytes in lowered:
                private_hash_owners.add(relative)

            matches = list(API_ID_OWNER_RE.finditer(data))
            if matches:
                require(len(matches) == 1, f"compiled API ID owner marker is duplicated in {relative}")
                api_id = matches[0].group(1).decode("ascii")
                require(
                    api_id == EXPECTED_API_ID,
                    f"compiled API ID owner has the wrong Build124 canary identity in {relative}",
                )
                api_id_owners[relative] = api_id

        marker_owners = set(api_id_owners)
        require(main_relative in marker_owners, "compiled API ID owner marker is missing from the main executable")
        require(main_relative in private_hash_owners, "configured API hash is missing from the main compiled credential owner")

        non_executable_markers = sorted(marker_owners - executable_owners)
        require(
            not non_executable_markers,
            "compiled API ID owner marker escaped bundle executables into " + ", ".join(non_executable_markers),
        )
        non_executable_hashes = sorted(private_hash_owners - executable_owners)
        require(
            not non_executable_hashes,
            "configured API hash escaped bundle executables into " + ", ".join(non_executable_hashes),
        )
        require(
            marker_owners == private_hash_owners,
            "compiled API ID/hash owner sets do not match",
        )

        return CredentialVerificationResult(api_id=EXPECTED_API_ID, hash_owner=main_relative)


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/Jerkgram-Build124-canary.ipa")
    expected_hash = os.environ.get("JERKGRAM_TELEGRAM_API_HASH", "")
    result = verify_ipa_credentials(ipa, expected_hash)
    print("[Build124 API IPA verify] GREEN")
    print(f"[Build124 API IPA verify] approved API ID is compiled at {result.hash_owner}; private hash value was not logged")


if __name__ == "__main__":
    main()
