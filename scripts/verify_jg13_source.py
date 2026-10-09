#!/usr/bin/env python3
"""Check materialized owners and retain the Stable semantic verifiers."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/swiftgram-src"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    config = json.loads((ROOT / "jerkgram-migration.json").read_text())
    manifest = json.loads((ROOT / "patches/jg13-stable.product.sha256.json").read_text())
    for name in manifest:
        if name.endswith(".swift"):
            text = (SOURCE / name).read_text()
            require("<<<<<<< " not in text and ">>>>>>> " not in text, f"Unresolved owner: {name}")
    identity = (SOURCE / "submodules/TelegramPresentationData/Sources/JerkgramStrings.swift").read_text()
    require(f'displayVersion = "{config["product_display_version"]}"' in identity, "Wrong display version")
    require(f'technicalVersion = "{config["product_technical_version"]}"' in identity, "Wrong telemetry version")
    require('"1.0.2"' not in identity, "Stale product version")
    auth = (SOURCE / "submodules/TelegramApi/Sources/Api43.swift").read_text()
    require('("botAuthToken", ConstructorParameterDescription("[REDACTED]"))' in auth, "Bot token diagnostic not redacted")
    require('serializeString(botAuthToken, buffer: buffer, boxed: false)' in auth, "Bot login wire token lost")
    app = (SOURCE / "submodules/TelegramUI/Sources/AppDelegate.swift").read_text()
    require("func handleDidBecomeActive()" in app and "JerkgramTelemetry.shared.applicationDidBecomeActive()" in app, "Active telemetry owner lost")
    require("func handleDidEnterBackground()" in app and "JerkgramTelemetry.shared.applicationDidEnterBackground()" in app, "Background telemetry owner lost")
    require("setupAccountManager(" in app and "resetWalletLocalSecrets()" in app, "13.0 secure AccountManager owner lost")
    for name in [
        "verify_jg13_v12t_build133_blocked_reactions1.py",
        "verify_jg13_v12u_build133_blocked_activity1.py",
        "verify_jg13_v12v_build133_settings1.py",
        "verify_jg13_v12w_build133_music_overlay1.py",
        "verify_jg13_v12zc_build136_visible_order_cache1.py",
        "verify_jg13_v12zd_build137_performance1.py",
        "verify_jg13_build137_performance2.py",
    ]:
        subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=SOURCE, check=True)
    print("Source contracts VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")


if __name__ == "__main__":
    main()
