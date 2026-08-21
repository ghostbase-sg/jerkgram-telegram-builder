#!/usr/bin/env bash
set -euo pipefail
GHOSTBASE_BUILDER_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export USE_BAZEL_VERSION="${USE_BAZEL_VERSION:-8.4.2}"
BAZEL_BIN="${BAZEL_BIN:-bazelisk}"
GHOSTBASE_BAZEL_TARGET="${GHOSTBASE_BAZEL_TARGET:-//Telegram:Telegram}"
GHOSTBASE_PROBE_ONLY="${GHOSTBASE_PROBE_ONLY:-0}"

SIGN_DIR="${RUNNER_TEMP:-/tmp}/signing"
mkdir -p "$SIGN_DIR"

cd work/swiftgram-src
export GHOSTBASE_SOURCE_ROOT="$PWD"

EXPECTED_TELEGRAM_COMMIT="6ad963e5b62d354da79040f388ae2b9132fb17b8"
ACTUAL_TELEGRAM_COMMIT="$(git rev-parse HEAD)"

echo "== Telegram 12.9.2 source gate =="
echo "Expected: $EXPECTED_TELEGRAM_COMMIT"
echo "Actual:   $ACTUAL_TELEGRAM_COMMIT"

if [ "$ACTUAL_TELEGRAM_COMMIT" != "$EXPECTED_TELEGRAM_COMMIT" ]; then
  echo "ERROR: build script received an unexpected Telegram source"
  false
fi

echo "== clean stale GhostBase final artifacts =="
rm -rf ghostbase-final
mkdir -p ghostbase-final

echo
echo "== apply/verify GhostBase Edit History v0.9A patch =="
if grep -q "Version: v0.9A" submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift 2>/dev/null && grep -q "GhostBase v0.9A edit history context action" submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift 2>/dev/null; then
  echo "GhostBase v0.9A already applied; skip duplicate patch"
else
  # MARK: GhostBase clean source before v0.9F.3-lite
  echo "== clean source before GhostBase patch =="
  git reset --hard HEAD
  rm -rf submodules/SettingsUI/Sources/GhostBase
  rm -f submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift
  rm -f .GHOSTBASE_KEEP_DO_NOT_DELETE
  echo "== source status before GhostBase patch =="
  git status --short | head -40

  python3 ../../scripts/apply_ghostbase_v10q_sh2_ot2_combined.py
fi

echo
echo "== apply GhostBase v1.0R settings split =="
python3 ../../scripts/apply_ghostbase_v10r_menu.py

echo
echo "== apply GhostBase v1.0S =="
python3 ../../scripts/apply_ghostbase_v10s_public_controls.py

echo
echo "== apply GhostBase v1.0S post share fix =="
python3 ../../scripts/apply_ghostbase_v10s_post_share_fix.py
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10t.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10t_style_settings.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10t_style_menu.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10t_style_runtime.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10u.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10u_style_preview.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10u_appearance.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10w_voice_cleanup.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10w_forward_official.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10w_hide_phone_settings.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10w_metadata.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10w_native_style_page.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10x_runtime_fixes.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10x_copy_peer_id.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10w_generated_source.py"

echo
echo "== apply GhostBase v1.0V =="

echo "== verify GhostBase v1.0R settings split =="
grep -nE   'GhostBase v1.0R Settings Split|GhostBaseHome|GhostBaseGhostMode|GhostBaseMessages|GhostBaseProtectedContent|GhostBaseMediaStories|GhostBaseAppearance|GhostBaseDebugResearch|GhostBaseAbout'   submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift

echo "== verify GhostBase source patch =="
grep -RInE 'case ghostbase|openSettings\(\.ghostbase\)|case \.ghostbase|GhostBase|Telegram ID|KeychainFix' \
  submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift \
  submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift \
  submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift


echo "== verify required signing secrets =="
for v in CERT_B64 PROF_B64 P12_PASSWORD KEYCHAIN_PASSWORD; do
  eval "x=\${$v:-}"
  if [ -z "$x" ]; then
    echo "::error::$v is empty or missing"
    exit 1
  fi
done
echo "CERT_B64 length: ${#CERT_B64}"
echo "PROF_B64 length: ${#PROF_B64}"

echo "== bazelisk / bazel =="
which "$BAZEL_BIN"
"$BAZEL_BIN" --version || true

echo
echo "== init bazel rule submodules =="
git submodule sync --recursive
git submodule update --init --recursive --depth 1 \
  build-system/bazel-rules/apple_support \
  build-system/bazel-rules/rules_apple \
  build-system/bazel-rules/rules_swift \
  build-system/bazel-rules/rules_xcodeproj \
  build-system/bazel-rules/sourcekit-bazel-bsp

echo
echo "== init source submodules =="
git submodule update --init --recursive --depth 1 \
  submodules/LottieCpp/lottiecpp \
  submodules/TgVoipWebrtc/tgcalls \
  submodules/rlottie/rlottie \
  third-party/dav1d/dav1d \
  third-party/libvpx/libvpx \
  third-party/td/td \
  third-party/webrtc/webrtc

echo
echo "== create build configuration repo =="
rm -rf build-input/configuration-repository
mkdir -p build-input
cp -R build-system/example-configuration build-input/configuration-repository

printf '%s\n' 'module(name = "build_configuration", version = "0.0.0")' \
  > build-input/configuration-repository/MODULE.bazel

cat >> build-input/configuration-repository/variables.bzl <<'EOF'

# Added by GhostBase builder
telegram_bazel_path = "."
telegram_use_xcode_managed_codesigning = False

# Swiftgram config placeholder for BuildConfig
sg_config = "{}"
EOF

echo
echo "== decode provisioning profile =="
PROFILE="$SIGN_DIR/Telegram.mobileprovision"
PROFILE_PLIST="$SIGN_DIR/profile.plist"

printf "%s" "$PROF_B64" | base64 -D > "$PROFILE"
security cms -D -i "$PROFILE" > "$PROFILE_PLIST"

UUID=$(/usr/libexec/PlistBuddy -c "Print UUID" "$PROFILE_PLIST")

mkdir -p "$HOME/Library/MobileDevice/Provisioning Profiles"
cp "$PROFILE" "$HOME/Library/MobileDevice/Provisioning Profiles/$UUID.mobileprovision"

cp "$PROFILE" build-input/configuration-repository/provisioning/Telegram.mobileprovision
cp "$PROFILE" build-system/example-configuration/provisioning/Telegram.mobileprovision

echo "== profile =="
wc -c "$PROFILE"
shasum -a 256 "$PROFILE"
/usr/libexec/PlistBuddy -c "Print Entitlements:application-identifier" "$PROFILE_PLIST"
/usr/libexec/PlistBuddy -c "Print Entitlements:aps-environment" "$PROFILE_PLIST"

echo
echo "== decode repack import p12 =="
ORIG="$SIGN_DIR/original.p12"
PEM="$SIGN_DIR/exported.pem"
APPLE_P12="$SIGN_DIR/apple-compatible.p12"
KEYCHAIN="$RUNNER_TEMP/gb.keychain-db"

printf "%s" "$CERT_B64" | base64 -D > "$ORIG"

openssl pkcs12 \
  -in "$ORIG" \
  -nodes \
  -passin pass:"$P12_PASSWORD" \
  -out "$PEM"

openssl pkcs12 \
  -export \
  -in "$PEM" \
  -out "$APPLE_P12" \
  -passout pass:"$P12_PASSWORD" \
  -certpbe PBE-SHA1-3DES \
  -keypbe PBE-SHA1-3DES \
  -macalg sha1

security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
security set-keychain-settings -lut 21600 "$KEYCHAIN"

security import "$APPLE_P12" \
  -k "$KEYCHAIN" \
  -P "$P12_PASSWORD" \
  -A \
  -f pkcs12

security list-keychains -d user -s "$KEYCHAIN"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN"

echo "== identities =="
security find-identity -v -p codesigning "$KEYCHAIN"

echo
echo
echo "== patch BUILD compatibility globally =="
python3 ../../scripts/gb_patch_build.py

echo
echo "== cxxopts after global patch =="
grep -RIn "cxxopts[[:space:]]*=" Telegram submodules third-party Tests 2>/dev/null || true

echo
 echo "== patch Swift compatibility =="
python3 ../../scripts/gb_patch_swift.py

echo
echo "== global forbidden source grep =="
BAD="$(
find . -type f \( \
  -name "*.swift" -o \
  -name "*.m" -o \
  -name "*.mm" -o \
  -name "*.h" -o \
  -name "*.plist" -o \
  -name "*.entitlements" -o \
  -name "*.bzl" -o \
  -name "BUILD" -o \
  -name "BUILD.bazel" -o \
  -name "*.json" \
\) \
-not -path "*/.git/*" \
-not -path "*/bazel-*/*" \
-print0 | xargs -0 grep -InE 'app\.swiftgram\.ios|group\.app\.swiftgram\.ios|group\.4a348a9b186b700c\.10|group\.\\\(baseAppBundle' || true
)"

if [ -n "$BAD" ]; then
  echo "$BAD"
  echo "ERROR: forbidden Swiftgram/AppGroup source leftovers"
  exit 1
fi

echo "global forbidden source grep OK"

echo "== verify official Telegram signing config =="
echo "-- active config --"
grep -RInE 'telegram_team_id|telegram_bundle_id|telegram_app_group' \
  build-input/configuration-repository build-system/example-configuration || true

BAD_OFFICIAL="$(
grep -RInE 'telegram_team_id = "C67CF9S4VU"|telegram_bundle_id = "ph\.telegra\.Telegraph"|C67CF9S4VU\.ph\.telegra\.Telegraph' \
  Telegram build-input/configuration-repository build-system/example-configuration 2>/dev/null || true
)"
if [ -n "$BAD_OFFICIAL" ]; then
  echo "$BAD_OFFICIAL"
  echo "ERROR: official Telegram signing config leftovers"
  exit 1
fi
echo "official Telegram signing config OK"

echo "== verify official AppGroup entitlements =="
BAD_APPGROUP="$(
grep -RInE 'group\.app\.pumpkin6584\.lion7414|group\.\{telegram_bundle_id\}' \
  Telegram build-input/configuration-repository build-system/example-configuration 2>/dev/null || true
)"
if [ -n "$BAD_APPGROUP" ]; then
  echo "$BAD_APPGROUP"
  echo "ERROR: official AppGroup entitlement leftovers"
  exit 1
fi
echo "official AppGroup entitlements OK"

echo "== verify global Swift AppGroup patch =="
if grep -RInE 'guard let baseAppBundle|let baseAppBundle[A-Za-z0-9_]*[[:space:]]*=[[:space:]]*$' Swiftgram 2>/dev/null; then
  echo "Global Swift AppGroup verification failed"
  exit 1
fi


echo
echo "== patch unsupported entitlements =="
python3 ../../scripts/gb_patch_entitlements.py

echo "== skip Swiftgram-only compile probe for official Telegram =="

echo
echo "== verify helper scripts syntax =="
python3 -m py_compile ../../scripts/gb_patch_swift.py
python3 -m py_compile ../../scripts/gb_patch_entitlements.py
python3 -m py_compile ../../scripts/gb_verify_device_ipa.py

echo "[GhostBase] Fix v1.0E Push/RegisterDevice Swift helper syntax"
python3 ../../scripts/fix_ghostbase_push_probe_swift_v10e.py

echo "== real build probe =="
echo "GHOSTBASE_PROBE_ONLY=$GHOSTBASE_PROBE_ONLY"
echo "GHOSTBASE_BAZEL_TARGET=$GHOSTBASE_BAZEL_TARGET"

echo "== apply/verify GhostBase v1.0Y final overlay =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_bot_auth_core.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_bot_login_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_bot_token_redaction.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10z_bot_login_runtime.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_multiselect_forward.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_repeated_voice.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10y_hidden_gifts_probe.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10z_hidden_gifts_core.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10z_hidden_gifts_deep_probe.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10y_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10z_hidden_gifts_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10z_bot_login_generated_source.py"

python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10za_hidden_gifts_send.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10za_hidden_gifts_self_anonymous.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10za_hidden_gifts_send_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10za_hidden_gifts_self_anonymous_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10za_bot_capability_core.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10za_bot_capability_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10za_bot_capability_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10z_scheduled_voice_lifecycle.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10za_scheduled_voice_redirect.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10z_scheduled_voice_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10za_scheduled_voice_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zb_bot_difference_probe.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zb_bot_difference_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zb_bot_difference_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zb_seasonal_gifts.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zb_seasonal_gifts_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zc_bot_inbox.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zc_bot_inbox_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10ze_botsafe1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10ze_botsafe1_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zd_profileintel1_core.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zd_profileintel1_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zd_profileintel1_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zf_botsafe2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zf_botsafe2_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zf_profileintel2_core.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zf_profileintel2_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zf_profileintel2_generated_source.py"

# MARK: GhostBase v1.0ZG Build 85 package
echo "== apply/verify GhostBase v1.0ZG Build 85 =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_accountunlock_botlogout.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_botmulti1_diagnostics.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_private_invite_probe.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_profileintel3_personal_channel.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_gifthistory1_core.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_gifthistory1_ui.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zg_profileintel2_cleanup.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_accountunlock_botlogout_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_botmulti1_diagnostics_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_private_invite_probe_generated_source.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_profileintel3_personal_channel_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_gifthistory1_core_generated_source.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_gifthistory1_ui_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zg_profileintel2_cleanup_generated_source.py"
# END MARK: GhostBase v1.0ZG Build 85 package

# MARK: GhostBase v1.0ZH Build 86 full package
echo "== apply/verify GhostBase v1.0ZH Build 86 full package =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zh_botbootstrap1_botdedupe1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zh_gifthistory2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zh_presencehistory1.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v10zh_profileui1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zh_botbootstrap1_botdedupe1_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zh_gifthistory2_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zh_presencehistory1_generated_source.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v10zh_profileui1_generated_source.py"
# END MARK: GhostBase v1.0ZH Build 86 full package

# MARK: GhostBase v1.1a Build 87 full package
echo "== apply/verify GhostBase v1.1a Build 87 full package =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11a_bot_repair_backfill.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11a_profile_hub_channel.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11a_presence_global.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11a_transcription.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11a_version.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11a_bot_repair_backfill_generated_source.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11a_profile_hub_channel_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11a_presence_global_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11a_transcription_generated_source.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11a_version_generated_source.py"
# END MARK: GhostBase v1.1a Build 87 full package

# MARK: GhostBase v1.1B integrated release
echo "== apply/verify GhostBase v1.1B integrated release =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11b_presence_global2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11b_bot_backfill3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11b_transcription2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11b_hidden_gifts1.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11b_profile_hub2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11b_presence_global2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11b_bot_backfill3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11b_transcription2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11b_hidden_gifts1.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11b_profile_hub2.py"
# END MARK: GhostBase v1.1B integrated release


# MARK: GhostBase v1.1C Stage 1 candidate

echo "== apply/verify GhostBase v1.1C Stage 1 candidate =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_glass_core1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_botstate4.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_settingsglass1.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_profileglass1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_giftsglass1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11c_version.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11c_glass_core1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11c_botstate4.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11c_settingsglass1.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11c_profileglass1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11c_giftsglass1.py"
echo "== v1.1C version verifier superseded by v1.1D =="
# END MARK: GhostBase v1.1C Stage 1 candidate

# MARK: GhostBase v1.1D reference rebuild candidate
echo "== apply/verify GhostBase v1.1D reference rebuild candidate =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_glass_core2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_botbackfill4_safe.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_settings_global2.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_profile_reference2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_gifts_glass2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11d_version.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_glass_core2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_botbackfill4_safe.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_settings_global2.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_profile_reference2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_gifts_glass2.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11d_version.py"
# END MARK: GhostBase v1.1D reference rebuild candidate

# MARK: GhostBase v1.1E audit rebuild candidate
echo "== apply/verify GhostBase v1.1E audit rebuild candidate =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11e_glass_runtime3.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11e_profile_native3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11e_bot_shadow_history1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11e_settings_gifts3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11e_version.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11e_glass_runtime3.py"
# V11F-DISABLED-OLD-PROFILE-UI: python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11e_profile_native3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11e_bot_shadow_history1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11e_settings_gifts3.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11e_version.py"
# END MARK: GhostBase v1.1E audit rebuild candidate
# MARK: GhostBase v1.1F profile header blur
echo "== apply/verify GhostBase v1.1F profile header blur =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11f_profile_header_blur1.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11f_profile_header_blur1.py"
# END MARK: GhostBase v1.1F profile header blur
# MARK: GhostBase v1.1G unified recovery
echo "== apply/verify GhostBase v1.1G unified recovery =="
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/apply_ghostbase_v11g_unified_recovery1.py"

echo "== fix GhostBase v1.1G SettingsUI dedup =="
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/fix_ghostbase_v11g_settings_dedup.py"

echo "== fix GhostBase v1.1G PeerInfo compile =="
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/fix_ghostbase_v11g_peerinfo_compile.py"
python3 "$GHOSTBASE_BUILDER_ROOT/scripts/verify_ghostbase_v11g_unified_recovery1.py"

echo "== apply GhostBase v1.1H recovery =="
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11h_recovery1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11i_profile_final1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/fix_ghostbase_v11i_profile_history_compile.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11i_profile_final1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11k_profile_polish2.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11k_profile_polish2.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11l_profile_state_animation1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11l_profile_state_animation1.py"

python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11m_runtime_core1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11m_runtime_core1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11m_animation_coexist1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11m_animation_coexist1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11m_gifts_glass1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11m_gifts_glass1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11m_music_player_glass1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11m_music_player_glass1.py"

python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11n_profile_core_final1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11n_profile_core_final1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11o_visual_reset1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11o_visual_reset1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11p_full_correction1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11p_full_correction1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11q_full_runtime_correction1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11q_full_runtime_correction1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11r_runtime_polish1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11r_runtime_polish1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11s_runtime_recovery1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11s_runtime_recovery1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11t_build105_full1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11t_build105_full1.py"

# GhostBase v1.1U / Build106
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11u_build106_final1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11u_build106_final1_generated_source.py"

# GhostBase v1.1V / Build107
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_ghostbase_v11v_build107_quoteemoji_stickerfallback1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_ghostbase_v11v_build107_quoteemoji_stickerfallback1.py"

python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_jerkgram_v11w_build108_foundation1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_jerkgram_v11w_build108_foundation1.py"

python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_jerkgram_v11x_build109_foundation_hotfix1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_jerkgram_v11x_build109_foundation_hotfix1.py"

python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/apply_jerkgram_v11y_build110_icons_ui_recovery_polish1.py"
python3 "${GHOSTBASE_BUILDER_ROOT}/scripts/verify_jerkgram_v11y_build110_icons_ui_recovery_polish1.py"

echo "== Jerkgram v1.1Z Build111: native Glass Composer + UI fixes =="
python3 ../../scripts/apply_jerkgram_v11z_build111_glass_composer_ui_fix1.py
python3 ../../scripts/verify_jerkgram_v11z_build111_glass_composer_ui_fix1.py
python3 ../../scripts/apply_jerkgram_v12a_build112_composer_alternates_extensions1.py
python3 ../../scripts/verify_jerkgram_v12a_build112_composer_alternates_extensions1.py
# END MARK: GhostBase v1.1G unified recovery
"$BAZEL_BIN" build ${BAZEL_EXTRA_ARGS:-} \
  --enable_workspace \
  -c opt \
  --apple_platform_type=ios \
  --ios_multi_cpus=arm64 \
  --check_direct_dependencies=off \
  --//Telegram:disableExtensions=false \
  --//Telegram:disableProvisioningProfiles=true \
  "$GHOSTBASE_BAZEL_TARGET"

echo
echo

if [ "${GHOSTBASE_PROBE_ONLY:-0}" = "1" ]; then
  echo "== probe-only build OK =="
  exit 0
fi

echo
echo "== save IPA before verifier =="
mkdir -p ghostbase-final
if [ -f bazel-bin/Telegram/Telegram.ipa ]; then
  cp -f bazel-bin/Telegram/Telegram.ipa ghostbase-final/GhostBase.ipa
  echo "IPA=bazel-bin/Telegram/Telegram.ipa" > ghostbase-final/info.txt
  echo "Final=ghostbase-final/GhostBase.ipa" >> ghostbase-final/info.txt
  TELEGRAM_VERSION="$(python3 -c 'import json; print(json.load(open("versions.json"))["app"])')"
  TELEGRAM_COMMIT="$(git rev-parse HEAD)"
  TELEGRAM_TAG="$(git tag --points-at HEAD | head -n 1)"
  echo "TelegramVersion=$TELEGRAM_VERSION" >> ghostbase-final/info.txt
  echo "TelegramCommit=$TELEGRAM_COMMIT" >> ghostbase-final/info.txt
  echo "TelegramTag=$TELEGRAM_TAG" >> ghostbase-final/info.txt
  cat ghostbase-final/info.txt
  ls -lh ghostbase-final/GhostBase.ipa
else
  echo "ERROR: bazel-bin/Telegram/Telegram.ipa missing"
  exit 1
fi

echo "== patch final IPA AppGroup .10 before verifier =="
../../scripts/patch_final_ipa_appgroup10.sh ghostbase-final/GhostBase.ipa

echo "== strict GhostBase final IPA marker gate =="
TMP_GB_CHECK="$(mktemp -d)"
unzip -q "ghostbase-final/GhostBase.ipa" -d "$TMP_GB_CHECK"

echo "-- detected GhostBase markers --"




LC_ALL=C grep -RaoE "Version: v1\.1G-unified-recovery|SH1 Share Scheduled Send|GhostBase\.SH1\.ShareScheduledIntercept|OT1 Timer Media Local Keep|GhostBase\.OT1\.OutgoingKeepBlocked" "$TMP_GB_CHECK/Payload" 2>/dev/null | sort -u | sed -n '1,160p' || true

echo "-- verify Version: v1.1G-unified-recovery --"
if ! LC_ALL=C grep -Rao "Version: v1.1G-unified-recovery" "$TMP_GB_CHECK/Payload" >/dev/null 2>&1; then
  echo "::error::Final IPA does not contain Version: v1.1G-unified-recovery"
  exit 1
fi


echo "-- verify SH1 marker --"
if ! LC_ALL=C grep -Rao "SH1 Share Scheduled Send" "$TMP_GB_CHECK/Payload" >/dev/null 2>&1; then
  echo "::error::Final IPA does not contain SH1 marker"
  exit 1
fi

echo "-- verify OT1 marker --"
if ! LC_ALL=C grep -Rao "OT1 Timer Media Local Keep" "$TMP_GB_CHECK/Payload" >/dev/null 2>&1; then
  echo "::error::Final IPA does not contain OT1 marker"
  exit 1
fi


echo "== strict GhostBase final IPA marker gate OK =="


echo
echo "== publish final IPA with ph.telegra.Telegraph =="
python3 ../../scripts/gb_public_bundle_id_final.py \
  ghostbase-final/GhostBase.ipa

echo
echo "== finalize JerkGram display name =="
python3 ../../scripts/jerkgram_finalize_display_name.py \
  ghostbase-final/GhostBase.ipa

echo
echo "== verify Build109 final JerkGram IPA =="
python3 ../../scripts/verify_jerkgram_v11x_build109_final_ipa.py \
  ghostbase-final/GhostBase.ipa

echo "== finalize Build110 display name: Jerkgram =="
python3 ../../scripts/jerkgram_finalize_display_name_build110.py ghostbase-final/GhostBase.ipa

echo "== finalize Build112 native Composer alternate registration =="
python3 ../../scripts/jerkgram_finalize_composer_alternates_build112.py \
  ghostbase-final/GhostBase.ipa

echo "== verify Jerkgram Build112 final IPA: Composer alternates + Official extensions =="
python3 ../../scripts/verify_jerkgram_v12a_build112_final_ipa.py \
  ghostbase-final/GhostBase.ipa
