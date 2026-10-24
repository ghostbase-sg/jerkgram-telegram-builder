"""Select the existing ListView backend without changing message/layout implementations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "patches/jg13-history-backend.sha256.json"

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def manifest():
    m = json.loads(MANIFEST.read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    parent = json.loads((ROOT / "patches/jg13-expanded-diagnostics.sha256.json").read_text())
    if m["upstream_sha"] != config["upstream_new_sha"] or m["before_sha256"] != parent["owners"][m["owner"]]["after_sha256"]:
        raise RuntimeError("History backend reviewed parent/pin changed")
    return m

def transform(text):
    m = manifest()
    if digest(text) != m["before_sha256"] or text.count(m["old"]) != 1:
        raise RuntimeError("History backend requires the exact preceding owner")
    updated = text.replace(m["old"], m["new"], 1)
    if digest(updated) != m["after_sha256"]:
        raise RuntimeError("History backend output changed")
    return updated

def restore(text):
    m = manifest()
    if digest(text) != m["after_sha256"] or text.count(m["new"]) != 1:
        raise RuntimeError("History backend final owner changed")
    parent = text.replace(m["new"], m["old"], 1)
    if digest(parent) != m["before_sha256"]:
        raise RuntimeError("History backend original bytes lost")
    return parent

def preceding_owner(name, text):
    m = manifest()
    if name == m["owner"] and digest(text) == m["after_sha256"]:
        return restore(text)
    return text

def verify_backend(source):
    m = manifest()
    restore((Path(source) / m["owner"]).read_text())
    return {m["owner"]: {"after_sha256": m["after_sha256"]}}

def apply_backend(source):
    m = manifest()
    target = Path(source) / m["owner"]
    updated = transform(target.read_text())
    target.write_text(updated)
    verify_backend(source)
