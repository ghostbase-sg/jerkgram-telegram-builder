from pathlib import Path
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest

from scripts.jerkgram_public_source import (
    build_manifest,
    classify_exclusion,
    load_policy,
    safe_symlink_target,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "scripts" / "jerkgram_public_source_policy.json"


class PublicSourcePrimitiveTests(unittest.TestCase):
    def test_manifest_is_sorted_and_captures_hash_mode_size(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "z.swift").write_text("z\n", encoding="utf-8")
            a = root / "a.swift"
            a.write_text("a\n", encoding="utf-8")
            a.chmod(0o755)

            manifest = build_manifest(root)
            self.assertEqual([item["path"] for item in manifest], ["a.swift", "z.swift"])
            first = manifest[0]
            self.assertEqual(first["type"], "file")
            self.assertEqual(first["sha256"], hashlib.sha256(b"a\n").hexdigest())
            self.assertEqual(first["size"], 2)
            self.assertEqual(first["mode"], "0755")

    def test_safe_relative_symlink_is_preserved_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "dir").mkdir()
            (root / "dir" / "target.txt").write_text("ok", encoding="utf-8")
            os.symlink("target.txt", root / "dir" / "link.txt")
            self.assertEqual(safe_symlink_target(root, root / "dir" / "link.txt"), "target.txt")
            manifest = build_manifest(root)
            link = [item for item in manifest if item["path"] == "dir/link.txt"][0]
            self.assertEqual(link["type"], "symlink")
            self.assertEqual(link["target"], "target.txt")

    def test_absolute_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            os.symlink("/tmp", root / "bad")
            with self.assertRaises(ValueError):
                safe_symlink_target(root, root / "bad")

    def test_escaping_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "dir").mkdir()
            os.symlink("../../outside", root / "dir" / "bad")
            with self.assertRaises(ValueError):
                safe_symlink_target(root, root / "dir" / "bad")

    def test_exclusions_are_explicit_generated_or_vcs_state(self):
        policy = load_policy(POLICY_PATH)
        self.assertIsNotNone(classify_exclusion(Path(".git/config"), policy))
        self.assertIsNotNone(classify_exclusion(Path("submodules/X/.git"), policy))
        self.assertIsNotNone(classify_exclusion(Path("bazel-out"), policy))
        self.assertIsNotNone(classify_exclusion(Path("bazel-bin/foo"), policy))
        self.assertIsNotNone(classify_exclusion(Path("ghostbase-final/out.ipa"), policy))
        self.assertIsNotNone(classify_exclusion(Path("build-input/configuration-repository/variables.bzl"), policy))
        self.assertIsNone(classify_exclusion(Path("scripts/internal-looking.py"), policy))
        self.assertIsNone(classify_exclusion(Path("submodules/SettingsUI/Sources/GhostBase/Legacy.swift"), policy))


class PublicSourceSecretScannerTests(unittest.TestCase):
    def test_private_key_marker_fails(self):
        from scripts.jerkgram_public_source import scan_materialized_tree
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "secret.txt").write_text("-----BEGIN PRIVATE KEY-----\nabc\n", encoding="utf-8")
            findings = scan_materialized_tree(root, {})
            self.assertTrue(any("private key" in f["reason"].lower() for f in findings))

    def test_sensitive_file_extensions_fail(self):
        from scripts.jerkgram_public_source import scan_materialized_tree
        for suffix in (".p12", ".pfx", ".mobileprovision", ".key"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / ("credential" + suffix)).write_bytes(b"x")
                findings = scan_materialized_tree(root, {})
                self.assertTrue(findings)

    def test_github_token_prefix_fails(self):
        from scripts.jerkgram_public_source import scan_materialized_tree
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "x.txt").write_text("token=ghp_1234567890abcdefghijklmnop", encoding="utf-8")
            findings = scan_materialized_tree(root, {})
            self.assertTrue(findings)

    def test_exact_env_secret_value_fails_without_leaking_value(self):
        from scripts.jerkgram_public_source import scan_materialized_tree
        secret = "0123456789abcdef0123456789abcdef"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build-input").mkdir()
            (root / "build-input" / "config.txt").write_text(f"api_hash={secret}\n", encoding="utf-8")
            findings = scan_materialized_tree(root, {"JERKGRAM_TELEGRAM_API_HASH": secret})
            self.assertTrue(findings)
            self.assertNotIn(secret, json.dumps(findings))

    def test_secret_inside_excluded_build_configuration_still_fails(self):
        from scripts.jerkgram_public_source import scan_materialized_tree
        secret = "super-secret-hash-value"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = root / "build-input" / "configuration-repository"
            cfg.mkdir(parents=True)
            (cfg / "variables.bzl").write_text(f'secret = "{secret}"\n', encoding="utf-8")
            findings = scan_materialized_tree(root, {"JERKGRAM_TELEGRAM_API_HASH": secret})
            self.assertTrue(findings)


class PublicSourceExportTests(unittest.TestCase):

    def test_export_rejects_output_inside_materialized_tree(self):
        from scripts.jerkgram_public_source import export_public_tree
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            (src / "a.swift").write_text("a\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                export_public_tree(src, src / "public", load_policy(POLICY_PATH), env={})

    def test_export_rejects_materialized_root_as_output(self):
        from scripts.jerkgram_public_source import export_public_tree
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            (src / "a.swift").write_text("a\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                export_public_tree(src, src, load_policy(POLICY_PATH), env={})

    def test_export_copies_retained_files_byte_identically_and_preserves_mode_symlink(self):
        from scripts.jerkgram_public_source import export_public_tree
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "src"
            out = base / "out"
            src.mkdir()
            (src / "Telegram").mkdir()
            keep = src / "Telegram" / "main.swift"
            keep.write_bytes(b"print(\"ok\")\n")
            keep.chmod(0o755)
            (src / "scripts").mkdir()
            (src / "scripts" / "internal-looking.py").write_text("KEEP\n", encoding="utf-8")
            (src / "submodules" / "SettingsUI" / "Sources" / "GhostBase").mkdir(parents=True)
            (src / "submodules" / "SettingsUI" / "Sources" / "GhostBase" / "Legacy.swift").write_text("legacy\n", encoding="utf-8")
            (src / "ghostbase-final").mkdir()
            (src / "ghostbase-final" / "out.ipa").write_bytes(b"generated")
            (src / ".git").mkdir()
            (src / ".git" / "config").write_text("metadata", encoding="utf-8")
            os.symlink("main.swift", src / "Telegram" / "main-link.swift")

            result = export_public_tree(src, out, load_policy(POLICY_PATH), env={})
            self.assertEqual((out / "Telegram" / "main.swift").read_bytes(), b"print(\"ok\")\n")
            self.assertEqual(stat.S_IMODE((out / "Telegram" / "main.swift").stat().st_mode), 0o755)
            self.assertEqual((out / "scripts" / "internal-looking.py").read_text(), "KEEP\n")
            self.assertTrue((out / "submodules" / "SettingsUI" / "Sources" / "GhostBase" / "Legacy.swift").exists())
            self.assertFalse((out / "ghostbase-final").exists())
            self.assertFalse((out / ".git").exists())
            self.assertTrue((out / "Telegram" / "main-link.swift").is_symlink())
            self.assertEqual(os.readlink(out / "Telegram" / "main-link.swift"), "main.swift")
            self.assertTrue(any(item["path"].startswith("ghostbase-final") for item in result["excluded"]))

    def test_export_fails_before_exclusion_when_secret_is_in_excluded_path(self):
        from scripts.jerkgram_public_source import export_public_tree
        secret = "do-not-export-this-value"
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "src"
            out = base / "out"
            cfg = src / "build-input" / "configuration-repository"
            cfg.mkdir(parents=True)
            (cfg / "variables.bzl").write_text(secret, encoding="utf-8")
            with self.assertRaises(RuntimeError):
                export_public_tree(src, out, load_policy(POLICY_PATH), env={"JERKGRAM_TELEGRAM_API_HASH": secret})


class PublicSourceVerifierTests(unittest.TestCase):

    def test_excluded_bazel_symlink_may_escape_without_blocking_export(self):
        from scripts.jerkgram_public_source import export_public_tree, verify_export
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "src"
            out = base / "out"
            src.mkdir()
            (src / "Telegram.swift").write_text("ok\n", encoding="utf-8")
            os.symlink("../../external-bazel-output", src / "bazel-bin")
            policy = load_policy(POLICY_PATH)
            export_public_tree(src, out, policy, env={})
            self.assertFalse((out / "bazel-bin").exists())
            result = verify_export(src, out, policy)
            self.assertTrue(result["ok"], result["errors"])

    def _fixture(self, base: Path):
        src = base / "src"
        out = base / "out"
        src.mkdir()
        (src / "Telegram").mkdir()
        a = src / "Telegram" / "a.swift"
        a.write_text("A\n", encoding="utf-8")
        a.chmod(0o644)
        b = src / "Telegram" / "b.swift"
        b.write_text("B\n", encoding="utf-8")
        os.symlink("b.swift", src / "Telegram" / "b-link.swift")
        return src, out

    def test_verifier_accepts_exact_export(self):
        from scripts.jerkgram_public_source import export_public_tree, verify_export
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            policy = load_policy(POLICY_PATH)
            export_public_tree(src, out, policy, env={})
            result = verify_export(src, out, policy)
            self.assertTrue(result["ok"])
            self.assertEqual(result["errors"], [])

    def test_verifier_detects_missing_retained_file(self):
        from scripts.jerkgram_public_source import export_public_tree, verify_export
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            policy = load_policy(POLICY_PATH)
            export_public_tree(src, out, policy, env={})
            (out / "Telegram" / "a.swift").unlink()
            result = verify_export(src, out, policy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("missing" in e for e in result["errors"]))

    def test_verifier_detects_unexpected_file(self):
        from scripts.jerkgram_public_source import export_public_tree, verify_export
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            policy = load_policy(POLICY_PATH)
            export_public_tree(src, out, policy, env={})
            (out / "unexpected.txt").write_text("x", encoding="utf-8")
            result = verify_export(src, out, policy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("unexpected" in e for e in result["errors"]))

    def test_verifier_detects_changed_bytes_mode_and_symlink_target(self):
        from scripts.jerkgram_public_source import export_public_tree, verify_export
        with tempfile.TemporaryDirectory() as td:
            src, out = self._fixture(Path(td))
            policy = load_policy(POLICY_PATH)
            export_public_tree(src, out, policy, env={})
            (out / "Telegram" / "a.swift").write_text("CHANGED\n", encoding="utf-8")
            (out / "Telegram" / "b.swift").chmod(0o755)
            link = out / "Telegram" / "b-link.swift"
            link.unlink()
            os.symlink("a.swift", link)
            result = verify_export(src, out, policy)
            self.assertFalse(result["ok"])
            joined = "\n".join(result["errors"])
            self.assertIn("mismatch", joined)
            self.assertIn("Telegram/a.swift", joined)
            self.assertIn("Telegram/b.swift", joined)
            self.assertIn("Telegram/b-link.swift", joined)

    def test_manifest_json_writer_is_stable(self):
        from scripts.jerkgram_public_source import write_json
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "m.json"
            payload = [{"path": "b"}, {"path": "a"}]
            write_json(path, payload)
            first = path.read_bytes()
            write_json(path, payload)
            self.assertEqual(first, path.read_bytes())
            self.assertTrue(first.endswith(b"\n"))


class PublicSourceArchiveTests(unittest.TestCase):
    def test_deterministic_tar_xz_has_identical_hash_for_same_tree(self):
        from scripts.jerkgram_public_source import create_deterministic_tar_xz
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "source"
            root.mkdir()
            (root / "a.swift").write_text("A\n", encoding="utf-8")
            (root / "dir").mkdir()
            exe = root / "dir" / "tool.sh"
            exe.write_text("#!/bin/sh\n", encoding="utf-8")
            exe.chmod(0o755)
            os.symlink("a.swift", root / "link.swift")
            first = base / "one.tar.xz"
            second = base / "two.tar.xz"
            h1 = create_deterministic_tar_xz(root, first, arc_prefix="Jerkgram-1.0.0-source")
            h2 = create_deterministic_tar_xz(root, second, arc_prefix="Jerkgram-1.0.0-source")
            self.assertEqual(h1, h2)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_release_metadata_contains_only_public_provenance_and_optional_ipa(self):
        from scripts.jerkgram_public_source import write_release_metadata, sha256_path
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            archive = base / "Jerkgram-1.0.0-source.tar.xz"
            archive.write_bytes(b"archive")
            manifest = base / "public-source-manifest.json"
            manifest.write_text("[]\n", encoding="utf-8")
            ipa = base / "Jerkgram-1.0.0.ipa"
            ipa.write_bytes(b"ipa")
            out = base / "JERKGRAM_RELEASE.json"
            payload = write_release_metadata(
                out,
                version="1.0.0",
                build_number="124",
                archive_path=archive,
                public_manifest_path=manifest,
                ipa_path=ipa,
            )
            self.assertEqual(payload["jerkgramVersion"], "1.0.0")
            self.assertEqual(payload["buildNumber"], "124")
            self.assertEqual(payload["publicSourceTag"], "v1.0.0")
            self.assertEqual(payload["upstream"]["tag"], "release-12.9.2")
            self.assertEqual(payload["upstream"]["commit"], "6ad963e5b62d354da79040f388ae2b9132fb17b8")
            self.assertEqual(payload["sourceArchive"]["sha256"], sha256_path(archive))
            self.assertEqual(payload["sourceManifest"]["sha256"], sha256_path(manifest))
            self.assertEqual(payload["ipa"]["sha256"], sha256_path(ipa))
            text = out.read_text(encoding="utf-8")
            for forbidden in ("builderCommit", "ghostbase-sg", "/root/", "patch-chain"):
                self.assertNotIn(forbidden, text)


class PublicSourceCliTests(unittest.TestCase):
    def test_export_and_verify_cli_end_to_end(self):
        repo = Path(__file__).resolve().parents[1]
        exporter = repo / "scripts" / "jerkgram_export_public_source.py"
        verifier = repo / "scripts" / "verify_jerkgram_public_source.py"
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "materialized"
            src.mkdir()
            (src / "Telegram").mkdir()
            (src / "Telegram" / "App.swift").write_text("hello\n", encoding="utf-8")
            (src / "ghostbase-final").mkdir()
            (src / "ghostbase-final" / "temp.ipa").write_bytes(b"temp")
            out = base / "release"

            run = subprocess.run(
                [
                    "python3", str(exporter),
                    "--materialized-tree", str(src),
                    "--version", "1.0.0",
                    "--build-number", "124",
                    "--output", str(out),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertTrue((out / "source" / "Telegram" / "App.swift").exists())
            self.assertFalse((out / "source" / "ghostbase-final").exists())
            self.assertTrue((out / "internal-materialized-manifest.json").exists())
            self.assertTrue((out / "public-source-manifest.json").exists())
            self.assertTrue((out / "excluded-paths.json").exists())
            self.assertTrue((out / "JERKGRAM_RELEASE.json").exists())
            archive = out / "Jerkgram-1.0.0-source.tar.xz"
            self.assertTrue(archive.exists())
            self.assertTrue((out / "Jerkgram-1.0.0-source.tar.xz.sha256").exists())

            verify = subprocess.run(
                [
                    "python3", str(verifier),
                    "--materialized-tree", str(src),
                    "--export-dir", str(out),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

            (out / "source" / "Telegram" / "App.swift").write_text("mutated\n", encoding="utf-8")
            verify2 = subprocess.run(
                [
                    "python3", str(verifier),
                    "--materialized-tree", str(src),
                    "--export-dir", str(out),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(verify2.returncode, 0)
            self.assertIn("mismatch", (verify2.stdout + verify2.stderr).lower())


if __name__ == "__main__":
    unittest.main()
