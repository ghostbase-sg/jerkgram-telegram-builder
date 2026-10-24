#!/usr/bin/env python3
"""Check materialized owners and retain the Stable semantic verifiers."""
from pathlib import Path
import json
import subprocess
import sys
from materialize_jg13_expanded_diagnostics import verify_expanded
from materialize_jg13_portable_copy import verify_portable_copy
from configure_jg13_release_ui import verify_release_ui
from materialize_jg13_premium_icons import verify_icons
from materialize_jg13_download_boost import verify_boost
from materialize_jg13_sponsored import verify_sponsored
from materialize_jg13_profile_capture import verify_profile_capture
from materialize_jg13_stars_gift import verify_stars_gift
from materialize_jg13_history_backend import verify_backend

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
    require(f'build = "{config["build_number"]}"' in identity, "Wrong product build")
    require(f'telegramBase = "{config["upstream_new_version"]}"' in identity, "Wrong upstream display identity")
    build_owner = (SOURCE / "Telegram/BUILD").read_text()
    require(f'<key>CFBundleShortVersionString</key>\n    <string>{config["bundle_short_version"]}</string>' in build_owner, "Wrong generated bundle version owner")
    require('"1.0.2"' not in identity, "Stale product version")
    auth = (SOURCE / "submodules/TelegramApi/Sources/TLObjectSupport.swift").read_text()
    require('fieldName == "botAuthToken" ? "[REDACTED]"' in auth, "Bot token diagnostic not redacted")
    require('TLSerialize(call, &writer, true)' in auth, "API runtime serialization owner changed")
    app = (SOURCE / "submodules/TelegramUI/Sources/AppDelegate.swift").read_text()
    require("func handleDidBecomeActive()" in app and "JerkgramTelemetry.shared.applicationDidBecomeActive()" in app, "Active telemetry owner lost")
    require("func handleDidEnterBackground()" in app and "JerkgramTelemetry.shared.applicationDidEnterBackground()" in app, "Background telemetry owner lost")
    scene = (SOURCE / "submodules/TelegramUI/Sources/SceneDelegate.swift").read_text()
    require("configuration.delegateClass = SceneDelegate.self" in app, "Primary scene delegate routing lost")
    require("appDelegate?.handleDidBecomeActive()" in scene and "appDelegate?.handleDidEnterBackground()" in scene, "13.0 scene lifecycle routing lost")
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
    verify_expanded(SOURCE, final_owners=verify_release_ui(SOURCE))
    verify_portable_copy(SOURCE)
    verify_icons(SOURCE)
    verify_boost(SOURCE)
    verify_sponsored(SOURCE)
    verify_profile_capture(SOURCE)
    verify_stars_gift(SOURCE)
    verify_backend(SOURCE)
    print("Source contracts VERIFIED; NOT COMPILED / NOT RUNTIME TESTED")


if __name__ == "__main__":
    main()
