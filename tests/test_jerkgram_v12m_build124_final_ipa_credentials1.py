from pathlib import Path
import importlib.util
import plistlib
import tempfile
import unittest
import zipfile


REPO = Path(__file__).resolve().parents[1]
VERIFY = REPO / "scripts" / "verify_jerkgram_build124_telegram_api_ipa1.py"
EXPECTED_API_ID = "22732185"
TEST_API_HASH = "0123456789abcdef0123456789abcdef"
OFFICIAL_API_HASH = "7245de8e747a0d6fbe11f7cc14fcc0bb"


class Build124FinalIpaCredentialTests(unittest.TestCase):
    def load_verifier(self):
        spec = importlib.util.spec_from_file_location("build124_api_ipa_verify", VERIFY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def build_ipa(
        self,
        root: Path,
        *,
        main_bytes: bytes,
        resource_bytes: bytes = b"resource",
        extension_bytes: bytes = b"extension",
    ) -> Path:
        payload = root / "payload" / "Payload"
        app = payload / "Telegram.app"
        plugins = app / "PlugIns"
        extension = plugins / "ShareExtension.appex"
        extension.mkdir(parents=True)
        (app / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "Telegram",
            "CFBundleIdentifier": "ph.telegra.Telegraph",
        }))
        (app / "Telegram").write_bytes(main_bytes)
        (app / "Build124Fixture.dat").write_bytes(resource_bytes)
        (extension / "Info.plist").write_bytes(plistlib.dumps({
            "CFBundleExecutable": "ShareExtension",
            "CFBundleIdentifier": "ph.telegra.Telegraph.Share",
        }))
        (extension / "ShareExtension").write_bytes(extension_bytes)

        ipa = root / "Build124-canary.ipa"
        with zipfile.ZipFile(ipa, "w") as archive:
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root / "payload"))
        return ipa

    def good_main(self) -> bytes:
        return (
            b"MachO-fixture\x00"
            + f"JERKGRAM_BUILD124_API_ID={EXPECTED_API_ID}".encode("ascii")
            + b"\x00"
            + TEST_API_HASH.encode("ascii")
            + b"\x00"
        )

    def test_accepts_expected_macro_derived_owner_and_hash_only_in_main_executable(self):
        module = self.load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            ipa = self.build_ipa(Path(directory), main_bytes=self.good_main())
            result = module.verify_ipa_credentials(ipa, TEST_API_HASH)
        self.assertEqual(result.api_id, EXPECTED_API_ID)
        self.assertEqual(result.hash_owner, "Payload/Telegram.app/Telegram")

    def test_rejects_wrong_or_sample_api_id_owner_marker(self):
        module = self.load_verifier()
        for api_id in ("8", "12345678", "22732184"):
            with self.subTest(api_id=api_id), tempfile.TemporaryDirectory() as directory:
                main = (
                    f"JERKGRAM_BUILD124_API_ID={api_id}\x00{TEST_API_HASH}"
                ).encode("ascii")
                ipa = self.build_ipa(Path(directory), main_bytes=main)
                with self.assertRaises(RuntimeError):
                    module.verify_ipa_credentials(ipa, TEST_API_HASH)

    def test_rejects_official_sample_hash_in_any_app_or_extension_payload(self):
        module = self.load_verifier()
        for location in ("main", "resource", "extension"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as directory:
                kwargs = {"main_bytes": self.good_main()}
                kwargs[f"{location}_bytes"] = (
                    self.good_main() + OFFICIAL_API_HASH.encode("ascii")
                    if location == "main"
                    else OFFICIAL_API_HASH.encode("ascii")
                )
                ipa = self.build_ipa(Path(directory), **kwargs)
                with self.assertRaises(RuntimeError):
                    module.verify_ipa_credentials(ipa, TEST_API_HASH)

    def test_private_hash_is_allowed_only_in_exact_main_executable_owner(self):
        module = self.load_verifier()
        for location in ("resource", "extension"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as directory:
                kwargs = {"main_bytes": self.good_main()}
                kwargs[f"{location}_bytes"] = TEST_API_HASH.encode("ascii")
                ipa = self.build_ipa(Path(directory), **kwargs)
                with self.assertRaises(RuntimeError) as raised:
                    module.verify_ipa_credentials(ipa, TEST_API_HASH)
                self.assertNotIn(TEST_API_HASH, str(raised.exception))

    def test_requires_private_hash_in_main_executable_without_echoing_it(self):
        module = self.load_verifier()
        with tempfile.TemporaryDirectory() as directory:
            main = f"JERKGRAM_BUILD124_API_ID={EXPECTED_API_ID}".encode("ascii")
            ipa = self.build_ipa(Path(directory), main_bytes=main)
            with self.assertRaises(RuntimeError) as raised:
                module.verify_ipa_credentials(ipa, TEST_API_HASH)
        self.assertNotIn(TEST_API_HASH, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
