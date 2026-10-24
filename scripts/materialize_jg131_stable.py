"""Reconstruct the reviewed 13.1.1 port while retaining the historical Stable patch."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def reviewed_stable_patch():
    manifest = json.loads((ROOT / "patches/jg131-stable-port.sha256.json").read_text())
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    if manifest["upstream_sha"] != config["upstream_new_sha"]:
        raise RuntimeError("Stable port upstream changed")
    original = (ROOT / "patches/jg13-stable.product.patch").read_bytes()
    delta = ROOT / "patches/jg131-stable-port.delta"
    if hashlib.sha256(original).hexdigest() != manifest["original_patch_sha256"] or hashlib.sha256(delta.read_bytes()).hexdigest() != manifest["port_delta_sha256"]:
        raise RuntimeError("Stable port input changed")
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        target = temp / "patches/jg13-stable.product.patch"
        target.parent.mkdir()
        target.write_bytes(original)
        subprocess.run(["git", "init", "-q", str(temp)], check=True)
        subprocess.run(["git", "apply", "--whitespace=nowarn", str(delta)], cwd=temp, check=True)
        result = target.read_bytes()
    if hashlib.sha256(result).hexdigest() != manifest["effective_patch_sha256"]:
        raise RuntimeError("Stable port output changed")
    output = ROOT / "work/jg131-reviewed-stable.patch"
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(result)
    return output
