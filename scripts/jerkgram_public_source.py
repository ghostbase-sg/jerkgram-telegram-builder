from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


def load_policy(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def classify_exclusion(relpath: Path, policy: dict[str, Any]) -> dict[str, str] | None:
    parts = relpath.parts
    rel = relpath.as_posix().strip("/")
    for rule in policy.get("exclude", []):
        kind = rule["kind"]
        value = rule["value"].strip("/")
        if kind == "segment" and value in parts:
            return rule
        if kind == "root-prefix" and parts and parts[0].startswith(value):
            return rule
        if kind == "root-path" and parts and parts[0] == value:
            return rule
        if kind == "prefix" and (rel == value or rel.startswith(value + "/")):
            return rule
    return None


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def safe_symlink_target(root: Path, path: Path) -> str:
    root = root.resolve()
    raw = os.readlink(path)
    if os.path.isabs(raw):
        raise ValueError(f"absolute symlink is not allowed: {path}")
    resolved = (path.parent / raw).resolve(strict=False)
    if not _is_within(root, resolved):
        raise ValueError(f"symlink escapes materialized tree: {path}")
    return raw


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root: Path, policy: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    root = root.resolve()
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        mode = f"{stat.S_IMODE(st.st_mode):04o}"
        if stat.S_ISLNK(st.st_mode):
            rule = classify_exclusion(path.relative_to(root), policy) if policy is not None else None
            target = os.readlink(path) if rule is not None else safe_symlink_target(root, path)
            entries.append({
                "path": rel,
                "type": "symlink",
                "mode": mode,
                "size": len(target.encode("utf-8")),
                "target": target,
            })
        elif stat.S_ISREG(st.st_mode):
            entries.append({
                "path": rel,
                "type": "file",
                "mode": mode,
                "size": st.st_size,
                "sha256": _sha256_file(path),
            })
    return entries


SENSITIVE_ENV_NAMES = (
    "JERKGRAM_TELEGRAM_API_ID",
    "JERKGRAM_TELEGRAM_API_HASH",
    "P12_PASSWORD",
    "KEYCHAIN_PASSWORD",
    "CERT_B64",
    "PROF_B64",
)
SENSITIVE_SUFFIXES = {".p12", ".pfx", ".mobileprovision", ".key"}
PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
)
TOKEN_PREFIXES = (
    b"ghp_", b"github_pat_", b"gho_", b"ghu_", b"ghs_", b"ghr_",
)


def scan_materialized_tree(root: Path, env) -> list[dict[str, str]]:
    root = Path(root).resolve()
    findings: list[dict[str, str]] = []
    exact_values = {
        name: str(env.get(name, ""))
        for name in SENSITIVE_ENV_NAMES
        if str(env.get(name, "")).strip()
    }
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        try:
            st = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(st.st_mode):
            # Symlink safety is handled separately; do not follow links while scanning.
            continue
        if not stat.S_ISREG(st.st_mode):
            continue
        if path.suffix.lower() in SENSITIVE_SUFFIXES:
            findings.append({"path": rel, "reason": f"sensitive file type {path.suffix.lower()}"})
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if any(marker in data for marker in PRIVATE_KEY_MARKERS):
            findings.append({"path": rel, "reason": "private key material"})
        if any(prefix in data for prefix in TOKEN_PREFIXES):
            findings.append({"path": rel, "reason": "GitHub/private token-like value"})
        for name, value in exact_values.items():
            encoded = value.encode("utf-8", errors="ignore")
            if encoded and encoded in data:
                findings.append({"path": rel, "reason": f"matches protected environment value {name}"})
    return findings


def export_public_tree(materialized_root: Path, public_root: Path, policy: dict[str, Any], env=None) -> dict[str, Any]:
    materialized_root = Path(materialized_root).resolve()
    public_root = Path(public_root).resolve()
    if public_root == materialized_root or _is_within(materialized_root, public_root):
        raise ValueError("public export root must be outside the materialized source tree")
    env = os.environ if env is None else env

    findings = scan_materialized_tree(materialized_root, env)
    if findings:
        summary = "; ".join(f"{f['path']}: {f['reason']}" for f in findings[:20])
        raise RuntimeError(f"public source export blocked by sensitive material: {summary}")

    if public_root.exists():
        import shutil
        shutil.rmtree(public_root)
    public_root.mkdir(parents=True, exist_ok=True)

    excluded: list[dict[str, str]] = []
    for path in sorted(materialized_root.rglob("*"), key=lambda p: p.relative_to(materialized_root).as_posix()):
        rel = path.relative_to(materialized_root)
        rule = classify_exclusion(rel, policy)
        if rule is not None:
            excluded.append({"path": rel.as_posix(), "reason": rule["reason"]})
            continue
        st = path.lstat()
        dest = public_root / rel
        if stat.S_ISDIR(st.st_mode):
            dest.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(dest, stat.S_IMODE(st.st_mode))
            except OSError:
                pass
        elif stat.S_ISLNK(st.st_mode):
            target = safe_symlink_target(materialized_root, path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, dest)
        elif stat.S_ISREG(st.st_mode):
            import shutil
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest, follow_symlinks=False)
            os.chmod(dest, stat.S_IMODE(st.st_mode))
    return {"excluded": excluded}


def write_json(path: Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def verify_export(materialized_root: Path, public_root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    internal = build_manifest(materialized_root, policy=policy)
    public = build_manifest(public_root)
    expected_entries = {
        item["path"]: item
        for item in internal
        if classify_exclusion(Path(item["path"]), policy) is None
    }
    public_entries = {item["path"]: item for item in public}
    errors: list[str] = []

    missing = sorted(set(expected_entries) - set(public_entries))
    unexpected = sorted(set(public_entries) - set(expected_entries))
    errors.extend(f"missing retained path: {path}" for path in missing)
    errors.extend(f"unexpected public path: {path}" for path in unexpected)

    for path in sorted(set(expected_entries) & set(public_entries)):
        expected = expected_entries[path]
        actual = public_entries[path]
        if expected != actual:
            errors.append(f"manifest mismatch: {path}")

    return {
        "ok": not errors,
        "errors": errors,
        "internal_manifest": internal,
        "public_manifest": public,
    }


UPSTREAM_REPOSITORY = "TelegramMessenger/Telegram-iOS"
UPSTREAM_TAG = "release-12.9.2"
UPSTREAM_COMMIT = "6ad963e5b62d354da79040f388ae2b9132fb17b8"


def sha256_path(path: Path) -> str:
    return _sha256_file(Path(path))


def _normalize_tarinfo(info):
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.pax_headers = {}
    return info


def create_deterministic_tar_xz(public_root: Path, archive_path: Path, arc_prefix: str) -> str:
    import tarfile

    public_root = Path(public_root).resolve()
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    paths = [public_root] + sorted(
        public_root.rglob("*"), key=lambda p: p.relative_to(public_root).as_posix()
    )
    with tarfile.open(archive_path, mode="w:xz", format=tarfile.GNU_FORMAT) as tar:
        for path in paths:
            if path == public_root:
                arcname = arc_prefix
            else:
                arcname = f"{arc_prefix}/{path.relative_to(public_root).as_posix()}"
            st = path.lstat()
            if stat.S_ISLNK(st.st_mode):
                safe_symlink_target(public_root, path)
            info = tar.gettarinfo(str(path), arcname=arcname)
            info = _normalize_tarinfo(info)
            if info.isfile():
                with path.open("rb") as f:
                    tar.addfile(info, f)
            else:
                tar.addfile(info)
    return sha256_path(archive_path)


def write_release_metadata(
    output_path: Path,
    *,
    version: str,
    build_number: str,
    archive_path: Path,
    public_manifest_path: Path,
    ipa_path: Path | None = None,
    source_tag: str | None = None,
) -> dict[str, Any]:
    archive_path = Path(archive_path)
    public_manifest_path = Path(public_manifest_path)
    payload: dict[str, Any] = {
        "schemaVersion": 1,
        "jerkgramVersion": str(version),
        "buildNumber": str(build_number),
        "publicSourceTag": source_tag or f"v{version}",
        "upstream": {
            "repository": UPSTREAM_REPOSITORY,
            "tag": UPSTREAM_TAG,
            "commit": UPSTREAM_COMMIT,
        },
        "sourceArchive": {
            "filename": archive_path.name,
            "sha256": sha256_path(archive_path),
        },
        "sourceManifest": {
            "filename": public_manifest_path.name,
            "sha256": sha256_path(public_manifest_path),
        },
        "ipa": None,
    }
    if ipa_path is not None:
        ipa_path = Path(ipa_path)
        payload["ipa"] = {
            "filename": ipa_path.name,
            "sha256": sha256_path(ipa_path),
        }
    write_json(output_path, payload)
    return payload
