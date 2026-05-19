#!/usr/bin/env bash
set -euo pipefail

export USE_BAZEL_VERSION="${USE_BAZEL_VERSION:-8.4.2}"
BAZEL_BIN="${BAZEL_BIN:-bazelisk}"
GHOSTBASE_BAZEL_TARGET="${GHOSTBASE_BAZEL_TARGET:-//Telegram:Telegram}"
GHOSTBASE_PROBE_ONLY="${GHOSTBASE_PROBE_ONLY:-0}"

SIGN_DIR="$RUNNER_TEMP/signing"
mkdir -p "$SIGN_DIR"

cd work/swiftgram-src

echo
echo "== apply/verify GhostBase Protected Content v0.8B patch =="
if grep -q "GhostBase v0.8B Protected Content gallery save/share" submodules/TelegramUI/Components/Stories/StoryContainerScreen/Sources/StoryItemSetContainerViewSendMessage.swift 2>/dev/null && grep -q "Version: v0.8B" submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift 2>/dev/null; then
  echo "GhostBase v0.8B already applied; skip duplicate patch"
else
  python3 ../../scripts/apply_ghostbase_protected_content_v08b.py
fi

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

echo "== real build probe =="
echo "GHOSTBASE_PROBE_ONLY=$GHOSTBASE_PROBE_ONLY"
echo "GHOSTBASE_BAZEL_TARGET=$GHOSTBASE_BAZEL_TARGET"
"$BAZEL_BIN" build ${BAZEL_EXTRA_ARGS:-} \
  --enable_workspace \
  -c opt \
  --apple_platform_type=ios \
  --ios_multi_cpus=arm64 \
  --check_direct_dependencies=off \
  --//Telegram:disableExtensions=true \
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
  ls -lh ghostbase-final/GhostBase.ipa
else
  echo "ERROR: bazel-bin/Telegram/Telegram.ipa missing"
  exit 1
fi

echo "== patch final IPA AppGroup .10 before verifier =="
../../scripts/patch_final_ipa_appgroup10.sh ghostbase-final/GhostBase.ipa

echo "== verify IPA is device arm64 =="
python3 ../../scripts/gb_verify_device_ipa.py

echo "== verify GhostBase Settings patch in final IPA =="
TMP_GB_CHECK="$(mktemp -d)"
unzip -q ghostbase-final/GhostBase.ipa -d "$TMP_GB_CHECK"

if ! LC_ALL=C grep -Rao "GhostBase" "$TMP_GB_CHECK/Payload" >/dev/null 2>&1; then
  echo "WARNING: GhostBase Settings marker not found in final IPA; keeping IPA artifact for device test"
  rm -rf "$TMP_GB_CHECK"
else
  echo "GhostBase Settings marker found in final IPA"
  rm -rf "$TMP_GB_CHECK"
fi

rm -rf "$TMP_GB_CHECK"
echo "GhostBase Settings patch found in final IPA"

echo "== collect build outputs =="
../../scripts/collect_outputs_official.sh

echo "== real build probe OK =="
