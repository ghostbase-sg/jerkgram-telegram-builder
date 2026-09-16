#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
NETWORKER = ROOT / "src/lib/mtproto/networker.ts"
OLD = "device_model: initConnectionParams.deviceModel,"
NEW = "device_model: 'Jerkgram Notifications',"


def patch_networker_text(text: str) -> str:
    if NEW in text:
        if text.count(NEW) != 1:
            raise RuntimeError("[jerkgram-device-model-v05] duplicate Jerkgram device model")
        return text
    if text.count(OLD) != 1:
        raise RuntimeError("[jerkgram-device-model-v05] pinned initConnection device_model anchor changed")
    text = text.replace(OLD, NEW, 1)
    if OLD in text:
        raise RuntimeError("[jerkgram-device-model-v05] upstream device model survived")
    return text


def patch_tree(root: Path) -> None:
    target = root / "src/lib/mtproto/networker.ts"
    if not target.is_file():
        raise RuntimeError(f"[jerkgram-device-model-v05] missing {target}")
    target.write_text(patch_networker_text(target.read_text(encoding="utf-8")), encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-device-model-v05] OK")
    print("  initConnection.device_model = Jerkgram Notifications")


if __name__ == "__main__":
    main()
