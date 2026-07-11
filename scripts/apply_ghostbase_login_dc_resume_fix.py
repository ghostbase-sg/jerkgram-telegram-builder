#!/usr/bin/env python3

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    str(ROOT / "work/swiftgram-src")
))

p = SRC / "submodules/TelegramCore/Sources/Authorization.swift"
s = p.read_text()

old = '''                        return updatedAccount.network.request(sendCode, automaticFloodWait: false)
'''

new = '''                        UserDefaults.standard.set(
                            "forcedNetworkResume:dc=\\(updatedMasterDatacenterId)",
                            forKey: "GhostBase.LOGINPROBE.Stage"
                        )
                        updatedAccount.network.shouldKeepConnection.set(.single(true))

                        return updatedAccount.network.request(sendCode, automaticFloodWait: false)
'''

if "forcedNetworkResume:dc=" not in s:
    if old not in s:
        raise SystemExit("[DC RESUME FIX] retry anchor not found")
    s = s.replace(old, new, 1)

p.write_text(s)
print("[DC RESUME FIX] OK")
